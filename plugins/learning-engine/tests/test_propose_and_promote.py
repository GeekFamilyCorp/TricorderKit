# -*- coding: utf-8 -*-
"""Tests propose_skill_update.py + promote_skill.py — création draft + gate de promotion."""
import json

import _common as C
import propose_skill_update as P
import promote_skill as PR


# ── propose_skill_update ─────────────────────────────────────────────────────────
def test_proposal_is_valid_and_draft_only(tmp_path, valid_lesson, capsys):
    ldir = tmp_path / "lessons"
    ldir.mkdir()
    (ldir / f"{valid_lesson['lesson_id']}.json").write_text(
        json.dumps(valid_lesson), encoding="utf-8")
    drafts = tmp_path / "skills" / "mangatracker-lookup" / "drafts"
    rc = P.main(["--skill-id", "mangatracker-lookup", "--lessons-dir", str(ldir),
                 "--drafts-dir", str(drafts), "--format", "json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    draft_json = list(drafts.glob("*.json"))
    assert draft_json, "draft écrit dans drafts/"
    proposal = json.loads(draft_json[0].read_text(encoding="utf-8"))
    assert C.validate(proposal, "skill_update_proposal") == []
    # tous les tests à pending au départ
    assert set(proposal["tests"].values()) == {"pending"}
    assert proposal["status"] == "draft_created"
    assert "drafts" in proposal["draft_path"].lower()


def test_no_accepted_lessons_errors(tmp_path, valid_lesson, capsys):
    ldir = tmp_path / "lessons"
    ldir.mkdir()
    observed = dict(valid_lesson, status="observed")
    (ldir / "obs.json").write_text(json.dumps(observed), encoding="utf-8")
    rc = P.main(["--skill-id", "x", "--lessons-dir", str(ldir),
                 "--drafts-dir", str(tmp_path / "skills" / "x" / "drafts"),
                 "--format", "json"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["error"]["code"] == "ERR_NO_LESSONS"


# ── promote_skill ────────────────────────────────────────────────────────────────
def _proposal(tests_state="pending", reviewed=False, rollback=True, draft="skills/x/drafts/p.json"):
    tests = {t: tests_state for t in PR.REQUIRED_TESTS}
    p = {
        "proposal_id": "sup_2026_06_11_x",
        "date": "2026-06-11",
        "skill_id": "x",
        "proposed_change": "Router vers official_sources_first par défaut.",
        "evidence": [{"claim": "official surclasse mangaupdates"}],
        "tests": tests,
        "rollback": {"available": rollback},
        "draft_path": draft,
        "status": "test_passed",
        "human_review_required": True,
    }
    if reviewed:
        p["reviewed_by"] = "Sébastien"
        p["tests"]["human_validation"] = "passed"
    return p


def test_promotion_blocked_when_tests_pending(tmp_path, capsys):
    p = _proposal(tests_state="pending", reviewed=False)
    pf = tmp_path / "p.json"
    pf.write_text(json.dumps(p), encoding="utf-8")
    rc = PR.main(["--proposal", str(pf), "--format", "json"])  # dry-run par défaut
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "error"
    assert out["error"]["code"] == "ERR_GATE_BLOCKED"
    assert any("pending" in b for b in out["output"]["data"]["blockers"])


def test_promotion_blocked_without_human_review(tmp_path, capsys):
    p = _proposal(tests_state="passed", reviewed=False)  # tests ok mais pas de reviewed_by
    pf = tmp_path / "p.json"
    pf.write_text(json.dumps(p), encoding="utf-8")
    rc = PR.main(["--proposal", str(pf), "--format", "json"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert "reviewed_by" in " ".join(out["output"]["data"]["blockers"]) or \
           "human_validation" in " ".join(out["output"]["data"]["blockers"])


def test_gate_passes_dry_run(tmp_path, capsys):
    p = _proposal(tests_state="passed", reviewed=True)
    pf = tmp_path / "p.json"
    pf.write_text(json.dumps(p), encoding="utf-8")
    rc = PR.main(["--proposal", str(pf), "--format", "json"])  # dry-run
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "dry_run"
    assert out["output"]["data"]["resulting_status"] == "promoted"


def test_apply_promotes_with_backup(tmp_path, capsys):
    p = _proposal(tests_state="passed", reviewed=True,
                  draft=str(tmp_path / "skills" / "x" / "drafts" / "p.json"))
    pf = tmp_path / "p.json"
    pf.write_text(json.dumps(p), encoding="utf-8")
    # skill actif existant + nouveau contenu
    target = tmp_path / "skills" / "x" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("# ancienne version\n", encoding="utf-8")
    new = tmp_path / "new.md"
    new.write_text("# nouvelle version promue\n", encoding="utf-8")
    backup = tmp_path / "skills" / "x" / "backups" / "SKILL.md.bak"
    rc = PR.main(["--proposal", str(pf), "--apply",
                  "--draft-content", str(new), "--backup-path", str(backup),
                  "--target-skill-md", str(target), "--format", "json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    assert backup.exists() and "ancienne" in backup.read_text(encoding="utf-8")
    assert "nouvelle version promue" in target.read_text(encoding="utf-8")
    # proposition mise à jour
    assert json.loads(pf.read_text(encoding="utf-8"))["status"] == "promoted"
