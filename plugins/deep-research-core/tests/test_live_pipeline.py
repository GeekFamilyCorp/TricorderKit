"""
test_live_pipeline.py — TricorderKit deep-research-core / MangaTracker
Tests live (vrais appels réseau) couvrant collect_sources + pipeline complet.

Lancement :
    pytest plugins/deep-research-core/tests/test_live_pipeline.py --live -v
    pytest plugins/deep-research-core/tests/test_live_pipeline.py --live -v -k mangadex
    pytest plugins/deep-research-core/tests/test_live_pipeline.py --live -v -k jikan
    pytest plugins/deep-research-core/tests/test_live_pipeline.py --live -v -k anilist

Requis : accès internet (pas de mock). GitHub token optionnel (GITHUB_PERSONAL_ACCESS_TOKEN).
"""
from __future__ import annotations

import sys
import json
import subprocess
import tempfile
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
    """Exécute collect_sources.py et retourne le JSON parsé."""
    import os
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [sys.executable, str(COLLECT_SCRIPT)] + args,
        capture_output=True,
        encoding="utf-8",   # décode stdout/stderr en UTF-8, pas cp1252
        errors="replace",   # caractères invalides remplacés, jamais d'exception
        cwd=str(ROOT),
        env=env,
    )
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        return {"_raw": (result.stdout or "")[:500], "_err": (result.stderr or "")[:500], "_returncode": result.returncode}


# ============================================================================
# Tests unitaires (sans réseau) — validations de config
# ============================================================================

def test_collect_script_exists():
    """Le script collect_sources.py est présent."""
    assert COLLECT_SCRIPT.exists(), f"Script manquant : {COLLECT_SCRIPT}"


