"""
Tests contrat — tk-orchestrator budget_guard phase 2
TricorderKit v0.9 — S2
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Ajouter le répertoire tk-orchestrator au path
TK_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TK_DIR))

from budget.token_tracker import (
    INTENT_BUDGETS,
    ORCHESTRATOR_BASE_BUDGET,
    SESSION_ALERT_THRESHOLD,
    SESSION_BUDGET_DEFAULT,
    TASK_TIERS,
    GuardResult,
    TaskTier,
    guard_action,
    tier_for_intent,
    tier_from_complexity,
)


# ── Constantes ────────────────────────────────────────────────────────────────

def test_session_budget_default():
    assert SESSION_BUDGET_DEFAULT == 30_000

def test_session_alert_threshold():
    assert SESSION_ALERT_THRESHOLD == 0.80

def test_task_tiers_complete():
    assert set(TASK_TIERS.keys()) == {"T1", "T2", "T3"}

def test_intent_budgets_keys():
    expected = {"query", "action", "workflow", "research", "audit", "unknown"}
    assert set(INTENT_BUDGETS.keys()) == expected


# ── Tier classification ───────────────────────────────────────────────────────

def test_tier_t1_query():
    tier = tier_for_intent("query")
    assert tier.level == "T1"
    assert tier.model_target == "claude-haiku-4-5-20251001"

def test_tier_t1_unknown():
    tier = tier_for_intent("unknown")
    assert tier.level == "T1"

def test_tier_t2_action():
    tier = tier_for_intent("action")
    assert tier.level == "T2"
    assert tier.model_target == "claude-sonnet-4-6"

def test_tier_t2_audit():
    tier = tier_for_intent("audit")
    assert tier.level == "T2"

def test_tier_t3_workflow():
    tier = tier_for_intent("workflow")
    assert tier.level == "T3"
    assert tier.model_target == "claude-opus-4-6"

def test_tier_t3_research():
    tier = tier_for_intent("research")
    assert tier.level == "T3"


# ── tier_from_complexity escalade ─────────────────────────────────────────────

def test_complexity_escalade_code_multifile():
    """has_code + has_multifile → T3 quel que soit l'intent de base"""
    tier = tier_from_complexity("query", has_code=True, has_multifile=True)
    assert tier.level == "T3"

def test_complexity_escalade_code_only():
    """has_code seul → T1→T2"""
    tier = tier_from_complexity("query", has_code=True, has_multifile=False)
    assert tier.level == "T2"

def test_complexity_escalade_destructive():
    """is_destructive → T1→T2"""
    tier = tier_from_complexity("unknown", is_destructive=True)
    assert tier.level == "T2"

def test_complexity_no_escalade_t3():
    """T3 reste T3 sans escalade"""
    tier = tier_from_complexity("workflow")
    assert tier.level == "T3"

def test_complexity_long_request_escalade():
    """request > 500 chars + T1 → T2"""
    tier = tier_from_complexity("query", request_length=600)
    assert tier.level == "T2"


# ── guard_action logic ────────────────────────────────────────────────────────

def test_guard_proceed_safe():
    result = guard_action("query", session_used=1000, session_budget=30_000)
    assert result.action == "proceed"
    assert result.alert_level == "SAFE"

def test_guard_proceed_alert_zone():
    """80-100% → proceed mais ALERT"""
    result = guard_action("action", session_used=25_000, session_budget=30_000)
    assert result.action == "proceed"
    assert result.alert_level == "ALERT"

def test_guard_pause_over_budget():
    """session_used >= budget → pause"""
    result = guard_action("query", session_used=30_000, session_budget=30_000)
    assert result.action == "pause"

def test_guard_abort_mode():
    """on_budget_exceeded=abort → abort"""
    result = guard_action("query", session_used=30_000, session_budget=30_000,
                          on_budget_exceeded="abort")
    assert result.action == "abort"

def test_guard_pause_projected_over():
    """session OK mais tâche projetée dépasse le budget → pause"""
    result = guard_action("research", session_used=29_000, session_budget=30_000)
    assert result.action == "pause"

def test_guard_result_fields():
    result = guard_action("workflow", session_used=5_000)
    assert isinstance(result, GuardResult)
    d = result.to_dict()
    for key in ("action", "reason", "session_used", "session_budget",
                "session_pct", "tier", "model_target", "alert_level"):
        assert key in d, f"Champ manquant : {key}"


# ── CLI contrat JSON ──────────────────────────────────────────────────────────

ORCHESTRATOR = TK_DIR / "orchestrator.py"

def run_cli(*args):
    result = subprocess.run(
        [sys.executable, str(ORCHESTRATOR)] + list(args),
        capture_output=True, text=True, cwd=str(TK_DIR)
    )
    return result

def test_cli_budget_guard_json():
    r = run_cli("budget-guard", "--intent", "query", "--session-used", "1000")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["status"] == "success"
    assert "guard" in data["output"]["data"]

def test_cli_budget_guard_tier_detail():
    r = run_cli("budget-guard", "--intent", "workflow", "--session-used", "0")
    data = json.loads(r.stdout)
    td = data["output"]["data"]["tier_detail"]
    assert td["level"] == "T3"
    assert td["model_target"] == "claude-opus-4-6"

def test_cli_session_budget_json():
    r = run_cli("session-budget", "--session-used", "15000")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    out = data["output"]["data"]
    assert out["session_used"] == 15000
    assert out["session_budget"] == 30000
    assert "tasks_remaining_estimate" in out

def test_cli_session_budget_alert():
    r = run_cli("session-budget", "--session-used", "25000")
    data = json.loads(r.stdout)
    assert data["output"]["data"]["alert_level"] == "ALERT"
