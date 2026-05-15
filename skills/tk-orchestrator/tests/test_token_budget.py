"""
test_token_budget.py — Tests du gestionnaire de budget token
TricorderKit v0.8 — tk-orchestrator v0.2.0
"""

import sys
from pathlib import Path


import pytest
from budget.token_tracker import (
    estimate_tokens, allocate_budget, TokenBudget, budget_report,
    ORCHESTRATOR_BASE_BUDGET, INTENT_BUDGETS, SAFETY_BUFFER_PCT,
)


# ── Tests : estimate_tokens ───────────────────────────────────────────────

class TestEstimateTokens:

    def test_empty_string_returns_zero(self):
        assert estimate_tokens("") == 0

    def test_four_chars_one_token(self):
        assert estimate_tokens("abcd") == 1

    def test_eight_chars_two_tokens(self):
        assert estimate_tokens("abcdefgh") == 2

    def test_minimum_one_for_nonempty(self):
        assert estimate_tokens("a") == 1

    def test_long_text(self):
        text = "a" * 400
        assert estimate_tokens(text) == 100

    def test_japanese_text_overestimates(self):
        # Kanji = ~2 bytes par char en UTF-8, heuristique sûre (sur-estimation ok)
        text = "ワンピース" * 10  # 50 chars
        result = estimate_tokens(text)
        assert result >= 1  # Pas de crash, résultat cohérent


# ── Tests : allocate_budget ────────────────────────────────────────────────

class TestAllocateBudget:

    def test_query_budget(self):
        alloc = allocate_budget("query")
        expected_total = ORCHESTRATOR_BASE_BUDGET + INTENT_BUDGETS["query"]
        assert alloc.allocated == expected_total

    def test_research_budget_larger_than_query(self):
        query_alloc = allocate_budget("query")
        research_alloc = allocate_budget("research")
        assert research_alloc.allocated > query_alloc.allocated

    def test_safety_buffer_is_20pct(self):
        alloc = allocate_budget("action")
        expected_buffer = int(alloc.allocated * SAFETY_BUFFER_PCT)
        assert alloc.safety_buffer == expected_buffer

    def test_effective_equals_allocated_minus_buffer(self):
        alloc = allocate_budget("workflow")
        assert alloc.effective_budget == alloc.allocated - alloc.safety_buffer

    def test_input_estimation(self):
        text = "a" * 400  # 100 tokens
        alloc = allocate_budget("query", text)
        assert alloc.input_estimated == 100

    def test_unknown_intent_uses_default(self):
        alloc = allocate_budget("unknown")
        assert alloc.allocated == ORCHESTRATOR_BASE_BUDGET + 300

    def test_all_intent_types(self):
        for intent in ["query", "action", "workflow", "research", "audit", "unknown"]:
            alloc = allocate_budget(intent)
            assert alloc.allocated > 0
            assert alloc.effective_budget > 0
            assert alloc.safety_buffer > 0


# ── Tests : TokenBudget ────────────────────────────────────────────────────────

class TestTokenBudget:

    def test_from_intent_creates_budget(self):
        budget = TokenBudget.from_intent("query")
        assert budget.total > 0
        assert budget.effective > 0
        assert budget.used == 0

    def test_can_allocate_within_budget(self):
        budget = TokenBudget.from_intent("query")
        assert budget.can_allocate(10) is True

    def test_cannot_allocate_over_budget(self):
        budget = TokenBudget(total=100, effective=80)
        assert budget.can_allocate(81) is False

    def test_consume_increments_used(self):
        budget = TokenBudget(total=1000, effective=800)
        budget.consume(100, "test")
        assert budget.used == 100

    def test_consume_returns_false_when_over(self):
        budget = TokenBudget(total=100, effective=80)
        result = budget.consume(90, "over")
        assert result is False
        assert budget.used == 90  # Consommé quand même, mais flaggué

    def test_remaining_decreases_with_consumption(self):
        budget = TokenBudget(total=1000, effective=800)
        budget.consume(200, "step1")
        assert budget.remaining() == 600

    def test_remaining_never_negative(self):
        budget = TokenBudget(total=100, effective=80)
        budget.consume(200, "overflow")
        assert budget.remaining() == 0

    def test_level_safe_at_start(self):
        budget = TokenBudget.from_intent("query")
        assert budget.level() == "SAFE"

    def test_level_critical_when_full(self):
        budget = TokenBudget(total=100, effective=100)
        budget.consume(100, "all")
        assert budget.level() == "CRITICAL"

    def test_to_dict_keys(self):
        budget = TokenBudget.from_intent("query")
        d = budget.to_dict()
        assert "allocated" in d
        assert "effective" in d
        assert "used" in d
        assert "remaining" in d
        assert "level" in d

    def test_to_schema_dict_structure(self):
        budget = TokenBudget(total=1000, effective=800)
        budget.consume(100, "test")
        schema = budget.to_schema_dict()
        assert "input" in schema
        assert "output" in schema
        assert "total" in schema
        assert schema["total"] == 100
        assert schema["input"] + schema["output"] == schema["total"]

    def test_history_tracks_consumptions(self):
        budget = TokenBudget.from_intent("workflow")
        budget.consume(50, "step_1", step=1)
        budget.consume(30, "step_2", step=2)
        assert len(budget.history) == 2
        assert budget.history[0].purpose == "step_1"


# ── Tests : budget_report ───────────────────────────────────────────────────

class TestBudgetReport:

    def test_report_has_required_keys(self):
        report = budget_report("research")
        assert "intent_type" in report
        assert "allocated_tokens" in report
        assert "safety_buffer" in report
        assert "effective_budget" in report
        assert "breakdown" in report

    def test_report_breakdown_sums_correctly(self):
        report = budget_report("query")
        breakdown = report["breakdown"]
        expected = breakdown["orchestration_base"] + breakdown["action_budget"]
        assert report["allocated_tokens"] == expected
