"""Tests du routeur SLM local (PoC G2).

Ne nécessitent NI Ollama NI réseau : on valide le chargement des profils, la
construction de la consigne, le repli sûr quand Ollama est absent, et le dry-run.
"""
import importlib.util
import json
from pathlib import Path

import pytest

POC_DIR = Path(__file__).resolve().parents[1]


def _load_module():
    spec = importlib.util.spec_from_file_location("local_router", POC_DIR / "local_router.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lr = _load_module()


@pytest.fixture
def profiles(tmp_path):
    cfg = {
        "default_profile": "episodic",
        "profiles": {
            "episodic": {"when": "historique, logs, reprise", "mcp_config": "./e.json"},
            "domain": {"when": "données, templates, fiches", "mcp_config": "./d.json"},
            "dev": {"when": "code, git, shell", "mcp_config": "./v.json"},
        },
    }
    p = tmp_path / "profiles.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return lr.load_profiles(p)


def test_load_profiles_ok(profiles):
    assert profiles["default_profile"] == "episodic"
    assert set(profiles["profiles"]) == {"episodic", "domain", "dev"}


def test_load_profiles_missing(tmp_path):
    with pytest.raises(SystemExit):
        lr.load_profiles(tmp_path / "absent.json")


def test_default_profile_fallback_when_invalid(tmp_path):
    cfg = {"default_profile": "ghost", "profiles": {"a": {"when": "x"}}}
    p = tmp_path / "p.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    loaded = lr.load_profiles(p)
    assert loaded["default_profile"] == "a"  # repli sur le premier profil


def test_system_instruction_lists_all_profiles(profiles):
    instr = lr.build_system_instruction(profiles)
    for key in profiles["profiles"]:
        assert key in instr


def test_route_keyword_fastpath_no_server(monkeypatch, profiles):
    # Prompt net -> tranché par mots-clés, SANS toucher au serveur (qui est down ici).
    monkeypatch.setattr(lr, "OLLAMA_API_BASE", "http://127.0.0.1:9")
    decision = lr.route("audit securite du depot git et refactor du code", profiles, lr.DEFAULT_MODEL)
    assert decision["profile"] == "dev"
    assert "keyword" in decision["reason"]


def test_route_ambiguous_falls_back_to_default_when_server_down(monkeypatch, profiles):
    # Prompt sans mot-clé -> SLM sollicité -> serveur down -> profil par défaut (jamais bloquant).
    monkeypatch.setattr(lr, "OLLAMA_API_BASE", "http://127.0.0.1:9")
    decision = lr.route("fais le truc maintenant", profiles, lr.DEFAULT_MODEL)
    assert decision["profile"] == "episodic"  # default_profile
    assert "défaut" in decision["reason"]


def test_keyword_decision_margin(profiles):
    best, margin, scores = lr.keyword_decision("audit securite git refactor code shell", profiles)
    assert best == "dev"
    assert margin >= 1


def test_launch_agent_dry_run_no_exec(capsys):
    cfg = {"mcp_config": "./e.json", "agent_cmd": ["claude"]}
    rc = lr.launch_agent(cfg, "ma demande", dry_run=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY-RUN" in out and "ma demande" in out
