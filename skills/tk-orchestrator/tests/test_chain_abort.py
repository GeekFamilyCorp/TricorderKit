"""
test_chain_abort.py — Tests de la politique Abort-on-Failure
TricorderKit v0.8 — tk-orchestrator v0.2.0
"""

import sys
from pathlib import Path
from typing import Dict, Optional


import pytest
from context.chain_executor import (
    ChainExecutor, ChainStep, ChainResult,
    CHAIN_STATUS_SUCCESS, CHAIN_STATUS_ERROR,
    CHAIN_STATUS_SKIPPED, CHAIN_STATUS_LIMIT, CHAIN_STATUS_DRY_RUN,
    MAX_CHAIN_STEPS,
)
from budget.token_tracker import TokenBudget


# ── Helpers ───────────────────────────────────────────────────────────────

def make_budget(total: int = 2000) -> TokenBudget:
    return TokenBudget(total=total, effective=int(total * 0.8))


def make_step(tool: str = "mock-tool", cmd: str = "run") -> ChainStep:
    return ChainStep(tool=tool, command=cmd, args={})


def runner_always_success(step: ChainStep, prev: Optional[Dict], dry_run: bool) -> Dict:
    return {"status": "success", "output": {"result": "ok"}, "tokens": 10}


def runner_always_error(step: ChainStep, prev: Optional[Dict], dry_run: bool) -> Dict:
    return {"status": "error", "output": None, "tokens": 0, "error": "Mock error"}


def runner_fail_at(n: int):
    """Runner qui échoue à l'étape n (1-indexed)."""
    call_count = {"count": 0}
    def runner(step: ChainStep, prev: Optional[Dict], dry_run: bool) -> Dict:
        call_count["count"] += 1
        if call_count["count"] == n:
            return {"status": "error", "output": None, "tokens": 0, "error": f"Step {n} failed"}
        return {"status": "success", "output": {"result": "ok"}, "tokens": 10}
    return runner


def runner_raises():
    """Runner qui lève une exception."""
    def runner(step: ChainStep, prev: Optional[Dict], dry_run: bool) -> Dict:
        raise RuntimeError("Unexpected crash")
    return runner


# ── Tests : Exécution normale ───────────────────────────────────────────────

class TestChainNormalExecution:

    def test_single_step_success(self):
        executor = ChainExecutor(budget=make_budget())
        result = executor.execute([make_step()], runner_always_success)
        assert result.overall_status == CHAIN_STATUS_SUCCESS
        assert len(result.steps) == 1
        assert result.steps[0].status == CHAIN_STATUS_SUCCESS

    def test_three_steps_all_success(self):
        executor = ChainExecutor(budget=make_budget())
        steps = [make_step(f"tool-{i}") for i in range(3)]
        result = executor.execute(steps, runner_always_success)
        assert result.overall_status == CHAIN_STATUS_SUCCESS
        assert result.success_count == 3
        assert result.skipped_count == 0

    def test_tokens_accumulated(self):
        executor = ChainExecutor(budget=make_budget())
        steps = [make_step() for _ in range(3)]
        result = executor.execute(steps, runner_always_success)
        assert result.total_tokens == 30  # 3 × 10 tokens


# ── Tests : Abort-on-Failure ────────────────────────────────────────────────

