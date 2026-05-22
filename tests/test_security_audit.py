"""
test_security_audit.py — Tests security-audit-cli
TricorderKit v0.9

Couvre :
  - secret_scanner   : détection CRITICAL/HIGH, faux positifs, fichiers test
  - anonymization_checker : termes privés, fichiers clean, multi-termes
  - security_runner  : dry-run output contract, build_output statuts
  - intégration      : scan répertoire réel (plugins/security-audit-cli/)
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

# -- Chemin vers le plugin ----------------------------------------------------

PLUGIN_DIR = Path(__file__).parent.parent / "plugins" / "security-audit-cli"
sys.path.insert(0, str(PLUGIN_DIR))

from secret_scanner import (
    SecretFinding,
    SecretScanResult,
    SecretPattern,
    scan_secrets,
    _is_false_positive,
    _is_test_path,
)
from anonymization_checker import (
    AnonViolation,
    AnonCheckResult,
    DEFAULT_PRIVATE_TERMS,
    check_anonymization,
    check_file_anonymization,
)
from security_runner import _build_output


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def tmp_clean_file(tmp_path: Path) -> Path:
    """Fichier Python sans secret ni terme privé."""
    f = tmp_path / "clean.py"
    f.write_text('# fichier propre\nDEBUG = True\nNAME = "tricorderkit"\n', encoding="utf-8")
    return f


@pytest.fixture
def tmp_secret_file(tmp_path: Path) -> Path:
    """Fichier contenant une clé Anthropic hardcodée."""
    f = tmp_path / "bad_secrets.py"
    f.write_text(
        'ANTHROPIC_KEY = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"\n',
        encoding="utf-8",
    )
    return f


@pytest.fixture
def tmp_anon_file(tmp_path: Path) -> Path:
    """Fichier contenant des termes privés."""
    f = tmp_path / "private.md"
    f.write_text(
        "# Notes\nCe projet utilise Japan-Alliance pour le vault.\nMangaTracker gère les CLIs.\n",
        encoding="utf-8",
    )
    return f


@pytest.fixture
def tmp_false_positive_file(tmp_path: Path) -> Path:
    """Fichier avec faux positifs (placeholder/example)."""
    f = tmp_path / "config_example.py"
    f.write_text(
        'API_KEY = "your_api_key_here"\nPASSWORD = "changeme"\n',
        encoding="utf-8",
    )
    return f


@pytest.fixture
def tmp_test_dir(tmp_path: Path) -> Path:
    """Répertoire tests/ avec une clé hardcodée (sévérité dégradée)."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    f = tests_dir / "test_config.py"
    f.write_text(
        'ANTHROPIC_KEY = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"\n',
        encoding="utf-8",
    )
    return tests_dir


# =============================================================================
# secret_scanner — Tests unitaires
# =============================================================================

class TestSecretScannerClean:
    def test_clean_file_returns_no_findings(self, tmp_clean_file: Path) -> None:
        result = scan_secrets(tmp_clean_file)
        assert result.clean is True
        assert result.findings == []
        assert result.files_scanned == 1

    def test_clean_dir_returns_no_findings(self, tmp_path: Path, tmp_clean_file: Path) -> None:
        result = scan_secrets(tmp_path)
        assert result.clean is True

    def test_false_positive_not_flagged(self, tmp_false_positive_file: Path) -> None:
        result = scan_secrets(tmp_false_positive_file)
        assert result.clean is True, f"Faux positif détecté : {result.findings}"


class TestSecretScannerDetection:
    def test_anthropic_key_detected_as_critical(self, tmp_secret_file: Path) -> None:
        result = scan_secrets(tmp_secret_file)
        assert result.clean is False
        assert result.has_critical is True
        findings = [f for f in result.findings if f.pattern_id == "anthropic_api_key"]
        assert len(findings) >= 1
        assert findings[0].severity == "CRITICAL"

    def test_finding_has_masked_snippet(self, tmp_secret_file: Path) -> None:
        result = scan_secrets(tmp_secret_file)
        assert result.findings
        snippet = result.findings[0].matched_snippet
        # Le snippet ne doit pas contenir la valeur complète
        assert "sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789" not in snippet

    def test_critical_in_test_dir_downgraded_to_high(self, tmp_test_dir: Path) -> None:
        result = scan_secrets(tmp_test_dir)
        assert result.clean is False
        for f in result.findings:
            if f.in_test_file:
                assert f.severity != "CRITICAL", "CRITICAL doit être dégradé à HIGH dans tests/"

    def test_private_key_header_detected(self, tmp_path: Path) -> None:
        f = tmp_path / "key.pem"
        f.write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----\n")
        result = scan_secrets(f)
        assert result.has_critical is True

    def test_db_connection_string_detected(self, tmp_path: Path) -> None:
        f = tmp_path / "db.py"
        f.write_text('DB_URL = "postgresql://admin:s3cr3tpassword@localhost:5432/mydb"\n')
        result = scan_secrets(f)
        assert result.clean is False
        assert any(f.pattern_id == "db_connection_string" for f in result.findings)


