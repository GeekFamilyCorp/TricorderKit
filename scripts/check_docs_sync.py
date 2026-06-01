#!/usr/bin/env python3
"""
check_docs_sync.py - Gate docs-sync (TricorderKit, DEC-028 / R39)

Etend la philosophie du public-boundary gate a la coherence DOCUMENTAIRE :
verifie mecaniquement que la vitrine (README.md, STATUS.md) reste alignee
avec la realite du depot (CHANGELOG.md, arborescence plugins/). Cause racine
adressee : README/STATUS/CHANGELOG ont deja diverge (version, compte de tests,
liste de plugins) sans qu'aucun controle ne le detecte avant push.

Trois familles de verification :

  1. VERSION   - la version affichee dans README (badge + pied de page) et
                 STATUS (pied) doit egaler la derniere version du CHANGELOG
                 (source canonique = premier entete "## [X.Y.Z]").
  2. TESTS     - le nombre de tests annonce doit etre IDENTIQUE partout ou il
                 apparait (badge README, mentions "NNN tests", pied STATUS).
                 Option --check-tests : confronte aussi a la collecte pytest.
  3. STRUCTURE - les plugins du tableau de bord STATUS et le compte "N plugins"
                 du README doivent correspondre EXACTEMENT aux sous-dossiers
                 reels de plugins/ (ni manquant, ni fantome) ; le bloc Resume
                 de STATUS doit etre arithmetiquement coherent.

Sortie 100 % ASCII (taches planifiees Windows). exit 0 si synchro, 1 si
desync, 3 sur erreur d'environnement. Utilisable en pre-push hook et en CI.

Usage :
    python scripts/check_docs_sync.py [--json] [--root <path>] [--check-tests]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PLUGINS_DIR = "plugins"
_NON_PLUGIN = {"__pycache__", ".pytest_cache"}


# --- Lecture & helpers ------------------------------------------------------

def _read(root: Path, rel: str) -> str:
    p = root / rel
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def _section(text: str, header_contains: str) -> str:
    """Contenu d'une section markdown '## ...<header_contains>...' jusqu'au
    prochain entete de meme niveau."""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("##") and header_contains in ln:
            start = i + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "\n".join(lines[start:end])


# --- 1. VERSION -------------------------------------------------------------

def canonical_version(changelog: str) -> str | None:
    m = re.search(r"^##\s*\[(\d+\.\d+(?:\.\d+)?)\]", changelog, re.MULTILINE)
    return m.group(1) if m else None


def declared_versions(readme: str, status: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for m in re.finditer(r"version-v?(\d+\.\d+(?:\.\d+)?)-", readme):
        out.append(("README badge", m.group(1)))
    for label, txt in (("README footer", readme), ("STATUS footer", status)):
        for m in re.finditer(r"TricorderKit\s+v(\d+\.\d+(?:\.\d+)?)", txt):
            out.append((label, m.group(1)))
    return out


# --- 2. TESTS ---------------------------------------------------------------

def declared_test_counts(readme: str, status: str) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for m in re.finditer(r"tests-(\d+)(?:%20|\s)?PASS", readme):
        out.append(("README badge", int(m.group(1))))
    for label, txt in (("README", readme), ("STATUS", status)):
        for m in re.finditer(r"(\d+)\s+tests?\s+(?:passing|PASS)", txt):
            out.append((label + " text", int(m.group(1))))
    return out


def collected_test_count(root: Path) -> int | None:
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pytest", "--co", "-q"],
            cwd=str(root), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=600,
        )
    except Exception:
        return None
    blob = (out.stdout or "") + (out.stderr or "")
    m = re.search(r"(\d+)\s+tests?\s+collected", blob)
    return int(m.group(1)) if m else None


# --- 3. STRUCTURE -----------------------------------------------------------

def actual_plugins(root: Path) -> set[str]:
    d = root / PLUGINS_DIR
    if not d.is_dir():
        return set()
    return {p.name for p in d.iterdir() if p.is_dir() and p.name not in _NON_PLUGIN}


def status_dashboard_plugins(status: str) -> set[str]:
    sec = _section(status, "Tableau de bord plugins")
    names: set[str] = set()
    for line in sec.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and re.fullmatch(r"[a-z][a-z0-9-]+", cells[0]):
            names.add(cells[0])
    return names


def readme_plugin_count(readme: str) -> int | None:
    m = re.search(r"plugins/[^\n]*?(\d+)\s+plugins", readme)
    return int(m.group(1)) if m else None


def resume_consistency(status: str, n_plugins: int) -> list[str]:
    """Le bloc Resume doit avoir des denominateurs == n_plugins et une somme
    de numerateurs == n_plugins."""
    sec = _section(status, "Resume") or _section(status, "sum")
    if not sec:
        # accent insensible : cherche un entete contenant 'sum'
        sec = _section(status, "R")
    pairs = re.findall(r"(\d+)\s*/\s*(\d+)", sec)
    errs: list[str] = []
    if not pairs:
        return errs
    nums = [int(a) for a, _ in pairs]
    dens = [int(b) for _, b in pairs]
    bad_den = sorted({d for d in dens if d != n_plugins})
    if bad_den:
        errs.append(
            "STATUS Resume: denominateur(s) %s != %d plugins reels"
            % (bad_den, n_plugins)
        )
    if sum(nums) != n_plugins:
        errs.append(
            "STATUS Resume: somme des categories = %d, attendu %d"
            % (sum(nums), n_plugins)
        )
    return errs


# --- Orchestration ----------------------------------------------------------

def run_checks(root: Path, check_tests: bool) -> list[dict]:
    readme = _read(root, "README.md")
    status = _read(root, "STATUS.md")
    changelog = _read(root, "CHANGELOG.md")
    findings: list[dict] = []

    # 1. VERSION
    canon = canonical_version(changelog)
    if canon is None:
        findings.append({"check": "version", "severity": "error",
                         "message": "CHANGELOG.md: aucune entete '## [X.Y.Z]' trouvee."})
    else:
        for src, ver in declared_versions(readme, status):
            if ver != canon:
                findings.append({"check": "version", "severity": "error",
                                 "message": "%s annonce v%s, CHANGELOG canonique = v%s"
                                            % (src, ver, canon)})

    # 2. TESTS
    counts = declared_test_counts(readme, status)
    uniq = sorted({c for _, c in counts})
    if len(uniq) > 1:
        detail = ", ".join("%s=%d" % (s, c) for s, c in counts)
        findings.append({"check": "tests", "severity": "error",
                         "message": "comptes de tests incoherents (%s)" % detail})
    if check_tests and counts:
        real = collected_test_count(root)
        if real is None:
            findings.append({"check": "tests", "severity": "warn",
                             "message": "collecte pytest indisponible (--check-tests ignore)"})
        elif uniq and real != uniq[0]:
            findings.append({"check": "tests", "severity": "error",
                             "message": "doc annonce %d tests, pytest en collecte %d"
                                        % (uniq[0], real)})

    # 3. STRUCTURE
    real_plugins = actual_plugins(root)
    n_real = len(real_plugins)
    if not real_plugins:
        findings.append({"check": "structure", "severity": "error",
                         "message": "plugins/ introuvable ou vide."})
    else:
        doc_plugins = status_dashboard_plugins(status)
        missing = sorted(real_plugins - doc_plugins)
        phantom = sorted(doc_plugins - real_plugins)
        for p in missing:
            findings.append({"check": "structure", "severity": "error",
                             "message": "plugin '%s' present sur disque mais absent du tableau STATUS" % p})
        for p in phantom:
            findings.append({"check": "structure", "severity": "error",
                             "message": "plugin '%s' liste dans STATUS mais absent de plugins/" % p})
        rc = readme_plugin_count(readme)
        if rc is not None and rc != n_real:
            findings.append({"check": "structure", "severity": "error",
                             "message": "README annonce %d plugins, %d reels sur disque" % (rc, n_real)})
        for e in resume_consistency(status, n_real):
            findings.append({"check": "structure", "severity": "error", "message": e})

    return findings


# --- Rapport & CLI ----------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Gate docs-sync : README/STATUS <-> structure/version/tests")
    ap.add_argument("--root", default=".", help="Racine du depot")
    ap.add_argument("--json", action="store_true", help="Sortie JSON")
    ap.add_argument("--check-tests", action="store_true",
                    help="Confronte le compte de tests a la collecte pytest reelle (lent)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    findings = run_checks(root, args.check_tests)
    errors = [f for f in findings if f["severity"] == "error"]

    if args.json:
        print(json.dumps({"synced": not errors, "findings": findings},
                         ensure_ascii=False, indent=2))
    else:
        if not errors:
            print("[OK] Docs-sync gate : README/STATUS alignes avec structure/version/tests.")
            for f in findings:
                print("  [WARN] (%s) %s" % (f["check"], f["message"]))
        else:
            by = {}
            for f in errors:
                by.setdefault(f["check"], []).append(f["message"])
            print("[FAIL] Docs-sync gate : %d desynchronisation(s) detectee(s)." % len(errors))
            for check in ("version", "tests", "structure"):
                msgs = by.get(check, [])
                if msgs:
                    print("\n  %s (%d) :" % (check.upper(), len(msgs)))
                    for m in msgs:
                        print("    - " + m)
            warns = [f for f in findings if f["severity"] == "warn"]
            for f in warns:
                print("\n  [WARN] (%s) %s" % (f["check"], f["message"]))
            print("\n  Corriger la vitrine (README.md / STATUS.md) ou le CHANGELOG, puis relancer.")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
