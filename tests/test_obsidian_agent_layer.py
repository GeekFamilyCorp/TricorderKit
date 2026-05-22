"""
test_obsidian_agent_layer.py — Tests obsidian-agent-layer
TricorderKit v0.9 M5

Couvre sans services réels (dry_run=True / pure functions) :
  vault_router.py    — resolve_vault(), list_vaults(), VaultRouterError
  note_builder.py    — _slugify(), _yaml_value(), build_*_note(), build_note()
  obsidian_client.py — ObsidianClient dry_run, rate_limit, ClientResult, create_client()

Usage:
  pytest tests/test_obsidian_agent_layer.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ── Import des modules du plugin ──────────────────────────────────────────────
PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "obsidian-agent-layer"
sys.path.insert(0, str(PLUGIN_DIR))

from vault_router import (
    VaultId, VaultConfig, VaultRouterError,
    resolve_vault, list_vaults, VAULT_CONFIGS,
)
from note_builder import (
    NoteSpec, BuiltNote,
    build_note, build_manga_note, build_anime_note,
    build_seiyuu_note, build_studio_note, build_generic_note,
    _slugify, _yaml_value,
)
from obsidian_client import ObsidianClient, ClientResult, create_client


# ═══════════════════════════════════════════════════════════════════════════════
# vault_router
# ═══════════════════════════════════════════════════════════════════════════════

def test_resolve_vault_explicit_claude():
    """explicit='claude-vault' → VaultId.CLAUDE."""
    cfg = resolve_vault(explicit_vault="claude-vault")
    assert cfg.vault_id == VaultId.CLAUDE


def test_resolve_vault_by_type_manga():
    """note_type='manga' → notes-vault."""
    cfg = resolve_vault(note_type="manga")
    assert cfg.vault_id == VaultId.NOTES


def test_resolve_vault_by_path_prefix():
    """path='Mangas/One-Piece.md' → notes-vault."""
    cfg = resolve_vault(note_path="Mangas/One-Piece.md")
    assert cfg.vault_id == VaultId.NOTES


def test_resolve_vault_default():
    """Aucun argument → claude-vault (défaut)."""
    cfg = resolve_vault()
    assert cfg.vault_id == VaultId.CLAUDE


def test_resolve_vault_unknown_raises():
    """Vault inconnu → VaultRouterError."""
    with pytest.raises(VaultRouterError, match="Vault inconnu"):
        resolve_vault(explicit_vault="does-not-exist")


def test_list_vaults_returns_configs():
    """list_vaults() retourne au moins 2 configs."""
    vaults = list_vaults()
    assert len(vaults) >= 2
    ids = [v.vault_id for v in vaults]
    assert VaultId.CLAUDE in ids
    assert VaultId.NOTES in ids


# ═══════════════════════════════════════════════════════════════════════════════
# note_builder — helpers
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("text,expected", [
    ("One Piece",    "One-Piece"),
    ("Chainsaw Man!", "Chainsaw-Man"),
    ("  DR Stone  ", "DR-Stone"),
    ("Berserk",      "Berserk"),
])
def test_slugify(text, expected):
    assert _slugify(text) == expected


@pytest.mark.parametrize("value,expected", [
    (None,          "null"),
    (True,          "true"),
    (False,         "false"),
    (42,            "42"),
    ([],            "[]"),
    ("simple",      "simple"),
    ("has: colon",  '"has: colon"'),
])
def test_yaml_value(value, expected):
    assert _yaml_value(value) == expected


def test_yaml_value_list_multiline():
    result = _yaml_value(["a", "b"])
    assert "- a" in result
    assert "- b" in result


# ═══════════════════════════════════════════════════════════════════════════════
# note_builder — build_*_note
# ═══════════════════════════════════════════════════════════════════════════════

def test_build_manga_note_path():
    """Path = Mangas/<title>/<slug>.md"""
    spec = NoteSpec(note_type="manga", title="One Piece",
                    fields={"author": "Oda Eiichiro"})
    note = build_manga_note(spec)
    assert note.path == "Mangas/One Piece/One-Piece.md"
    assert note.note_type == "manga"


def test_build_manga_note_frontmatter():
    """Contenu commence par frontmatter YAML valide."""
    spec = NoteSpec(note_type="manga", title="Berserk",
                    fields={"author": "Miura Kentaro", "volumes": 41})
    note = build_manga_note(spec)
    assert note.content.startswith("---")
    assert "type: manga" in note.content
    assert "Miura Kentaro" in note.content


def test_build_manga_note_tags_include_manga():
    """Tags inclut toujours 'manga'."""
    spec = NoteSpec(note_type="manga", title="Test", tags=["shonen"])
    note = build_manga_note(spec)
    assert "- manga" in note.content
    assert "- shonen" in note.content


def test_build_anime_note_path():
    """Path = Animes/<title>/<slug>.md"""
    spec = NoteSpec(note_type="anime", title="Attack on Titan",
                    fields={"studio": "MAPPA"})
    note = build_anime_note(spec)
    assert note.path.startswith("Animes/")
    assert note.note_type == "anime"


def test_build_seiyuu_note_path():
    """Path = Personnes/Seiyuu/<slug>.md"""
    spec = NoteSpec(note_type="seiyuu", title="Hanazawa Kana")
    note = build_seiyuu_note(spec)
    assert note.path.startswith("Personnes/Seiyuu/")


def test_build_studio_note_path():
    """Path = Studios/<slug>.md"""
    spec = NoteSpec(note_type="studio", title="Madhouse",
                    fields={"founded": "1972"})
    note = build_studio_note(spec)
    assert note.path.startswith("Studios/")


def test_build_generic_note_default_folder():
    """Sans folder explicite → 10_INBOX."""
    spec = NoteSpec(note_type="note", title="Ma note")
    note = build_generic_note(spec)
    assert note.path.startswith("10_INBOX/")


def test_build_note_dispatcher_seiyuu():
    """build_note() avec type='seiyuu' → Personnes/Seiyuu/."""
    spec = NoteSpec(note_type="seiyuu", title="Miyuki Sawashiro")
    note = build_note(spec)
    assert note.path.startswith("Personnes/Seiyuu/")


# ═══════════════════════════════════════════════════════════════════════════════
# obsidian_client
# ═══════════════════════════════════════════════════════════════════════════════

def test_dry_run_write_note():
    """write_note en dry_run → success=True, dry_run=True."""
    client = ObsidianClient(vault_id=VaultId.CLAUDE, dry_run=True)
    op = client.write_note("test/note.md", "# Test")
    assert op.success
    assert op.dry_run
    assert op.operation == "create"


def test_dry_run_patch_note():
    """patch_note en dry_run → success=True, operation='patch'."""
    client = ObsidianClient(vault_id=VaultId.CLAUDE, dry_run=True)
    op = client.patch_note("test/note.md", "old text", "new text")
    assert op.success
    assert op.operation == "patch"


def test_rate_limit_raises():
    """Dépasser max_ops_per_session → RuntimeError."""
    client = ObsidianClient(vault_id=VaultId.CLAUDE, dry_run=True, max_ops_per_session=2)
    client.write_note("a.md", "x")
    client.write_note("b.md", "y")
    with pytest.raises(RuntimeError, match="Rate-limit"):
        client.write_note("c.md", "z")


def test_create_structured_note_dry_run():
    """create_structured_note() → retourne (BuiltNote, NoteOpResult)."""
    client = ObsidianClient(vault_id=VaultId.NOTES, dry_run=True)
    spec = NoteSpec(
        note_type="manga",
        title="Dragon Ball",
        fields={"author": "Toriyama Akira", "volumes": 42},
    )
    note, op = client.create_structured_note(spec)
    assert isinstance(note, BuiltNote)
    assert op.success
    assert "Dragon Ball" in note.path


def test_client_result_success_property():
    """notes_failed=0 → result.success=True."""
    r = ClientResult(notes_created=3, notes_failed=0)
    assert r.success is True


def test_client_result_failure_property():
    """notes_failed>0 → result.success=False."""
    r = ClientResult(notes_created=2, notes_failed=1)
    assert r.success is False


def test_skill_output_required_keys():
    """to_skill_output() retourne toutes les clés du contrat."""
    r = ClientResult(notes_created=1, vault_id="claude-vault")
    out = r.to_skill_output(duration_ms=100)
    for key in ("status", "skill_name", "skill_version", "timestamp",
                "duration_ms", "output"):
        assert key in out, f"Clé manquante : {key}"
    assert out["skill_name"] == "obsidian-agent-layer"


def test_create_client_factory():
    """create_client() retourne un ObsidianClient configuré."""
    client = create_client(note_type="manga", dry_run=True)
    assert isinstance(client, ObsidianClient)
    assert client.dry_run is True
    # manga → notes-vault
    assert client.vault_config.vault_id == VaultId.NOTES
