#!/usr/bin/env python3
"""check_static.py — contrôles déterministes, hors LLM, sur un ou plusieurs SKILL.md.

Bibliothèque standard uniquement (pas de PyYAML : le frontmatter est parsé à la main,
sur le sous-ensemble YAML réellement utilisé par nos skills).

Contrôles (ERREUR = fait échouer, AVERTISSEMENT = signalé seulement) :
  FM-KEYS      clés de frontmatter hors {name, description, license, allowed-tools,
               metadata, compatibility}  (disable-model-invocation → avertissement, exception
               documentée des skills manuels)
  FM-NAME      name absent, non kebab-case, ou différent du nom du dossier
  DESC-LEN     description absente ou > 1024 caractères ; chevrons interdits
  DESC-EXCL    description sans « ne pas utiliser pour » / renvoi → (avertissement)
  BODY-LEN     corps (hors frontmatter) > 500 lignes
  PATH-SESSION chemin de session en dur  /sessions/<id>  (le motif /sessions/* est toléré)
  PATH-WIN     chemin personnel Windows  C:\\Users\\…
  IP           adresse IPv4 en dur
  MODEL-VER    nom de modèle versionné (claude-…-4-5, opus-4, sonnet-4.5, haiku-3, …)
  REF-SKILL    renvoi « → skill » vers un skill absent de la liste fournie
  CHANGELOG    section Changelog absente

Usage :
  check_static.py SKILL.md [SKILL.md …] [--known-skills a,b,plugin:c] [--scan-root DIR …]
                  [--ignore-refs a,b] [--json] [--strict]
  --known-skills   liste explicite (séparateur virgule) ; les formes « plugin:skill » et
                   « skill » sont acceptées
  --scan-root      racine(s) à parcourir pour découvrir les skills existants
                   (*/skills/*/SKILL.md, */SKILL.md, skills/*/SKILL.md)
  --strict         les avertissements comptent comme des erreurs
  --json           sortie machine (une entrée par fichier)
Code retour : 0 si aucune erreur, 1 sinon, 2 si un fichier est illisible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
TOLERATED_KEYS = {"disable-model-invocation"}  # valide Claude Code/Cowork, refusé par quick_validate
MAX_DESC = 1024
MAX_BODY_LINES = 500

RE_SESSION_PATH = re.compile(r"/sessions/(?!\*)[A-Za-z0-9_-]+")
RE_WIN_PATH = re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE)
RE_IP = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?!\.?\d)")
RE_MODEL_VER = re.compile(
    r"(?i)\b("
    r"claude-(?:[a-z]+-)*\d(?:[-.]\d+)*"        # claude-opus-4-5, claude-3-5-sonnet, claude-sonnet-5
    r"|(?:opus|sonnet|haiku|fable)[-_ ]?\d(?:[.-]\d+)*"  # opus-4, sonnet 4.5, haiku3
    r")\b"
)
# renvoi « → skill », « (→ plugin:skill) », « → `skill` ».
# Groupes : 1 = parenthèse ouvrante éventuelle, 2 = backtick, 3 = token, 4 = caractère suivant.
RE_ARROW_REF = re.compile(r"(\(?)\s*(?:→|->)\s*(`?)([a-z0-9][a-z0-9:_-]*)`?(.?)")
# tokens fréquents après une flèche de séquence, jamais des skills
ARROW_STOPLIST = {"fast", "default", "deep", "plan-gate", "t1", "t2", "t3", "go", "stop"}
RE_CHANGELOG = re.compile(r"^#{1,6}\s+.*changelog", re.IGNORECASE | re.MULTILINE)
RE_KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# --------------------------------------------------------------------------- frontmatter
def split_frontmatter(text: str) -> tuple[list[str] | None, str]:
    """Retourne (lignes du frontmatter, corps). frontmatter=None si absent."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:])
    return None, text


