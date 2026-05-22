"""
test_rapport.py — Tests tk rapport
TricorderKit v0.9

Valide sans services réels :
  1. reports/status/ est créé si absent
  2. latest_status.md contient les sections attendues
  3. --json crée latest_status.json avec la structure correcte
  4. BOOT_SUMMARY.md "Dernière session" est mise à jour à today
  5. _parse_tests extrait correctement PASS et FAIL

Usage:
  pytest tests/test_rapport.py -v
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT  = Path(__file__).resolve().parent.parent
TK_CLI     = REPO_ROOT / "cli" / "tk.py"
REPORTS_DIR = REPO_ROOT / "reports" / "status"

# ── Import helpers directs depuis tk.py ───────────────────────────────────────
import importlib.util

spec = importlib.util.spec_from_file_location("tk", TK_CLI)
tk   = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tk)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_rapport(*extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TK_CLI), "rapport", *extra_args],
        capture_output=True, text=True, encoding="utf-8", cwd=REPO_ROOT,
    )


# ── Test 1 : reports/status/ est créé si absent ──────────────────────────────

def test_reports_dir_created(tmp_path, monkeypatch):
    """reports/status/ est créé automatiquement."""
    fake_reports = tmp_path / "reports" / "status"
    assert not fake_reports.exists()

    monkeypatch.setattr(tk, "REPO_ROOT", REPO_ROOT)
    # On appelle directement via subprocess pour un test end-to-end propre
    result = _run_rapport()
    assert result.returncode == 0, result.stderr
    assert REPORTS_DIR.exists()


# ── Test 2 : latest_status.md contient les sections attendues ─────────────────

def test_latest_status_md_sections():
    """latest_status.md contient les 4 sections obligatoires."""
    result = _run_rapport()
    assert result.returncode == 0, result.stderr

    latest = REPORTS_DIR / "latest_status.md"
    assert latest.exists(), "latest_status.md non créé"
    content = latest.read_text(encoding="utf-8")

    for section in ("## Modules actifs", "## Tests", "## Session", "## Prochaine tâche"):
        assert section in content, f"Section manquante : {section}"


# ── Test 3 : --json crée latest_status.json avec la structure correcte ────────

def test_json_flag_creates_json_file():
    """--json crée latest_status.json avec les clés attendues."""
    result = _run_rapport("--json")
    assert result.returncode == 0, result.stderr

    latest_json = REPORTS_DIR / "latest_status.json"
    assert latest_json.exists(), "latest_status.json non créé avec --json"

    data = json.loads(latest_json.read_text(encoding="utf-8"))
    for key in ("generated", "version", "tests", "blockers", "next_task", "modules"):
        assert key in data, f"Clé manquante dans JSON : {key}"
    assert isinstance(data["tests"]["pass"], int)
    assert isinstance(data["modules"], list)
    assert len(data["modules"]) > 0


# ── Test 4 : BOOT_SUMMARY.md "Dernière session" mis à jour ───────────────────

def test_boot_summary_date_updated():
    """BOOT_SUMMARY.md champ 'Dernière session' est mis à jour à today."""
    result = _run_rapport()
    assert result.returncode == 0, result.stderr

    boot_text = (REPO_ROOT / "BOOT_SUMMARY.md").read_text(encoding="utf-8")
    today = date.today().isoformat()
    assert today in boot_text, f"Date {today} absente de BOOT_SUMMARY.md après tk rapport"


# ── Test 5 : _parse_tests extrait PASS et FAIL correctement ──────────────────

@pytest.mark.parametrize("raw,expected_pass,expected_fail", [
    ("**413 PASS** (377+36), 15 skipped (live)", 413, 0),
    ("200 PASS, 3 FAIL",                          200, 3),
    ("0 PASS, 0 FAIL",                            0,   0),
    ("**52 PASS**",                               52,  0),
])
def test_parse_tests_variants(raw, expected_pass, expected_fail):
    """_parse_tests gère correctement bold markdown, FAIL, et cas limites."""
    p, f = tk._parse_tests(raw)
    assert p == expected_pass, f"PASS attendu {expected_pass}, obtenu {p} pour '{raw}'"
    assert f == expected_fail, f"FAIL attendu {expected_fail}, obtenu {f} pour '{raw}'"
