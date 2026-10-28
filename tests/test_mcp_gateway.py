# -*- coding: utf-8 -*-
"""
Tests du gouverneur MCP machine-lisible (mcp/scripts/mcp_gateway.py).
DEC-046 / N3 — deny-by-default, audit .mcp.json, contrat skill_output.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GATEWAY_DIR = REPO_ROOT / "mcp" / "scripts"
GATEWAY = GATEWAY_DIR / "mcp_gateway.py"
SKILL_CONTRACT = REPO_ROOT / "core" / "contracts" / "skill_output.schema.json"

if str(GATEWAY_DIR) not in sys.path:
    sys.path.insert(0, str(GATEWAY_DIR))

import mcp_gateway as gw  # noqa: E402


# ── Fixtures ────────────────────────────────────────────────────────────────────
@pytest.fixture
def allow():
    return gw.load_allowlist()


def _contract_validator():
    import jsonschema
    schema = json.loads(SKILL_CONTRACT.read_text(encoding="utf-8"))
    cls = getattr(jsonschema, "Draft7Validator", None) or jsonschema.validators.validator_for(schema)
    return cls(schema)


# ── decide() : deny-by-default ──────────────────────────────────────────────────
def test_decide_allows_declared_tool(allow):
    d = gw.decide(allow, "graph-server", "graphify_store")
    assert d["allowed"] is True
    assert d["permission"] == "write"
    assert d["dry_run_default"] is True


def test_decide_denies_undeclared_server(allow):
    d = gw.decide(allow, "rogue-server", "anything")
    assert d["allowed"] is False
    assert "non declare" in d["reason"]


def test_decide_denies_undeclared_tool(allow):
    d = gw.decide(allow, "vault-search", "delete_everything")
    assert d["allowed"] is False


def test_decide_denies_forbidden_pattern(allow):
    d = gw.decide(allow, "vault-search", "shell_exec")
    assert d["allowed"] is False
    assert "banni" in d["reason"]


# ── audit() ─────────────────────────────────────────────────────────────────────
def test_audit_real_config_is_clean(allow):
    cfg = gw.load_mcp_config()
    res = gw.audit(allow, cfg)
    assert res["violations"] == []


def test_audit_flags_undeclared_server(allow):
    cfg = {"mcpServers": {"sneaky": {"type": "stdio", "command": "node", "args": []}}}
    res = gw.audit(allow, cfg)
    kinds = {v["kind"] for v in res["violations"]}
    assert "undeclared_server" in kinds


def test_audit_flags_inline_secret(allow):
    cfg = {"mcpServers": {"graph-server": {"type": "stdio", "command": "node",
            "env": {"NEO4J_PASSWORD": "hunter2_plaintext"}}}}
    res = gw.audit(allow, cfg)
    kinds = {v["kind"] for v in res["violations"]}
    assert "inline_secret" in kinds


def test_audit_accepts_env_reference(allow):
    cfg = {"mcpServers": {"graph-server": {"type": "stdio", "command": "node",
            "env": {"NEO4J_PASSWORD": "${NEO4J_PASSWORD}"}}}}
    res = gw.audit(allow, cfg)
    assert all(v["kind"] != "inline_secret" for v in res["violations"])


# ── Contrat skill_output ────────────────────────────────────────────────────────
def test_skill_output_success_conforms_contract():
    env = gw.skill_output("success", "ok", data={"x": 1})
    errors = list(_contract_validator().iter_errors(env))
    assert errors == [], errors


def test_skill_output_error_conforms_contract():
    env = gw.skill_output("error", "nope",
                          error={"code": "X", "message": "y",
                                 "recoverable": True, "rollback_available": False})
    errors = list(_contract_validator().iter_errors(env))
    assert errors == [], errors


# ── Bout-en-bout : codes retour CLI ─────────────────────────────────────────────
def _run(*args):
    return subprocess.run([sys.executable, str(GATEWAY), *args],
                          cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8")


def test_cli_allowlist_check_allowed_exit0():
    r = _run("allowlist-check", "--server", "graph-server", "--tool", "graphify_ping")
    assert r.returncode == 0
    assert json.loads(r.stdout)["output"]["data"]["allowed"] is True


def test_cli_allowlist_check_denied_exit1():
    r = _run("allowlist-check", "--server", "rogue", "--tool", "x")
    assert r.returncode == 1


def test_cli_audit_real_exit0():
    r = _run("audit")
    assert r.returncode == 0
