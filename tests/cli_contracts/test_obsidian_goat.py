"""
tests/cli_contracts/test_obsidian_goat.py
Tests de contrat CLI pour obsidian-goat v0.1.0.
Vérifie : dry-run, output JSON contractuel, gestion d'erreurs.
Aucune écriture sur le vault réel — tout en dry-run ou vault fictif.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

GOAT_PATH = Path(__file__).parent.parent.parent / "tools" / "obsidian-goat" / "obsidian_goat.py"
PYTHON    = sys.executable


def run_goat(*args, cache_path: str = None) -> dict:
    """Exécute obsidian-goat et parse l'output JSON."""
    env = os.environ.copy()
    if cache_path:
        env["OBSIDIAN_GOAT_CACHE"] = cache_path
    else:
        env["OBSIDIAN_GOAT_CACHE"] = "/tmp/obsidian-goat-contract-test.db"

    result = subprocess.run(
        [PYTHON, "-u", str(GOAT_PATH), *args],
        capture_output=True,
        text=True,
        env=env
    )
    assert result.stdout.strip(), f"Pas de stdout. stderr={result.stderr!r}"
    return json.loads(result.stdout.strip())


@pytest.fixture(autouse=True)
def temp_cache(tmp_path):
    """Cache SQLite temporaire pour chaque test."""
    cache = str(tmp_path / "test-goat.db")
    os.environ["OBSIDIAN_GOAT_CACHE"] = cache
    yield cache
    # Cleanup géré par tmp_path


class TestDryRunContract:
    """Tous les dry-runs doivent retourner status=dry_run et ne pas écrire."""

    def test_update_hot_cache_dry_run(self, temp_cache):
        data = run_goat("--dry-run", "update-hot-cache", "--content", "# TEST")
        assert data["status"] == "dry_run"
        assert data["skill_name"] == "obsidian-goat"
        assert "skill_version" in data
        assert "timestamp" in data
        assert "output" in data
        assert data["output"]["dry_run"] is True
        assert data["output"]["command"] == "update-hot-cache"
        assert "operations" in data["output"]
        assert len(data["output"]["operations"]) >= 1

    def test_append_log_dry_run(self, temp_cache):
        data = run_goat("--dry-run", "append-log", "--entry", "Test session log")
        assert data["status"] == "dry_run"
        assert data["output"]["command"] == "append-log"
        assert any("Daily_Logs" in op for op in data["output"]["operations"])

    def test_write_note_dry_run(self, temp_cache):
        data = run_goat("--dry-run", "write-note", "test/note.md",
                        "--content", "# Hello", "--vault", "claude-vault")
        assert data["status"] == "dry_run"
        assert data["output"]["command"] == "write-note"

    def test_append_log_dry_run_with_date(self, temp_cache):
        data = run_goat("--dry-run", "append-log",
                        "--entry", "Test", "--date", "2026-05-18")
        assert data["status"] == "dry_run"
        assert "2026-05-18" in str(data["output"]["operations"])


class TestOutputSchema:
    """Vérifie la conformité au contrat JSON skill_output.schema.json."""

    def test_required_top_level_fields(self, temp_cache):
        data = run_goat("--dry-run", "update-hot-cache", "--content", "# X")
        required = ["status", "skill_name", "skill_version", "timestamp", "output"]
        for field in required:
            assert field in data, f"Champ requis manquant: {field}"

    def test_skill_name_is_obsidian_goat(self, temp_cache):
        data = run_goat("--dry-run", "update-hot-cache", "--content", "# X")
        assert data["skill_name"] == "obsidian-goat"

    def test_skill_version_semver(self, temp_cache):
        import re
        data = run_goat("--dry-run", "update-hot-cache", "--content", "# X")
        assert re.match(r"^\d+\.\d+\.\d+$", data["skill_version"])

    def test_timestamp_iso8601(self, temp_cache):
        data = run_goat("--dry-run", "update-hot-cache", "--content", "# X")
        from datetime import datetime
        # Valider que le timestamp est parseable en ISO 8601
        ts = data["timestamp"].replace("Z", "+00:00")
        datetime.fromisoformat(ts)  # raises si invalide

    def test_output_has_next_steps(self, temp_cache):
        data = run_goat("--dry-run", "update-hot-cache", "--content", "# X")
        assert "next_steps" in data["output"]
        assert isinstance(data["output"]["next_steps"], list)

    def test_output_has_command(self, temp_cache):
        data = run_goat("--dry-run", "append-log", "--entry", "x")
        assert "command" in data["output"]


