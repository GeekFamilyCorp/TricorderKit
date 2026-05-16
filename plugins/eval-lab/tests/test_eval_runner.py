"""
test_eval_runner.py — Tests d'intégration eval_runner.py
TricorderKit eval-lab v0.1.0

Tests bout-en-bout : fixture JSON → eval → résultat attendu.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval_runner import app
from baseline_store import BaselineStore

runner = CliRunner()


# -- Fixtures locales ---------------------------------------------------------

@pytest.fixture
def fixtures_dir(tmp_path, valid_output):
    fx_dir = tmp_path / "fixtures"
    fx_dir.mkdir()
    (fx_dir / "test-skill.json").write_text(
        json.dumps(valid_output), encoding="utf-8"
    )
    return fx_dir


@pytest.fixture
def tmp_db(tmp_path):
    return tmp_path / "test.sqlite"


# -- validate-schema ----------------------------------------------------------

class TestValidateSchemaCommand:
    def test_valid_json_file_exits_zero(self, tmp_path, valid_output, tmp_schema):
        f = tmp_path / "output.json"
        f.write_text(json.dumps(valid_output), encoding="utf-8")
        result = runner.invoke(app, ["validate-schema", str(f)])
        assert result.exit_code == 0

    def test_invalid_json_file_exits_nonzero(self, tmp_path, output_missing_status, tmp_schema):
        f = tmp_path / "bad.json"
        f.write_text(json.dumps(output_missing_status), encoding="utf-8")
        result = runner.invoke(app, ["validate-schema", str(f)])
        assert result.exit_code != 0

    def test_missing_file_exits_one(self, tmp_path):
        result = runner.invoke(app, ["validate-schema", str(tmp_path / "nope.json")])
        assert result.exit_code == 1

    def test_json_flag_produces_json_output(self, tmp_path, valid_output, tmp_schema):
        f = tmp_path / "output.json"
        f.write_text(json.dumps(valid_output), encoding="utf-8")
        result = runner.invoke(app, ["validate-schema", str(f), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "valid" in data
        assert data["valid"] is True


# -- dry-run ------------------------------------------------------------------

class TestDryRunCommand:
    def test_dry_run_no_args_exits_one(self):
        result = runner.invoke(app, ["dry-run"])
        assert result.exit_code == 1

    def test_dry_run_does_not_write_to_db(self, tmp_path, tmp_db, valid_output, monkeypatch):
        fx_dir = tmp_path / "fixtures"
        fx_dir.mkdir()
        (fx_dir / "test-skill.json").write_text(json.dumps(valid_output), encoding="utf-8")
        monkeypatch.setattr("eval_runner._FIXTURES_DIR", fx_dir)

        runner.invoke(app, ["dry-run", "test-skill", "--db", str(tmp_db)])

        store = BaselineStore(tmp_db)
        history = store.get_history("test-skill")
        store.close()
        assert len(history) == 0


# -- eval ---------------------------------------------------------------------

class TestEvalCommand:
    def test_eval_valid_skill_exits_zero(self, tmp_path, tmp_db, valid_output, monkeypatch):
        fx_dir = tmp_path / "fixtures"
        fx_dir.mkdir()
        (fx_dir / "test-skill.json").write_text(json.dumps(valid_output), encoding="utf-8")
        monkeypatch.setattr("eval_runner._FIXTURES_DIR", fx_dir)

        result = runner.invoke(app, ["eval", "test-skill", "--db", str(tmp_db)])
        assert result.exit_code == 0

    def test_eval_logs_to_history(self, tmp_path, tmp_db, valid_output, monkeypatch):
        fx_dir = tmp_path / "fixtures"
        fx_dir.mkdir()
        (fx_dir / "test-skill.json").write_text(json.dumps(valid_output), encoding="utf-8")
        monkeypatch.setattr("eval_runner._FIXTURES_DIR", fx_dir)

        runner.invoke(app, ["eval", "test-skill", "--db", str(tmp_db)])

        store = BaselineStore(tmp_db)
        history = store.get_history("test-skill")
        store.close()
        assert len(history) == 1
        assert history[0].status == "pass"

    def test_eval_no_args_exits_one(self):
        result = runner.invoke(app, ["eval"])
        assert result.exit_code == 1

    def test_eval_update_baseline(self, tmp_path, tmp_db, valid_output, monkeypatch):
        fx_dir = tmp_path / "fixtures"
        fx_dir.mkdir()
        (fx_dir / "test-skill.json").write_text(json.dumps(valid_output), encoding="utf-8")
        monkeypatch.setattr("eval_runner._FIXTURES_DIR", fx_dir)

        runner.invoke(app, ["eval", "test-skill", "--db", str(tmp_db), "--update-baseline"])

        store = BaselineStore(tmp_db)
        assert store.baseline_exists("test-skill") is True
        store.close()

    def test_eval_json_output_is_valid(self, tmp_path, tmp_db, valid_output, monkeypatch):
        fx_dir = tmp_path / "fixtures"
        fx_dir.mkdir()
        (fx_dir / "test-skill.json").write_text(json.dumps(valid_output), encoding="utf-8")
        monkeypatch.setattr("eval_runner._FIXTURES_DIR", fx_dir)

        result = runner.invoke(app, ["eval", "test-skill", "--db", str(tmp_db), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] in ("success", "partial", "error", "dry_run")
        assert "output" in data

    def test_eval_critical_violation_exits_two(self, tmp_path, tmp_db, output_missing_status, monkeypatch):
        fx_dir = tmp_path / "fixtures"
        fx_dir.mkdir()
        (fx_dir / "bad-skill.json").write_text(json.dumps(output_missing_status), encoding="utf-8")
        monkeypatch.setattr("eval_runner._FIXTURES_DIR", fx_dir)

        result = runner.invoke(app, ["eval", "bad-skill", "--db", str(tmp_db)])
        assert result.exit_code == 2

    def test_eval_all_flag(self, tmp_path, tmp_db, valid_output, monkeypatch):
        fx_dir = tmp_path / "fixtures"
        fx_dir.mkdir()
        for i in range(3):
            o = dict(valid_output)
            o["skill_name"] = f"skill-{i}"
            (fx_dir / f"skill-{i}.json").write_text(json.dumps(o), encoding="utf-8")
        monkeypatch.setattr("eval_runner._FIXTURES_DIR", fx_dir)

        result = runner.invoke(app, ["eval", "--all", "--db", str(tmp_db)])
        assert result.exit_code == 0

        store = BaselineStore(tmp_db)
        total = sum(len(store.get_history(f"skill-{i}")) for i in range(3))
        store.close()
        assert total == 3


# -- report -------------------------------------------------------------------

class TestReportCommand:
    def test_report_empty_db_shows_info(self, tmp_db):
        result = runner.invoke(app, ["report", "--db", str(tmp_db)])
        assert "Aucune baseline" in result.output or result.exit_code == 0

    def test_report_after_eval(self, tmp_path, tmp_db, valid_output, monkeypatch):
        fx_dir = tmp_path / "fixtures"
        fx_dir.mkdir()
        (fx_dir / "test-skill.json").write_text(json.dumps(valid_output), encoding="utf-8")
        monkeypatch.setattr("eval_runner._FIXTURES_DIR", fx_dir)

        store = BaselineStore(tmp_db)
        store.save_baseline("test-skill", valid_output)
        store.log_eval("test-skill", "1.0.0", "pass", [], [], "abc123")
        store.close()

        result = runner.invoke(app, ["report", "--db", str(tmp_db)])
        assert "test-skill" in result.output
