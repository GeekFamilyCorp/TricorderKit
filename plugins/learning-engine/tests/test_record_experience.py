# -*- coding: utf-8 -*-
"""Tests record_experience.py — nominal + validation schéma en échec."""
import json

import _common as C
import record_experience as R


def test_build_card_is_schema_valid(valid_run):
    """Nominal : une carte construite depuis un run valide passe le schéma."""
    card = R.build_card(valid_run, "scraping_jp", "project-a")
    assert C.validate(card, "experience_card") == []
    assert card["strategy_used"] == "official_sources_first"
    assert card["status"] == "proposed"
    assert card["human_review_required"] is True
    # projection 0-100 -> 0-1
    assert 0.0 <= card["quality"]["relevance_score"] <= 1.0
    assert card["quality"]["relevance_score"] == 0.82


def test_card_id_format(valid_run):
    card = R.build_card(valid_run, "Scraping JP!", "project-a")
    # le slug normalise et le pattern du schéma doit matcher
    assert card["experience_card_id"].startswith("exp_2026_06_11_")
    assert C.validate(card, "experience_card") == []


def test_invalid_run_is_rejected(tmp_path, valid_run, capsys):
    """Échec : un run non conforme (status invalide) doit être refusé proprement."""
    bad = dict(valid_run)
    bad["status"] = "totally_wrong"
    p = tmp_path / "bad_run.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    rc = R.main(["--run", str(p), "--task-type", "scraping_jp",
                 "--project-scope", "project-a", "--format", "json"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "error"
    assert out["error"]["code"] == "ERR_SCHEMA_RUN"


def test_dry_run_writes_nothing(tmp_path, valid_run, capsys):
    p = tmp_path / "run.json"
    p.write_text(json.dumps(valid_run), encoding="utf-8")
    out_dir = tmp_path / "cards"
    rc = R.main(["--run", str(p), "--task-type", "scraping_jp",
                 "--project-scope", "project-a", "--out-dir", str(out_dir),
                 "--dry-run", "--format", "json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "dry_run"
    assert not out_dir.exists() or not list(out_dir.glob("*.json"))


def test_real_write_produces_valid_card(tmp_path, valid_run, capsys):
    p = tmp_path / "run.json"
    p.write_text(json.dumps(valid_run), encoding="utf-8")
    out_dir = tmp_path / "cards"
    rc = R.main(["--run", str(p), "--task-type", "scraping_jp",
                 "--project-scope", "project-a", "--out-dir", str(out_dir),
                 "--format", "json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    files = list(out_dir.glob("*.json"))
    assert len(files) == 1
    card = json.loads(files[0].read_text(encoding="utf-8"))
    assert C.validate(card, "experience_card") == []


def test_skill_output_envelope_conforms(tmp_path, valid_run, capsys):
    """La sortie elle-même respecte core/contracts/skill_output.schema.json."""
    import jsonschema
    contract = json.loads(C.SKILL_OUTPUT_CONTRACT.read_text(encoding="utf-8"))
    p = tmp_path / "run.json"
    p.write_text(json.dumps(valid_run), encoding="utf-8")
    R.main(["--run", str(p), "--task-type", "scraping_jp",
            "--project-scope", "project-a", "--out-dir", str(tmp_path / "c"),
            "--format", "json"])
    out = json.loads(capsys.readouterr().out)
    jsonschema.Draft7Validator(contract).validate(out)
