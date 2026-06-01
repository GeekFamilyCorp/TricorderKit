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
       - termes prives (Japan-Alliance, MangaTracker, mangatracker-cli)
         -> bloquant SAUF si le fichier est liste dans .check-anon-ignore ;
       - chemins personnels absolus (C:\\Users\\<nom-reel>\\, /home/<nom>/,
         /Users/<nom>/) -> TOUJOURS bloquant, jamais whiteliste ;
  3. sortie 100 % ASCII (pas d'emoji) -> fonctionne en tache planifiee Windows ;
  4. exit 0 si propre, exit 1 si fuite -> utilisable en pre-push hook et en CI.

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

PRIVATE_TERMS = ["Japan-Alliance", "MangaTracker", "mangatracker-cli"]

# Chemins personnels absolus. Le segment utilisateur ne doit pas etre un
# placeholder (<user>, <username>, <nom>, ...). Toujours bloquant.
PERSONAL_PATH_PATTERNS = [
    re.compile(r"C:\\Users\\(?!<)[^\\/<>\r\n\"']+", re.IGNORECASE),
    re.compile(r"/home/(?!<)[A-Za-z0-9._-]+/"),
    re.compile(r"/Users/(?!<)[A-Za-z0-9._-]+/"),
]

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
    term_res = [(t, re.compile(re.escape(t), re.IGNORECASE)) for t in PRIVATE_TERMS]
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
                for term, rx in term_res:
                    if rx.search(line):
                        findings.append({
                            "file": rel, "line": n, "kind": "private_term",
                            "match": term, "content": line.strip()[:120],
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
            print("\n  Corriger, ou whitelister un fichier LEGITIME dans .check-anon-ignore.")
            print("  (Les chemins personnels ne sont jamais whitelistables.)")

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
