"""
test_evaluators.py — Tests des evaluateurs de qualite eval-lab (N5, DEC-046).
TricorderKit eval-lab v0.1.0
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluators import (  # noqa: E402
    EVALUATORS, evaluate, evaluate_all, grade_for,
    eval_scraping_quality, eval_source_reliability, eval_dedup_quality,
    eval_rag_retrieval_quality, eval_cost_latency,
)


# ── grade_for ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("score,grade", [
    (95, "excellent"), (85, "excellent"), (70, "good"), (69.9, "warn"),
    (50, "warn"), (49, "fail"), (0, "fail"),
])
def test_grade_for_thresholds(score, grade):
    assert grade_for(score) == grade


# ── Structure commune ───────────────────────────────────────────────────────────
def test_result_shape_keys():
    r = eval_scraping_quality({"pages_fetched": 10, "items_extracted": 10})
    assert set(r) >= {"evaluator", "score", "grade", "passed", "sub_scores", "thresholds", "notes"}
    assert 0 <= r["score"] <= 100


# ── 1. scraping_quality ─────────────────────────────────────────────────────────
def test_scraping_quality_high_vs_low():
    high = eval_scraping_quality({"pages_fetched": 40, "items_extracted": 38, "errors": 0})
    low = eval_scraping_quality({"pages_fetched": 100, "items_extracted": 8, "errors": 10})
    assert high["score"] > low["score"]
    assert high["passed"] is True
    assert low["passed"] is False


# ── 2. source_reliability ───────────────────────────────────────────────────────
def test_source_reliability_official_fresh_beats_unofficial_stale():
    good = eval_source_reliability({"official_ratio": 1.0, "freshness_days": 1, "errors": 0, "items": 20})
    bad = eval_source_reliability({"official_ratio": 0.0, "freshness_days": 40, "errors": 5, "items": 20})
    assert good["score"] > bad["score"]
    assert good["sub_scores"]["freshness"] == 100.0
    assert bad["sub_scores"]["freshness"] == 0.0


# ── 3. dedup_quality ────────────────────────────────────────────────────────────
def test_dedup_quality_penalizes_false_positives():
    clean = eval_dedup_quality({"items": 100, "duplicates": 2, "false_dedup": 0})
    falsy = eval_dedup_quality({"items": 100, "duplicates": 2, "false_dedup": 20})
    assert clean["score"] > falsy["score"]
    assert any("faux positifs" in n for n in falsy["notes"])


# ── 4. rag_retrieval_quality ────────────────────────────────────────────────────
def test_rag_retrieval_quality_scales_with_metrics():
    strong = eval_rag_retrieval_quality({"precision_at_k": 0.9, "recall_at_k": 0.85, "mrr": 0.8})
    weak = eval_rag_retrieval_quality({"precision_at_k": 0.3, "recall_at_k": 0.2, "mrr": 0.25})
    assert strong["score"] > weak["score"]
    assert strong["passed"] is True


# ── 5. cost_latency ─────────────────────────────────────────────────────────────
def test_cost_latency_under_budget_is_perfect():
    ok = eval_cost_latency({"token_cost": 5000, "token_budget": 10000,
                            "latency_ms": 800, "latency_budget_ms": 2000})
    assert ok["score"] == 100.0
    assert ok["passed"] is True


def test_cost_latency_penalizes_overrun():
    over = eval_cost_latency({"token_cost": 20000, "token_budget": 10000,
                              "latency_ms": 5000, "latency_budget_ms": 2000})
    assert over["score"] < 100.0
    assert any("budget" in n for n in over["notes"])


# ── Dispatch & agregat ──────────────────────────────────────────────────────────
def test_evaluate_dispatch_and_unknown():
    assert evaluate("scraping_quality", {"pages_fetched": 10, "items_extracted": 9})["evaluator"] == "scraping_quality"
    with pytest.raises(KeyError):
        evaluate("nope", {})


def test_evaluate_all_only_relevant_evaluators():
    # Seules les dimensions mesurees sont notees.
    agg = evaluate_all({"precision_at_k": 0.8, "recall_at_k": 0.7, "mrr": 0.6})
    kinds = {e["evaluator"] for e in agg["evaluators"]}
    assert kinds == {"rag_retrieval_quality"}
    assert agg["count"] == 1
    assert 0 <= agg["overall_score"] <= 100


def test_registry_has_five_evaluators():
    assert len(EVALUATORS) == 5
