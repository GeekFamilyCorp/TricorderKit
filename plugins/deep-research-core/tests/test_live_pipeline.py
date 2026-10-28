"""
test_live_pipeline.py — TricorderKit deep-research-core
Tests couvrant collect_sources + pipeline complet (unitaires hors reseau, puis live).

Lancement :
    pytest plugins/deep-research-core/tests/test_live_pipeline.py -v
    pytest plugins/deep-research-core/tests/test_live_pipeline.py --live -v
    pytest plugins/deep-research-core/tests/test_live_pipeline.py --live -v -k github
    pytest plugins/deep-research-core/tests/test_live_pipeline.py --live -v -k arxiv

Live : acces internet requis (pas de mock). GitHub token optionnel (GITHUB_PERSONAL_ACCESS_TOKEN).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# -- Paths -------------------------------------------------------------------
PLUGIN_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = PLUGIN_DIR / "scripts"
COLLECT_SCRIPT = SCRIPTS_DIR / "collect_sources.py"
ROOT = PLUGIN_DIR.parent.parent


# ============================================================================
# Helpers
# ============================================================================

def _run_collect(args: list[str]) -> dict:
    """Execute collect_sources.py et retourne le JSON parse."""
    import os
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [sys.executable, str(COLLECT_SCRIPT)] + args,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
        env=env,
    )
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        return {"_raw": (result.stdout or "")[:500], "_err": (result.stderr or "")[:500], "_returncode": result.returncode}


_ARXIV_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>arXiv Query: all:vector databases</title>
  <entry>
    <id>http://arxiv.org/abs/2401.00001v1</id>
    <updated>2024-01-02T00:00:00Z</updated>
    <published>2024-01-01T00:00:00Z</published>
    <title>A Survey of
      Vector Databases</title>
    <summary>  We review approximate nearest neighbour indexes. </summary>
    <author><name>Ada Lovelace</name></author>
    <author><name>Grace Hopper</name></author>
  </entry>
</feed>
"""


# ============================================================================
# Tests unitaires (sans reseau) — validations de config et de parsing
# ============================================================================

def test_collect_script_exists():
    """Le script collect_sources.py est present."""
    assert COLLECT_SCRIPT.exists(), f"Script manquant : {COLLECT_SCRIPT}"


