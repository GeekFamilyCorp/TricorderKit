#!/usr/bin/env python3
"""
check_public_boundary.py - Gate anti-fuite avant push public (TricorderKit)

Cause racine corrigee (2026-06-01, DEC-026) : le checker d'anonymisation
existait mais n'etait jamais execute avant push, scannait tout l'arbre de
travail (faux positifs sur fichiers non suivis) et plantait sous Windows
(emoji cp1252). Ce gate :

  1. ne scanne QUE les fichiers SUIVIS par git (git ls-files) -> ce qui sera
     reellement pousse, pas les brouillons locaux ;
  2. detecte deux classes de fuite :
       - termes prives -> jamais ecrits en clair ici : empreintes SHA-256
         (plugins/security-audit-cli/private_terms.py) + TK_PRIVATE_TERMS
         + configs/local/private_terms.txt (non suivi). Cherches dans le
         CONTENU et dans le CHEMIN des fichiers (nom de dossier/fichier).
         Bloquant SAUF fichier liste dans .check-anon-ignore ;
       - chemins personnels absolus (C:\\Users\\<nom-reel>\\, /home/<nom>/,
         /Users/<nom>/) -> TOUJOURS bloquant, jamais whiteliste ;
  3. sortie 100 % ASCII (pas d'emoji) -> fonctionne en tache planifiee Windows ;
  4. exit 0 si propre, exit 1 si fuite -> utilisable en pre-push hook et en CI.

Durcissement 2026-10-27 (cause racine de la fuite constatee) : l'ancienne
version ne connaissait que 3 graphies exactes, ne regardait pas les chemins,
et .check-anon-ignore exemptait ~60 motifs (dont des dossiers entiers comme
cowork-scheduled-tasks/*, reports/*, docs/0x). Les graphies voisines
(espace, underscore, mot colle), les noms de dossiers et tout ce qui etait
whiteliste passaient donc sans alerte.

Usage :
    python scripts/check_public_boundary.py [--json] [--root <path>]
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins" / "security-audit-cli"))
from private_terms import find_terms, load_digests  # noqa: E402

# Chemins personnels absolus. Le segment utilisateur ne doit pas etre un
# placeholder (<user>, <username>, <nom>, ...). Toujours bloquant.
PERSONAL_PATH_PATTERNS = [
    re.compile(r"C:\\Users\\(?!<)[^\\/<>\r\n\"']+", re.IGNORECASE),
    re.compile(r"/home/(?!<)[A-Za-z0-9._-]+/"),
    re.compile(r"/Users/(?!<)[A-Za-z0-9._-]+/"),
]

# Donnees sensibles infra : IP tailnet (<TAILNET_CIDR>/10), hostnames VPS, emails reels.
# Bloquant SAUF fichier whiteliste (.check-anon-ignore) -- ex. la def du gate / docs anonymisation.
ALLOWED_EMAIL_DOMAINS = {"example.com", "example.org", "example.net"}
SENSITIVE_PATTERNS = [
    ("tailnet_ip", re.compile(r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b")),
    ("vps_hostname", re.compile(r"\b[A-Za-z0-9.-]+\.hstgr\.cloud\b", re.IGNORECASE)),
    ("real_email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    # IPv4 publique en dur (ex. IP VPS) -> bloquant. Les plages privees/reservees
    # (RFC1918, loopback, link-local, doc, CGNAT/tailnet, multicast) sont ecartees
    # par _is_private_or_reserved_ipv4 ci-dessous pour eviter les faux positifs.
    ("public_ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


def _is_private_or_reserved_ipv4(val: str) -> bool:
    """True si l'IPv4 n'est PAS une adresse publique routable (a ignorer)."""
    parts = val.split(".")
    if len(parts) != 4:
        return True
    try:
        a, b, c, d = (int(p) for p in parts)
    except ValueError:
        return True
    if any(x < 0 or x > 255 for x in (a, b, c, d)):
        return True  # pas une IPv4 valide -> ignorer
    if a == 10:
        return True                                   # 10/8 prive
    if a == 172 and 16 <= b <= 31:
        return True                                   # 172.16/12 prive
    if a == 192 and b == 168:
        return True                                   # 192.168/16 prive
    if a == 127:
        return True                                   # loopback
    if a == 169 and b == 254:
        return True                                   # link-local
    if a == 100 and 64 <= b <= 127:
        return True                                   # CGNAT/tailnet (deja couvert)
    if a == 0 or a >= 224:
        return True                                   # this-network / multicast / reserve
    if a == 192 and b == 0 and c == 2:
        return True                                   # TEST-NET-1 (doc)
    if a == 198 and b == 51 and c == 100:
        return True                                   # TEST-NET-2 (doc)
    if a == 203 and b == 0 and c == 113:
        return True                                   # TEST-NET-3 (doc)
    return False

# Fichiers qui DEFINISSENT les motifs (les contiennent volontairement) -> exempts du scan sensible.
SENSITIVE_EXEMPT = {
    "scripts/check_public_boundary.py",
    "docs/anonymization.md",
    "plugins/security-audit-cli/anonymization_checker.py",
}

IGNORE_FILE = ".check-anon-ignore"

_BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".pdf",
    ".zip", ".tar", ".gz", ".7z", ".sqlite", ".db", ".bin", ".exe",
    ".dll", ".so", ".whl", ".pyc", ".pyo", ".lock",
}


def load_ignore(root: Path) -> list[str]:
    p = root / IGNORE_FILE
    if not p.exists():
        return []
    return [
        ln.strip()
        for ln in p.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]


def is_ignored(rel: str, name: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(name, pat):
            return True
    return False


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=str(root), capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode != 0:
        print("[check_public_boundary] git ls-files a echoue", file=sys.stderr)
        sys.exit(3)
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def scan(root: Path) -> list[dict]:
    ignore = load_ignore(root)
    digests = load_digests(root)
    findings: list[dict] = []

    for rel in tracked_files(root):
        fpath = root / rel
        if fpath.suffix.lower() in _BINARY_EXT:
            continue
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            continue

        name = Path(rel).name
        ignored = is_ignored(rel.replace("\\", "/"), name, ignore)

        # Le chemin lui-meme peut trahir un terme prive (ex. dossier poc_<nom>)
        if not ignored:
            for label in find_terms(rel.replace("\\", "/"), digests):
                findings.append({
                    "file": rel, "line": 0, "kind": "private_term",
                    "match": label, "content": "(chemin du fichier)",
                })

        for n, line in enumerate(content.splitlines(), start=1):
            # Chemins personnels : TOUJOURS bloquant (jamais whiteliste)
            for pp in PERSONAL_PATH_PATTERNS:
                m = pp.search(line)
                if m:
                    findings.append({
                        "file": rel, "line": n, "kind": "personal_path",
                        "match": m.group(0)[:80], "content": line.strip()[:120],
                    })
            # Termes prives : bloquant sauf fichier whiteliste
            if not ignored:
                for label in find_terms(line, digests):
                    findings.append({
                        "file": rel, "line": n, "kind": "private_term",
                        # jamais le terme ni la ligne en clair : la sortie CI est publique
                        "match": label, "content": "(masque)",
                    })
            # Donnees sensibles infra (IP tailnet, hostname VPS, email reel) :
            # TOUJOURS bloquant (traverse la whitelist), sauf fichiers de definition.
            if rel.replace("\\", "/") not in SENSITIVE_EXEMPT:
                for kind, rx in SENSITIVE_PATTERNS:
                    m = rx.search(line)
                    if not m:
                        continue
                    val = m.group(0)
                    if kind == "real_email":
                        dom = val.rsplit("@", 1)[-1].lower()
                        if dom in ALLOWED_EMAIL_DOMAINS or any(
                            dom.endswith("." + d) for d in ALLOWED_EMAIL_DOMAINS
                        ):
                            continue
                    if kind == "public_ipv4" and _is_private_or_reserved_ipv4(val):
                        continue
                    findings.append({
                        "file": rel, "line": n, "kind": kind,
                        "match": val[:80], "content": line.strip()[:120],
                    })
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Gate anti-fuite avant push public")
    ap.add_argument("--root", default=".", help="Racine du depot")
    ap.add_argument("--json", action="store_true", help="Sortie JSON")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    findings = scan(root)

    if args.json:
        print(json.dumps({"clean": not findings, "findings": findings},
                         ensure_ascii=False, indent=2))
    else:
        if not findings:
            print("[OK] Public boundary gate : aucune fuite dans les fichiers suivis.")
        else:
            paths = [f for f in findings if f["kind"] == "personal_path"]
            terms = [f for f in findings if f["kind"] == "private_term"]
            print(f"[FAIL] Public boundary gate : {len(findings)} fuite(s) detectee(s).")
            if paths:
                print(f"\n  Chemins personnels ({len(paths)}) -- TOUJOURS bloquant :")
                for f in paths[:20]:
                    print(f"    {f['file']}:{f['line']}  ->  {f['match']}")
            if terms:
                print(f"\n  Termes prives hors whitelist ({len(terms)}) :")
                for f in terms[:20]:
                    print(f"    {f['file']}:{f['line']}  ->  {f['match']}")
            sens = [f for f in findings if f["kind"] not in ("personal_path", "private_term")]
            if sens:
                print(f"\n  Donnees sensibles infra ({len(sens)}) :")
                for f in sens[:20]:
                    print(f"    {f['file']}:{f['line']}  ->  {f['match']}  ({f['kind']})")
            print("\n  Corriger, ou whitelister un fichier LEGITIME dans .check-anon-ignore.")
            print("  (Les chemins personnels ne sont jamais whitelistables.)")

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
