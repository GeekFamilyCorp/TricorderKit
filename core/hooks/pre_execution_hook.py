#!/usr/bin/env python3
"""
pre_execution_hook — prépare le plan d'exécution pour l'observation.
Version : 0.2.0
Output : dict JSON-serializable

Améliorations v0.2.0 vs v0.1.0 :
- mkdir déplacé dans la fonction (plus de side-effect à l'import)
- Timestamps ISO-8601 UTC (au lieu de int epoch)
- risk_hint calculé à partir du contenu du plan (vs "UNKNOWN" fixe)
- estimated_tokens estimé par heuristique (vs 0 fixe)
- Chemin absolu résolu depuis __file__ (vs chemin relatif fragile)
- Pas de crash si le log échoue (comportement conservé)
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOKS_CACHE_DIR = _REPO_ROOT / ".cache" / "hooks"
PRE_EXECUTION_LOG = HOOKS_CACHE_DIR / "pre_execution.log"

_RISK_TABLE: Dict[str, str] = {
    "read":     "LOW",
    "query":    "LOW",
    "research": "LOW",
    "write":    "MEDIUM",
    "create":   "MEDIUM",
    "update":   "MEDIUM",
    "delete":   "HIGH",
    "push":     "HIGH",
    "deploy":   "HIGH",
    "migrate":  "CRITICAL",
    "drop":     "CRITICAL",
}
_DEFAULT_RISK = "MEDIUM"


def _estimate_risk(plan: Dict[str, Any]) -> str:
    if explicit := plan.get("risk_hint"):
        return str(explicit).upper()
    action_type = str(plan.get("action_type", "")).lower()
    if action_type in _RISK_TABLE:
        return _RISK_TABLE[action_type]
    name = str(plan.get("skill", plan.get("goat", plan.get("workflow", "")))).lower()
    if any(k in name for k in ("delete", "drop", "purge", "reset", "destroy")):
        return "HIGH"
    if any(k in name for k in ("write", "update", "push", "create", "patch")):
        return "MEDIUM"
    if any(k in name for k in ("read", "list", "get", "search", "query")):
        return "LOW"
    return _DEFAULT_RISK


def _estimate_tokens(plan: Dict[str, Any]) -> int:
    try:
        serialized = json.dumps(plan, ensure_ascii=False)
        return min(int(len(serialized) * 1.3), 50_000)
    except Exception:
        return 0


def run_pre_execution_hook(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Enrichit le plan avec des métadonnées d'observation.

    - hook_run_id : UUID v4, partageable avec Langfuse et Temporal.
    - hook_timestamp : ISO-8601 UTC.
    - risk_hint : LOW / MEDIUM / HIGH / CRITICAL (calculé).
    - estimated_tokens : heuristique 1.3 token/char.

    Logue en append dans .cache/hooks/pre_execution.log (JSON-lines).
    Ne lance aucune commande externe.
    """
    hook_run_id = str(uuid.uuid4())
    hook_timestamp = datetime.now(timezone.utc).isoformat()

    enriched_plan = dict(plan)
    enriched_plan.setdefault("hooks", {})
    enriched_plan["hooks"]["hook_run_id"] = hook_run_id
    enriched_plan["hooks"]["hook_timestamp"] = hook_timestamp
    enriched_plan["hooks"]["risk_hint"] = _estimate_risk(plan)
    enriched_plan["hooks"]["estimated_tokens"] = _estimate_tokens(plan)

    log_record = {
        "hook_run_id": hook_run_id,
        "timestamp": hook_timestamp,
        "plan": enriched_plan,
    }

    try:
        HOOKS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with PRE_EXECUTION_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_record, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return enriched_plan
