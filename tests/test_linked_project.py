#!/usr/bin/env python3
"""
test_linked_project.py — Tests des outils d'audit linked_project (TricorderKit v0.8)

Couvre :
  - tools/audit/linked_project_audit.py  (audit structure/git/config/secrets/cohérence)
  - tools/audit/local_vs_github_audit.py (diff local vs GitHub)

Stratégie :
  - Mode subprocess (comme test_cli_local.py) — pas d'import direct
  - Tests JSON contractuels (structure de sortie garantie)
  - Tests de robustesse (projets inconnus, args manquants)
  - Tests qui acceptent rc=0 ou 1 selon l'état réel (Git, réseau)

Usage :
  pytest tests/test_linked_project.py -v
  pytest tests/test_linked_project.py -v -k "json"
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# ─── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT    = Path(__file__).resolve().parent.parent
AUDIT_LP     = REPO_ROOT / "tools" / "audit" / "linked_project_audit.py"
AUDIT_GITHUB = REPO_ROOT / "tools" / "audit" / "local_vs_github_audit.py"
PYTHON       = sys.executable

# ─── Helpers ──────────────────────────────────────────────────────────────────

def run(script: Path, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONUTF8": "1"}
    return subprocess.run(
        [PYTHON, str(script), *args],
        capture_output=True, text=True,
        encoding="utf-8-sig",
        errors="replace",
        timeout=timeout,
        cwd=str(REPO_ROOT), env=env,
    )


def run_lp(*args, **kw) -> subprocess.CompletedProcess:
    """Raccourci pour linked_project_audit.py."""
    return run(AUDIT_LP, list(args), **kw)


def run_gh(*args, **kw) -> subprocess.CompletedProcess:
    """Raccourci pour local_vs_github_audit.py."""
    return run(AUDIT_GITHUB, list(args), **kw)


def assert_valid_json(output: str) -> dict | list:
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        pytest.fail(f"Output n'est pas du JSON valide : {e}\n---\n{output[:500]}")


# ─── Tests : linked_project_audit.py ─────────────────────────────────────────

class TestLinkedProjectAuditScriptExists:
    def test_script_exists(self):
        assert AUDIT_LP.exists(), f"Script introuvable : {AUDIT_LP}"

    def test_help_runs(self):
        r = run_lp("--help")
        assert r.returncode == 0
        assert "project" in r.stdout.lower() or "audit" in r.stdout.lower()


class TestLinkedProjectAuditList:
    def test_list_runs(self):
        r = run_lp("--list")
        assert r.returncode == 0, f"stderr: {r.stderr}"

    def test_list_contains_japan_alliance(self):
        r = run_lp("--list")
        combined = r.stdout + r.stderr
        assert "japan-alliance" in combined.lower() or "japan" in combined.lower()


class TestLinkedProjectAuditKnown:
    """Tests avec le projet japan-alliance — résultat dépend de l'état réel."""

    def test_audit_known_exits_0_or_1(self):
        r = run_lp("--project", "japan-alliance")
        assert r.returncode in (0, 1), (
            f"Exit inattendu: {r.returncode}\nstderr: {r.stderr}"
        )

    def test_audit_known_json_valid(self):
        r = run_lp("--project", "japan-alliance", "--format", "json")
        assert r.returncode in (0, 1)
        data = assert_valid_json(r.stdout)
        assert isinstance(data, dict)

    def test_audit_json_has_required_keys(self):
        r = run_lp("--project", "japan-alliance", "--format", "json")
        data = assert_valid_json(r.stdout)
        for key in ("project_id", "project_name", "root", "score", "summary", "findings"):
            assert key in data, f"Clé manquante dans le JSON : {key}"

    def test_audit_json_project_id_matches(self):
        r = run_lp("--project", "japan-alliance", "--format", "json")
        data = assert_valid_json(r.stdout)
        assert data["project_id"] == "japan-alliance"

    def test_audit_json_score_valid(self):
        r = run_lp("--project", "japan-alliance", "--format", "json")
        data = assert_valid_json(r.stdout)
        assert data["score"] in ("PASS", "WARN", "FAIL"), (
            f"Score invalide : {data['score']}"
        )

    def test_audit_json_summary_structure(self):
        r = run_lp("--project", "japan-alliance", "--format", "json")
        data = assert_valid_json(r.stdout)
        summary = data["summary"]
        for key in ("ok", "warn", "error"):
            assert key in summary, f"Clé summary.{key} manquante"
            assert isinstance(summary[key], int)

    def test_audit_json_findings_is_list(self):
        r = run_lp("--project", "japan-alliance", "--format", "json")
        data = assert_valid_json(r.stdout)
        assert isinstance(data["findings"], list)

    def test_audit_json_findings_structure(self):
        r = run_lp("--project", "japan-alliance", "--format", "json")
        data = assert_valid_json(r.stdout)
        for f in data["findings"]:
            assert "level" in f
            assert "category" in f
            assert "message" in f
            assert f["level"] in ("OK", "WARN", "ERROR")

    def test_audit_json_summary_counts_match_findings(self):
        """Vérification de cohérence : summary.ok+warn+error == len(findings)."""
        r = run_lp("--project", "japan-alliance", "--format", "json")
        data = assert_valid_json(r.stdout)
        s = data["summary"]
        total = s["ok"] + s["warn"] + s["error"]
        assert total == len(data["findings"]), (
            f"summary ({total}) != findings ({len(data['findings'])})"
        )

    def test_audit_markdown_contains_score(self):
        r = run_lp("--project", "japan-alliance")
        combined = r.stdout + r.stderr
        assert any(word in combined for word in ("PASS", "WARN", "FAIL")), (
            "Le Markdown doit afficher le score"
        )


