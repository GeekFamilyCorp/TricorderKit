# -*- coding: utf-8 -*-
"""Fixtures partagées pour les tests learning-engine (Lot A, DEC-046)."""
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def valid_run():
    """Run conforme à run_experience.schema.json."""
    return {
        "run_id": "run_2026-06-11_001",
        "workflow_id": "scraping_jp_daily",
        "trigger": "schedule",
        "status": "success",
        "started_at": "2026-06-11T03:00:00Z",
        "ended_at": "2026-06-11T03:04:00Z",
        "duration_seconds": 240,
        "inputs": {"sources": [{"name": "BookWalker", "url": "https://bookwalker.jp/"}]},
        "strategy_used": {"id": "official_sources_first", "version": "1.0"},
        "outputs": {"db_rows_created": 12, "db_rows_updated": 3},
        "metrics": {"pages_fetched": 40, "items_extracted": 30, "duplicates_detected": 2,
                    "official_sources_found": 5, "errors_count": 0,
                    "token_cost_estimate": 5000},
        "quality": {"score_global": 82, "score_freshness": 90,
                    "score_source_reliability": 88, "score_completeness": 75,
                    "score_dedup": 94},
        "human_review_required": True,
    }


@pytest.fixture
def make_card():
    """Fabrique une experience card valide minimale, paramétrable."""
    def _make(strategy="official_sources_first", relevance=0.8, task_type="scraping_jp",
              date="2026-06-11", idx="a"):
        return {
            "experience_card_id": f"exp_2026_06_11_scraping_jp_{idx}",
            "date": date,
            "task_type": task_type,
            "project_scope": "project-a",
            "strategy_used": strategy,
            "run_ids": [f"run_2026-06-11_{idx}"],
            "results": {"items_extracted": 30},
            "quality": {"relevance_score": relevance, "source_reliability_score": 0.85,
                        "completeness_score": 0.7, "freshness_score": 0.9,
                        "duplicate_rate": 0.05},
            "status": "proposed",
            "human_review_required": True,
        }
    return _make


@pytest.fixture
def valid_lesson():
    return {
        "lesson_id": "scraping_jp_official_001",
        "date": "2026-06-11",
        "task_type": "scraping_jp",
        "observation": "Sur 5 runs, official_sources_first performe bien (score 0.82).",
        "action": "Conserver official_sources_first comme stratégie de référence.",
        "confidence": 0.8,
        "evidence": ["run_2026-06-11_001"],
        "source_runs": ["run_2026-06-11_001"],
        "status": "accepted",
        "human_review_required": True,
    }
