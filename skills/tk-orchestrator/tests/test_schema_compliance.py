"""
test_schema_compliance.py — Validation output JSON contre skill_output.schema.json v1.0.0
TricorderKit v0.8 — tk-orchestrator v0.2.0

Vérifie que TOUS les outputs de l'orchestrateur sont conformes au contrat.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict

import pytest
import jsonschema

from orchestrator import (
    cmd_route, cmd_chain, cmd_budget_check, cmd_status, _build_output
)
from budget.token_tracker import TokenBudget


# ── Chargement du schema ────────────────────────────────────────────────────

_ROOT = Path(__file__).parent.parent.parent.parent  # TricorderKit_Project/
SCHEMA_PATH = _ROOT / "core" / "contracts" / "skill_output.schema.json"


@pytest.fixture(scope="module")
def schema():
    if not SCHEMA_PATH.exists():
        pytest.skip("Schema introuvable : {}".format(SCHEMA_PATH))
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate(output, schema):
    """Valide l'output contre le schema — leve AssertionError si invalide."""
    try:
        jsonschema.validate(instance=output, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail("Schema violation: {} at {}".format(e.message, list(e.path)))


# ── Tests : _build_output ─────────────────────────────────────────────────────

class TestBuildOutput:

    def test_success_output_valid(self, schema):
        budget = TokenBudget(total=500, effective=400)
        budget.consume(100, "test")
        output = _build_output(
            status="success",
            summary="Test output OK",
            data={"test": True},
            budget=budget,
            duration_ms=100,
        )
        validate(output, schema)

    def test_error_output_valid(self, schema):
        output = _build_output(
            status="error",
            summary="Erreur de test",
            data={},
            error={
                "code": "TEST_ERROR",
                "message": "Erreur de test",
                "recoverable": True,
                "rollback_available": False,
            },
        )
        validate(output, schema)

    def test_dry_run_output_valid(self, schema):
        output = _build_output(
            status="dry_run",
            summary="Dry run simule",
            data={"would_execute": True},
            dry_run_report={
                "actions_that_would_run": ["GET /repos"],
                "estimated_tokens": 100,
                "estimated_duration_ms": 200,
                "risk_level": "LOW",
            },
        )
        validate(output, schema)

    def test_partial_output_valid(self, schema):
        output = _build_output(
            status="partial",
            summary="Execution partielle — 1/3 steps OK",
            data={"chain": {"overall_status": "partial"}},
            error={
                "code": "CHAIN_ABORTED_STEP_2",
                "message": "Step 2 failed",
                "recoverable": True,
                "rollback_available": False,
            },
        )
        validate(output, schema)

    def test_required_fields_present(self, schema):
        output = _build_output(
            status="success",
            summary="Minimal output",
            data={},
        )
        required = ["status", "skill_name", "skill_version", "timestamp", "output"]
        for field in required:
            assert field in output, "Champ requis manquant : {}".format(field)

    def test_skill_name_correct(self, schema):
        output = _build_output(status="success", summary="test", data={})
        assert output["skill_name"] == "tk-orchestrator"

    def test_skill_version_semver(self, schema):
        output = _build_output(status="success", summary="test", data={})
        assert re.match(r"^\d+\.\d+\.\d+$", output["skill_version"])

    def test_timestamp_iso8601(self, schema):
        output = _build_output(status="success", summary="test", data={})
        ts = output["timestamp"]
        assert "T" in ts
        assert ts.endswith("Z") or "+" in ts

    def test_output_summary_max_500_chars(self, schema):
        long_summary = "x" * 600
        output = _build_output(status="success", summary=long_summary, data={})
        assert len(output["output"]["summary"]) <= 500

    def test_tokens_used_structure(self, schema):
        budget = TokenBudget(total=1000, effective=800)
        budget.consume(200, "test")
        output = _build_output(status="success", summary="test", data={}, budget=budget)
        tokens = output["tokens_used"]
        assert "input" in tokens
        assert "output" in tokens
        assert "total" in tokens
        assert tokens["total"] == 200


# ── Tests : cmd_status ────────────────────────────────────────────────────────

class TestCmdStatusCompliance:

    def test_status_output_valid(self, schema):
        output = cmd_status(root=_ROOT)
        validate(output, schema)


# ── Tests : cmd_budget_check ──────────────────────────────────────────────────

class TestCmdBudgetCheckCompliance:

    @pytest.mark.parametrize("intent", ["query", "action", "workflow", "research", "audit"])
    def test_budget_check_valid_for_all_intents(self, schema, intent):
        output = cmd_budget_check(intent_type=intent)
        validate(output, schema)


# ── Tests : cmd_route (dry_run uniquement) ──────────────────────────────────

class TestCmdRouteCompliance:

    def test_route_dry_run_valid_schema(self, schema):
        output = cmd_route(
            request="liste les repos Claude",
            dry_run=True,
            root=_ROOT,
        )
        validate(output, schema)

    def test_route_no_tool_found_valid_schema(self, schema):
        """Si aucun tool trouve, l'output doit quand meme etre valide."""
        output = cmd_route(
            request="xyzzy plugh twisty little passages",
            dry_run=True,
            root=_ROOT,
        )
        validate(output, schema)
