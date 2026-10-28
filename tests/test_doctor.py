"""
test_doctor.py — Tests tk doctor
TricorderKit v0.9

Valide sans services réels :
  1. Python >= 3.11 toujours [OK] sur Python 3.14
  2. [WARN] .env quand absent (mock filesystem)
  3. Dossiers requis → [OK] quand présents (mock filesystem)
  4. Modules détectés : compte lu depuis STATUS.md
  5. Secrets → [OK] quand _check_secrets retourne [] (mock)
  6. JSON complet : structure + statuts valides (subprocess)

Usage:
  pytest tests/test_doctor.py -v
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TK_CLI    = REPO_ROOT / "cli" / "tk.py"

# ── Import direct de tk.py ────────────────────────────────────────────────────
spec = importlib.util.spec_from_file_location("tk", TK_CLI)
tk   = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tk)


class _Args:
    """Fake argparse.Namespace pour tests directs."""
    format     = "json"
    json_output = False


# ── Test 1 : Python >= 3.11 toujours [OK] ────────────────────────────────────

def test_python_check_always_ok(capsys):
    """Python 3.14 >= 3.11 → check toujours ok."""
    tk.cmd_doctor(_Args())
    data = json.loads(capsys.readouterr().out)
    py = next(c for c in data["checks"] if "Python" in c["label"])
    assert py["status"] == "ok"
    assert sys.version_info[:2] >= (3, 11)


# ── Test 2 : [WARN] quand .env absent ────────────────────────────────────────

def test_env_warn_when_missing(tmp_path, monkeypatch, capsys):
    """Quand .env est absent → status warn sur le check .env."""
    monkeypatch.setattr(tk, "REPO_ROOT",           tmp_path)
    monkeypatch.setattr(tk, "LINKED_PROJECTS_FILE", tmp_path / "linked_projects.yaml")
    monkeypatch.setattr(tk, "_check_docker_socket", lambda: True)
    monkeypatch.setattr(tk, "_check_secrets",       lambda: [])
    # STATUS.md minimal pour ne pas perturber le count
    (tmp_path / "STATUS.md").write_text("")

    tk.cmd_doctor(_Args())
    data = json.loads(capsys.readouterr().out)
    env_check = next(c for c in data["checks"] if ".env" in c["label"])
    assert env_check["status"] == "warn"
    assert "manquant" in env_check["label"]


# ── Test 3 : Dossiers requis → [OK] quand présents ───────────────────────────

def test_required_dirs_ok_when_present(tmp_path, monkeypatch, capsys):
    """Quand plugins/, skills/, reports/, memory/ existent → tous [OK]."""
    for d in ("plugins", "skills", "reports", "memory"):
        (tmp_path / d).mkdir()
    monkeypatch.setattr(tk, "REPO_ROOT",           tmp_path)
    monkeypatch.setattr(tk, "LINKED_PROJECTS_FILE", tmp_path / "linked_projects.yaml")
    monkeypatch.setattr(tk, "_check_docker_socket", lambda: True)
    monkeypatch.setattr(tk, "_check_secrets",       lambda: [])
    (tmp_path / "STATUS.md").write_text("")

    tk.cmd_doctor(_Args())
    data = json.loads(capsys.readouterr().out)
    dir_checks = [c for c in data["checks"] if "Dossier" in c["label"]]
    assert len(dir_checks) == 4
    assert all(c["status"] == "ok" for c in dir_checks)


# ── Test 4 : Modules détectés depuis STATUS.md ────────────────────────────────

def test_module_count_read_from_status_md(tmp_path, monkeypatch, capsys):
    """Le count de modules est lu depuis STATUS.md (2 lignes → 2 modules)."""
    status_content = (
        "| Plugin | Status | CLI | Tests | Docs | Production-ready |\n"
        "|---|---|---|---|---|---|\n"
        "| plugin-a | ✅ Actif | ✅ | ✅ | ✅ | ✅ |\n"
        "| plugin-b | ✅ Actif | ❌ | ❌ | ❌ | ❌ |\n"
    )
    (tmp_path / "STATUS.md").write_text(status_content, encoding="utf-8")
    monkeypatch.setattr(tk, "REPO_ROOT",           tmp_path)
    monkeypatch.setattr(tk, "LINKED_PROJECTS_FILE", tmp_path / "linked_projects.yaml")
    monkeypatch.setattr(tk, "_check_docker_socket", lambda: True)
    monkeypatch.setattr(tk, "_check_secrets",       lambda: [])

    tk.cmd_doctor(_Args())
    data = json.loads(capsys.readouterr().out)
    mod_check = next(c for c in data["checks"] if "Modules" in c["label"])
    assert "2" in mod_check["label"]
    assert mod_check["status"] == "ok"


# ── Test 5 : Secrets → [OK] quand _check_secrets retourne [] ─────────────────

def test_secrets_ok_when_none_found(monkeypatch, capsys):
    """_check_secrets() retournant [] → check secret status ok."""
    monkeypatch.setattr(tk, "_check_secrets", lambda: [])
    tk.cmd_doctor(_Args())
    data = json.loads(capsys.readouterr().out)
    sec = next(c for c in data["checks"] if "secret" in c["label"].lower())
    assert sec["status"] == "ok"
    assert sec["detail"] == ""


# ── Test 6 : JSON complet via subprocess ──────────────────────────────────────

def test_json_output_structure():
    """tk doctor --format json retourne 'checks' avec statuts valides."""
    result = subprocess.run(
        [sys.executable, str(TK_CLI), "doctor", "--format", "json"],
        capture_output=True, text=True, encoding="utf-8", cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)

    assert "checks" in data
    assert isinstance(data["checks"], list)
    assert len(data["checks"]) == 14  # 2 + 4 services + 1 env + 4 dirs + 1 modules + 1 projects + 1 secrets

    valid_statuses = {"ok", "warn", "fail"}
    for c in data["checks"]:
        assert "status" in c and "label" in c and "detail" in c
        assert c["status"] in valid_statuses, f"Statut invalide : {c['status']}"
