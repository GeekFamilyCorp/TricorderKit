# -*- coding: utf-8 -*-
"""
Tests du moteur de fiabilite des sources (N6, DEC-046).
Dry-run strict, scoring transparent, contrat skill_output.
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
ENGINE = SCRIPTS_DIR / "source_reliability_engine.py"
SKILL_CONTRACT = REPO_ROOT / "core" / "contracts" / "skill_output.schema.json"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import source_reliability_engine as sre  # noqa: E402

REF = dt.date(2026, 6, 11)


# ── Sous-scores ─────────────────────────────────────────────────────────────────
def test_freshness_full_then_zero():
    assert sre.freshness_score(dt.date(2026, 6, 11), REF) == 100.0
    assert sre.freshness_score(dt.date(2026, 5, 1), REF) == 0.0
    assert sre.freshness_score(None, REF) == 0.0


def test_freshness_decays_monotonically():
    a = sre.freshness_score(dt.date(2026, 6, 5), REF)
    b = sre.freshness_score(dt.date(2026, 6, 1), REF)
    assert 0.0 < b < a < 100.0


def test_extractability_and_dedup_and_reliability():
    assert sre.extractability_score(30, 40) == 75.0
    assert sre.extractability_score(0, 0) == 0.0
    assert sre.dedup_score(90, 10) == 90.0
    assert sre.reliability_score(98, 2) == 98.0


# ── Agregation ──────────────────────────────────────────────────────────────────
def test_score_source_high_vs_low():
    high = sre.score_source([
        {"source": "a", "official": True, "pages_fetched": 40, "items_extracted": 38,
         "duplicates": 1, "errors": 0, "latest_item_date": "2026-06-11"}], REF)
    low = sre.score_source([
        {"source": "b", "official": False, "pages_fetched": 50, "items_extracted": 8,
         "duplicates": 9, "errors": 7, "latest_item_date": "2026-04-01"}], REF)
    assert high["reliability_score"] > low["reliability_score"]
    assert high["sub_scores"]["officiality"] == 100.0
    assert low["sub_scores"]["officiality"] == 0.0


def test_build_proposals_computes_delta_from_registry():
    obs = [{"source": "a", "official": True, "pages_fetched": 10, "items_extracted": 10,
            "duplicates": 0, "errors": 0, "latest_item_date": "2026-06-11"}]
    props = sre.build_proposals(obs, {"a": 50.0}, REF)
    assert len(props) == 1
    assert props[0]["old_score"] == 50.0
    assert props[0]["delta"] == round(props[0]["new_score"] - 50.0, 1)


# ── Contrat skill_output ────────────────────────────────────────────────────────
def test_dryrun_envelope_conforms_contract():
    import jsonschema
    schema = json.loads(SKILL_CONTRACT.read_text(encoding="utf-8"))
    cls = getattr(jsonschema, "Draft7Validator", None) or jsonschema.validators.validator_for(schema)
    env = sre.skill_output_dryrun(
        sre.build_proposals(
            [{"source": "a", "official": True, "pages_fetched": 10, "items_extracted": 9,
              "duplicates": 0, "errors": 0, "latest_item_date": "2026-06-11"}], {}, REF),
        "resume de test")
    assert env["status"] == "dry_run"
    errors = list(cls(schema).iter_errors(env))
    assert errors == [], errors


# ── Bout-en-bout : lecture seule, exit 0, jamais d'ecriture ─────────────────────
def test_cli_reads_file_dryrun():
    # tempfile systeme (hors repo) : evite le piege .pytest_tmp verrouille (R36).
    import tempfile
    obs = [{"source": "a", "official": True, "pages_fetched": 10, "items_extracted": 10,
            "duplicates": 0, "errors": 0, "latest_item_date": "2026-06-11"}]
    d = Path(tempfile.mkdtemp(prefix="sre_test_"))
    try:
        f = d / "obs.json"
        f.write_text(json.dumps(obs), encoding="utf-8")
        r = subprocess.run([sys.executable, str(ENGINE), "--input", str(f),
                            "--ref-date", "2026-06-11"],
                           capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0
        env = json.loads(r.stdout)
        assert env["status"] == "dry_run"
        assert env["output"]["data"]["count"] == 1
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


def test_cli_empty_observations_ok():
    r = subprocess.run([sys.executable, str(ENGINE), "--input", "-"],
                       input="[]", capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0
    assert json.loads(r.stdout)["status"] == "dry_run"
