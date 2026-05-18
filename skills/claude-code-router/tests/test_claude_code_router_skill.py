"""Tests contrat pour skills/claude-code-router/SKILL.md"""
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "SKILL.md"
TEXT = SKILL.read_text(encoding="utf-8")


def test_skill_file_exists():
    assert SKILL.exists()

def test_skill_has_version():
    assert "0.1.0" in TEXT

def test_routing_table_present():
    assert "connector_hub" in TEXT
    assert "obsidian-goat" in TEXT
    assert "temporal" in TEXT.lower()

def test_dry_run_rule():
    assert "--dry-run" in TEXT
    assert "R3" in TEXT

def test_r1_cli_before_llm():
    assert "R1" in TEXT

def test_r7_anti_doublon():
    assert "R7" in TEXT
    assert "check-note" in TEXT

def test_output_format_json():
    assert '"status"' in TEXT
    assert '"route"' in TEXT

def test_obsidian_routing():
    assert "obsidian-goat read-note" in TEXT
    assert "obsidian-goat write-note" in TEXT

def test_temporal_routing():
    assert "dispatch_temporal.py" in TEXT

def test_guardrails():
    assert "Jamais" in TEXT or "jamais" in TEXT

def test_dependencies_listed():
    assert "mcp__workspace__bash" in TEXT
    assert "connector_hub.py" in TEXT
    assert "AGENTS.md" in TEXT
