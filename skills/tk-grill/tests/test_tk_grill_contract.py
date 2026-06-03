"""Smoke test contractuel pour le skill tk-grill.

Vérifie que SKILL.md respecte les invariants maison TricorderKit :
- frontmatter YAML présent et parsable (name == tk-grill)
- sections obligatoires présentes (pré-vol, protocole, gate Risk Guard, format de sortie)
- blocs de sortie contractuels cités (## 📋 À copier + ## 📊 Notes de fiabilité)
- au moins un exemple fourni

Exécution : pytest skills/tk-grill/tests/test_tk_grill_contract.py
"""
from __future__ import annotations

from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_skill_md_exists() -> None:
    assert SKILL_MD.is_file(), "SKILL.md manquant"


def test_frontmatter_name() -> None:
    text = _read(SKILL_MD)
    assert text.startswith("---"), "frontmatter YAML absent"
    head = text.split("---", 2)[1]
    assert "name: tk-grill" in head, "name != tk-grill dans le frontmatter"
    assert "description:" in head, "description absente du frontmatter"


@pytest.mark.parametrize(
    "needle",
    [
        "Pré-vol obligatoire",
        "Protocole d'interrogation",
        "Gate de sortie",
        "Risk Guard",
        "Une seule question à la fois",
        "DEC-016",
        "CLI avant LLM",
        "skill_output.schema.json",
    ],
)
def test_required_sections(needle: str) -> None:
    assert needle in _read(SKILL_MD), f"section/garde-fou manquant : {needle!r}"


def test_output_contract_blocks() -> None:
    text = _read(SKILL_MD)
    assert "## 📋 À copier" in text, "bloc '## 📋 À copier' manquant"
    assert "## 📊 Notes de fiabilité" in text, "bloc '## 📊 Notes de fiabilité' manquant"


def test_example_present() -> None:
    examples = list((SKILL_DIR / "examples").glob("*.md"))
    assert examples, "aucun exemple dans examples/"
    # l'exemple doit lui aussi porter les blocs de sortie contractuels
    sample = _read(examples[0])
    assert "## 📋 À copier" in sample
    assert "## 📊 Notes de fiabilité" in sample