class TestCheckNote:
    """Tests de check-note (lecture seule, pas de dry-run requis)."""

    def test_check_nonexistent_note(self, temp_cache):
        data = run_goat("check-note", "inexistant/note.md")
        assert data["status"] == "success"
        assert data["output"]["exists"] is False
        assert data["output"]["path"] == "inexistant/note.md"

    def test_check_note_with_vault_param(self, temp_cache):
        data = run_goat("check-note", "test.md", "--vault", "claude-vault")
        assert data["status"] == "success"
        assert data["output"]["vault"] == "claude-vault"

    def test_check_note_unknown_vault(self, temp_cache):
        data = run_goat("check-note", "test.md", "--vault", "inexistant-vault")
        # Doit retourner error, pas crash
        assert data["status"] == "error"


class TestWriteNote:
    """Tests de write-note sur vault temporaire."""

    def test_write_note_creates_file(self, temp_cache, tmp_path):
        """Écriture réelle dans un vault temporaire."""
        fake_vault = str(tmp_path / "vault")
        Path(fake_vault).mkdir()
        env = os.environ.copy()
        env["OBSIDIAN_VAULT_PATH"] = fake_vault
        env["OBSIDIAN_GOAT_CACHE"] = temp_cache

        result = subprocess.run(
            [PYTHON, "-u", str(GOAT_PATH), "write-note", "test/hello.md",
             "--content", "# Hello World", "--vault", "claude-vault"],
            capture_output=True, text=True, env=env
        )
        data = json.loads(result.stdout.strip())
        assert data["status"] == "success"
        assert data["output"]["action"] == "created"
        assert (Path(fake_vault) / "test" / "hello.md").exists()

    def test_write_note_no_force_blocks_overwrite(self, temp_cache, tmp_path):
        """Sans --force, ne doit pas écraser une note existante."""
        fake_vault = str(tmp_path / "vault")
        Path(fake_vault).mkdir()
        existing = Path(fake_vault) / "existing.md"
        existing.write_text("# Existing", encoding="utf-8")

        env = os.environ.copy()
        env["OBSIDIAN_VAULT_PATH"] = fake_vault
        env["OBSIDIAN_GOAT_CACHE"] = temp_cache

        result = subprocess.run(
            [PYTHON, "-u", str(GOAT_PATH), "write-note", "existing.md",
             "--content", "# New", "--vault", "claude-vault"],
            capture_output=True, text=True, env=env
        )
        data = json.loads(result.stdout.strip())
        assert data["status"] == "error"
        assert "force" in data["output"]["message"].lower()
        # Le fichier original est intact
        assert existing.read_text(encoding="utf-8") == "# Existing"


class TestAppendLog:
    """Tests de append-log sur vault temporaire."""

    def test_append_log_creates_file(self, temp_cache, tmp_path):
        fake_vault = str(tmp_path / "vault")
        Path(fake_vault).mkdir()
        env = os.environ.copy()
        env["OBSIDIAN_VAULT_PATH"] = fake_vault
        env["OBSIDIAN_GOAT_CACHE"] = temp_cache

        result = subprocess.run(
            [PYTHON, "-u", str(GOAT_PATH), "append-log",
             "--entry", "Test de session", "--date", "2026-05-18"],
            capture_output=True, text=True, env=env
        )
        data = json.loads(result.stdout.strip())
        assert data["status"] == "success"
        log_file = Path(fake_vault) / "10_INBOX" / "Daily_Logs" / "2026-05-18.md"
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "Test de session" in content

    def test_append_log_invalid_date(self, temp_cache):
        data = run_goat("append-log", "--entry", "x", "--date", "not-a-date")
        assert data["status"] == "error"
        assert "date" in data["output"]["message"].lower() or "format" in data["output"]["message"].lower()


class TestErrorHandling:
    """Vérification que les erreurs retournent JSON valide (pas de crash)."""

    def test_no_command_returns_error(self, temp_cache):
        env = os.environ.copy()
        env["OBSIDIAN_GOAT_CACHE"] = temp_cache
        result = subprocess.run(
            [PYTHON, "-u", str(GOAT_PATH)],
            capture_output=True, text=True, env=env
        )
        assert result.stdout.strip()
        data = json.loads(result.stdout.strip())
        assert data["status"] == "error"

    def test_json_output_always_valid(self, temp_cache):
        """Toute sortie doit être du JSON valide, même en cas d'erreur."""
        env = os.environ.copy()
        env["OBSIDIAN_GOAT_CACHE"] = temp_cache
        result = subprocess.run(
            [PYTHON, "-u", str(GOAT_PATH), "unknown-command"],
            capture_output=True, text=True, env=env
        )
        # Doit produire du JSON, pas un traceback
        try:
            json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            pytest.fail(f"Output non-JSON: {result.stdout!r}")


