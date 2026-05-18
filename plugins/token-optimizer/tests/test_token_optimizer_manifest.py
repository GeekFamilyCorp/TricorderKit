"""
Tests de conformité v0.8 du plugin token-optimizer.
Vérifie la structure du manifest.yml selon le standard TricorderKit v0.8.
"""
import pytest
import yaml
import re
from pathlib import Path

PLUGIN_DIR = Path(__file__).parent.parent
MANIFEST_PATH = PLUGIN_DIR / "manifest.yml"
REPO_ROOT = PLUGIN_DIR.parent.parent
SCHEMA_PATH = REPO_ROOT / "core" / "contracts" / "skill_output.schema.json"

EXPECTED_SKILLS = ["budget-tracker", "cli-compress", "context-compress",
                   "docs-fresh", "model-router", "task-classifier"]
EXPECTED_AGENTS = ["haiku-executor", "sonnet-executor", "opus-executor"]
EXPECTED_TIERS = {"haiku-executor": "T1", "sonnet-executor": "T2", "opus-executor": "T3"}


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
        assert manifest["name"] == "token-optimizer"

    def test_version_semver(self, manifest):
        assert re.match(r"^\d+\.\d+\.\d+$", manifest["version"])

    def test_type_is_plugin(self, manifest):
        assert manifest["type"] == "plugin"

    def test_tricorderkit_version(self, manifest):
        assert "0.8" in manifest["tricorderkit_version"]

    def test_updated_date(self, manifest):
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", manifest["updated"])


class TestSkillsDeclaration:
    def test_skills_present(self, manifest):
        assert "skills" in manifest
        assert len(manifest["skills"]) == 6, "6 skills attendus"

    def test_all_expected_skills(self, manifest):
        names = [s["name"] for s in manifest["skills"]]
        for expected in EXPECTED_SKILLS:
            assert expected in names, f"Skill manquant: {expected}"

    def test_skill_fields(self, manifest):
        for skill in manifest["skills"]:
            assert "name" in skill
            assert "path" in skill
            assert "triggers" in skill
            assert "output_schema" in skill

    def test_skill_paths_exist(self, manifest):
        for skill in manifest["skills"]:
            path = PLUGIN_DIR / skill["path"]
            assert path.exists(), f"SKILL.md introuvable: {skill['path']}"

    def test_skill_output_schema(self, manifest):
        for skill in manifest["skills"]:
            assert "skill_output.schema.json" in skill["output_schema"]

    def test_skill_triggers_non_empty(self, manifest):
        for skill in manifest["skills"]:
            assert len(skill["triggers"]) >= 1


class TestAgentsDeclaration:
    def test_agents_present(self, manifest):
        assert "agents" in manifest, "Bloc agents obligatoire pour token-optimizer"
        assert len(manifest["agents"]) == 3

    def test_all_agents_present(self, manifest):
        names = [a["name"] for a in manifest["agents"]]
        for expected in EXPECTED_AGENTS:
            assert expected in names

    def test_agent_fields(self, manifest):
        for agent in manifest["agents"]:
            assert "name" in agent
            assert "path" in agent
            assert "model" in agent
            assert "tier" in agent
            assert "description" in agent

    def test_agent_tiers(self, manifest):
        for agent in manifest["agents"]:
            assert agent["tier"] in ["T1", "T2", "T3"]
            expected_tier = EXPECTED_TIERS.get(agent["name"])
            if expected_tier:
                assert agent["tier"] == expected_tier, f"{agent['name']} doit être {expected_tier}"

    def test_agent_paths_exist(self, manifest):
        for agent in manifest["agents"]:
            path = PLUGIN_DIR / agent["path"]
            assert path.exists(), f"Agent file introuvable: {agent['path']}"


class TestScheduledTasks:
    def test_scheduled_tasks_present(self, manifest):
        assert "scheduled_tasks" in manifest

    def test_daily_budget_task(self, manifest):
        names = [t["name"] for t in manifest["scheduled_tasks"]]
        assert "daily-budget-morning-check" in names

    def test_task_has_cron(self, manifest):
        for task in manifest["scheduled_tasks"]:
            assert "schedule" in task
            # Vérification basique format cron (5 champs)
            fields = task["schedule"].split()
            assert len(fields) == 5, f"Schedule cron invalide: {task['schedule']}"


class TestScripts:
    def test_scripts_declared(self, manifest):
        assert "scripts" in manifest
        assert len(manifest["scripts"]) >= 2

    def test_script_paths_exist(self, manifest):
        for script in manifest["scripts"]:
            path = PLUGIN_DIR / script["path"]
            assert path.exists(), f"Script introuvable: {script['path']}"

    def test_script_commands_declared(self, manifest):
        for script in manifest["scripts"]:
            assert "commands" in script
            assert len(script["commands"]) >= 1


class TestConfig:
    def test_config_present(self, manifest):
        assert "config" in manifest

    def test_config_keys(self, manifest):
        config = manifest["config"]
        assert "default_tier" in config
        assert "budget_alert_threshold" in config
        assert "caveman_mode" in config
        assert "compress_levels" in config

    def test_compress_levels(self, manifest):
        levels = manifest["config"]["compress_levels"]
        assert "lite" in levels
        assert "full" in levels
        assert "ultra" in levels

    def test_budget_threshold_range(self, manifest):
        threshold = manifest["config"]["budget_alert_threshold"]
        assert 0.0 < threshold < 1.0, "Seuil budget doit être entre 0 et 1"

    def test_default_tier_valid(self, manifest):
        assert manifest["config"]["default_tier"] in ["T1", "T2", "T3"]


class TestV08Changes:
    def test_v08_changes_present(self, manifest):
        assert "v0_8_changes" in manifest
        assert len(manifest["v0_8_changes"]) >= 1


class TestGlobalContract:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), f"Schema JSON introuvable: {SCHEMA_PATH}"
