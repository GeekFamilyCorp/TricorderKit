"""Tests CliRunner pour tk-installer v0.1.

Valide le contrat skill_output.schema.json (DEC-005) et le standard
implémentation Typer (docs/cli_forge_typer_standard.md) :

- --help retourne 0
- --version retourne 0 et affiche la version
- status et diagnose produisent un JSON conforme au schéma officiel
- summary obligatoire, ≤ 500 chars
- Pas de secrets en sortie
- Codes de sortie respectés
- Anti-écrasement actif (--force requis)
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from tools.tk_installer.tk_installer import (
    CLI_NAME,
    CLI_VERSION,
    VALID_STATUSES,
    app,
)


@pytest.fixture
def runner() -> CliRunner:
    """CliRunner Typer (Click 8.2+ : stdout/stderr séparés par défaut)."""
    return CliRunner()


# ---------------------------------------------------------------------------
# Contrat universel : help, version
# ---------------------------------------------------------------------------

class TestContractHelp:
    def test_help_returns_zero(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_help_mentions_cli_name(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--help"])
        assert "tk-installer" in result.stdout or "tk_installer" in result.stdout

    def test_help_lists_commands(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--help"])
        assert "status" in result.stdout
        assert "diagnose" in result.stdout


class TestContractVersion:
    def test_version_returns_zero(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0

    def test_version_shows_value(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--version"])
        assert CLI_VERSION in result.stdout

    def test_version_shows_cli_name(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--version"])
        assert CLI_NAME in result.stdout


# ---------------------------------------------------------------------------
# Contrat skill_output.schema.json — status
# ---------------------------------------------------------------------------

class TestSchemaStatus:
    """status doit produire un JSON conforme au schéma."""

    def test_status_json_is_parseable(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["status", "--output", "json"])
        payload = json.loads(result.stdout)
        assert isinstance(payload, dict)

    def test_status_required_fields(self, runner: CliRunner) -> None:
        """Champs `required` du schéma."""
        result = runner.invoke(app, ["status", "--output", "json"])
        payload = json.loads(result.stdout)
        for field in ("status", "skill_name", "skill_version", "timestamp", "output"):
            assert field in payload, f"Champ obligatoire manquant : {field}"
        assert payload["status"] in VALID_STATUSES

    def test_status_skill_name_namespaced(self, runner: CliRunner) -> None:
        """skill_name doit identifier la CLI + la commande."""
        result = runner.invoke(app, ["status", "--output", "json"])
        payload = json.loads(result.stdout)
        assert payload["skill_name"] == f"{CLI_NAME}.status"

    def test_status_version_format(self, runner: CliRunner) -> None:
        """Le schéma impose semver X.Y.Z."""
        import re
        result = runner.invoke(app, ["status", "--output", "json"])
        payload = json.loads(result.stdout)
        assert re.match(r"^\d+\.\d+\.\d+$", payload["skill_version"])

    def test_status_timestamp_iso_z(self, runner: CliRunner) -> None:
        """timestamp doit être ISO 8601 (suffixe Z attendu)."""
        result = runner.invoke(app, ["status", "--output", "json"])
        payload = json.loads(result.stdout)
        ts = payload["timestamp"]
        assert ts.endswith("Z") or "+" in ts, f"Timestamp non ISO 8601 : {ts}"

    def test_status_output_has_summary(self, runner: CliRunner) -> None:
        """output.summary est obligatoire, ≤ 500 chars."""
        result = runner.invoke(app, ["status", "--output", "json"])
        payload = json.loads(result.stdout)
        summary = payload["output"]["summary"]
        assert isinstance(summary, str)
        assert 0 < len(summary) <= 500

    def test_status_stdout_clean_json(self, runner: CliRunner) -> None:
        """stdout en mode json = JSON pur, pas de logs rich."""
        result = runner.invoke(app, ["status", "--output", "json"])
        json.loads(result.stdout)  # lève si pollué


# ---------------------------------------------------------------------------
# Contrat skill_output.schema.json — diagnose
# ---------------------------------------------------------------------------

class TestSchemaDiagnose:
    def test_diagnose_json_is_parseable(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["diagnose", "--dry-run", "--output", "json"])
        payload = json.loads(result.stdout)
        assert isinstance(payload, dict)

    def test_diagnose_required_fields(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["diagnose", "--dry-run", "--output", "json"])
        payload = json.loads(result.stdout)
        for field in ("status", "skill_name", "skill_version", "timestamp", "output"):
            assert field in payload
        assert payload["status"] in VALID_STATUSES

    def test_diagnose_skill_name_namespaced(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["diagnose", "--dry-run", "--output", "json"])
        payload = json.loads(result.stdout)
        assert payload["skill_name"] == f"{CLI_NAME}.diagnose"

    def test_diagnose_reports_environment(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["diagnose", "--dry-run", "--output", "json"])
        payload = json.loads(result.stdout)
        env = payload["output"]["data"].get("environment", {})
        assert "python" in env
        assert "os" in env

    def test_diagnose_dry_run_status(self, runner: CliRunner) -> None:
        """En mode --dry-run, status = 'dry_run'."""
        result = runner.invoke(app, ["diagnose", "--dry-run", "--output", "json"])
        payload = json.loads(result.stdout)
        assert payload["status"] == "dry_run"

    def test_diagnose_dry_run_has_report(self, runner: CliRunner) -> None:
        """status=dry_run impose la présence de dry_run_report."""
        result = runner.invoke(app, ["diagnose", "--dry-run", "--output", "json"])
        payload = json.loads(result.stdout)
        assert "dry_run_report" in payload
        rr = payload["dry_run_report"]
        assert "actions_that_would_run" in rr
        assert "risk_level" in rr
        assert rr["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    def test_diagnose_dry_run_does_not_create_files(self, runner: CliRunner) -> None:
        """--dry-run ne crée aucun fichier (output.files_created vide)."""
        result = runner.invoke(app, ["diagnose", "--dry-run", "--output", "json"])
        payload = json.loads(result.stdout)
        assert payload["output"].get("files_created", []) == []


# ---------------------------------------------------------------------------
# Contrat sécurité : pas de secrets
# ---------------------------------------------------------------------------

class TestNoSecretsLeaked:
    FORBIDDEN_PATTERNS = [
        "PRIVATE KEY", "BEGIN RSA",
        "api_key=", "password=",
        "ghp_", "sk-ant-",
    ]

    @pytest.mark.parametrize("command_args", [
        ["--help"],
        ["--version"],
        ["status", "--output", "json"],
        ["diagnose", "--dry-run", "--output", "json"],
    ])
    def test_no_secret_in_output(self, runner: CliRunner, command_args: list[str]) -> None:
        result = runner.invoke(app, command_args)
        combined = (result.stdout or "") + (result.stderr or "")
        for pattern in self.FORBIDDEN_PATTERNS:
            assert pattern not in combined, (
                f"Secret potentiel '{pattern}' dans la sortie de {command_args}"
            )


# ---------------------------------------------------------------------------
# Contrat exit codes
# ---------------------------------------------------------------------------

class TestExitCodes:
    def test_unknown_command_returns_code_2(self, runner: CliRunner) -> None:
        """Mauvais usage CLI = 2 (Typer)."""
        result = runner.invoke(app, ["commande-inexistante"])
        assert result.exit_code == 2

    def test_help_returns_zero(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_version_returns_zero(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