def parse_frontmatter(fm_lines: list[str]) -> dict:
    """Parseur YAML minimal : clés de niveau 0, scalaires (quoted ou non), blocs > | >- |-,
    et un niveau d'imbrication (metadata:). Suffisant pour nos SKILL.md."""
    data: dict = {}
    i = 0
    n = len(fm_lines)
    while i < n:
        line = fm_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line.startswith((" ", "\t")):
            i += 1  # ligne imbriquée orpheline : ignorée
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, value = m.group(1), m.group(2).strip()
        if value in (">", "|", ">-", "|-", ">+", "|+"):
            block: list[str] = []
            i += 1
            while i < n and (fm_lines[i].startswith((" ", "\t")) or not fm_lines[i].strip()):
                block.append(fm_lines[i].strip())
                i += 1
            joiner = " " if value.startswith(">") else "\n"
            data[key] = joiner.join(b for b in block if b)
            continue
        if value == "":
            nested: dict = {}
            i += 1
            while i < n and (fm_lines[i].startswith((" ", "\t")) or not fm_lines[i].strip()):
                sub = fm_lines[i].strip()
                sm = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", sub)
                if sm:
                    nested[sm.group(1)] = unquote(sm.group(2).strip())
                i += 1
            data[key] = nested
            continue
        data[key] = unquote(value)
        i += 1
    return data


def unquote(v: str) -> str:
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


# --------------------------------------------------------------------------- known skills
def discover_skills(roots: list[str]) -> set[str]:
    found: set[str] = set()
    for root in roots:
        r = Path(root)
        if not r.is_dir():
            continue
        for p in list(r.glob("*/skills/*/SKILL.md")) + list(r.glob("skills/*/SKILL.md")) + list(r.glob("*/SKILL.md")) + list(r.glob("*/*/SKILL.md")):
            found.add(p.parent.name)
            fm, _ = split_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            if fm:
                name = parse_frontmatter(fm).get("name")
                if isinstance(name, str) and name:
                    found.add(name)
    return found


def normalize_known(items: set[str]) -> set[str]:
    out: set[str] = set()
    for it in items:
        it = it.strip()
        if not it:
            continue
        out.add(it)
        if ":" in it:
            out.add(it.split(":", 1)[1])
    return out


# --------------------------------------------------------------------------- checks
def check_file(path: Path, known: set[str], strict: bool, ignore_refs: set[str] | None = None) -> dict:
    ignore_refs = ignore_refs or set()
    result = {"file": str(path), "errors": [], "warnings": [], "stats": {}}
    err, warn = result["errors"], result["warnings"]
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        err.append(f"IO: {e}")
        return result

    fm_lines, body = split_frontmatter(text)
    if fm_lines is None:
        err.append("FM-MISSING: frontmatter YAML absent ou non fermé")
        fm = {}
    else:
        fm = parse_frontmatter(fm_lines)

    # clés
    for k in fm:
        if k in ALLOWED_KEYS:
            continue
        if k in TOLERATED_KEYS:
            warn.append(f"FM-KEYS: clé `{k}` tolérée (skill manuel) mais refusée par quick_validate.py")
        else:
            err.append(f"FM-KEYS: clé `{k}` interdite (autorisées : {', '.join(sorted(ALLOWED_KEYS))})")

    # name
    name = fm.get("name")
    if not isinstance(name, str) or not name:
        err.append("FM-NAME: `name` absent")
    else:
        if not RE_KEBAB.match(name):
            err.append(f"FM-NAME: `{name}` n'est pas en kebab-case")
        if len(name) > 64:
            err.append(f"FM-NAME: `{name}` > 64 caractères")
        if path.parent.name != name:
            warn.append(f"FM-NAME: `{name}` ≠ nom du dossier `{path.parent.name}`")

    # description
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        err.append("DESC-LEN: `description` absente")
        desc = ""
    else:
        desc = desc.strip()
        result["stats"]["description_chars"] = len(desc)
        if len(desc) > MAX_DESC:
            err.append(f"DESC-LEN: description = {len(desc)} caractères (> {MAX_DESC})")
        if "<" in desc or ">" in desc:
            err.append("DESC-LEN: chevrons < > interdits dans la description")
        low = desc.lower()
        if "ne pas utiliser" not in low and "ne pas activer" not in low and "→" not in desc:
            warn.append("DESC-EXCL: description sans exclusion « Ne pas utiliser pour → X »")

    # corps
    body_lines = body.count("\n") + (1 if body and not body.endswith("\n") else 0)
    result["stats"]["body_lines"] = body_lines
    if body_lines > MAX_BODY_LINES:
        err.append(f"BODY-LEN: corps = {body_lines} lignes (> {MAX_BODY_LINES})")

    # chemins / IP / modèles — sur tout le fichier
    for m in RE_SESSION_PATH.finditer(text):
        err.append(f"PATH-SESSION: chemin de session en dur `{m.group(0)}` (ligne {line_of(text, m.start())})")
    for m in RE_WIN_PATH.finditer(text):
        err.append(f"PATH-WIN: chemin personnel `{m.group(0)}…` (ligne {line_of(text, m.start())})")
    for m in RE_IP.finditer(text):
        ip = m.group(0)
        if ip.startswith("127.") or ip in ("0.0.0.0",):
            continue  # loopback : la stack locale est en 127.0.0.1 par conception, pas une fuite
        if all(0 <= int(o) <= 255 for o in ip.split(".")):
            err.append(f"IP: adresse `{ip}` en dur (ligne {line_of(text, m.start())})")
    for m in RE_MODEL_VER.finditer(text):
        err.append(f"MODEL-VER: nom de modèle versionné `{m.group(0)}` (ligne {line_of(text, m.start())}) — utiliser un alias de models.json")

    # renvois → skill
    refs_checked = 0
    for m in RE_ARROW_REF.finditer(text):
        paren, tick, token, nxt = m.group(1), m.group(2), m.group(3), m.group(4)
        bare = token.split(":", 1)[1] if ":" in token else token
        if "_" in token or token in ARROW_STOPLIST or token in ignore_refs or bare in ignore_refs:
            continue
        if nxt and (nxt.isalpha() or nxt.isdigit()):
            continue  # token tronqué (accent, chiffre) : ce n'est pas un nom de skill
        after = text[m.end():m.end() + 1]
        if nxt in ("/", ".") and after and (after.isalnum() or after == "_"):
            continue  # chemin ou nom de fichier (references/x.md, inventory.sh)
        if bare.isdigit() or bare == name:
            continue
        kebab = ("-" in bare) or (":" in token)
        explicit = bool(tick) or bool(paren)          # « → `x` » ou « (→ x) »
        if not kebab and not explicit:
            continue
        refs_checked += 1
        if known and token not in known and bare not in known:
            msg = (f"REF-SKILL: renvoi `→ {token}` vers un skill inconnu (ligne {line_of(text, m.start())})"
                   " — corriger le renvoi, ou --ignore-refs si ce n'est pas un skill")
            # kebab-case ou (→ x) : erreur ; simple mot entre backticks : avertissement (peut être un champ)
            (err if (kebab or paren) else warn).append(msg)
    result["stats"]["arrow_refs"] = refs_checked
    if not known and refs_checked:
        warn.append(f"REF-SKILL: {refs_checked} renvoi(s) non vérifié(s) — passer --known-skills ou --scan-root")

    # changelog
    if not RE_CHANGELOG.search(body):
        err.append("CHANGELOG: aucune section `## Changelog`")

    if strict and warn:
        err.extend(f"(strict) {w}" for w in warn)
    return result


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


