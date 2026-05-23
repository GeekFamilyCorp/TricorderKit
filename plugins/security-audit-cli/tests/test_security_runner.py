"""
Tests — TricorderKit Security Audit CLI
"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from typer.testing import CliRunner
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from security_runner import app

runner = CliRunner()

@pytest.fixture
def tmp_project(tmp_path):
    (tmp_path / ".semgrep").mkdir()
    (tmp_path / "plugins").mkdir()
    return tmp_path

@pytest.fixture
def safe_python_file(tmp_project):
    f = tmp_project / "safe.py"
    f.write_text("import subprocess\nresult = subprocess.run(['ls', '-la'], capture_output=True)\n")
    return f

@pytest.fixture
def unsafe_python_file(tmp_project):
    f = tmp_project / "unsafe.py"
    f.write_text("import subprocess\nsubprocess.run('ls -la', shell=True)\n")
    return f

@pytest.fixture
def sha1_python_file(tmp_project):
    f = tmp_project / "bad_uuid.py"
    f.write_text("import hashlib\ndoc_id = hashlib.sha1(content.encode()).hexdigest()\n")
    return f

@pytest.fixture
def safe_docker_compose(tmp_project):
    f = tmp_project / "docker-compose.yml"
    f.write_text('services:\n  langfuse:\n    ports:\n      - "127.0.0.1:3001:3001"\n')
    return f

@pytest.fixture
def unsafe_docker_compose(tmp_project):
    f = tmp_project / "docker-compose.yml"
    f.write_text('services:\n  langfuse:\n    ports:\n      - "3001:3001"\n')
    return f

class TestScan:
    def test_scan_pass_no_findings(self, tmp_project, safe_python_file):
        semgrep_output = json.dumps({"results": [], "errors": []})
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(0, semgrep_output, "")):
            result = runner.invoke(app, ["scan", str(tmp_project)])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_scan_fail_with_findings(self, tmp_project, unsafe_python_file):
        finding = {"check_id": "no-shell-true", "path": str(unsafe_python_file),
                   "start": {"line": 2}, "extra": {"lines": "subprocess.run('ls -la', shell=True)"}}
        semgrep_output = json.dumps({"results": [finding], "errors": []})
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(1, semgrep_output, "")):
            result = runner.invoke(app, ["scan", str(tmp_project), "--strict"])
        assert result.exit_code == 1

    def test_scan_skip_if_semgrep_missing(self, tmp_project):
        with patch("security_runner._check_tool", return_value=False):
            result = runner.invoke(app, ["scan", str(tmp_project)])
        assert result.exit_code == 1
        assert "semgrep introuvable" in result.output

    def test_scan_no_strict_does_not_exit_1(self, tmp_project):
        finding = {"check_id": "no-shell-true", "path": "x.py", "start": {"line": 1}, "extra": {"lines": ""}}
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(0, json.dumps({"results": [finding]}), "")):
            result = runner.invoke(app, ["scan", str(tmp_project), "--no-strict"])
        assert result.exit_code == 0

class TestSecrets:
    def test_secrets_pass(self, tmp_project):
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(0, "", "")):
            result = runner.invoke(app, ["secrets", str(tmp_project)])
        assert result.exit_code == 0

    def test_secrets_fail(self, tmp_project):
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(1, "", "ANTHROPIC_API_KEY found")):
            result = runner.invoke(app, ["secrets", str(tmp_project), "--strict"])
        assert result.exit_code == 1

    def test_secrets_skip_graceful(self, tmp_project):
        with patch("security_runner._check_tool", return_value=False):
            result = runner.invoke(app, ["secrets", str(tmp_project)])
        assert result.exit_code == 0

class TestDocker:
    def test_docker_pass_with_127(self, tmp_project, safe_docker_compose):
        result = runner.invoke(app, ["docker", str(safe_docker_compose)])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_docker_fail_with_open_port(self, tmp_project, unsafe_docker_compose):
        result = runner.invoke(app, ["docker", str(unsafe_docker_compose), "--strict"])
        assert result.exit_code == 1

    def test_docker_missing_compose_file(self, tmp_project):
        result = runner.invoke(app, ["docker", str(tmp_project / "nonexistent.yml")])
        assert result.exit_code == 0

    def test_docker_fix_suggestion_shown(self, tmp_project, unsafe_docker_compose):
        result = runner.invoke(app, ["docker", str(unsafe_docker_compose), "--no-strict"])
        assert "127.0.0.1" in result.output

class TestUUID:
    def test_uuid_pass_no_sha1(self, tmp_project, safe_python_file):
        result = runner.invoke(app, ["uuid", str(tmp_project)])
        assert result.exit_code == 0

    def test_uuid_fail_sha1_found(self, tmp_project):
        """sha1 detecte -> FAIL."""
        (tmp_project / "bad.py").write_text("import hashlib\ndoc_id = hashlib.sha1(b'x').hexdigest()\n")
        result = runner.invoke(app, ["uuid", str(tmp_project), "--strict"])
        assert result.exit_code == 1

    def test_uuid_excludes_venv(self, tmp_project):
        venv_dir = tmp_project / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        (venv_dir / "bad.py").write_text("import hashlib\nhashlib.sha1(b'x')\n")
        result = runner.invoke(app, ["uuid", str(tmp_project)])
        assert result.exit_code == 0

class TestFullAudit:
    def test_full_audit_all_pass(self, tmp_project, safe_python_file, safe_docker_compose):
        semgrep_output = json.dumps({"results": []})
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(0, semgrep_output, "")):
            result = runner.invoke(app, ["full-audit", str(tmp_project)])
        assert result.exit_code == 0

    def test_full_audit_strict_exit_1_on_any_failure(self, tmp_project, unsafe_python_file):
        semgrep_output = json.dumps({"results": [
            {"check_id": "no-shell-true", "path": str(unsafe_python_file),
             "start": {"line": 2}, "extra": {"lines": "shell=True"}}
        ]})
        with patch("security_runner._check_tool", return_value=True), \
             patch("security_runner._run", return_value=(1, semgrep_output, "")):
            result = runner.invoke(app, ["full-audit", str(tmp_project), "--strict"])
        assert result.exit_code == 1

    def test_full_audit_shows_summary_table(self, tmp_project):
        with patch("security_runner._check_tool", return_value=False), \
             patch("security_runner._run", return_value=(0, json.dumps({"results": []}), "")):
            result = runner.invoke(app, ["full-audit", str(tmp_project)])
        assert "scan" in result.output
        assert "docker" in result.output

class TestRunHelper:
    def test_run_uses_list_not_string(self):
        import security_runner
        calls = []
        def mock_run(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return MagicMock(returncode=0, stdout="", stderr="")
        with patch("subprocess.run", side_effect=mock_run):
            security_runner._run(["echo", "hello"])
        cmd, kwargs = calls[0]
        assert isinstance(cmd, list)
        assert kwargs.get("shell", False) is False