class TestReplaceIdR29:
    """Garde-fou R29 : remplacement d'ID borné au token complet (piège ED040)."""

    def _make_vault(self, tmp_path):
        (tmp_path / "fiches").mkdir()
        (tmp_path / "99_Migration_Backups").mkdir()
        (tmp_path / "fiches" / "MA017.md").write_text(
            "editeur: [[ED040_shueisha]]\nVoir ED040_shueisha.\n", encoding="utf-8")
        (tmp_path / "fiches" / "trap.md").write_text(
            "editeur: [[ED040_shufu_to_seikatsu_sha]]\n", encoding="utf-8")
        (tmp_path / "99_Migration_Backups" / "old.md").write_text(
            "ED040_shueisha\n", encoding="utf-8")
        return tmp_path

    def test_dry_run_token_complet(self, tmp_path, temp_cache):
        v = self._make_vault(tmp_path)
        data = run_goat("replace-id", "ED040_shueisha", "ED039_shueisha",
                        "--root", str(v), cache_path=temp_cache)
        o = data["output"]
        assert data["status"] == "dry_run"
        assert o["applied"] is False
        assert o["replacements_total"] == 2
        assert o["files_count"] == 1          # trap.md non concernée
        assert o["files_scanned"] == 2        # backup exclu

    def test_prefixe_nu_protege_les_tokens(self, tmp_path, temp_cache):
        v = self._make_vault(tmp_path)
        data = run_goat("replace-id", "ED040", "ED039",
                        "--root", str(v), cache_path=temp_cache)
        o = data["output"]
        assert o["replacements_total"] == 0   # aucun remplacement : préfixe nu
        assert o["naked_prefix_input"] is True
        assert "ED040_shueisha" in o["protected_prefix_tokens"]
        assert "ED040_shufu_to_seikatsu_sha" in o["protected_prefix_tokens"]
        assert "warning_naked_prefix" in o

    def test_apply_corrige_sans_corrompre(self, tmp_path, temp_cache):
        v = self._make_vault(tmp_path)
        data = run_goat("replace-id", "ED040_shueisha", "ED039_shueisha",
                        "--root", str(v), "--apply", cache_path=temp_cache)
        assert data["status"] == "success"
        assert data["output"]["applied"] is True
        assert "ED039_shueisha" in (v / "fiches" / "MA017.md").read_text(encoding="utf-8")
        # La fiche piège ne doit JAMAIS être modifiée
        assert (v / "fiches" / "trap.md").read_text(encoding="utf-8") == \
            "editeur: [[ED040_shufu_to_seikatsu_sha]]\n"

    def test_old_egal_new_refuse(self, tmp_path, temp_cache):
        v = self._make_vault(tmp_path)
        data = run_goat("replace-id", "ST013_MAPPA", "ST013_MAPPA",
                        "--root", str(v), cache_path=temp_cache)
        assert data["status"] == "error"


class TestNextIdR34:
    """next-id : prochain ID libre pour un préfixe + collision (R34)."""

    def _vault(self, tmp_path):
        (tmp_path / "f").mkdir()
        (tmp_path / "f" / "ST013_MAPPA.md").write_text("x\n", encoding="utf-8")
        (tmp_path / "f" / "ST024_ufotable.md").write_text("x\n", encoding="utf-8")
        (tmp_path / "f" / "queue.md").write_text("voir ST027 et ST040 reserves\n", encoding="utf-8")
        return tmp_path

    def test_next_id_apres_max(self, tmp_path, temp_cache):
        v = self._vault(tmp_path)
        data = run_goat("next-id", "ST", "--root", str(v), cache_path=temp_cache)
        o = data["output"]
        assert data["status"] == "success"
        assert o["max_used"] == 40            # ST040 réservé dans queue.md
        assert o["next_id"] == "ST041"

    def test_check_id_occupe(self, tmp_path, temp_cache):
        v = self._vault(tmp_path)
        data = run_goat("next-id", "ST", "--root", str(v), "--check", "ST013", cache_path=temp_cache)
        assert data["output"]["check"]["free"] is False

    def test_check_id_libre(self, tmp_path, temp_cache):
        v = self._vault(tmp_path)
        data = run_goat("next-id", "ST", "--root", str(v), "--check", "ST500", cache_path=temp_cache)
        assert data["output"]["check"]["free"] is True

    def test_prefix_vide_001(self, tmp_path, temp_cache):
        (tmp_path / "empty").mkdir()
        data = run_goat("next-id", "MG", "--root", str(tmp_path / "empty"), cache_path=temp_cache)
        assert data["output"]["next_id"] == "MG001"

    def test_prefix_invalide_refuse(self, tmp_path, temp_cache):
        data = run_goat("next-id", "ST1", "--root", str(tmp_path), cache_path=temp_cache)
        assert data["status"] == "error"
