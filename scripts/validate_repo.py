#!/usr/bin/env python3
"""
validate_repo.py — TricorderKit v0.7
Valide que l'arborescence du repo respecte la structure attendue.

Usage :
    python scripts/validate_repo.py              # rapport complet
    python scripts/validate_repo.py --fix        # crée des STUBS pour les fichiers manquants
                                                 # ⚠️  les stubs sont signalés séparément
                                                 #     et n'améliorent pas le score réel
    python scripts/validate_repo.py --show-stubs # liste tous les stubs actifs dans le repo
Output : JSON (summary + détails par catégorie)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# ── Répertoire racine ────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent

# ── Marqueur de stub ─────────────────────────────────────────────────────────
# Présent dans tous les fichiers créés par --fix.
# check_required_files() et check_placeholders() l'utilisent pour les détecter.
# Ne pas modifier ce marqueur sans regénérer tous les stubs existants.
PLACEHOLDER_MARKER = "TRICORDERKIT_STUB_PLACEHOLDER"

PLACEHOLDER_TEMPLATE = """\
# TODO — stub créé automatiquement par validate_repo.py --fix
# {marker}
#
# Ce fichier est un PLACEHOLDER vide. Il ne remplace pas le vrai contenu.
# Action requise : remplacez ce fichier par l'implémentation réelle.
#
# Pour lister tous les stubs actifs dans ce repo :
#   python scripts/validate_repo.py --show-stubs
""".format(marker=PLACEHOLDER_MARKER)

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
    "core/mainbrain/MainBrain_v1.5.md",
    "core/contracts/skill_output.schema.json",
]

REQUIRED_DIRS = [
    "plugins",
    "skills",
    "tools",
    "tests",
    "scripts",
    "core",
    ".planning",
]

PLUGIN_REQUIRED = ["README.md", "SKILL.md", "manifest.yml"]
CLI_REQUIRED = ["manifest.yml"]


# ── Vérifications ──────────────────────────────────────────────────────────
def _is_stub(path: Path) -> bool:
    """Retourne True si le fichier contient le marqueur de stub."""
    try:
        return PLACEHOLDER_MARKER in path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        return False


def check_required_files() -> dict:
    """
    Classe chaque fichier obligatoire en trois catégories :
    - present  : fichier réel (contenu non-stub)
    - stubs    : fichier créé par --fix (placeholder)
    - missing  : fichier absent

    Le score global utilise real_score (stubs exclus) pour ne pas masquer
    les manques réels.
    """
    missing, present, stubs = [], [], []
    for f in REQUIRED_FILES:
        path = ROOT / f
        if not path.exists():
            missing.append(f)
        elif _is_stub(path):
            stubs.append(f)
        else:
            present.append(f)
    total = len(REQUIRED_FILES)
    return {
        "present":    present,
        "stubs":      stubs,
        "missing":    missing,
        "score":      round((len(present) + len(stubs)) / total * 100, 1) if total else 0,
        "real_score": round(len(present) / total * 100, 1) if total else 0,
    }


def check_required_dirs() -> dict:
    missing, present = [], []
    for d in REQUIRED_DIRS:
        path = ROOT / d
        (present if path.exists() else missing).append(d)
    return {
        "present": present,
        "missing": missing,
        "score":   round(len(present) / len(REQUIRED_DIRS) * 100, 1),
    }


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
    return {
        "plugins":  results,
        "total":    len(results),
        "complete": len(complete),
        "score":    round(len(complete) / len(results) * 100, 1) if results else 0,
    }


def check_cli_registry() -> dict:
    """Vérifie les CLIs dans tools/ (structure STATE.md v0.7)."""
    registry_path = ROOT / "plugins" / "cli-forge" / "registry.yml"
    if not registry_path.exists():
        return {"status": "missing", "message": "registry.yml introuvable dans plugins/cli-forge/"}

    tools_dir = ROOT / "tools"
    if not tools_dir.exists():
        return {"status": "empty", "clis": [], "message": "répertoire tools/ absent"}

    results = []
    for cli_dir in sorted(tools_dir.iterdir()):
        if not cli_dir.is_dir():
            continue
        missing = [f for f in CLI_REQUIRED if not (cli_dir / f).exists()]
        py_files = list(cli_dir.glob("*.py"))
        results.append({
            "name":         cli_dir.name,
            "has_manifest": (cli_dir / "manifest.yml").exists(),
            "has_script":   len(py_files) > 0,
            "script":       py_files[0].name if py_files else None,
            "missing":      missing,
            "status":       "ready" if not missing and py_files else "incomplete",
        })
    return {
        "clis":  results,
        "total": len(results),
        "ready": len([r for r in results if r["status"] == "ready"]),
    }


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
    return {
        "skills": results,
        "total":  len(results),
        "valid":  len([r for r in results if r["status"] == "valid"]),
    }


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
    return {
        "files":    files,
        "complete": all(files.values()),
        "score":    round(sum(files.values()) / len(files) * 100, 1),
    }


def check_placeholders() -> list:
    """Scanne tout le repo et retourne les fichiers contenant le marqueur de stub."""
    stubs = []
    extensions = {".md", ".json", ".yml", ".yaml", ".py", ".txt", ".toml"}
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in extensions:
            if _is_stub(path):
                stubs.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return sorted(stubs)


# ── Fix manquants ──────────────────────────────────────────────────────────
def fix_missing(missing_files: list) -> list:
    """Crée des fichiers stub pour les fichiers manquants."""
    created = []
    for f in missing_files:
        path = ROOT / f
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(PLACEHOLDER_TEMPLATE, encoding="utf-8")
            created.append(f)
    return created


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="validate_repo — TricorderKit v0.7",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemples :\n"
            "  python scripts/validate_repo.py\n"
            "  python scripts/validate_repo.py --fix\n"
            "  python scripts/validate_repo.py --show-stubs\n"
            "  python scripts/validate_repo.py --output json\n"
        ),
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Créer des stubs pour les fichiers manquants (signalés séparément, n'améliorent pas le score réel)",
    )
    parser.add_argument(
        "--show-stubs",
        action="store_true",
        help="Lister tous les fichiers stub actifs dans le repo puis quitter",
    )
    parser.add_argument("--output", choices=["json", "pretty"], default="pretty")
    args = parser.parse_args()

    # ── Mode --show-stubs uniquement ────────────────────────────────────────
    if args.show_stubs:
        stubs = check_placeholders()
        if args.output == "json":
            print(json.dumps({"stubs": stubs, "count": len(stubs)}, indent=2, ensure_ascii=False))
        else:
            if stubs:
                print(f"\n⚠️  {len(stubs)} stub(s) détecté(s) — à remplacer par le vrai contenu :")
                for s in stubs:
                    print(f"   ↳ {s}")
            else:
                print("\n✅ Aucun stub détecté — tous les fichiers ont du contenu réel.")
            print()
        sys.exit(0 if not stubs else 2)

    # ── Rapport complet ──────────────────────────────────────────────────────
    files    = check_required_files()
    dirs     = check_required_dirs()
    plugins  = check_plugins()
    clis     = check_cli_registry()
    skills   = check_skills()
    planning = check_planning()

    # Score global basé sur real_score (stubs exclus) pour refléter l'état réel
    scores = [files["real_score"], dirs["score"], planning.get("score", 0)]
    global_score = round(sum(scores) / len(scores), 1)

    result = {
        "timestamp":     datetime.utcnow().isoformat() + "Z",
        "global_score":  global_score,
        "status":        "healthy" if global_score >= 80 else ("partial" if global_score >= 50 else "critical"),
        "stubs_present": len(files["stubs"]) > 0,
        "sections": {
            "required_files": files,
            "required_dirs":  dirs,
            "planning":       planning,
            "plugins":        plugins,
            "cli_registry":   clis,
            "skills":         skills,
        },
    }

    # ── Appliquer --fix si demandé ───────────────────────────────────────────
    if args.fix:
        if files["missing"]:
            print(
                "\n⚠️  --fix : création de fichiers STUB uniquement.\n"
                "   Ces stubs n'ont aucun contenu réel et n'améliorent pas le score réel.\n"
                "   Utilisez --show-stubs pour les retrouver et les remplacer.\n"
            )
            created = fix_missing(files["missing"])
            result["fix_applied"] = created
        else:
            print("\nℹ️  --fix : aucun fichier manquant à créer.\n")

    # ── Affichage ─────────────────────────────────────────────────────────────
    if args.output == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        icon = {"healthy": "✅", "partial": "⚠️", "critical": "❌"}.get(result["status"], "?")
        print(f"\n{icon}  TricorderKit Repo Health — {result['global_score']}% réel ({result['status'].upper()})")
        print(f"   Timestamp : {result['timestamp']}")

        # Fichiers
        f = result["sections"]["required_files"]
        n_real    = len(f["present"])
        n_stubs   = len(f["stubs"])
        n_missing = len(f["missing"])
        n_total   = n_real + n_stubs + n_missing
        stub_note = f", dont {n_stubs} stub(s) ⚠️" if n_stubs else ""
        print(f"\n📁 Fichiers obligatoires : {n_real}/{n_total} réels ({f['real_score']}%){stub_note}")
        for s in f["stubs"]:
            print(f"   ⚠️  stub    : {s}  ← à remplacer par le vrai contenu")
        for m in f["missing"]:
            print(f"   ❌ manquant : {m}")

        # Répertoires
        d = result["sections"]["required_dirs"]
        print(f"\n📂 Répertoires : {len(d['present'])}/{len(d['present'])+len(d['missing'])} ({d['score']}%)")
        for m in d["missing"]:
            print(f"   ❌ manquant : {m}")

        # Planning
        p = result["sections"]["planning"]
        planning_status = "✅ complet" if p.get("complete") else f"⚠️ {p.get('score', 0)}%"
        print(f"\n📋 Planning : {planning_status}")

        # Plugins
        pl = result["sections"]["plugins"]
        print(f"\n🔌 Plugins : {pl.get('complete', 0)}/{pl.get('total', 0)} complets")
        for plugin in pl.get("plugins", []):
            ico = "✅" if plugin["status"] == "valid" else "⚠️"
            suffix = f" — manque : {plugin['missing']}" if plugin["missing"] else ""
            print(f"   {ico} {plugin['name']}{suffix}")

        # CLIs
        cl = result["sections"]["cli_registry"]
        print(f"\n⚡ CLIs (tools/) : {cl.get('ready', 0)}/{cl.get('total', 0)} prêtes")
        for cli in cl.get("clis", []):
            ico = "✅" if cli["status"] == "ready" else "⚠️"
            print(f"   {ico} {cli['name']}")
        if cl.get("message"):
            print(f"   ℹ️  {cl['message']}")

        # Skills
        sk = result["sections"]["skills"]
        print(f"\n🎯 Skills : {sk.get('valid', 0)}/{sk.get('total', 0)} valides")

        # Résultat --fix
        if result.get("fix_applied"):
            print(f"\n🔧 Stubs créés ({len(result['fix_applied'])}) :")
            for f_path in result["fix_applied"]:
                print(f"   ↳ {f_path}")
            print("   ⚠️  Ces fichiers sont des placeholders vides.")
            print("   ⚠️  Lancez --show-stubs pour les retrouver ultérieurement.")
        print()

    sys.exit(0 if result["status"] in ("healthy", "partial") else 1)


if __name__ == "__main__":
    main()