class TestSecretScannerHelpers:
    def test_is_test_path_true(self) -> None:
        assert _is_test_path(Path("project/tests/test_config.py")) is True

    def test_is_test_path_false(self) -> None:
        assert _is_test_path(Path("project/src/config.py")) is False

    def test_nonexistent_path_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            scan_secrets(tmp_path / "nonexistent.py")


class TestSecretScanResultContract:
    def test_to_dict_shape(self, tmp_secret_file: Path) -> None:
        result = scan_secrets(tmp_secret_file)
        d = result.to_dict()
        assert "clean" in d
        assert "files_scanned" in d
        assert "findings" in d
        assert isinstance(d["findings"], list)

    def test_clean_result_to_dict(self, tmp_clean_file: Path) -> None:
        result = scan_secrets(tmp_clean_file)
        d = result.to_dict()
        assert d["clean"] is True
        assert d["findings"] == []
        assert d["critical_count"] == 0


# =============================================================================
# anonymization_checker — Tests unitaires
# =============================================================================

class TestAnonCheckerClean:
    def test_clean_file_passes(self, tmp_clean_file: Path) -> None:
        result = check_anonymization(tmp_clean_file)
        assert result.clean is True
        assert result.violations == []

    def test_clean_dir_passes(self, tmp_path: Path, tmp_clean_file: Path) -> None:
        result = check_anonymization(tmp_path)
        assert result.clean is True

    def test_terms_checked_populated(self, tmp_clean_file: Path) -> None:
        result = check_anonymization(tmp_clean_file)
        assert result.terms_checked == DEFAULT_PRIVATE_TERMS


class TestAnonCheckerViolations:
    def test_private_term_detected(self, tmp_anon_file: Path) -> None:
        result = check_anonymization(tmp_anon_file)
        assert result.clean is False
        terms = {v.term for v in result.violations}
        assert "Japan-Alliance" in terms
        assert "MangaTracker" in terms

    def test_violation_has_line_number(self, tmp_anon_file: Path) -> None:
        result = check_anonymization(tmp_anon_file)
        for v in result.violations:
            assert v.line_number >= 1

    def test_violation_line_content_truncated(self, tmp_path: Path) -> None:
        f = tmp_path / "long.md"
        f.write_text("Japan-Alliance " + "x" * 200 + "\n")
        result = check_anonymization(f)
        assert result.violations
        assert len(result.violations[0].line_content) <= 120

    def test_custom_terms(self, tmp_path: Path) -> None:
        f = tmp_path / "custom.py"
        f.write_text('SECRET_PROJECT = "InternalCodename"\n')
        result = check_anonymization(f, private_terms=["InternalCodename"])
        assert result.clean is False
        assert result.violations[0].term == "InternalCodename"

    def test_case_insensitive_detection(self, tmp_path: Path) -> None:
        f = tmp_path / "case.md"
        f.write_text("utilise japan-alliance\n")
        result = check_anonymization(f)
        assert result.clean is False

    def test_violations_by_term_groups_correctly(self, tmp_anon_file: Path) -> None:
        result = check_anonymization(tmp_anon_file)
        by_term = result.violations_by_term()
        assert "Japan-Alliance" in by_term
        assert "MangaTracker" in by_term


class TestAnonCheckerContract:
    def test_to_dict_shape(self, tmp_anon_file: Path) -> None:
        result = check_anonymization(tmp_anon_file)
        d = result.to_dict()
        required = {"clean", "files_scanned", "violations_count", "violations", "terms_checked"}
        assert required.issubset(d.keys())

    def test_nonexistent_path_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            check_anonymization(tmp_path / "ghost.md")

    def test_check_file_anonymization_shortcut(self, tmp_anon_file: Path) -> None:
        result = check_file_anonymization(tmp_anon_file)
        assert result.clean is False


