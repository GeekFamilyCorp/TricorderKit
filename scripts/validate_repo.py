#!/usr/bin/env python3
"""
validate_repo.py — TricorderKit v0.7
Valide que l'arborescence du repo respecte la structure attendue.
Usage :
    python scripts/validate_repo.py
    python scripts/validate_repo.py --fix   # crée les fichiers manquants
Output : JSON (summary + détails par catégorie)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# ── Répertoire racine ────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent

# ── Structure attendue ───────────────────────────────────────────────────────
REQUIRED_FILES = [
    "README.md",
    "README_FIRST.md",
    "AGENTS.md",
    "CLAUDE.md",
    "CHANGELOG.md",
    "docker-compose.yml",
    ".planning/STATE.md",
    ".planning/TASKS.md",
    ".planning/DECISIONS.md",
    ".planning/RISKS.md",
    ".planning/ROADMAP_v0.7.md",
    "core/mainbrain/MainBrain_v1.4.md",
    "core/contracts/skill_output.schema.json",
]

REQUIRED_DIRS = [
    "plugins",
    "skills",
    "cli",
    "mcp",
    "vault",
    "tests",
    "scripts",
    "core",
    ".planning",
]

PLUGIN_REQUIRED = ["README.md", "SKILL.md", "manifest.yml"]

CLI_REQUIRED = ["manifest.yml"]


# ── Vérifications ──────────────────────────────────────────────────────────
def check_required_files() -> dict:
    missing, present = [], []
    for f in REQUIRED_FILES:
        path = ROOT / f
        (present if path.exists() else missing).append(f)
    return {"present": present, "missing": missing,
            "score": len(present) / len(REQUIRED_FILES) * 100}


def check_required_dirs() -> dict:
    missing, present = [], []
    for d in REQUIRED_DIRS:
        path = ROOT / d
        (present if path.exists() else missing).append(d)
    return {"present": present, "missing": missing,
            "score": len(present) / len(REQUIRED_DIRS) * 100}


def check_plugins() -> dict:
    plugins_dir = ROOT / "plugins"
    if not plugins_dir.exists():
        return {"status": "missing", "plugins": []}

    results = []
    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        missing = [f for f in PLUGIN_REQUIRED if not (plugin_dir / f).exists()]
        results.append({
            "name":    plugin_dir.name,
            "status":  "valid" if not missing else "incomplete",
            "missing": missing,
        })
    complete = [r for r in results if r["status"] == "valid"]
    return {"plugins": results, "total": len(results),
            "complete": len(complete),
            "score": (len(complete) / len(results) * 100) if results else 0}


def check_cli_registry() -> dict:
    registry_path = ROOT / "plugins" / "cli-forge" / "registry.yml"
    if not registry_path.exists():
        return {"status": "missing", "message": "registry.yml introuvable"}

    generated_dir = ROOT / "plugins" / "cli-forge" / "generated"
    if not generated_dir.exists():
        return {"status": "empty", "clis": []}

    results = []
    for cli_dir in sorted(generated_dir.iterdir()):
        if not cli_dir.is_dir():
            continue
        missing = [f for f in CLI_REQUIRED if not (cli_dir / f).exists()]
        py_files = list(cli_dir.glob("*.py"))
        results.append({
            "name":       cli_dir.name,
            "has_manifest": (cli_dir / "manifest.yml").exists(),
            "has_script": len(py_files) > 0,
            "script":     py_files[0].name if py_files else None,
            "missing":    missing,
            "status":     "ready" if not missing and py_files else "incomplete",
        })
    return {"clis": results, "total": len(results),
            "ready": len([r for r in results if r["status"] == "ready"])}


def check_skills() -> dict:
    skills_dir = ROOT / "skills"
    if not skills_dir.exists():
        return {"status": "missing", "skills": []}

    results = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        has_skill_md = (skill_dir / "SKILL.md").exists()
        results.append({
            "name":   skill_dir.name,
            "status": "valid" if has_skill_md else "missing_SKILL.md",
        })
    return {"skills": results, "total": len(results),
            "valid": len([r for r in results if r["status"] == "valid"])}


def check_planning() -> dict:
    planning_dir = ROOT / ".planning"
    if not planning_dir.exists():
        return {"status": "missing"}

    files = {
        "STATE.md":    (planning_dir / "STATE.md").exists(),
        "TASKS.md":    (planning_dir / "TASKS.md").exists(),
        "DECISIONS.md":(planning_dir / "DECISIONS.md").exists(),
        "RISKS.md":    (planning_dir / "RISKS.md").exists(),
        "ROADMAP.md":  any(planning_dir.glob("ROADMAP*.md")),
    }
    complete = all(files.values())
    return {"files": files, "complete": complete,
            "score": sum(files.values()) / len(files) * 100}


# ── Fix manquants ──────────────────────────────────────────────────────────
PLACEHOLDER = "# TODO — fichier à compléter\n\n*Généré automatiquement par validate_repo.py*\n"

def fix_missing(missing_files: list) -> list:
    created = []
    for f in missing_files:
        path = ROOT / f
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(PLACEHOLDER, encoding="utf-8")
            created.append(f)
    return created


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="validate_repo — TricorderKit v0.7")
    parser.add_argument("--fix",    action="store_true", help="Créer les fichiers manquants")
    parser.add_argument("--output", choices=["json", "pretty"], default="pretty")
    args = parser.parse_args()

    files    = check_required_files()
    dirs     = check_required_dirs()
    plugins  = check_plugins()
    clis     = check_cli_registry()
    skills   = check_skills()
    planning = check_planning()

    # Score global
    scores = [files["score"], dirs["score"], planning.get("score", 0)]
    global_score = sum(scores) / len(scores)

    result = {
        "timestamp":    datetime.utcnow().isoformat() + "Z",
        "global_score": round(global_score, 1),
        "status":       "healthy" if global_score >= 80 else ("partial" if global_score >= 50 else "critical"),
        "sections": {
            "required_files": files,
            "required_dirs":  dirs,
            "planning":       planning,
            "plugins":        plugins,
            "cli_registry":   clis,
            "skills":         skills,
        }
    }

    # Fix si demandé
    if args.fix and files["missing"]:
        created = fix_missing(files["missing"])
        result["fix_applied"] = created

    if args.output == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        icon = {"healthy": "✅", "partial": "⚠️", "critical": "❌"}.get(result["status"], "?")
        print(f"\n{icon}  TricorderKit Repo Health — {result['global_score']}% ({result['status'].upper()})")
        print(f"   Timestamp : {result['timestamp']}")

        f = result["sections"]["required_files"]
        print(f"\n📁 Fichiers obligatoires : {len(f['present'])}/{len(f['present'])+len(f['missing'])} ({f['score']:.0f}%)")
        for m in f["missing"]:
            print(f"   ❌ manquant : {m}")

        d = result["sections"]["required_dirs"]
        print(f"\n📂 Répertoires : {len(d['present'])}/{len(d['present'])+len(d['missing'])} ({d['score']:.0f}%)")
        for m in d["missing"]:
            print(f"   ❌ manquant : {m}")

        p = result["sections"]["planning"]
        planning_status = '✅ complet' if p.get('complete') else f'⚠️ {p.get("score", 0):.0f}%'
        print(f"\n📋 Planning : {planning_status}")

        pl = result["sections"]["plugins"]
        print(f"\n🔌 Plugins : {pl.get('complete',0)}/{pl.get('total',0)} complets")
        for plugin in pl.get("plugins", []):
            ico = "✅" if plugin["status"] == "valid" else "⚠️"
            print(f"   {ico} {plugin['name']}" + (f" — manque : {plugin['missing']}" if plugin["missing"] else ""))

        cl = result["sections"]["cli_registry"]
        print(f"\n⚡ CLIs : {cl.get('ready',0)}/{cl.get('total',0)} prêtes")
        for cli in cl.get("clis", []):
            ico = "✅" if cli["status"] == "ready" else "⚠️"
            print(f"   {ico} {cli['name']}")

        sk = result["sections"]["skills"]
        print(f"\n🎯 Skills : {sk.get('valid',0)}/{sk.get('total',0)} valides")

        if result.get("fix_applied"):
            print(f"\n🔧 Fichiers créés par --fix : {result['fix_applied']}")
        print()

    sys.exit(0 if result["status"] in ("healthy", "partial") else 1)


if __name__ == "__main__":
    main()
