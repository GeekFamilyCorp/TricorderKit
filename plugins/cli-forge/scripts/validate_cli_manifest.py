#!/usr/bin/env python3
"""
validate_cli_manifest.py — TricorderKit cli-forge
Valide un manifest YAML CLI contre le schéma JSON officiel.
Usage :
    python validate_cli_manifest.py <path/to/manifest.yml>
    python validate_cli_manifest.py --all          # valide tous les manifests du registre
Output : JSON (success / errors)
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(json.dumps({"status": "error", "message": "PyYAML non installé. Lancer : pip install pyyaml"}))
    sys.exit(1)

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    print(json.dumps({"status": "error", "message": "jsonschema non installé. Lancer : pip install jsonschema"}))
    sys.exit(1)

# ── Chemins ───────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
PLUGIN_DIR   = SCRIPT_DIR.parent
SCHEMA_PATH  = PLUGIN_DIR / "cli_manifest.schema.json"
GENERATED    = PLUGIN_DIR / "generated"


# ── Chargement du schéma ──────────────────────────────────────────────────────────────
def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        print(json.dumps({"status": "error", "message": f"Schéma introuvable : {SCHEMA_PATH}"}))
        sys.exit(1)
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Validation d'un manifest ─────────────────────────────────────────────────────────────
def validate_manifest(manifest_path: Path, schema: dict) -> dict:
    result = {
        "manifest": str(manifest_path),
        "status": "unknown",
        "errors": [],
        "warnings": [],
        "security_warnings": [],
    }

    if not manifest_path.exists():
        result["status"] = "error"
        result["errors"].append(f"Fichier introuvable : {manifest_path}")
        return result

    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result["status"] = "error"
        result["errors"].append(f"YAML invalide : {e}")
        return result

    if not isinstance(manifest, dict):
        result["status"] = "error"
        result["errors"].append("Le manifest doit être un objet YAML")
        return result

    try:
        validate(instance=manifest, schema=schema)
    except ValidationError as e:
        result["status"] = "error"
        result["errors"].append(f"Schema : {e.message} (path: {'.'.join(str(p) for p in e.path)})")
        return result

    # Règles métier TricorderKit
    if manifest.get("output_formats", [None])[0] != "json":
        result["warnings"].append("JSON devrait être le premier format dans output_formats")

    if not manifest.get("dry_run", False):
        result["warnings"].append("dry_run devrait être true (recommandé pour toutes les CLIs)")

    cache = manifest.get("cache", {})
    if not cache.get("sqlite", False):
        result["warnings"].append("cache.sqlite recommandé pour les appels répétés")

    if "token_budget" not in manifest:
        result["warnings"].append("token_budget non défini — ajouter max_per_call et warn_at")

    sec = manifest.get("security_status", {})
    if not sec.get("audited", False):
        result["security_warnings"].append("security_status.audited = false — audit requis avant prod")
    if not sec.get("prompt_injection_checked", False):
        result["security_warnings"].append("prompt_injection_checked = false")
    if not sec.get("network_access_checked", False):
        result["security_warnings"].append("network_access_checked = false")

    if not manifest.get("forbidden_commands"):
        result["warnings"].append("forbidden_commands vide — documenter les commandes interdites")

    if result["errors"]:
        result["status"] = "error"
    elif result["warnings"] or result["security_warnings"]:
        result["status"] = "warnings"
    else:
        result["status"] = "valid"

    result["name"]    = manifest.get("name", "unknown")
    result["version"] = manifest.get("version", "unknown")
    return result


def validate_all(schema: dict) -> dict:
    manifests = list(GENERATED.rglob("manifest.yml"))
    if not manifests:
        return {
            "status": "warning",
            "message": "Aucun manifest trouvé dans plugins/cli-forge/generated/",
            "results": []
        }

    results  = [validate_manifest(m, schema) for m in manifests]
    errors   = [r for r in results if r["status"] == "error"]
    warnings = [r for r in results if r["status"] == "warnings"]
    valid    = [r for r in results if r["status"] == "valid"]

    return {
        "status":   "error" if errors else ("warnings" if warnings else "valid"),
        "total":    len(results),
        "valid":    len(valid),
        "warnings": len(warnings),
        "errors":   len(errors),
        "results":  results,
    }


def main():
    parser = argparse.ArgumentParser(description="validate_cli_manifest — TricorderKit cli-forge")
    parser.add_argument("manifest", nargs="?", help="Chemin vers le manifest.yml à valider")
    parser.add_argument("--all",    action="store_true", help="Valider tous les manifests")
    parser.add_argument("--output", choices=["json", "pretty"], default="pretty")
    args = parser.parse_args()

    schema = load_schema()

    if args.all:
        result = validate_all(schema)
    elif args.manifest:
        result = validate_manifest(Path(args.manifest), schema)
    else:
        parser.print_help()
        sys.exit(0)

    if args.output == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        status_icon = {"valid": "OK", "warnings": "WARN", "error": "FAIL"}.get(result["status"], "?")
        print(f"\n[{status_icon}]  Result : {result['status'].upper()}")

        if "total" in result:
            print(f"   Total : {result['total']} | OK {result['valid']} | WARN {result['warnings']} | FAIL {result['errors']}")

        for r in result.get("results", [result]):
            icon = {"valid": "OK", "warnings": "WARN", "error": "FAIL"}.get(r["status"], "?")
            print(f"\n  [{icon}]  {r.get('name', r.get('manifest', '?'))} {r.get('version', '')}")
            for e in r.get("errors", []):
                print(f"       ERROR: {e}")
            for w in r.get("warnings", []):
                print(f"       WARN:  {w}")
            for s in r.get("security_warnings", []):
                print(f"       SEC:   {s}")

        print()

    sys.exit(0 if result["status"] in ("valid", "warnings") else 1)


if __name__ == "__main__":
    main()
