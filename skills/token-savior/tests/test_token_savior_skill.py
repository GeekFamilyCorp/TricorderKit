"""Tests contrat pour skills/token-savior/SKILL.md"""
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "SKILL.md"
TEXT = SKILL.read_text(encoding="utf-8")


def test_skill_file_exists():
    assert SKILL.exists()

def test_skill_has_version():
    assert "0.1.0" in TEXT

def test_skill_has_trigger():
    assert "token-savior" in TEXT and "Trigger" in TEXT

def test_compression_levels_defined():
    for level in ["lite", "full", "ultra"]:
        assert level in TEXT

def test_r15_caveman_protocol():
    assert "R15" in TEXT
    assert "STATUS" in TEXT and "ACTION" in TEXT and "RESULT" in TEXT

def test_no_compress_t3_rule():
    assert "T3" in TEXT

def test_deactivation_keywords():
    assert "token-savior off" in TEXT

def test_dependencies_listed():
    assert "AGENTS.md" in TEXT
    assert "token-optimizer" in TEXT