class TestLinkedProjectAuditUnknown:
    """Robustesse : projet inconnu."""

    def test_audit_unknown_exits_nonzero(self):
        r = run_lp("--project", "projet-fantome")
        assert r.returncode != 0, "Un projet inconnu doit retourner un code d'erreur"

    def test_audit_unknown_json_score_is_fail(self):
        r = run_lp("--project", "projet-fantome", "--format", "json")
        assert r.returncode != 0
        data = assert_valid_json(r.stdout)
        assert data["score"] == "FAIL"

    def test_audit_unknown_json_has_error_finding(self):
        r = run_lp("--project", "projet-fantome", "--format", "json")
        data = assert_valid_json(r.stdout)
        error_findings = [f for f in data["findings"] if f["level"] == "ERROR"]
        assert len(error_findings) > 0, "Doit contenir au moins un finding ERROR"

    def test_audit_unknown_error_message_mentions_project(self):
        r = run_lp("--project", "projet-fantome", "--format", "json")
        data = assert_valid_json(r.stdout)
        error_messages = " ".join(f["message"] for f in data["findings"] if f["level"] == "ERROR")
        assert "projet-fantome" in error_messages.lower() or "absent" in error_messages.lower()


class TestLinkedProjectAuditNoArgs:
    def test_no_args_exits_nonzero(self):
        r = run_lp()
        assert r.returncode != 0

    def test_no_args_prints_usage(self):
        r = run_lp()
        combined = r.stdout + r.stderr
        assert "usage" in combined.lower() or "project" in combined.lower()


# ─── Tests : local_vs_github_audit.py ────────────────────────────────────────

class TestLocalVsGithubScriptExists:
    def test_script_exists(self):
        assert AUDIT_GITHUB.exists(), f"Script introuvable : {AUDIT_GITHUB}"

    def test_help_runs(self):
        r = run_gh("--help")
        assert r.returncode == 0
        combined = r.stdout + r.stderr
        assert "format" in combined.lower() or "project" in combined.lower()


class TestLocalVsGithubDefault:
    """Sans argument — audit TricorderKit lui-même."""

    def test_default_runs(self):
        r = run_gh(timeout=45)
        # Peut retourner 1 si dirty ou ahead — c'est un état valide
        assert r.returncode in (0, 1), (
            f"Exit inattendu: {r.returncode}\nstderr: {r.stderr}"
        )

    def test_default_json_valid(self):
        r = run_gh("--format", "json", timeout=45)
        assert r.returncode in (0, 1)
        data = assert_valid_json(r.stdout)
        assert isinstance(data, list)

    def test_default_json_non_empty(self):
        r = run_gh("--format", "json", timeout=45)
        data = assert_valid_json(r.stdout)
        assert len(data) > 0, "La liste d'audits doit contenir au moins TricorderKit"

    def test_default_json_has_tricorderkit(self):
        r = run_gh("--format", "json", timeout=45)
        data = assert_valid_json(r.stdout)
        names = [a.get("name", "") for a in data]
        assert any("tricorder" in n.lower() for n in names), (
            f"TricorderKit introuvable dans les noms : {names}"
        )

    def test_default_json_repo_structure(self):
        r = run_gh("--format", "json", timeout=45)
        data = assert_valid_json(r.stdout)
        for repo in data:
            for key in ("name", "root", "branch", "status", "commits_ahead", "commits_behind"):
                assert key in repo, f"Clé manquante dans le JSON repo : {key}"

    def test_default_json_status_valid_values(self):
        r = run_gh("--format", "json", timeout=45)
        data = assert_valid_json(r.stdout)
        valid = {"SYNCED", "AHEAD", "BEHIND", "DIRTY", "ERROR"}
        for repo in data:
            assert repo["status"] in valid, (
                f"Status invalide pour {repo['name']} : {repo['status']}"
            )

    def test_default_json_commits_are_integers(self):
        r = run_gh("--format", "json", timeout=45)
        data = assert_valid_json(r.stdout)
        for repo in data:
            assert isinstance(repo["commits_ahead"], int)
            assert isinstance(repo["commits_behind"], int)