class TestAbortOnFailure:

    def test_first_step_fails_aborts_rest(self):
        executor = ChainExecutor(budget=make_budget())
        steps = [make_step(f"tool-{i}") for i in range(3)]
        result = executor.execute(steps, runner_always_error)
        assert result.overall_status == "partial"
        assert result.aborted_at_step == 1
        assert result.steps[0].status == CHAIN_STATUS_ERROR
        assert result.steps[1].status == CHAIN_STATUS_SKIPPED
        assert result.steps[2].status == CHAIN_STATUS_SKIPPED

    def test_step_2_fails_step_3_skipped(self):
        executor = ChainExecutor(budget=make_budget())
        steps = [make_step(f"tool-{i}") for i in range(3)]
        result = executor.execute(steps, runner_fail_at(2))
        assert result.overall_status == "partial"
        assert result.aborted_at_step == 2
        assert result.steps[0].status == CHAIN_STATUS_SUCCESS
        assert result.steps[1].status == CHAIN_STATUS_ERROR
        assert result.steps[2].status == CHAIN_STATUS_SKIPPED

    def test_abort_reason_is_populated(self):
        executor = ChainExecutor(budget=make_budget())
        steps = [make_step()]
        result = executor.execute(steps, runner_always_error)
        assert result.abort_reason is not None
        assert len(result.abort_reason) > 0

    def test_exception_in_runner_is_caught(self):
        executor = ChainExecutor(budget=make_budget())
        steps = [make_step(), make_step()]
        result = executor.execute(steps, runner_raises())
        assert result.overall_status == "partial"
        assert result.steps[0].status == CHAIN_STATUS_ERROR
        assert result.steps[1].status == CHAIN_STATUS_SKIPPED

    def test_partial_tokens_still_counted(self):
        executor = ChainExecutor(budget=make_budget())
        steps = [make_step("t1"), make_step("t2"), make_step("t3")]
        result = executor.execute(steps, runner_fail_at(2))
        # Seule étape 1 (success) a des tokens
        assert result.total_tokens == 10


# ── Tests : Limite de steps ─────────────────────────────────────────────────

class TestChainLimit:

    def test_max_steps_not_exceeded(self):
        executor = ChainExecutor(budget=make_budget(), max_steps=3)
        steps = [make_step(f"tool-{i}") for i in range(5)]
        result = executor.execute(steps, runner_always_success)
        # Les steps au-delà de la limite sont tronqués
        executed = [s for s in result.steps if s.status != CHAIN_STATUS_SKIPPED]
        assert len(executed) <= 3

    def test_default_max_steps_is_five(self):
        assert MAX_CHAIN_STEPS == 5

    def test_exactly_five_steps_ok(self):
        executor = ChainExecutor(budget=make_budget())
        steps = [make_step(f"tool-{i}") for i in range(5)]
        result = executor.execute(steps, runner_always_success)
        assert result.overall_status == CHAIN_STATUS_SUCCESS


# ── Tests : Dry-run ────────────────────────────────────────────────────────────

class TestDryRun:

    def test_dry_run_does_not_execute_runner(self):
        """En dry_run, le runner ne doit pas être appelé."""
        call_count = {"n": 0}

        def counting_runner(step, prev, dry_run):
            call_count["n"] += 1
            return {"status": "success", "output": {}, "tokens": 0}

        executor = ChainExecutor(budget=make_budget(), dry_run=True)
        steps = [make_step()]
        result = executor.execute(steps, counting_runner)
        assert call_count["n"] == 0

    def test_dry_run_status_is_dry_run(self):
        executor = ChainExecutor(budget=make_budget(), dry_run=True)
        steps = [make_step()]
        result = executor.execute(steps, runner_always_success)
        assert result.overall_status == CHAIN_STATUS_DRY_RUN

    def test_dry_run_steps_marked_dry_run(self):
        executor = ChainExecutor(budget=make_budget(), dry_run=True)
        steps = [make_step(), make_step()]
        result = executor.execute(steps, runner_always_success)
        for step in result.steps:
            assert step.status == CHAIN_STATUS_DRY_RUN


# ── Tests : to_dict ───────────────────────────────────────────────────────────────

class TestChainResultDict:

    def test_to_dict_has_required_keys(self):
        executor = ChainExecutor(budget=make_budget())
        result = executor.execute([make_step()], runner_always_success)
        d = result.to_dict()
        assert "overall_status" in d
        assert "steps" in d
        assert "total_tokens" in d
        assert "summary" in d

    def test_steps_in_dict_have_step_number(self):
        executor = ChainExecutor(budget=make_budget())
        steps = [make_step(), make_step()]
        result = executor.execute(steps, runner_always_success)
        d = result.to_dict()
        assert d["steps"][0]["step"] == 1
        assert d["steps"][1]["step"] == 2
