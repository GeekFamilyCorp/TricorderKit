#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""restic_backup.py — Sauvegarde dedupliquee a snapshots (restic), generique et parametree.

Remplace un miroir type robocopy /MIR : restic ne rescanne pas tout, il compare via son index,
deduplique et versionne (snapshots). Fonctionne sur un depot LOCAL (disque externe) ou DISTANT
via le backend rclone (SFTP, S3, etc.) — sans dependre de ssh.exe sur Windows.

Aucun chemin, hote ou secret n'est code en dur : tout passe par arguments/variables d'env.

Exemples :
  # depot local sur disque externe
  python restic_backup.py --source /chemin/vers/data --repo /mnt/backup/mon-repo \
      --password-file ~/.secrets/restic-pass

  # depot distant via un remote rclone deja configure (nom au choix, ex. "monremote")
  python restic_backup.py --source /chemin/vers/data --repo "rclone:monremote:/backups/mon-repo" \
      --password-file ~/.secrets/restic-pass

Actions : init | backup (defaut, auto-init) | snapshots.
Le mot de passe vient de --password-file, ou RESTIC_PASSWORD_FILE / RESTIC_PASSWORD.
"""
import argparse
import os
import shutil
import subprocess
import sys


def build_env(args):
    env = dict(os.environ)
    env["RESTIC_REPOSITORY"] = args.repo
    if args.password_file:
        env["RESTIC_PASSWORD_FILE"] = args.password_file
    if args.repo.startswith("rclone:") and args.rclone_program:
        env["PATH"] = os.path.dirname(args.rclone_program) + os.pathsep + env.get("PATH", "")
    return env


def run(restic, env, extra):
    return subprocess.run([restic] + extra, env=env, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser(description="Sauvegarde restic dedupliquee (local ou rclone).")
    ap.add_argument("action", nargs="?", default="backup",
                    choices=["init", "backup", "snapshots", "forget", "check"])
    ap.add_argument("--source", help="Dossier a sauvegarder (requis pour backup).")
    ap.add_argument("--repo", required=True, help="Depot restic : chemin local ou 'rclone:REMOTE:/chemin'.")
    ap.add_argument("--password-file", help="Fichier contenant le mot de passe du depot.")
    ap.add_argument("--restic", default=shutil.which("restic") or "restic", help="Chemin de l'executable restic.")
    ap.add_argument("--rclone-program", help="Chemin de rclone si depot rclone et rclone hors PATH.")
    ap.add_argument("--tag", default="auto", help="Tag du snapshot.")
    ap.add_argument("--exclude", action="append", default=[], help="Motif d'exclusion (repetable).")
    # Retention (action forget) : conserve N snapshots par fenetre, puis prune l'espace.
    ap.add_argument("--keep-last", type=int, default=0, help="Garde les N derniers snapshots.")
    ap.add_argument("--keep-daily", type=int, default=0, help="Garde N snapshots quotidiens.")
    ap.add_argument("--keep-weekly", type=int, default=0, help="Garde N snapshots hebdomadaires.")
    ap.add_argument("--keep-monthly", type=int, default=0, help="Garde N snapshots mensuels.")
    ap.add_argument("--prune", action="store_true", help="Libere l'espace des snapshots oublies (forget).")
    args = ap.parse_args()

    env = build_env(args)
    restic = args.restic

    if args.action == "snapshots":
        r = run(restic, env, ["snapshots"])
        sys.stdout.write(r.stdout + r.stderr)
        return r.returncode

    if args.action == "check":
        r = run(restic, env, ["check"])
        sys.stdout.write(r.stdout + r.stderr)
        return r.returncode

    if args.action == "forget":
        keep = []
        for name, val in (("last", args.keep_last), ("daily", args.keep_daily),
                          ("weekly", args.keep_weekly), ("monthly", args.keep_monthly)):
            if val:
                keep += ["--keep-" + name, str(val)]
        if not keep:
            ap.error("forget requiert au moins un --keep-* (last/daily/weekly/monthly).")
        extra = ["forget"] + keep
        if args.prune:
            extra.append("--prune")
        r = run(restic, env, extra)
        sys.stdout.write(r.stdout + r.stderr)
        return r.returncode

    if run(restic, env, ["cat", "config"]).returncode != 0:
        r = run(restic, env, ["init"])
        sys.stdout.write("[init] " + (r.stdout + r.stderr).strip() + "\n")
        if r.returncode != 0:
            return r.returncode
    if args.action == "init":
        return 0

    if not args.source:
        ap.error("--source est requis pour l'action backup")
    extra = ["backup", args.source, "--tag", args.tag]
    for pat in args.exclude:
        extra += ["--exclude", pat]
    r = run(restic, env, extra)
    sys.stdout.write(r.stdout + r.stderr)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
