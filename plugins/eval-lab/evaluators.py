#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluators.py — Evaluateurs de qualite eval-lab (TricorderKit, DEC-046 / N5).

Cinq evaluateurs notent un run (metrics dict) sur une grille 0..100 et lui
attribuent une note (grade). Fonctions PURES (zero dependance pip, zero effet
de bord) : faciles a tester et a composer.

  - scraping_quality      : extraction vs pages, erreurs, completude
  - source_reliability    : officialite, fraicheur, erreurs (signal par run)
  - dedup_quality         : taux de doublons + faux positifs de dedup
  - rag_retrieval_quality : precision@k, rappel@k, MRR
  - cost_latency          : respect des budgets tokens et latence

Chaque evaluateur retourne :
  {evaluator, score, grade, sub_scores, thresholds, notes}

`evaluate(kind, metrics)` dispatch ; `EVALUATORS` liste les types disponibles.
Grade : score >= 85 excellent | >= 70 good | >= 50 warn | < 50 fail.
"""
from __future__ import annotations

from typing import Any, Callable

# Seuils de notation communs (grille §16).
GRADE_THRESHOLDS = [(85.0, "excellent"), (70.0, "good"), (50.0, "warn"), (0.0, "fail")]
PASS_GRADES = {"excellent", "good"}


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def grade_for(score: float) -> str:
    for threshold, label in GRADE_THRESHOLDS:
        if score >= threshold:
            return label
    return "fail"


def _num(metrics: dict, key: str, default: float = 0.0) -> float:
    v = metrics.get(key, default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _result(kind: str, score: float, sub: dict, thresholds: dict,
            notes: list[str]) -> dict:
    score = round(_clamp(score), 1)
    return {
        "evaluator": kind,
        "score": score,
        "grade": grade_for(score),
        "passed": grade_for(score) in PASS_GRADES,
        "sub_scores": {k: round(_clamp(v), 1) for k, v in sub.items()},
        "thresholds": thresholds,
        "notes": notes,
    }


# ── 1. scraping_quality ─────────────────────────────────────────────────────────
def eval_scraping_quality(metrics: dict) -> dict:
    """Note la qualite d'un run de scraping.

    Entrees : pages_fetched, items_extracted, errors, expected_items (optionnel).
    """
    pages = _num(metrics, "pages_fetched")
    items = _num(metrics, "items_extracted")
    errors = _num(metrics, "errors")
    expected = _num(metrics, "expected_items", items)

    extraction = 100.0 * min(1.0, items / pages) if pages > 0 else (0.0 if items <= 0 else 50.0)
    error_health = 100.0 * (1 - errors / (items + errors)) if (items + errors) > 0 else 100.0
    completeness = 100.0 * min(1.0, items / expected) if expected > 0 else 100.0

    sub = {"extraction": extraction, "error_health": error_health, "completeness": completeness}
    score = 0.45 * extraction + 0.25 * error_health + 0.30 * completeness
    notes = []
    if pages > 0 and items / pages < 0.3:
        notes.append("taux d'extraction faible (< 0.3 item/page)")
    if errors > 0:
        notes.append(f"{int(errors)} erreur(s) de scraping")
    return _result("scraping_quality", score, sub,
                   {"pass": ">=70", "warn": "50-69", "fail": "<50"}, notes)


# ── 2. source_reliability ───────────────────────────────────────────────────────
def eval_source_reliability(metrics: dict) -> dict:
    """Note la fiabilite des sources d'un run (signal agrege par run).

    Entrees : official_ratio (0..1), freshness_days, errors, items.
    """
    official_ratio = _clamp(_num(metrics, "official_ratio"), 0.0, 1.0)
    freshness_days = _num(metrics, "freshness_days", 999)
    errors = _num(metrics, "errors")
    items = _num(metrics, "items", _num(metrics, "items_extracted"))

    officiality = 100.0 * official_ratio
    if freshness_days <= 2:
        freshness = 100.0
    elif freshness_days >= 30:
        freshness = 0.0
    else:
        freshness = 100.0 * (1 - (freshness_days - 2) / 28)
    error_health = 100.0 * (1 - errors / (items + errors)) if (items + errors) > 0 else 100.0

    sub = {"officiality": officiality, "freshness": freshness, "error_health": error_health}
    score = 0.45 * officiality + 0.35 * freshness + 0.20 * error_health
    notes = []
    if official_ratio < 0.5:
        notes.append("moins de 50% de sources officielles")
    if freshness_days > 14:
        notes.append(f"contenu age ({int(freshness_days)} j)")
    return _result("source_reliability", score, sub,
                   {"pass": ">=70", "warn": "50-69", "fail": "<50"}, notes)


# ── 3. dedup_quality ────────────────────────────────────────────────────────────
def eval_dedup_quality(metrics: dict) -> dict:
    """Note la qualite de la deduplication.

    Entrees : items, duplicates, false_dedup (faux positifs : items uniques
    fusionnes a tort).
    """
    items = _num(metrics, "items", _num(metrics, "items_extracted"))
    duplicates = _num(metrics, "duplicates")
    false_dedup = _num(metrics, "false_dedup")

    total = items + duplicates
    dup_handling = 100.0 * (1 - duplicates / total) if total > 0 else 100.0
    # Penalite forte pour les faux positifs (fusions a tort) : plus grave.
    precision = 100.0 * (1 - false_dedup / items) if items > 0 else 100.0

    sub = {"dup_handling": dup_handling, "precision": precision}
    score = 0.50 * dup_handling + 0.50 * precision
    notes = []
    if total > 0 and duplicates / total > 0.2:
        notes.append("taux de doublons eleve (> 20%)")
    if false_dedup > 0:
        notes.append(f"{int(false_dedup)} fusion(s) a tort (faux positifs)")
    return _result("dedup_quality", score, sub,
                   {"pass": ">=70", "warn": "50-69", "fail": "<50"}, notes)


# ── 4. rag_retrieval_quality ────────────────────────────────────────────────────
def eval_rag_retrieval_quality(metrics: dict) -> dict:
    """Note la qualite de recuperation RAG.

    Entrees : precision_at_k (0..1), recall_at_k (0..1), mrr (0..1).
    """
    precision = _clamp(_num(metrics, "precision_at_k"), 0.0, 1.0)
    recall = _clamp(_num(metrics, "recall_at_k"), 0.0, 1.0)
    mrr = _clamp(_num(metrics, "mrr"), 0.0, 1.0)

    sub = {"precision_at_k": precision * 100, "recall_at_k": recall * 100, "mrr": mrr * 100}
    score = (0.40 * precision + 0.35 * recall + 0.25 * mrr) * 100
    notes = []
    if precision < 0.5:
        notes.append("precision@k faible (< 0.5)")
    if recall < 0.5:
        notes.append("rappel@k faible (< 0.5)")
    return _result("rag_retrieval_quality", score, sub,
                   {"pass": ">=70", "warn": "50-69", "fail": "<50"}, notes)


# ── 5. cost_latency ─────────────────────────────────────────────────────────────
def eval_cost_latency(metrics: dict) -> dict:
    """Note le respect des budgets de cout (tokens) et de latence.

    Entrees : token_cost, token_budget, latency_ms, latency_budget_ms.
    Un run sous budget = 100 ; au-dela, penalite proportionnelle au depassement.
    """
    token_cost = _num(metrics, "token_cost")
    token_budget = _num(metrics, "token_budget")
    latency = _num(metrics, "latency_ms")
    latency_budget = _num(metrics, "latency_budget_ms")

    def budget_score(used: float, budget: float) -> float:
        if budget <= 0:
            return 100.0  # pas de budget defini -> neutre
        if used <= budget:
            return 100.0
        overrun = (used - budget) / budget
        return _clamp(100.0 - overrun * 100.0)

    cost_score = budget_score(token_cost, token_budget)
    latency_score = budget_score(latency, latency_budget)

    sub = {"cost": cost_score, "latency": latency_score}
    score = 0.55 * cost_score + 0.45 * latency_score
    notes = []
    if token_budget > 0 and token_cost > token_budget:
        notes.append(f"budget tokens depasse ({int(token_cost)} > {int(token_budget)})")
    if latency_budget > 0 and latency > latency_budget:
        notes.append(f"budget latence depasse ({int(latency)} > {int(latency_budget)} ms)")
    return _result("cost_latency", score, sub,
                   {"pass": ">=70", "warn": "50-69", "fail": "<50"}, notes)


# ── Registre & dispatch ─────────────────────────────────────────────────────────
EVALUATORS: dict[str, Callable[[dict], dict]] = {
    "scraping_quality": eval_scraping_quality,
    "source_reliability": eval_source_reliability,
    "dedup_quality": eval_dedup_quality,
    "rag_retrieval_quality": eval_rag_retrieval_quality,
    "cost_latency": eval_cost_latency,
}


def evaluate(kind: str, metrics: dict) -> dict:
    """Applique un evaluateur nomme a un dict de metriques."""
    fn = EVALUATORS.get(kind)
    if fn is None:
        raise KeyError(f"evaluateur inconnu: {kind!r} (connus: {', '.join(EVALUATORS)})")
    return fn(metrics or {})


def evaluate_all(metrics: dict) -> dict:
    """Applique tous les evaluateurs pertinents et agrege le score global.

    Seuls les evaluateurs dont au moins une metrique d'entree est presente sont
    appliques (evite de penaliser un run pour une dimension non mesuree).
    """
    inputs_by_kind = {
        "scraping_quality": ("pages_fetched", "items_extracted", "errors", "expected_items"),
        "source_reliability": ("official_ratio", "freshness_days"),
        "dedup_quality": ("duplicates", "false_dedup"),
        "rag_retrieval_quality": ("precision_at_k", "recall_at_k", "mrr"),
        "cost_latency": ("token_cost", "token_budget", "latency_ms", "latency_budget_ms"),
    }
    results = []
    for kind, keys in inputs_by_kind.items():
        if any(k in metrics for k in keys):
            results.append(evaluate(kind, metrics))
    overall = round(sum(r["score"] for r in results) / len(results), 1) if results else 0.0
    return {
        "overall_score": overall,
        "overall_grade": grade_for(overall),
        "passed": grade_for(overall) in PASS_GRADES,
        "evaluators": results,
        "count": len(results),
    }
