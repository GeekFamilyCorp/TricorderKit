"""
conftest.py — Fixtures partagées pour les tests eval-lab
TricorderKit eval-lab v0.1.0
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

# -- Output de référence conforme au schéma -----------------------------------

VALID_OUTPUT = {
    "status": "success",
    "skill_name": "test-skill",
    "skill_version": "1.0.0",
    "timestamp": "2026-05-16T00:00:00+00:00",
    "duration_ms": 1200,
    "tokens_used": {"input": 100, "output": 50, "total": 150},
    "output": {
        "summary": "Test réussi — 5 items traités",
        "data": {"total_items": 5, "processed": 5, "errors": 0},
        "files_created": [],
        "next_steps": ["Vérifier les résultats"],
    },
}


@pytest.fixture
def valid_output() -> dict:
    """Output valide conforme à skill_output.schema.json."""
    return dict(VALID_OUTPUT)


@pytest.fixture
def output_missing_status() -> dict:
    """Output sans champ 'status' (violation CRITICAL)."""
    o = dict(VALID_OUTPUT)
    del o["status"]
    return o


@pytest.fixture
def output_wrong_status() -> dict:
    """Output avec status invalide (violation CRITICAL)."""
    o = dict(VALID_OUTPUT)
    o["status"] = "unknown_status"
    return o


@pytest.fixture
def output_missing_summary() -> dict:
    """Output sans output.summary (violation HIGH)."""
    import copy
    o = copy.deepcopy(VALID_OUTPUT)
    del o["output"]["summary"]
    return o


@pytest.fixture
def output_token_mismatch() -> dict:
    """Output avec tokens_used incoherents (input+output != total)."""
    import copy
    o = copy.deepcopy(VALID_OUTPUT)
    o["tokens_used"] = {"input": 100, "output": 50, "total": 999}
    return o


@pytest.fixture
def output_duration_aberrant() -> dict:
    """Output avec duration_ms hors bornes (> 300 000ms)."""
    import copy
    o = copy.deepcopy(VALID_OUTPUT)
    o["duration_ms"] = 500_000
    return o


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    """Chemin temporaire pour une base SQLite de test."""
    return tmp_path / "test_baselines.sqlite"


@pytest.fixture
def tmp_schema(tmp_path: Path) -> Path:
    """Schema JSON minimal pour les tests unitaires de schema_validator."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["status", "skill_name", "skill_version", "timestamp", "output"],
        "properties": {
            "status": {"type": "string", "enum": ["success", "partial", "error", "dry_run"]},
            "skill_name": {"type": "string"},
            "skill_version": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "duration_ms": {"type": "integer"},
            "tokens_used": {
                "type": "object",
                "properties": {
                    "input": {"type": "integer"},
                    "output": {"type": "integer"},
                    "total": {"type": "integer"},
                },
            },
            "output": {
                "type": "object",
                "required": ["summary"],
                "properties": {
                    "summary": {"type": "string", "maxLength": 500},
                    "data": {"type": "object"},
                    "files_created": {"type": "array"},
                    "next_steps": {"type": "array"},
                },
            },
        },
    }
    path = tmp_path / "skill_output.schema.json"
    path.write_text(json.dumps(schema), encoding="utf-8")
    return path
