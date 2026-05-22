"""
test_security_audit.py — Tests security-audit-cli
TricorderKit v0.9 M5

Couvre sans services réels :
  secret_scanner.py       — scan_secrets(), faux positifs, sévérité, to_dict
  pattern_checker.py      — check_patterns(), nosec, eval, subprocess shell=True
  anonymization_checker.py — check_anonymization(), termes privés, custom, casse

Usage:
  pytest tests/test_security_audit.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ── Import des modules du plugin ──────────────────────────────────────────────
PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "security-audit-cli"
sys.path.insert(0, str(PLUGIN_DIR))

from secret_scanner import scan_secrets
from pattern_checker import check_patterns
from anonymization_checker import check_anonymization


# ═══════════════════════════════════════════════════════════════════════════════
# secret_scanner
# ═══════════════════════════════════════════════════════════════════════════════

def test_scan_secrets_clean_file(tmp_path):
    """Fichier sans secret → result.clean == True, 0 findings."""
    f = tmp_path / "clean.py"
    f.write_text('x = 1\nprint("hello")\n', encoding="utf-8")
    result = scan_secrets(f)
    assert result.clean
    assert result.findings == []
    assert result.files_scanned == 1


def test_scan_secrets_detects_anthropic_key(tmp_path):
    """Clé Anthropic au format réel → CRITICAL finding."""
    f = tmp_path / "config.py"
    f.write_text('API_KEY = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890"\n',
                 encoding="utf-8")
    result = scan_secrets(f)
    assert not result.clean
    assert result.has_critical
    assert any(h.pattern_id == "anthropic_api_key" for h in result.findings)


def test_scan_secrets_false_positive_excluded(tmp_path):
    """api_key = 'your_api_key_here' → faux positif, non remonté."""
    f = tmp_path / "example.py"
    f.write_text("api_key = 'your_api_key_here'\n", encoding="utf-8")
    result = scan_secrets(f)
    assert result.clean, f"Faux positif remonté : {result.findings}"


def test_scan_secrets_test_file_downgrades_severity(tmp_path):
    """CRITICAL dans tests/ → downgrade vers HIGH (in_test_file=True)."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    f = tests_dir / "test_config.py"
    f.write_text('KEY = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890"\n',
                 encoding="utf-8")
    result = scan_secrets(tests_dir)
    assert not result.clean
    assert all(h.severity != "CRITICAL" for h in result.findings)
    assert any(h.in_test_file for h in result.findings)


def test_scan_secrets_to_dict_keys(tmp_path):
    """to_dict() retourne toutes les clés attendues."""
    f = tmp_path / "clean.py"
    f.write_text("x = 1\n", encoding="utf-8")
    d = scan_secrets(f).to_dict()
    for key in ("clean", "files_scanned", "files_skipped",
                "findings_count", "critical_count", "high_count", "findings"):
        assert key in d, f"Clé manquante dans to_dict() : {key}"


def test_scan_secrets_db_connection_string(tmp_path):
    """Connection string DB avec credentials → CRITICAL."""
    f = tmp_path / "db.py"
    f.write_text(
        'DSN = "postgresql://admin:supersecret@db.example.com:5432/prod"\n',
        encoding="utf-8",
    )
    result = scan_secrets(f)
    assert not result.clean
    crits = [h for h in result.findings if h.pattern_id == "db_connection_string"]
    assert crits, "db_connection_string non détecté"
    assert crits[0].severity == "CRITICAL"


# ═══════════════════════════════════════════════════════════════════════════════
# pattern_checker
# ═══════════════════════════════════════════════════════════════════════════════

def test_check_patterns_clean_file(tmp_path):
    """Fichier sans anti-pattern → result.clean == True."""
    f = tmp_path / "safe.py"
    f.write_text("import os\nprint(os.getcwd())\n", encoding="utf-8")
    result = check_patterns(f)
    assert result.clean
    assert result.active_findings == []


def test_check_patterns_eval_detected(tmp_path):
    """eval() → HIGH finding."""
    f = tmp_path / "risky.py"
    f.write_text("result = eval(user_input)\n", encoding="utf-8")
    result = check_patterns(f)
    assert not result.clean
    hits = [h for h in result.active_findings if h.rule_id == "eval_usage"]
    assert hits, "eval_usage non détecté"
    assert hits[0].severity == "HIGH"


def test_check_patterns_nosec_suppresses(tmp_path):
    """eval() avec # nosec eval → supprimé, result.clean == True."""
    f = tmp_path / "nosec.py"
    f.write_text("result = eval(safe_expr)  # nosec eval\n", encoding="utf-8")
    result = check_patterns(f)
    assert result.clean, f"Attendu clean après nosec, trouvé : {result.active_findings}"


def test_check_patterns_subprocess_shell_true(tmp_path):
    """subprocess.run(..., shell=True) → HIGH finding."""
    f = tmp_path / "shell.py"
    f.write_text("import subprocess\nsubprocess.run(cmd, shell=True)\n",
                 encoding="utf-8")
    result = check_patterns(f)
    hits = [h for h in result.active_findings if h.rule_id == "subprocess_shell_true"]
    assert hits, "subprocess_shell_true non détecté"


def test_check_patterns_to_dict_keys(tmp_path):
    """to_dict() retourne les clés attendues."""
    f = tmp_path / "ok.py"
    f.write_text("x = 1\n", encoding="utf-8")
    d = check_patterns(f).to_dict()
    for key in ("clean", "files_scanned", "files_skipped",
                "findings_count", "suppressed_count", "findings"):
        assert key in d, f"Clé manquante dans to_dict() : {key}"


# ═══════════════════════════════════════════════════════════════════════════════
# anonymization_checker
# ═══════════════════════════════════════════════════════════════════════════════

def test_check_anonymization_clean_file(tmp_path):
    """Fichier sans terme privé → result.clean == True."""
    f = tmp_path / "public.md"
    f.write_text("# Sample linked project\nNo private terms here.\n",
                 encoding="utf-8")
    result = check_anonymization(f)
    assert result.clean
    assert result.violations == []


def test_check_anonymization_detects_default_term(tmp_path):
    """'Japan-Alliance' dans le fichier → violation CRITICAL."""
    f = tmp_path / "README.md"
    f.write_text("This project is linked to Japan-Alliance vault.\n",
                 encoding="utf-8")
    result = check_anonymization(f)
    assert not result.clean
    assert result.has_critical
    assert "Japan-Alliance" in [v.term for v in result.violations]


def test_check_anonymization_custom_terms(tmp_path):
    """Terme custom passé en paramètre → détecté."""
    f = tmp_path / "config.yaml"
    f.write_text("project: SuperSecretProject\n", encoding="utf-8")
    result = check_anonymization(f, private_terms=["SuperSecretProject"])
    assert not result.clean
    assert any(v.term == "SuperSecretProject" for v in result.violations)


def test_check_anonymization_case_insensitive(tmp_path):
    """Détection insensible à la casse : 'japan-alliance' détecté."""
    f = tmp_path / "note.md"
    f.write_text("linked to japan-alliance system\n", encoding="utf-8")
    result = check_anonymization(f)
    assert not result.clean


def test_check_anonymization_to_dict_keys(tmp_path):
    """to_dict() retourne toutes les clés attendues."""
    f = tmp_path / "clean.txt"
    f.write_text("nothing here\n", encoding="utf-8")
    d = check_anonymization(f).to_dict()
    for key in ("clean", "files_scanned", "files_skipped",
                "terms_checked", "violations_count", "violations"):
        assert key in d, f"Clé manquante : {key}"