class TestLocalVsGithubProject:
    """--project japan-alliance — audit du seul linked_project."""

    def test_project_known_runs(self):
        r = run_gh("--project", "japan-alliance", timeout=45)
        assert r.returncode in (0, 1), (
            f"Exit inattendu: {r.returncode}\nstderr: {r.stderr}"
        )

    def test_project_known_json_valid(self):
        r = run_gh("--project", "japan-alliance", "--format", "json", timeout=45)
        assert r.returncode in (0, 1)
        data = assert_valid_json(r.stdout)
        assert isinstance(data, list)

    def test_project_known_json_single_entry(self):
        r = run_gh("--project", "japan-alliance", "--format", "json", timeout=45)
        data = assert_valid_json(r.stdout)
        # Avec --project on n'audite qu'un seul repo
        assert len(data) == 1, (
            f"--project devrait retourner 1 repo, got {len(data)}"
        )

    def test_project_known_json_name(self):
        r = run_gh("--project", "japan-alliance", "--format", "json", timeout=45)
        data = assert_valid_json(r.stdout)
        # Le nom contient "japan" ou "alliance"
        name = data[0].get("name", "")
        assert "japan" in name.lower() or "alliance" in name.lower()


class TestLocalVsGithubUnknown:
    def test_project_unknown_exits_nonzero(self):
        r = run_gh("--project", "projet-fantome", timeout=15)
        assert r.returncode != 0

    def test_project_unknown_error_in_output(self):
        r = run_gh("--project", "projet-fantome", timeout=15)
        combined = r.stdout + r.stderr
        assert "projet-fantome" in combined.lower() or "absent" in combined.lower()


class TestLocalVsGithubAll:
    """--all — TricorderKit + tous les linked_projects actifs."""

    def test_all_runs(self):
        r = run_gh("--all", timeout=60)
        assert r.returncode in (0, 1)

    def test_all_json_valid(self):
        r = run_gh("--all", "--format", "json", timeout=60)
        assert r.returncode in (0, 1)
        data = assert_valid_json(r.stdout)
        assert isinstance(data, list)

    def test_all_json_includes_tricorderkit(self):
        r = run_gh("--all", "--format", "json", timeout=60)
        data = assert_valid_json(r.stdout)
        names = [a.get("name", "") for a in data]
        assert any("tricorder" in n.lower() for n in names)

    def test_all_json_includes_japan_alliance(self):
        r = run_gh("--all", "--format", "json", timeout=60)
        data = assert_valid_json(r.stdout)
        names = [a.get("name", "").lower() for a in data]
        assert any("japan" in n or "alliance" in n for n in names)


# ─── Tests : encoding ─────────────────────────────────────────────────────────

class TestAuditEncoding:
    def test_no_unicode_error_linked_project(self):
        r = run_lp("--project", "japan-alliance")
        assert "UnicodeEncodeError" not in r.stderr
        assert "charmap" not in r.stderr

    def test_no_unicode_error_github_audit(self):
        r = run_gh(timeout=45)
        assert "UnicodeEncodeError" not in r.stderr
        assert "charmap" not in r.stderr

    def test_json_unicode_linked_project(self):
        r = run_lp("--project", "japan-alliance", "--format", "json")
        data = assert_valid_json(r.stdout)
        assert data is not None

    def test_json_unicode_github_audit(self):
        r = run_gh("--format", "json", timeout=45)
        data = assert_valid_json(r.stdout)
        assert data is not None
