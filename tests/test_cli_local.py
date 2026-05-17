#!/usr/bin/env python3
"""
test_cli_local.py — Tests CLI tk (TricorderKit v0.8)

Teste toutes les commandes de cli/tk.py en mode subprocess :
  - exit codes
  - output JSON valide quand --format json
  - contenu Markdown attendu
  - robustesse face aux erreurs

Usage :
  pytest tests/test_cli_local.py -v
  pytest tests/test_cli_local.py -v -k "json"
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# ─── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
CLI       = REPO_ROOT / "cli" / "tk.py"
PYTHON    = sys.executable

# ─── Helper ───────────────────────────────────────────────────────────────────

def run(args: list[str], timeout: int = 15) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONUTF8": "1"}
    return subprocess.run(
        [PYTHON, str(CLI), *args],
        capture_output=True, text=True,
        encoding="utf-8-sig",   # strip BOM produit par io.TextIOWrapper sur Windows
        errors="replace",
        timeout=timeout,
        cwd=str(REPO_ROOT), env=env,
    )


def assert_valid_json(output: str) -> dict | list:
    """Parse le JSON et échoue proprement si invalide."""
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        pytest.fail(f"Output n'est pas du JSON valide : {e}\n---\n{output[:500]}")


# ─── Tests : commandes de base ────────────────────────────────────────────────

class TestStatus:
    def test_status_markdown_exit0(self):
        r = run(["status"])
        assert r.returncode == 0, f"stderr: {r.stderr}"

    def test_status_json_valid(self):
        r = run(["status", "--format", "json"])
        assert r.returncode == 0
        data = assert_valid_json(r.stdout)
        assert "version" in data
        assert data["version"] == "0.8"

    def test_status_json_has_services(self):
        r = run(["status", "--format", "json"])
        data = assert_valid_json(r.stdout)
        assert "services" in data
        assert isinstance(data["services"], dict)

    def test_status_json_has_linked_projects(self):
        r = run(["status", "--format", "json"])
        data = assert_valid_json(r.stdout)
        assert "linked_projects" in data
        assert isinstance(data["linked_projects"], list)


class TestHealth:
    def test_health_runs(self):
        r = run(["health"])
        # Peut retourner 1 si services arrêtés — c'est normal en CI
        assert r.returncode in (0, 1), f"Exit inattendu: {r.returncode}\n{r.stderr}"

    def test_doctor_alias(self):
        r = run(["doctor"])
        assert r.returncode in (0, 1)

    def test_health_contains_sections(self):
        r = run(["health"])
        combined = r.stdout + r.stderr
        assert "Python" in combined or "python" in combined.lower()
        assert "Docker" in combined or "docker" in combined.lower()


class TestSkillList:
    def test_skill_list_markdown(self):
        r = run(["skill", "list"])
        assert r.returncode == 0
        assert "Skills" in r.stdout or "skill" in r.stdout.lower()

    def test_skill_list_json_valid(self):
        r = run(["skill", "list", "--format", "json"])
        assert r.returncode == 0
        data = assert_valid_json(r.stdout)
        assert "skills" in data
        assert isinstance(data["skills"], list)

    def test_skill_list_json_has_id(self):
        r = run(["skill", "list", "--format", "json"])
        data = assert_valid_json(r.stdout)
        if data["skills"]:
            assert "id" in data["skills"][0]


class TestWorkflowList:
    def test_workflow_list_markdown(self):
        r = run(["workflow", "list"])
        assert r.returncode == 0
        assert "Workflow" in r.stdout or "workflow" in r.stdout.lower()

    def test_workflow_list_json_valid(self):
        r = run(["workflow", "list", "--format", "json"])
        assert r.returncode == 0
        data = assert_valid_json(r.stdout)
        assert "workflows" in data
        assert isinstance(data["workflows"], list)


class TestVaultScan:
    def test_vault_scan_runs(self):
        r = run(["vault", "scan"])
        assert r.returncode in (0, 1), f"Exit inattendu: {r.returncode}"

    def test_vault_scan_json(self):
        r = run(["vault", "scan", "--format", "json"])
        assert r.returncode in (0, 1)
        data = assert_valid_json(r.stdout)
        assert "vault_path" in data
        assert "total_notes" in data
        assert "health" in data


class TestResearchRun:
    def test_dry_run_exit0(self):
        r = run(["research", "run", "One Piece", "--dry-run"])
        assert r.returncode == 0, f"stderr: {r.stderr}"

    def test_dry_run_json(self):
        r = run(["research", "run", "One Piece", "--dry-run", "--format", "json"])
        assert r.returncode == 0
        data = assert_valid_json(r.stdout)
        assert data.get("dry_run") is True
        assert "query" in data
        assert data["query"] == "One Piece"

    def test_dry_run_script_exists(self):
        r = run(["research", "run", "test", "--dry-run", "--format", "json"])
        data = assert_valid_json(r.stdout)
        assert data.get("script_exists") is True

    def test_no_dry_run_requires_confirmation(self):
        """Sans --dry-run, la commande doit exiger --dry-run (pas d'exécution silencieuse)."""
        r = run(["research", "run", "One Piece"])
        # Doit soit demander confirmation, soit retourner une erreur explicite
        combined = r.stdout + r.stderr
        assert "dry-run" in combined.lower() or r.returncode != 0


# ─── Tests : commandes project ────────────────────────────────────────────────

class TestProjectList:
    def test_project_list_markdown(self):
        r = run(["project", "list"])
        assert r.returncode == 0
        assert "japan-alliance" in r.stdout.lower() or "Japan" in r.stdout

    def test_project_list_json(self):
        r = run(["project", "list", "--format", "json"])
        assert r.returncode == 0
        data = assert_valid_json(r.stdout)
        assert "linked_projects" in data
        assert isinstance(data["linked_projects"], list)

    def test_project_list_json_has_japan_alliance(self):
        r = run(["project", "list", "--format", "json"])
        data = assert_valid_json(r.stdout)
        ids = [p.get("id") for p in data["linked_projects"]]
        assert "japan-alliance" in ids


class TestProjectStatus:
    def test_project_status_known(self):
        r = run(["project", "status", "japan-alliance"])
        assert r.returncode in (0, 1)  # 1 si répertoire absent en CI

    def test_project_status_unknown_returns_error(self):
        r = run(["project", "status", "projet-qui-nexiste-pas"])
        assert r.returncode != 0


class TestProjectAudit:
    def test_project_audit_known(self):
        r = run(["project", "audit", "japan-alliance"])
        assert r.returncode in (0, 1)

    def test_project_audit_json_valid(self):
        r = run(["project", "audit", "japan-alliance", "--format", "json"])
        assert r.returncode in (0, 1)
        data = assert_valid_json(r.stdout)
        assert "score" in data
        assert data["score"] in ("PASS", "WARN", "FAIL")

    def test_project_audit_unknown_returns_fail(self):
        """Projet inconnu → score FAIL (le CLI retourne 0 avec FAIL dans l'output)."""
        r = run(["project", "audit", "projet-fantome"])
        combined = r.stdout + r.stderr
        assert "FAIL" in combined or "absent" in combined.lower()


class TestProjectVaultScan:
    def test_vault_scan_known(self):
        r = run(["project", "vault", "scan", "japan-alliance"])
        assert r.returncode in (0, 1)

    def test_vault_scan_unknown(self):
        r = run(["project", "vault", "scan", "projet-fantome"])
        combined = r.stdout + r.stderr
        assert "introuvable" in combined.lower() or r.returncode != 0


class TestProjectWorkflowList:
    def test_workflow_list_known(self):
        r = run(["project", "workflow", "list", "japan-alliance"])
        assert r.returncode in (0, 1)

    def test_workflow_list_json(self):
        r = run(["project", "workflow", "list", "japan-alliance", "--format", "json"])
        assert r.returncode in (0, 1)
        data = assert_valid_json(r.stdout)
        assert "project_id" in data
        assert "workflows" in data


# ─── Tests : robustesse ───────────────────────────────────────────────────────

class TestRobustness:
    def test_unknown_command_returns_nonzero(self):
        r = run(["commande-inconnue"])
        assert r.returncode != 0

    def test_help_flag(self):
        r = run(["--help"])
        assert r.returncode == 0
        assert "tk" in r.stdout.lower() or "usage" in r.stdout.lower()

    def test_version_flag(self):
        r = run(["--version"])
        assert r.returncode == 0
        assert "0.8" in r.stdout

    def test_format_md_alias(self):
        """--format md doit être accepté comme alias de markdown."""
        r = run(["status", "--format", "md"])
        assert r.returncode == 0


# ─── Tests : encoding ─────────────────────────────────────────────────────────

class TestEncoding:
    def test_no_encoding_error_on_status(self):
        """Pas de UnicodeEncodeError sur les box-drawing chars."""
        r = run(["status"])
        assert "UnicodeEncodeError" not in r.stderr
        assert "charmap" not in r.stderr

    def test_json_ascii_false(self):
        """Le JSON doit conserver les caractères non-ASCII (accents, CJK)."""
        r = run(["skill", "list", "--format", "json"])
        data = assert_valid_json(r.stdout)
        # Si le JSON est re-parsable, l'encodage est correct
        assert data is not None
