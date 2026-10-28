#!/usr/bin/env python3
"""
janitor.py — Garbage collection / archivage à froid (G4, fichier 06 §1).

Exécute la règle DÉJÀ ÉCRITE dans `claude-vault/60_ARCHIVE/ARCHIVE_INDEX.md` :
les Daily Logs / notes traitées de plus de N jours sont marquées `status: archived`
puis déplacées vers `60_ARCHIVE/Processed/`. Ne supprime jamais (« toujours archiver »).

DRY-RUN PAR DÉFAUT : sans `--apply`, le script ne fait que lister ce qu'il ferait.
La compression en embeddings (vecteurs Qdrant) est branchée plus tard via G3.

Usage :
    python3 janitor.py --vault /chemin/claude-vault                 # dry-run
    python3 janitor.py --vault /chemin/claude-vault --days 90       # seuil
    python3 janitor.py --vault /chemin/claude-vault --apply         # exécute
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

DEFAULT_DAYS = 90
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def parse_note_date(path: Path) -> dt.date | None:
    """Date depuis le nom (Daily Log YYYY-MM-DD) sinon mtime du fichier."""
    m = DATE_RE.search(path.stem)
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    try:
        return dt.date.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return None


def already_archived(path: Path) -> bool:
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:400]
    except OSError:
        return True
    return "status: archived" in head


def collect(vault: Path, days: int) -> list[Path]:
    """Notes candidates à l'archivage : Daily Logs + Processed inbox > seuil."""
    cutoff = dt.date.today() - dt.timedelta(days=days)
    scopes = [vault / "10_INBOX" / "Daily_Logs"]
    found: list[Path] = []
    for scope in scopes:
        if not scope.is_dir():
            continue
        for note in scope.rglob("*.md"):
            d = parse_note_date(note)
            if d and d < cutoff and not already_archived(note):
                found.append(note)
    return sorted(found)


def archive(note: Path, vault: Path, apply: bool) -> str:
    dest_dir = vault / "60_ARCHIVE" / "Processed"
    dest = dest_dir / note.name
    if not apply:
        return f"DRY-RUN  {note.relative_to(vault)}  ->  60_ARCHIVE/Processed/{note.name}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.date.today().isoformat()
    txt = note.read_text(encoding="utf-8", errors="ignore")
    if txt.startswith("---"):
        txt = txt.replace("---", f"---\nstatus: archived\narchived_on: {stamp}", 1)
    else:
        txt = f"---\nstatus: archived\narchived_on: {stamp}\n---\n\n" + txt
    note.write_text(txt, encoding="utf-8")
    shutil.move(str(note), str(dest))
    return f"ARCHIVED {note.name}  ->  60_ARCHIVE/Processed/"


def main() -> int:
    ap = argparse.ArgumentParser(description="Janitor cold-archive (G4).")
    ap.add_argument("--vault", required=True, help="Racine du claude-vault")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Seuil d'ancienneté (def: 90)")
    ap.add_argument("--apply", action="store_true", help="Exécute (sinon dry-run)")
    args = ap.parse_args()

    vault = Path(args.vault)
    if not vault.is_dir():
        sys.exit(f"[janitor] vault introuvable : {vault}")

    candidates = collect(vault, args.days)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[janitor] {mode} · seuil {args.days} j · {len(candidates)} note(s) candidate(s)")
    for note in candidates:
        print("  " + archive(note, vault, args.apply))
    if not candidates:
        print("  (rien à archiver)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
