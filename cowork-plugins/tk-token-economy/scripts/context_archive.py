#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
context_archive.py - Archive datée d'un contexte avant compression (skill context-compress).

Copie un fichier (le contexte complet, exporté en markdown) vers
~/.tk-token-economy/context-archive/<AAAAMMJJ-HHMMSS>_<nom>.md pour permettre un rollback.
Ne fait rien d'autre : pas de compression, pas de suppression (NO-DROP).

Usage:
    python3 context_archive.py <fichier>            # archive et affiche le chemin créé
    python3 context_archive.py --stdin --name x     # archive le contenu lu sur stdin
    python3 context_archive.py --list               # liste les archives existantes
"""

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ARCHIVE_DIR = Path.home() / ".tk-token-economy" / "context-archive"


def archive_path(name):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name) or "contexte"
    if not safe.endswith(".md"):
        safe += ".md"
    return ARCHIVE_DIR / f"{stamp}_{safe}"


def main():
    ap = argparse.ArgumentParser(description="Archive datée d'un contexte (copie simple).")
    ap.add_argument("source", nargs="?", help="fichier à archiver")
    ap.add_argument("--stdin", action="store_true", help="lire le contenu sur stdin")
    ap.add_argument("--name", default=None, help="nom logique (avec --stdin)")
    ap.add_argument("--list", action="store_true", help="lister les archives")
    args = ap.parse_args()

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    if args.list:
        files = sorted(ARCHIVE_DIR.glob("*.md"))
        if not files:
            print("Aucune archive.")
        for f in files:
            print(f"{f.name}\t{f.stat().st_size} o")
        return 0

    if args.stdin:
        content = sys.stdin.read()
        if not content.strip():
            print("stdin vide : rien archivé.", file=sys.stderr)
            return 1
        dest = archive_path(args.name or "contexte")
        dest.write_text(content, encoding="utf-8")
    elif args.source:
        src = Path(args.source)
        if not src.is_file():
            print(f"Fichier introuvable : {src}", file=sys.stderr)
            return 1
        dest = archive_path(args.name or src.name)
        shutil.copy2(src, dest)
    else:
        ap.error("fournir un fichier, --stdin ou --list")

    # R71 : 0 seulement si l'effet annoncé a eu lieu
    if not dest.is_file() or dest.stat().st_size == 0:
        print("Archive non écrite.", file=sys.stderr)
        return 1
    print(str(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
