#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rclone_mirror.py — Miroir incremental d'un dossier via rclone (remplace robocopy /MIR).

rclone `sync` ne transfere que les deltas et fonctionne aussi bien vers une cible LOCALE
(disque externe) que DISTANTE (remote rclone deja configure : SFTP, S3, WebDAV...).
Aucun chemin/hote code en dur.

Exemples :
  # miroir local -> disque externe
  python rclone_mirror.py --src /chemin/data --dst /mnt/backup/data

  # miroir local -> remote rclone (nom au choix, ex. "monremote")
  python rclone_mirror.py --src /chemin/data --dst "monremote:/backups/data"

Options : --dry (simulation, aucune ecriture), --transfers N, --delete-excluded.
"""
import argparse
import shutil
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser(description="Miroir incremental via rclone sync.")
    ap.add_argument("--src", required=True, help="Source (dossier local ou remote:chemin).")
    ap.add_argument("--dst", required=True, help="Destination (dossier local ou remote:chemin).")
    ap.add_argument("--rclone", default=shutil.which("rclone") or "rclone", help="Chemin de l'executable rclone.")
    ap.add_argument("--transfers", type=int, default=16, help="Nombre de transferts paralleles.")
    ap.add_argument("--dry", action="store_true", help="Simulation (--dry-run).")
    ap.add_argument("--exclude", action="append", default=[], help="Motif d'exclusion (repetable).")
    args = ap.parse_args()

    cmd = [args.rclone, "sync", args.src, args.dst,
           "--transfers", str(args.transfers), "--fast-list", "--progress"]
    for pat in args.exclude:
        cmd += ["--exclude", pat]
    if args.dry:
        cmd.append("--dry-run")
    print("RUN:", " ".join(cmd))
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
