"""
test_schema_validator.py — Tests unitaires schema_validator.py
TricorderKit eval-lab v0.1.0
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from schema_validator import (
    SchemaValidationResult,
    ViolationDetail,
    validate_json_string,
    validate_output,
)


# -- validate_output ----------------------------------------------------------

class TestValidateOutput:
    def test_valid_output_passes(self, valid_output, tmp_schema):
        result = validate_output(valid_output, schema_path=tmp_schema)
        assert result.valid is True
        assert result.violations == []
        assert result.skill_name == "test-skill"
        assert result.skill_version == "1.0.0"

    def test_missing_status_is_critical(self, output_missing_status, tmp_schema):
        result = validate_output(output_missing_status, schema_path=tmp_schema)
        assert result.valid is False
        assert result.has_critical is True
        critical = [v for v in result.violations if v.severity == "CRITICAL"]
        assert len(critical) >= 1

    def test_wrong_status_enum_is_critical(self, output_wrong_status, tmp_schema):
        result = validate_output(output_wrong_status, schema_path=tmp_schema)
        assert result.valid is False
        critical = [v for v in result.violations if v.severity == "CRITICAL"]
        assert len(critical) >= 1

    def test_missing_summary_detected(self, output_missing_summary, tmp_schema):
        result = validate_output(output_missing_summary, schema_path=tmp_schema)
        assert result.valid is False
        paths = [v.path for v in result.violations]
        assert any("summary" in p or "output" in p for p in paths)

    def test_summary_too_long_is_medium(self, valid_output, tmp_schema):
        import copy
        o = copy.deepcopy(valid_output)
        o["output"]["summary"] = "x" * 600
        result = validate_output(o, schema_path=tmp_schema)
        assert result.valid is False
        medium = [v for v in result.violations if v.severity == "MEDIUM"]
        assert len(medium) >= 1

    def test_schema_file_not_found_raises(self, valid_output):
        with pytest.raises(FileNotFoundError):
            validate_output(valid_output, schema_path=Path("/nonexistent/schema.json"))

    def test_skill_name_extracted_from_output(self, valid_output, tmp_schema):
        result = validate_output(valid_output, schema_path=tmp_schema)
        assert result.skill_name == valid_output["skill_name"]
        assert result.skill_version == valid_output["skill_version"]

    def test_empty_output_has_multiple_violations(self, tmp_schema):
        result = validate_output({}, schema_path=tmp_schema)
        assert result.valid is False
        assert len(result.violations) >= 5


# -- validate_json_string -----------------------------------------------------

class TestValidateJsonString:
    def test_valid_json_string_passes(self, valid_output, tmp_schema):
        json_str = json.dumps(valid_output)
        result = validate_json_string(json_str, schema_path=tmp_schema)
        assert result.valid is True

    def test_invalid_json_returns_critical_violation(self):
        result = validate_json_string("{ invalid json }")
        assert result.valid is False
        assert result.has_critical is True
        assert result.violations[0].validator == "json_parse"

    def test_empty_string_returns_critical_violation(self):
        result = validate_json_string("")
        assert result.valid is False
        assert result.has_critical is True


# -- SchemaValidationResult ---------------------------------------------------

class TestSchemaValidationResult:
    def test_has_critical_false_when_no_critical(self):
        result = SchemaValidationResult(
            valid=False,
            violations=[
                ViolationDetail(path="x", message="msg", validator="type", severity="MEDIUM")
            ],
        )
        assert result.has_critical is False

    def test_has_critical_true_when_critical_present(self):
        result = SchemaValidationResult(
            valid=False,
            violations=[
                ViolationDetail(path="status", message="msg", validator="required", severity="CRITICAL")
            ],
        )
        assert result.has_critical is True

    def test_to_dict_structure(self, valid_output, tmp_schema):
        result = validate_output(valid_output, schema_path=tmp_schema)
        d = result.to_dict()
        assert "valid" in d
        assert "violations" in d
        assert "skill_name" in d
        assert "skill_version" in d
        assert isinstance(d["violations"], list)
