#!/usr/bin/env python3
"""
check_preflight_contract.py — TricorderKit
Vérifie, sans rien exécuter, que chaque plugin déclare un contrat d'entrée
(bloc `preflight:` du manifest.yml) conforme à core/contracts/skill_preflight.schema.json.

Ce que le contrat déclare : entrées, dépendances, variables d'environnement,
conditions d'arrêt, réessai borné, retour arrière, escalade vers l'humain.

Usage :
    python scripts/check_preflight_contract.py            # mode avertissement (sortie 0 si aucun bloc invalide)
    python scripts/check_preflight_contract.py --strict   # un plugin sans contrat = échec (sortie 1)

Codes de sortie :
    0  aucun contrat invalide (les absences sont seulement signalées, hors --strict)
    1  au moins un contrat invalide, ou une absence en --strict
    2  erreur d'outillage (schéma introuvable, dépendance Python manquante)

Sécurité : le script lit des manifests ; il ne lit JAMAIS la valeur d'une
variable d'environnement et ne contacte aucun service.
Output : JSON.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "core" / "contracts" / "skill_preflight.schema.json"
PLUGINS_DIR = ROOT / "plugins"

# Chemins personnels interdits dans un contrat (frontière publique R37).
PERSONAL_PATH = re.compile(r"([A-Za-z]:\\Users\\|/home/[^/\s]+/|/Users/[^/\s]+/)")


def _load_deps():
    try:
        import yaml  # type: ignore
        import jsonschema  # type: ignore
    except ImportError as exc:  # pragma: no cover
        print(json.dumps({"status": "tooling_error", "error": f"dépendance manquante : {exc.name}"}))
        sys.exit(2)
    return yaml, jsonschema


def _strings(node):
    """Toutes les chaînes d'un bloc YAML (valeurs et clés), parcours récursif."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _strings(k)
            yield from _strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _strings(v)


def check_plugin(plugin_dir: Path, validator, yaml) -> dict:
    """Retourne le résultat pour un plugin : ok | missing_manifest | missing_preflight | invalid."""
    manifest = plugin_dir / "manifest.yml"
    result: dict = {"plugin": plugin_dir.name, "errors": []}
    if not manifest.exists():
        result["status"] = "missing_manifest"
        return result
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # YAML illisible
        result["status"] = "invalid"
        result["errors"].append(f"YAML illisible : {exc}")
        return result
    block = data.get("preflight") if isinstance(data, dict) else None
    if block is None:
        result["status"] = "missing_preflight"
        return result

    errors = [
        f"{'/'.join(str(p) for p in e.absolute_path) or '<racine>'} : {e.message}"
        for e in sorted(validator.iter_errors(block), key=lambda e: list(e.absolute_path))
    ]
    if any(PERSONAL_PATH.search(s) for s in _strings(block)):
        errors.append("chemin personnel détecté dans le contrat (R37)")
    result["status"] = "invalid" if errors else "ok"
    result["errors"] = errors
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--strict", action="store_true", help="un plugin sans contrat fait échouer le contrôle")
    parser.add_argument("--plugins-dir", type=Path, default=PLUGINS_DIR)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    args = parser.parse_args(argv)

    yaml, jsonschema = _load_deps()
    if not args.schema.exists():
        print(json.dumps({"status": "tooling_error", "error": f"schéma introuvable : {args.schema.name}"}))
        return 2
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    plugins = sorted(p for p in args.plugins_dir.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))
    results = [check_plugin(p, validator, yaml) for p in plugins]

    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    missing = counts.get("missing_manifest", 0) + counts.get("missing_preflight", 0)
    failed = counts.get("invalid", 0) > 0 or (args.strict and missing > 0)

    print(json.dumps({
        "check": "preflight_contract",
        "mode": "strict" if args.strict else "warn",
        "status": "fail" if failed else "pass",
        "summary": {"plugins": len(results), **counts},
        "results": results,
    }, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