def test_trusted_sources_yaml_valid():
    """trusted_sources.yml est parsable et contient les domaines requis."""
    import yaml
    sources_file = PLUGIN_DIR / "sources" / "trusted_sources.yml"
    assert sources_file.exists(), "trusted_sources.yml manquant"
    with open(sources_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "manga" in data, "Domaine 'manga' absent de trusted_sources.yml"
    assert "anime" in data, "Domaine 'anime' absent de trusted_sources.yml"
    assert "github" in data, "Domaine 'github' absent de trusted_sources.yml"
    assert "scoring_weights" in data, "scoring_weights absent"


def test_dry_run_manga():
    """collect_sources --dry-run manga retourne le contrat de sortie correct."""
    data = _run_collect(["--query", "One Piece", "--domain", "manga", "--dry-run"])
    assert data.get("status") == "success", f"Status inattendu: {data.get('status')}"
    assert "output" in data
    assert "data" in data["output"]
    assert data["output"]["data"]["dry_run"] is True
    assert data["output"]["data"]["total_items"] > 0


def test_dry_run_anime():
    """collect_sources --dry-run anime retourne le contrat de sortie correct."""
    data = _run_collect(["--query", "Naruto", "--domain", "anime", "--dry-run"])
    assert data.get("status") == "success", f"Status inattendu: {data.get('status')}"
    assert data["output"]["data"]["dry_run"] is True


# ============================================================================
# Tests live — appels réseau réels
# ============================================================================

@pytest.mark.live
class TestMangaDexLive:
    """Tests live MangaDex REST API."""

    def test_mangadex_one_piece_returns_results(self):
        """MangaDex retourne des résultats pour 'One Piece'."""
        data = _run_collect(["--query", "One Piece", "--domain", "manga", "--sources", "MangaDex API"])
        assert data.get("status") == "success", f"Erreur: {data}"
        items = data["output"]["data"]["items"]
        assert len(items) > 0, "Aucun résultat MangaDex pour 'One Piece'"

    def test_mangadex_result_has_required_fields(self):
        """Chaque item MangaDex contient les champs contractuels."""
        data = _run_collect(["--query", "Berserk", "--domain", "manga", "--sources", "MangaDex API"])
        items = data.get("output", {}).get("data", {}).get("items", [])
        assert len(items) > 0, "Aucun résultat MangaDex pour 'Berserk'"
        for item in items[:3]:
            assert "id" in item, f"Champ 'id' manquant : {item}"
            assert "title" in item, f"Champ 'title' manquant : {item}"
            assert "source" in item, f"Champ 'source' manquant : {item}"
            assert item["source"] == "mangadex"
            assert "source_url" in item

    def test_mangadex_title_is_non_empty_string(self):
        """Le titre MangaDex est une chaîne non vide (vérification normalisation i18n)."""
        data = _run_collect(["--query", "Dragon Ball", "--domain", "manga", "--sources", "MangaDex API"])
        items = data.get("output", {}).get("data", {}).get("items", [])
        for item in items[:5]:
            assert isinstance(item.get("title"), str), f"Titre non string: {item}"
            assert len(item["title"]) > 0, f"Titre vide: {item}"


@pytest.mark.live
class TestJikanLive:
    """Tests live Jikan API (wrapper MyAnimeList)."""

    def test_jikan_one_piece_returns_results(self):
        """Jikan retourne des résultats pour 'One Piece'."""
        data = _run_collect(["--query", "One Piece", "--domain", "manga", "--sources", "Jikan API"])
        assert data.get("status") == "success", f"Erreur: {data}"
        items = data["output"]["data"]["items"]
        assert len(items) > 0, "Aucun résultat Jikan pour 'One Piece'"

    def test_jikan_result_has_score_and_rank(self):
        """Les items Jikan incluent score et rank (données MAL)."""
        data = _run_collect(["--query", "Vinland Saga", "--domain", "manga", "--sources", "Jikan API"])
        items = data.get("output", {}).get("data", {}).get("items", [])
        assert len(items) > 0, "Aucun résultat Jikan pour 'Vinland Saga'"
        first = items[0]
        assert "score" in first, f"Champ 'score' manquant: {first}"
        assert "rank" in first, f"Champ 'rank' manquant: {first}"
        assert "authors" in first, f"Champ 'authors' manquant: {first}"
        assert "genres" in first, f"Champ 'genres' manquant: {first}"
        assert first["source"] == "jikan"

    def test_jikan_result_has_source_url(self):
        """L'URL source Jikan pointe vers MyAnimeList."""
        data = _run_collect(["--query", "Fullmetal Alchemist", "--domain", "manga", "--sources", "Jikan API"])
        items = data.get("output", {}).get("data", {}).get("items", [])
        assert len(items) > 0
        for item in items[:3]:
            url = item.get("source_url", "")
            assert "myanimelist.net" in url, f"source_url inattendu: {url}"


def _anilist_available() -> bool:
    """Vérifie que l'API AniList répond (skip si 403 / panne)."""
    try:
        import requests as _req
        # Requête GraphQL minimale sans variable $
        r = _req.post(
            "https://graphql.anilist.co",
            json={"query": "{ Page(perPage: 1) { media(type: ANIME) { id } } }"},
            headers={"Content-Type": "application/json", "User-Agent": "TricorderKit/0.7"},
            timeout=8,
        )
        return r.status_code == 200
    except Exception:
        return False


_skip_anilist = pytest.mark.skipif(
    not _anilist_available(),
    reason="AniList API indisponible (403 / panne — vérifier https://discord.gg/anilist)",
)


@pytest.mark.live
class TestAniListLive:
    """Tests live AniList GraphQL API."""

    @_skip_anilist
    def test_anilist_naruto_returns_results(self):
        """AniList retourne des résultats pour 'Naruto'."""
        data = _run_collect(["--query", "Naruto", "--domain", "anime", "--sources", "AniList GraphQL"])
        assert data.get("status") == "success", f"Erreur: {data}"
        items = data["output"]["data"]["items"]
        assert len(items) > 0, "Aucun résultat AniList pour 'Naruto'"

    @_skip_anilist
    def test_anilist_result_has_required_fields(self):
        """Chaque item AniList contient les champs contractuels."""
        data = _run_collect(["--query", "Attack on Titan", "--domain", "anime", "--sources", "AniList GraphQL"])
        items = data.get("output", {}).get("data", {}).get("items", [])
        assert len(items) > 0, "Aucun résultat AniList pour 'Attack on Titan'"
        for item in items[:3]:
            assert "id" in item
            assert "title" in item
            assert "source" in item
            assert item["source"] == "anilist"
            assert "source_url" in item
            assert "anilist.co" in item["source_url"]

    @_skip_anilist
    def test_anilist_result_has_studio_and_score(self):
        """Les items AniList incluent studios et score."""
        data = _run_collect(["--query", "Fullmetal Alchemist Brotherhood", "--domain", "anime", "--sources", "AniList GraphQL"])
        items = data.get("output", {}).get("data", {}).get("items", [])
        assert len(items) > 0
        first = items[0]
        assert "studios" in first, f"Champ 'studios' manquant: {first}"
        assert "score" in first, f"Champ 'score' manquant: {first}"
        assert "episodes" in first, f"Champ 'episodes' manquant: {first}"


@pytest.mark.live
class TestMultiSourceLive:
    """Tests live pipeline multi-source (MangaDex + Jikan en parallèle)."""

    def test_multi_source_manga_collects_from_both(self):
        """Pipeline manga collecte depuis MangaDex et Jikan simultanément."""
        data = _run_collect(["--query", "Naruto", "--domain", "manga"])
        assert data.get("status") == "success", f"Erreur pipeline: {data}"
        items = data["output"]["data"]["items"]
        assert len(items) > 0, "Aucun résultat multi-source"
        sources_found = {item.get("source") for item in items}
        assert "mangadex" in sources_found, f"MangaDex absent des sources: {sources_found}"
        assert "jikan" in sources_found, f"Jikan absent des sources: {sources_found}"

    def test_output_contract_structure(self):
        """Le contrat de sortie complet est respecté (skill_name, timestamp, output.summary)."""
        data = _run_collect(["--query", "One Piece", "--domain", "manga"])
        assert data.get("skill_name") == "deep-research-core:collect_sources"
        assert "skill_version" in data
        assert "timestamp" in data
        assert "summary" in data.get("output", {})
        assert "next_steps" in data.get("output", {})
        assert "score_reliability.py" in data["output"]["next_steps"]

    def test_total_items_matches_items_list(self):
        """total_items correspond à len(items) — cohérence interne."""
        data = _run_collect(["--query", "Berserk", "--domain", "manga"])
        output_data = data.get("output", {}).get("data", {})
        total = output_data.get("total_items", -1)
        items = output_data.get("items", [])
        assert total == len(items), f"total_items={total} ≠ len(items)={len(items)}"


@pytest.mark.live
class TestCacheLive:
    """Tests live du mécanisme de cache SQLite."""

    def test_second_call_faster_than_first(self):
        """Le cache SQLite accélère le deuxième appel (TTL non expiré)."""
        import time
        query = "Vagabond"

        t0 = time.monotonic()
        data1 = _run_collect(["--query", query, "--domain", "manga", "--sources", "MangaDex API"])
        t1 = time.monotonic() - t0

        t0 = time.monotonic()
        data2 = _run_collect(["--query", query, "--domain", "manga", "--sources", "MangaDex API"])
        t2 = time.monotonic() - t0

        assert data1.get("status") == "success"
        assert data2.get("status") == "success"
        # Le 2e appel doit être au moins 2× plus rapide (cache hit)
        assert t2 < t1 * 0.7, f"Cache inefficace: t1={t1:.2f}s, t2={t2:.2f}s"
