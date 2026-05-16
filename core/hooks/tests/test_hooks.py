#!/usr/bin/env python3
"""
tests/test_hooks.py — Suite de tests pytest pour la Hook Layer v0.2.0

Couverture :
- pre_intent_hook : domaines, scoring, hook_id, timestamp, cli_hints
- pre_execution_hook : enrichissement du plan, risk_hint, estimated_tokens
- post_execution_hook : quality_score, tokens_used, schema_valid

Lance avec : pytest core/hooks/tests/test_hooks.py -v
"""
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from core.hooks.pre_intent_hook import run_pre_intent_hook
from core.hooks.pre_execution_hook import run_pre_execution_hook, _estimate_risk, _estimate_tokens
from core.hooks.post_execution_hook import run_post_execution_hook, _compute_quality_score


class TestPreIntentHook:

    def test_returns_required_keys(self):
        out = run_pre_intent_hook("test simple")
        assert "raw_input" in out
        assert "hook_id" in out
        assert "timestamp" in out
        assert "metadata" in out

    def test_hook_id_is_valid_uuid(self):
        out = run_pre_intent_hook("une requête quelconque")
        uid = uuid.UUID(out["hook_id"])
        assert uid.version == 4

    def test_timestamp_is_iso8601(self):
        out = run_pre_intent_hook("test")
        dt = datetime.fromisoformat(out["timestamp"])
        assert dt.tzinfo is not None

    def test_domain_manga(self):
        out = run_pre_intent_hook("Dis-moi tout sur le manga One Piece et ses volumes")
        assert out["metadata"]["domain"] == "manga_anime"
        assert out["metadata"]["requires_deep_research"] is True
        assert "may_use_mangatracker_cli" in out["metadata"]["cli_hints"]

    def test_domain_github(self):
        out = run_pre_intent_hook("Crée un pull request sur le repo TricorderKit")
        assert out["metadata"]["domain"] == "github"
        assert "may_use_github_goat" in out["metadata"]["cli_hints"]

    def test_domain_security(self):
        out = run_pre_intent_hook("Lance un scan semgrep et trivy sur le repo")
        assert out["metadata"]["domain"] == "security"
        assert "may_use_security_audit_cli" in out["metadata"]["cli_hints"]

    def test_domain_eval(self):
        out = run_pre_intent_hook("Lance les tests pytest et l'eval-lab")
        assert out["metadata"]["domain"] == "eval"

    def test_domain_obsidian(self):
        out = run_pre_intent_hook("Mets à jour la note obsidian dans le vault")
        assert out["metadata"]["domain"] == "obsidian"

    def test_domain_other(self):
        out = run_pre_intent_hook("Bonjour, quelle heure est-il ?")
        assert out["metadata"]["domain"] == "other"
        assert out["metadata"]["requires_deep_research"] is False

    def test_non_string_input_tolerated(self):
        out = run_pre_intent_hook(42)
        assert out["raw_input"] == "42"

    def test_empty_input(self):
        out = run_pre_intent_hook("")
        assert out["metadata"]["domain"] == "other"

    def test_multi_domain_scoring_picks_best(self):
        out = run_pre_intent_hook("manga github github github")
        assert out["metadata"]["domain"] == "github"
        assert out["metadata"]["domain_scores"].get("github", 0) > \
               out["metadata"]["domain_scores"].get("manga_anime", 0)


class TestPreExecutionHook:

    def _minimal_plan(self, **kwargs) -> dict:
        base = {"skill": "mangatracker-lookup", "input": "One Piece"}
        base.update(kwargs)
        return base

    def test_returns_hooks_block(self):
        out = run_pre_execution_hook(self._minimal_plan())
        hooks = out["hooks"]
        assert "hook_run_id" in hooks
        assert "hook_timestamp" in hooks
        assert "risk_hint" in hooks
        assert "estimated_tokens" in hooks

    def test_hook_run_id_is_uuid(self):
        out = run_pre_execution_hook(self._minimal_plan())
        assert uuid.UUID(out["hooks"]["hook_run_id"]).version == 4

    def test_timestamp_is_iso8601(self):
        out = run_pre_execution_hook(self._minimal_plan())
        assert datetime.fromisoformat(out["hooks"]["hook_timestamp"]).tzinfo is not None

    def test_estimated_tokens_positive(self):
        out = run_pre_execution_hook(self._minimal_plan())
        assert out["hooks"]["estimated_tokens"] > 0

    def test_estimated_tokens_grows_with_plan_size(self):
        small = run_pre_execution_hook({"skill": "x"})
        large = run_pre_execution_hook({"skill": "x", "context": "a" * 5000})
        assert large["hooks"]["estimated_tokens"] > small["hooks"]["estimated_tokens"]

    def test_risk_hint_read(self):
        assert _estimate_risk({"action_type": "read"}) == "LOW"

    def test_risk_hint_delete(self):
        assert _estimate_risk({"action_type": "delete"}) == "HIGH"

    def test_risk_hint_explicit(self):
        assert _estimate_risk({"risk_hint": "CRITICAL"}) == "CRITICAL"

    def test_risk_hint_name_heuristic(self):
        assert _estimate_risk({"goat": "delete-old-notes"}) == "HIGH"
        assert _estimate_risk({"skill": "search-results"}) == "LOW"

    def test_plan_not_mutated(self):
        plan = {"skill": "test", "input": "foo"}
        original = dict(plan)
        run_pre_execution_hook(plan)
        assert plan == original


class TestPostExecutionHook:

    def _plan_with_hooks(self, hook_run_id: str = None) -> dict:
        rid = hook_run_id or str(uuid.uuid4())
        return {
            "skill": "mangatracker-lookup",
            "hooks": {
                "hook_run_id": rid,
                "hook_timestamp": datetime.now(timezone.utc).isoformat(),
                "risk_hint": "LOW",
                "estimated_tokens": 200,
            },
        }

    def _full_result(self) -> dict:
        return {
            "status": "ok",
            "output": "Résultat de recherche",
            "sources": ["https://source1.jp"],
            "reliability": "high",
        }

    def test_quality_score_full(self):
        score, breakdown = _compute_quality_score(self._full_result())
        assert score == 1.0
        assert all(breakdown.values())

    def test_quality_score_partial(self):
        result = {"status": "ok", "output": "data"}
        score, breakdown = _compute_quality_score(result)
        assert score == 0.5
        assert breakdown["has_status"] is True
        assert breakdown["has_sources"] is False

    def test_quality_score_empty(self):
        score, _ = _compute_quality_score({})
        assert score == 0.0

    def test_hook_run_id_propagated(self):
        rid = str(uuid.uuid4())
        out = run_post_execution_hook(self._plan_with_hooks(rid), self._full_result())
        assert out["hooks"]["hook_run_id"] == rid

    def test_tokens_used_from_result(self):
        plan = self._plan_with_hooks()
        result = {**self._full_result(), "tokens_used": 123}
        out = run_post_execution_hook(plan, result)
        assert out["hooks"]["tokens_used"] == 123

    def test_tokens_used_fallback_to_estimated(self):
        out = run_post_execution_hook(self._plan_with_hooks(), self._full_result())
        assert out["hooks"]["tokens_used"] == 200

    def test_no_mutation_of_original_result(self):
        plan = self._plan_with_hooks()
        result = self._full_result()
        original = dict(result)
        run_post_execution_hook(plan, result)
        assert result == original
