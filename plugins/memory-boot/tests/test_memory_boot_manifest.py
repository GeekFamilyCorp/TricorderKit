"""
Tests de conformité v0.8 du plugin memory-boot.
Vérifie la structure du manifest.yml selon le standard TricorderKit v0.8.
"""
import pytest
import yaml
import os
from pathlib import Path

PLUGIN_DIR = Path(__file__).parent.parent
MANIFEST_PATH = PLUGIN_DIR / "manifest.yml"
REPO_ROOT = PLUGIN_DIR.parent.parent
SCHEMA_PATH = REPO_ROOT / "core" / "contracts" / "skill_output.schema.json"


@pytest.fixture(scope="module")
def manifest():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestManifestStructure:
    def test_manifest_exists(self):
        assert MANIFEST_PATH.exists(), "manifest.yml doit exister"

    def test_required_fields(self, manifest):
        required = ["name", "version", "description", "type", "tricorderkit_version", "updated"]
        for field in required:
            assert field in manifest, f"Champ requis manquant: {field}"

    def test_name(self, manifest):
        assert manifest["name"] == "memory-boot"

    def test_version_format(self, manifest):
        import re
        assert re.match(r"^\d+\.\d+\.\d+$", manifest["version"]), "Version doit être semver X.Y.Z"

    def test_type_is_plugin(self, manifest):
        assert manifest["type"] == "plugin"

    def test_tricorderkit_version(self, manifest):
        assert "0.8" in manifest["tricorderkit_version"]

    def test_updated_date_format(self, manifest):
        import re
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", manifest["updated"]), "Date doit être YYYY-MM-DD"


class TestSkillsDeclaration:
    def test_skills_present(self, manifest):
        assert "skills" in manifest, "Bloc skills obligatoire"
        assert len(manifest["skills"]) >= 1, "Au moins 1 skill requis"

    def test_skill_fields(self, manifest):
        for skill in manifest["skills"]:
            assert "name" in skill, "Skill doit avoir un nom"
            assert "path" in skill, "Skill doit avoir un path"
            assert "triggers" in skill, "Skill doit avoir des triggers"
            assert "output_schema" in skill, "Skill doit référencer output_schema"

    def test_skill_names(self, manifest):
        names = [s["name"] for s in manifest["skills"]]
        assert "memory-boot" in names, "Skill memory-boot doit être déclaré"
        assert "rapport" in names, "Skill rapport doit être déclaré"

    def test_skill_paths_exist(self, manifest):
        for skill in manifest["skills"]:
            skill_path = PLUGIN_DIR / skill["path"]
            assert skill_path.exists(), f"Fichier skill introuvable: {skill['path']}"

    def test_skill_output_schema_reference(self, manifest):
        for skill in manifest["skills"]:
            assert "skill_output.schema.json" in skill["output_schema"]

    def test_skill_triggers_non_empty(self, manifest):
        for skill in manifest["skills"]:
            assert len(skill["triggers"]) >= 1, f"Skill {skill['name']} doit avoir au moins 1 trigger"


class TestDependencies:
    def test_dependencies_present(self, manifest):
        assert "dependencies" in manifest, "Bloc dependencies obligatoire pour memory-boot"

    def test_mcp_dependency(self, manifest):
        deps = manifest.get("dependencies", {})
        assert "mcp" in deps, "Dépendances MCP requises"
        mcp_names = [m["name"] for m in deps["mcp"]]
        assert "obsidian-claude-vault" in mcp_names, "obsidian-claude-vault requis"

    def test_mcp_required_flag(self, manifest):
        for mcp in manifest["dependencies"]["mcp"]:
            assert "required" in mcp, "Flag required obligatoire par MCP"
            assert "reason" in mcp, "Raison obligatoire par MCP"


class TestConfig:
    def test_config_present(self, manifest):
        assert "config" in manifest, "Bloc config obligatoire"

    def test_config_paths(self, manifest):
        config = manifest["config"]
        required_keys = ["hot_cache_path", "patterns_path", "errors_path", "daily_log_path"]
        for key in required_keys:
            assert key in config, f"Config key manquante: {key}"

    def test_hot_cache_stale_days(self, manifest):
        config = manifest["config"]
        assert "hot_cache_stale_days" in config
        assert isinstance(config["hot_cache_stale_days"], int)
        assert config["hot_cache_stale_days"] > 0


class TestV08Changes:
    def test_v08_changes_present(self, manifest):
        assert "v0_8_changes" in manifest, "Changelog v0.8 obligatoire"
        assert len(manifest["v0_8_changes"]) >= 1, "Au moins 1 changement documenté"


class TestGlobalContract:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), f"Schema JSON introuvable: {SCHEMA_PATH}"