# =============================================================================
# security_runner — _build_output contract
# =============================================================================

class TestBuildOutput:
    def test_dry_run_status(self) -> None:
        out = _build_output(None, None, None, dry_run=True, duration_ms=0)
        assert out["status"] == "dry_run"
        assert "dry_run_report" in out

    def test_dry_run_report_has_actions(self) -> None:
        out = _build_output(None, None, None, dry_run=True, duration_ms=0)
        actions = out["dry_run_report"]["actions_that_would_run"]
        assert isinstance(actions, list)
        assert len(actions) >= 1

    def test_clean_audit_returns_success(self, tmp_clean_file: Path) -> None:
        anon = check_anonymization(tmp_clean_file)
        secrets = scan_secrets(tmp_clean_file)
        out = _build_output(anon, secrets, None, dry_run=False, duration_ms=42)
        assert out["status"] == "success"

    def test_critical_secret_returns_error(self, tmp_secret_file: Path) -> None:
        secrets = scan_secrets(tmp_secret_file)
        out = _build_output(None, secrets, None, dry_run=False, duration_ms=10)
        assert out["status"] == "error"
        assert out["output"]["data"]["has_critical"] is True

    def test_output_has_required_keys(self, tmp_clean_file: Path) -> None:
        anon = check_anonymization(tmp_clean_file)
        secrets = scan_secrets(tmp_clean_file)
        out = _build_output(anon, secrets, None, dry_run=False, duration_ms=10)
        required = {"status", "skill_name", "skill_version", "timestamp", "duration_ms", "output"}
        assert required.issubset(out.keys())

    def test_next_steps_not_empty(self, tmp_clean_file: Path) -> None:
        anon = check_anonymization(tmp_clean_file)
        secrets = scan_secrets(tmp_clean_file)
        out = _build_output(anon, secrets, None, dry_run=False, duration_ms=5)
        assert len(out["output"]["next_steps"]) >= 1

    def test_summary_max_500_chars(self, tmp_clean_file: Path) -> None:
        anon = check_anonymization(tmp_clean_file)
        secrets = scan_secrets(tmp_clean_file)
        out = _build_output(anon, secrets, None, dry_run=False, duration_ms=5)
        assert len(out["output"]["summary"]) <= 500

    def test_output_json_serializable(self, tmp_clean_file: Path) -> None:
        anon = check_anonymization(tmp_clean_file)
        secrets = scan_secrets(tmp_clean_file)
        out = _build_output(anon, secrets, None, dry_run=False, duration_ms=5)
        # Ne doit pas lever d'exception
        json.dumps(out)


# =============================================================================
# Intégration — scan répertoire réel du plugin
# =============================================================================

class TestIntegrationPluginDir:
    def test_plugin_dir_has_no_real_secrets(self) -> None:
        """Le répertoire security-audit-cli lui-même ne doit pas contenir de secrets réels."""
        result = scan_secrets(PLUGIN_DIR)
        critical = result.critical_findings
        # Tolérer uniquement les findings dans des fichiers de test ou patterns de démo
        real_criticals = [f for f in critical if not f.in_test_file]
        assert real_criticals == [], (
            f"Secrets CRITICAL détectés hors tests : {[(f.file_path, f.description) for f in real_criticals]}"
        )

    def test_plugin_dir_files_are_scanned(self) -> None:
        result = scan_secrets(PLUGIN_DIR)
        assert result.files_scanned >= 3  # security_runner, secret_scanner, anonymization_checker

    def test_plugin_dir_no_anon_violation(self) -> None:
        """Le plugin ne doit pas contenir de termes privés du projet."""
        result = check_anonymization(PLUGIN_DIR)
        # Japan-Alliance et MangaTracker peuvent apparaître dans les commentaires d'entête
        # mais pas dans du code fonctionnel — on tolère les .py uniquement si c'est dans des strings de doc
        violations_in_code = [
            v for v in result.violations
            if not v.line_content.strip().startswith(("#", "//", "*", '"""', "'''"))
        ]
        assert violations_in_code == [], (
            f"Termes privés dans du code : {[(v.file_path, v.term, v.line_content) for v in violations_in_code]}"
        )
