#!/usr/bin/env python3
"""
post_execution_hook — standardise les résultats pour l'auto-amélioration.
Version : 0.2.1
Output : dict JSON-serializable

Améliorations v0.2.1 vs v0.2.0 :
- Ajout champ hook_name dans log_record ("post_execution")
- Ajout champ skill_name extrait du plan (pour hook_stats.py)
- Alignement avec hook_policy R1 (format de log standardisé)
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOKS_CACHE_DIR = _REPO_ROOT / ".cache" / "hooks"
POST_EXECUTION_LOG = HOOKS_CACHE_DIR / "post_execution.log"
SCHEMA_PATH = _REPO_ROOT / "core" / "contracts" / "skill_output.schema.json"


def _load_schema() -> Optional[Dict[str, Any]]:
    try:
        if SCHEMA_PATH.exists():
            return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def _validate_schema(result: Dict[str, Any], schema: Optional[Dict[str, Any]]) -> tuple:
    if schema is None:
        return (None, [])
    try:
        import jsonschema  # type: ignore[import]
        errors = list(jsonschema.Draft7Validator(schema).iter_errors(result))
        return (len(errors) == 0, [e.message for e in errors])
    except ImportError:
        return (None, ["jsonschema not installed — validation skipped"])
    except Exception as exc:
        return (None, [str(exc)])


def _compute_quality_score(result: Dict[str, Any]) -> tuple:
    """Score structurel 0.0–1.0 basé sur 4 critères (0.25 chacun).

    - has_status    : "status" ou "statut"
    - has_output    : "output", "data", "result" ou "content"
    - has_sources   : "sources", "source" ou "references"
    - has_reliability : "reliability", "fiabilite" ou "confidence"
    """
    keys = {k.lower() for k in result.keys()}
    breakdown = {
        "has_status":      bool(keys & {"status", "statut"}),
        "has_output":      bool(keys & {"output", "data", "result", "content"}),
        "has_sources":     bool(keys & {"sources", "source", "references"}),
        "has_reliability": bool(keys & {"reliability", "fiabilite", "fiabilité", "confidence"}),
    }
    score = sum(1 for v in breakdown.values() if v) / len(breakdown)
    return round(score, 2), breakdown


_SCHEMA: Optional[Dict[str, Any]] = _load_schema()


def run_post_execution_hook(
    plan: Dict[str, Any],
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """Enrichit le résultat pour alimenter usage_observer et skill_eval.

    - Propage hook_run_id / hook_timestamp depuis le plan.
    - Calcule quality_score et quality_breakdown.
    - Extrait tokens_used si présent dans le résultat.
    - Valide contre skill_output.schema.json si disponible.
    - Logue en JSON-lines dans post_execution.log (format hook_policy R1).

    Ne réalise aucune écriture externe (Neo4j, Obsidian) — délégué à Temporal.
    """
    hooks_meta = plan.get("hooks", {})
    hook_run_id: Optional[str] = hooks_meta.get("hook_run_id")
    hook_timestamp = datetime.now(timezone.utc).isoformat()

    # Extraction du nom du skill/goat depuis le plan (pour hook_stats.py)
    skill_name: Optional[str] = (
        plan.get("skill")
        or plan.get("goat")
        or plan.get("name")
        or hooks_meta.get("skill_name")
    )

    tokens_used: Optional[int] = (
        result.get("tokens_used")
        or result.get("usage", {}).get("total_tokens")
        or hooks_meta.get("estimated_tokens")
    )

    quality_score, quality_breakdown = _compute_quality_score(result)
    schema_valid, schema_errors = _validate_schema(result, _SCHEMA)

    enriched_result = dict(result)
    enriched_result.setdefault("hooks", {})
    if hook_run_id is not None:
        enriched_result["hooks"]["hook_run_id"] = hook_run_id
    enriched_result["hooks"]["hook_timestamp"] = hook_timestamp
    enriched_result["hooks"]["quality_score"] = quality_score
    enriched_result["hooks"]["quality_breakdown"] = quality_breakdown
    enriched_result["hooks"]["tokens_used"] = tokens_used
    if schema_valid is not None:
        enriched_result["hooks"]["schema_valid"] = schema_valid
        enriched_result["hooks"]["schema_errors"] = schema_errors

    # Format log_record aligné avec hook_policy R1
    log_record = {
        "hook_name":    "post_execution",
        "skill_name":   skill_name,
        "hook_run_id":  hook_run_id,
        "timestamp":    hook_timestamp,
        "status":       "ok" if schema_valid is not False else "schema_error",
        "quality_score": quality_score,
        "schema_valid": schema_valid,
        "tokens_used":  tokens_used,
        "plan_risk_hint": hooks_meta.get("risk_hint"),
        "result_keys":  list(result.keys()),
    }

    try:
        HOOKS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with POST_EXECUTION_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_record, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return enriched_result
