#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pack_plugin.py — assemble un plugin Cowork (.plugin) a partir d'un ou plusieurs skills.

Pourquoi : depuis DEC-055, un ENSEMBLE de skills se distribue/installe comme PLUGIN dedie
(pas skill par skill). Ce packageur produit un .plugin conforme (zip a separateurs '/',
contrairement a Compress-Archive Windows qui met des '\' non conformes -> installeur en echec).

Usage :
  python tools/pack_plugin.py --name mon-plugin --out ./dist \\
      --desc "Description" --author GeekFamilyCorp \\
      --skill skills/god-mode --skill skills/code-corrector [...]

Produit ./dist/mon-plugin.plugin avec :
  .claude-plugin/plugin.json
  skills/<nom>/...   (copie de chaque dossier de skill passe en --skill)

GARDE-FOU R37 : ne JAMAIS empaqueter un skill privé (qui nomme la stack) dans un plugin
destiné au repo public. Plugins publics = skills generiques ; plugins prives = depot prive (vault / repo prive).
"""
import argparse
import json
import os
import shutil
import tempfile
import zipfile


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble un plugin Cowork (.plugin) depuis des skills.")
    ap.add_argument("--name", required=True, help="nom du plugin (kebab-case)")
    ap.add_argument("--out", required=True, help="dossier de sortie")
    ap.add_argument("--desc", default="", help="description du plugin")
    ap.add_argument("--author", default="GeekFamilyCorp")
    ap.add_argument("--version", default="0.1.0")
    ap.add_argument("--skill", action="append", default=[], metavar="DIR",
                    help="dossier d'un skill (repetable) ; doit contenir SKILL.md")
    args = ap.parse_args()

    skills = args.skill
    if not skills:
        ap.error("au moins un --skill est requis")
    for s in skills:
        if not os.path.isfile(os.path.join(s, "SKILL.md")):
            ap.error("dossier de skill invalide (SKILL.md absent) : %s" % s)

    stage = tempfile.mkdtemp(prefix="plugin_")
    try:
        os.makedirs(os.path.join(stage, ".claude-plugin"))
        manifest = {
            "name": args.name,
            "version": args.version,
            "description": args.desc,
            "author": {"name": args.author},
        }
        with open(os.path.join(stage, ".claude-plugin", "plugin.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        skills_root = os.path.join(stage, "skills")
        os.makedirs(skills_root)
        for s in skills:
            shutil.copytree(s, os.path.join(skills_root, os.path.basename(os.path.normpath(s))))

        os.makedirs(args.out, exist_ok=True)
        out = os.path.join(args.out, args.name + ".plugin")
        # zipfile ecrit des entrees a separateurs '/' (conforme ZIP) sur toutes plateformes.
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(stage):
                for fn in files:
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, stage).replace(os.sep, "/")
                    z.write(full, rel)
        n = sum(1 for s in skills)
        print("OK %s (%d skills)" % (out, n))
        return 0
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
