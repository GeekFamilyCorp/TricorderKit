"""
Tests — TricorderKit Security Audit CLI
plugins/security-audit-cli/tests/test_security_runner.py

Stratégie : tests unitaires isolés via mock de subprocess + filesystem temporaire.
Chaque commande du CLI est testée sur :
  - Cas nominal (PASS)
  - Cas d'échec (FAIL + exit code 1 en mode strict)
  - Absence d'outil (skip gracieux)
"""

import json
import re
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

# Import du CLI
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from security_runner import app

runner = CliRunner()


# ═══════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════

@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Crée un projet temporaire minimal."""
    (tmp_path / ".semgrep").mkdir()
    (tmp_path / "plugins").mkdir()
    return tmp_path


@pytest.fixture
def safe_python_file(tmp_project: Path) -> Path:
    """Fichier Python sans risque."""
    f = tmp_project / "safe.py"
    f.write_text(
        "import subprocess\n"
        "result = subprocess.run(['ls', '-la'], capture_output=True)\n"
    )
    return f


@pytest.fixture
def unsafe_python_file(tmp_project: Path) -> Path:
    """Fichier Python avec shell=True (injection potentielle)."""
    f = tmp_project / "unsafe.py"
    f.write_text(
        "import subprocess\n"
        "subprocess.run('ls -la', shell=True)\n"
    )
    return f


@pytest.fixture
def sha1_python_file(tmp_project: Path) -> Path:
    """Fichier Python avec hashlib.sha1 (mauvaise pratique Qdrant)."""
    f = tmp_project / "bad_uuid.py"
    f.write_text(
        "import hashlib\n"
        "doc_id = hashlib.sha1(content.encode()).hexdigest()\n"
    )
    return f


@pytest.fixture
def safe_docker_compose(tmp_project: Path) -> Path:
    """docker-compose.yml avec bind 127.0.0.1 (sécurisé)."""
    f = tmp_project / "docker-compose.yml"
    f.write_text(
        "services:\n"
        "  langfuse:\n"
        "    ports:\n"
        '      - "127.0.0.1:3001:3001"\n'
        "  qdrant:\n"
        "    ports:\n"
        '      - "127.0.0.1:6333:6333"\n'
    )
    return f


@pytest.fixture
def unsafe_docker_compose(tmp_project: Path) -> Path:
    """docker-compose.yml avec port exposé sur 0.0.0.0 (risqué)."""
    f = tmp_project / "docker-compose.yml"
    f.write_text(
        "services:\n"
        "  langfuse:\n"
        "    ports:\n"
        '      - "3001:3001"\n'
    )
    return f


# ═══════════════════════════════════════════
# Tests : commande `scan`
# ═══════════════════════════════════════════

class TestScan:
    def test_scan_pass_no_findings(self, tmp_project, safe_python_file):
        """Semgrep sans findings → exit 0."""
        semgrep_output = json.dumps({"results": [], "errors": []})
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(0, semgrep_output, "")):
            result = runner.invoke(app, ["scan", str(tmp_project)])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_scan_fail_with_findings(self, tmp_project, unsafe_python_file):
        """Semgrep avec findings → exit 1 en mode strict."""
        finding = {
            "check_id": "no-shell-true",
            "path": str(unsafe_python_file),
            "start": {"line": 2},
            "extra": {"lines": "subprocess.run('ls -la', shell=True)"},
        }
        semgrep_output = json.dumps({"results": [finding], "errors": []})
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(1, semgrep_output, "")):
            result = runner.invoke(app, ["scan", str(tmp_project), "--strict"])
        assert result.exit_code == 1
        assert "FAIL" in result.output

    def test_scan_skip_if_semgrep_missing(self, tmp_project):
        """Sans semgrep installé → exit 1 avec message clair (pas crash silencieux)."""
        with patch("security_runner._check_tool", return_value=False):
            result = runner.invoke(app, ["scan", str(tmp_project)])
        assert result.exit_code == 1
        assert "semgrep introuvable" in result.output

    def test_scan_no_strict_does_not_exit_1(self, tmp_project):
        """En mode non-strict, findings présents mais exit 0."""
        finding = {"check_id": "no-shell-true", "path": "x.py", "start": {"line": 1}, "extra": {"lines": ""}}
        semgrep_output = json.dumps({"results": [finding]})
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(0, semgrep_output, "")):
            result = runner.invoke(app, ["scan", str(tmp_project), "--no-strict"])
        assert result.exit_code == 0


# ═══════════════════════════════════════════
# Tests : commande `secrets`
# ═══════════════════════════════════════════

class TestSecrets:
    def test_secrets_pass(self, tmp_project):
        """Gitleaks propre → exit 0."""
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(0, "", "")):
            result = runner.invoke(app, ["secrets", str(tmp_project)])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_secrets_fail(self, tmp_project):
        """Secret détecté → exit 1."""
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(1, "", "ANTHROPIC_API_KEY found")):
            result = runner.invoke(app, ["secrets", str(tmp_project), "--strict"])
        assert result.exit_code == 1
        assert "FAIL" in result.output

    def test_secrets_skip_graceful(self, tmp_project):
        """Gitleaks absent → skip sans crash, exit 0."""
        with patch("security_runner._check_tool", return_value=False):
            result = runner.invoke(app, ["secrets", str(tmp_project)])
        assert result.exit_code == 0
        assert "skip" in result.output.lower() or "introuvable" in result.output.lower()


# ═══════════════════════════════════════════
# Tests : commande `docker`
# ═══════════════════════════════════════════

class TestDocker:
    def test_docker_pass_with_127(self, tmp_project, safe_docker_compose):
        """Ports bindés 127.0.0.1 → PASS."""
        result = runner.invoke(app, ["docker", str(safe_docker_compose)])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_docker_fail_with_open_port(self, tmp_project, unsafe_docker_compose):
        """Port 3001:3001 sans bind → FAIL."""
        result = runner.invoke(app, ["docker", str(unsafe_docker_compose), "--strict"])
        assert result.exit_code == 1
        assert "FAIL" in result.output

    def test_docker_missing_compose_file(self, tmp_project):
        """docker-compose.yml absent → skip, exit 0."""
        result = runner.invoke(app, ["docker", str(tmp_project / "nonexistent.yml")])
        assert result.exit_code == 0
        assert "skip" in result.output.lower() or "introuvable" in result.output.lower()

    def test_docker_fix_suggestion_shown(self, tmp_project, unsafe_docker_compose):
        """Le message de fix doit apparaître si port exposé."""
        result = runner.invoke(app, ["docker", str(unsafe_docker_compose), "--no-strict"])
        assert "127.0.0.1" in result.output


# ═══════════════════════════════════════════
# Tests : commande `uuid`
# ═══════════════════════════════════════════

class TestUUID:
    def test_uuid_pass_no_sha1(self, tmp_project, safe_python_file):
        """Pas de sha1 → PASS."""
        result = runner.invoke(app, ["uuid", str(tmp_project)])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_uuid_fail_sha1_found(self, tmp_project, sha1_python_file):
        """sha1 détecté → FAIL avec fix suggestion."""
        result = runner.invoke(app, ["uuid", str(tmp_project), "--strict"])
        assert result.exit_code == 1
        assert "FAIL" in result.output
        assert "uuid" in result.output.lower()

    def test_uuid_excludes_venv(self, tmp_project):
        """Les fichiers dans .venv ne doivent pas être scannés."""
        venv_dir = tmp_project / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        bad_file = venv_dir / "bad.py"
        bad_file.write_text("import hashlib\nhashlib.sha1(b'x')\n")

        result = runner.invoke(app, ["uuid", str(tmp_project)])
        assert result.exit_code == 0  # Le .venv est exclu → pas de FAIL


# ═══════════════════════════════════════════
# Tests : commande `full-audit`
# ═══════════════════════════════════════════

class TestFullAudit:
    def test_full_audit_all_pass(self, tmp_project, safe_python_file, safe_docker_compose):
        """Full audit propre → exit 0, tous PASS."""
        semgrep_output = json.dumps({"results": []})
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(0, semgrep_output, "")):
            result = runner.invoke(app, ["full-audit", str(tmp_project)])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_full_audit_strict_exit_1_on_any_failure(self, tmp_project, unsafe_python_file):
        """En mode --strict, un seul FAIL suffit à exit 1."""
        semgrep_output = json.dumps({"results": [
            {"check_id": "no-shell-true", "path": str(unsafe_python_file),
             "start": {"line": 2}, "extra": {"lines": "shell=True"}}
        ]})
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(1, semgrep_output, "")):
            result = runner.invoke(app, ["full-audit", str(tmp_project), "--strict"])
        assert result.exit_code == 1

    def test_full_audit_shows_summary_table(self, tmp_project):
        """Le tableau récapitulatif doit toujours être affiché."""
        with patch("security_runner._check_tool", return_value=False), \
             patch("security_runner._run", return_value=(0, json.dumps({"results": []}), "")):
            result = runner.invoke(app, ["full-audit", str(tmp_project)])
        assert "scan" in result.output
        assert "docker" in result.output
        assert "uuid" in result.output


# ═══════════════════════════════════════════
# Tests : helper _run (sécurité fondamentale)
# ═══════════════════════════════════════════

class TestRunHelper:
    def test_run_uses_list_not_string(self):
        """_run ne doit jamais appeler subprocess avec shell=True — test de régression."""
        import security_runner
        import subprocess as sp
        calls = []

        original_run = sp.run
        def mock_run(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            security_runner._run(["echo", "hello"])

        assert len(calls) == 1
        cmd, kwargs = calls[0]
        # La commande doit être une liste
        assert isinstance(cmd, list), "subprocess.run doit recevoir une liste, pas une string"
        # shell=True ne doit jamais être passé
        assert kwargs.get("shell", False) is False, "shell=True ne doit jamais être utilisé"
