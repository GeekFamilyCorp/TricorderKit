"""
test_regression_checker.py — Tests unitaires regression_checker.py
TricorderKit eval-lab v0.1.0
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from regression_checker import (
    RegressionDetail,
    RegressionResult,
    check_regression,
)


# -- Fixtures locales ---------------------------------------------------------

@pytest.fixture
def baseline(valid_output):
    return copy.deepcopy(valid_output)


# -- check_regression ---------------------------------------------------------

class TestCheckRegression:
    def test_identical_outputs_no_regressions(self, baseline, valid_output):
        result = check_regression(baseline, valid_output)
        assert result.has_regressions is False
        assert result.regressions == []

    def test_baseline_version_extracted(self, baseline, valid_output):
        result = check_regression(baseline, valid_output)
        assert result.baseline_version == baseline["skill_version"]
        assert result.current_version == valid_output["skill_version"]

    def test_field_missing_in_current_is_detected(self, baseline, valid_output):
        current = copy.deepcopy(valid_output)
        del current["skill_name"]
        result = check_regression(baseline, current)
        assert result.has_regressions is True
        missing = [r for r in result.regressions if r.kind == "field_missing"]
        assert len(missing) >= 1
        assert any(r.path == "skill_name" for r in missing)

    def test_critical_field_missing_is_critical(self, baseline, valid_output):
        for critical_field in ("status", "skill_name", "skill_version", "timestamp", "output"):
            current = copy.deepcopy(valid_output)
            del current[critical_field]
            result = check_regression(baseline, current)
            assert result.has_critical, f"Champ critique '{critical_field}' non detecte comme CRITICAL"

    def test_type_changed_is_detected(self, baseline, valid_output):
        current = copy.deepcopy(valid_output)
        current["skill_version"] = 100
        result = check_regression(baseline, current)
        assert result.has_regressions is True
        type_changes = [r for r in result.regressions if r.kind == "type_changed"]
        assert len(type_changes) >= 1

    def test_status_enum_invalid_is_critical(self, baseline, valid_output):
        current = copy.deepcopy(valid_output)
        current["status"] = "flying_saucer"
        result = check_regression(baseline, current)
        enum_issues = [r for r in result.regressions if r.kind == "enum_invalid"]
        assert len(enum_issues) >= 1
        assert any(r.severity == "CRITICAL" for r in enum_issues)

    def test_status_valid_values_accepted(self, baseline, valid_output):
        for valid_status in ("success", "partial", "error", "dry_run"):
            current = copy.deepcopy(valid_output)
            current["status"] = valid_status
            b = copy.deepcopy(baseline)
            b["status"] = valid_status
            result = check_regression(b, current)
            enum_issues = [r for r in result.regressions if r.kind == "enum_invalid"]
            assert len(enum_issues) == 0, f"Status '{valid_status}' rejete a tort"

    def test_token_mismatch_detected(self, baseline, output_token_mismatch):
        result = check_regression(baseline, output_token_mismatch)
        token_issues = [r for r in result.regressions if "tokens_used" in r.path]
        assert len(token_issues) >= 1

    def test_token_total_exceeded_is_high(self, baseline, valid_output):
        current = copy.deepcopy(valid_output)
        current["tokens_used"] = {"input": 150_000, "output": 100_000, "total": 250_000}
        result = check_regression(baseline, current)
        high = [r for r in result.regressions if r.path == "tokens_used.total" and r.severity == "HIGH"]
        assert len(high) >= 1

    def test_duration_aberrant_detected(self, baseline, output_duration_aberrant):
        result = check_regression(baseline, output_duration_aberrant)
        dur_issues = [r for r in result.regressions if r.path == "duration_ms"]
        assert len(dur_issues) >= 1

    def test_duration_valid_not_flagged(self, baseline, valid_output):
        result = check_regression(baseline, valid_output)
        dur_issues = [r for r in result.regressions if r.path == "duration_ms"]
        assert len(dur_issues) == 0

    def test_nested_field_missing_detected(self, baseline, valid_output):
        current = copy.deepcopy(valid_output)
        del current["output"]["summary"]
        result = check_regression(baseline, current)
        nested = [r for r in result.regressions if "summary" in r.path]
        assert len(nested) >= 1

    def test_recursive_depth_limit_respected(self, baseline, valid_output):
        current = copy.deepcopy(valid_output)
        current["output"]["data"]["level1"] = {"level2": {"level3": {"level4": "deep"}}}
        b = copy.deepcopy(baseline)
        b["output"]["data"]["level1"] = {"level2": {"level3": {"level4": "deep"}}}
        result = check_regression(b, current)
        # Pas d'exception = succes


# -- RegressionResult ---------------------------------------------------------

class TestRegressionResult:
    def test_has_critical_false_when_all_low(self):
        r = RegressionResult(
            has_regressions=True,
            regressions=[
                RegressionDetail("x", "field_missing", "str", "null", "LOW")
            ],
        )
        assert r.has_critical is False

    def test_has_critical_true_when_critical_present(self):
        r = RegressionResult(
            has_regressions=True,
            regressions=[
                RegressionDetail("status", "field_missing", "str", "null", "CRITICAL")
            ],
        )
        assert r.has_critical is True

    def test_to_dict_structure(self):
        r = RegressionResult(
            has_regressions=True,
            regressions=[
                RegressionDetail("status", "enum_invalid", "{'success',...}", "alien", "CRITICAL")
            ],
            baseline_version="1.0.0",
            current_version="1.1.0",
        )
        d = r.to_dict()
        assert d["has_regressions"] is True
        assert d["baseline_version"] == "1.0.0"
        assert d["current_version"] == "1.1.0"
        assert len(d["regressions"]) == 1
        reg = d["regressions"][0]
        assert reg["path"] == "status"
        assert reg["severity"] == "CRITICAL"