# --------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="SKILL.md ou dossiers de skill")
    ap.add_argument("--known-skills", default="", help="liste séparée par des virgules")
    ap.add_argument("--scan-root", action="append", default=[], help="racine(s) à parcourir pour découvrir les skills")
    ap.add_argument("--ignore-refs", default="", help="renvois → à ignorer (noms de tâches, d'outils…), séparés par des virgules")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)

    known = normalize_known(set(args.known_skills.split(",")))
    known |= normalize_known(discover_skills(args.scan_root))

    paths: list[Path] = []
    for f in args.files:
        p = Path(f)
        paths.append(p / "SKILL.md" if p.is_dir() else p)

    ignore_refs = {x.strip() for x in args.ignore_refs.split(",") if x.strip()}
    results = [check_file(p, known, args.strict, ignore_refs) for p in paths]

    if args.json:
        print(json.dumps({"known_skills": sorted(known), "results": results}, ensure_ascii=False, indent=2))
    else:
        total_err = 0
        for r in results:
            st = r["stats"]
            status = "OK " if not r["errors"] else "KO "
            print(f"[{status}] {r['file']}  (desc={st.get('description_chars', '?')} car., corps={st.get('body_lines', '?')} l., renvois={st.get('arrow_refs', 0)})")
            for e in r["errors"]:
                print(f"    ERREUR  {e}")
            for w in r["warnings"]:
                print(f"    AVERT   {w}")
            total_err += len(r["errors"])
        ok = sum(1 for r in results if not r["errors"])
        print(f"\n{ok}/{len(results)} fichier(s) sans erreur — {total_err} erreur(s), "
              f"{sum(len(r['warnings']) for r in results)} avertissement(s) ; skills connus : {len(known)}")

    if any("IO:" in e for r in results for e in r["errors"]):
        return 2
    return 0 if all(not r["errors"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