def test_trusted_sources_yaml_valid():
    """trusted_sources.yml est parsable et contient les domaines generiques requis."""
    import yaml
    sources_file = PLUGIN_DIR / "sources" / "trusted_sources.yml"
    assert sources_file.exists(), "trusted_sources.yml manquant"
    with open(sources_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "github" in data, "Domaine 'github' absent de trusted_sources.yml"
    assert "research" in data, "Domaine 'research' absent de trusted_sources.yml"
    names = {s["name"] for s in data["research"]}
    assert {"arXiv API", "Hacker News Algolia", "Wikipedia REST"} <= names
    assert "scoring_weights" in data, "scoring_weights absent"


def test_dry_run_github():
    """collect_sources --dry-run github retourne le contrat de sortie correct."""
    data = _run_collect(["--query", "vector databases", "--domain", "github", "--dry-run"])
    assert data.get("status") == "success", f"Status inattendu: {data}"
    assert "output" in data
    assert "data" in data["output"]
    assert data["output"]["data"]["dry_run"] is True
    assert data["output"]["data"]["total_items"] > 0


def test_dry_run_research():
    """collect_sources --dry-run research retourne le contrat de sortie correct."""
    data = _run_collect(["--query", "local-first software", "--domain", "research", "--dry-run"])
    assert data.get("status") == "success", f"Status inattendu: {data}"
    assert data["output"]["data"]["dry_run"] is True
    assert data["output"]["data"]["total_items"] == 3


def test_default_domain_is_github():
    """Sans --domain, la collecte porte sur le domaine github."""
    data = _run_collect(["--query", "temporal workflows", "--dry-run"])
    assert data["output"]["data"]["domain"] == "github"


def test_unknown_domain_returns_empty_success():
    """Un domaine non declare ne plante pas : 0 item, statut success."""
    data = _run_collect(["--query", "x", "--domain", "not-declared", "--dry-run"])
    assert data.get("status") == "success"
    assert data["output"]["data"]["total_items"] == 0


def test_parse_arxiv_atom():
    """Le parseur Atom arXiv normalise id, titre, auteurs et URL."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    import collect_sources

    items = collect_sources.parse_arxiv_atom(_ARXIV_SAMPLE)
    assert len(items) == 1
    item = items[0]
    assert item["id"] == "2401.00001v1"
    assert item["title"] == "A Survey of Vector Databases"
    assert item["authors"] == ["Ada Lovelace", "Grace Hopper"]
    assert item["source"] == "arxiv"
    assert item["source_url"] == "http://arxiv.org/abs/2401.00001v1"


def test_score_reliability_knows_research_sources():
    """score_reliability expose un alias court pour chaque source active."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    import score_reliability

    weights = score_reliability.load_source_weights(PLUGIN_DIR / "sources" / "trusted_sources.yml")
    for alias in ("github", "arxiv", "hackernews", "wikipedia"):
        assert alias in weights, f"alias {alias} absent: {sorted(weights)}"
    assert weights["arxiv"] == 0.95


# ============================================================================
# Tests live — appels reseau reels
# ============================================================================

@pytest.mark.live
class TestGitHubLive:
    """Tests live GitHub REST API."""

    def test_github_returns_results(self):
        data = _run_collect(["--query", "vector database", "--domain", "github", "--sources", "GitHub API"])
        assert data.get("status") == "success", f"Erreur: {data}"
        items = data["output"]["data"]["items"]
        assert len(items) > 0, "Aucun resultat GitHub"
        for item in items[:3]:
            assert item["source"] == "github"
            assert "github.com" in item["source_url"]


@pytest.mark.live
class TestArxivLive:
    """Tests live arXiv Atom API."""

    def test_arxiv_returns_results(self):
        data = _run_collect(["--query", "vector databases", "--domain", "research", "--sources", "arXiv API"])
        assert data.get("status") == "success", f"Erreur: {data}"
        items = data["output"]["data"]["items"]
        assert len(items) > 0, "Aucun resultat arXiv"
        first = items[0]
        assert first["source"] == "arxiv"
        assert "arxiv.org" in first["source_url"]
        assert isinstance(first["title"], str) and first["title"]


@pytest.mark.live
class TestResearchMultiSourceLive:
    """Tests live pipeline multi-source (domaine research)."""

    def test_output_contract_structure(self):
        data = _run_collect(["--query", "local-first software", "--domain", "research"])
        assert data.get("skill_name") == "deep-research-core:collect_sources"
        assert "skill_version" in data
        assert "timestamp" in data
        assert "summary" in data.get("output", {})
        assert "score_reliability.py" in data["output"]["next_steps"]

    def test_total_items_matches_items_list(self):
        data = _run_collect(["--query", "temporal workflows", "--domain", "research"])
        output_data = data.get("output", {}).get("data", {})
        assert output_data.get("total_items", -1) == len(output_data.get("items", []))


@pytest.mark.live
class TestCacheLive:
    """Tests live du mecanisme de cache SQLite."""

    def test_second_call_faster_than_first(self):
        import time
        query = "sqlite internals"

        t0 = time.monotonic()
        data1 = _run_collect(["--query", query, "--domain", "research", "--sources", "arXiv API"])
        t1 = time.monotonic() - t0

        t0 = time.monotonic()
        data2 = _run_collect(["--query", query, "--domain", "research", "--sources", "arXiv API"])
        t2 = time.monotonic() - t0

        assert data1.get("status") == "success"
        assert data2.get("status") == "success"
        assert t2 < t1 * 0.7, f"Cache inefficace: t1={t1:.2f}s, t2={t2:.2f}s"
