"""
test_live_sources.py — Tests live sources API publiques
TricorderKit deep-research-core v0.1.0

Tests en acces reel vers les APIs publiques.
Necessite --live : pytest tests/ --live

Couverture :
  - API REST MangaDex
  - Jikan (MyAnimeList)
  - AniList GraphQL
  - Pipeline complet collect -> deduplicate -> score

Note : les configurations de sources specifiques au domaine (trusted_sources.yml,
japanese_sources.yml) sont geries dans le depot de domaine correspondant.
Adaptez les constantes MANGADEX_BASE, JIKAN_BASE, ANILIST_URL selon votre domaine.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
import requests

from collect_sources import (
    _fetch_mangadex, _fetch_jikan, _fetch_anilist,
    build_output as collect_build_output,
)
from deduplicate_findings import Deduplicator
from score_reliability import (
    score_and_filter, build_output as score_build_output,
)

# -- Constantes ---------------------------------------------------------------
MANGADEX_BASE  = "https://api.mangadex.org"
JIKAN_BASE     = "https://api.jikan.moe/v4"
ANILIST_URL    = "https://graphql.anilist.co"
TIMEOUT        = 15
QUERY_MANGA    = "One Piece"
QUERY_ANIME    = "Fullmetal Alchemist"
QUERY_PIPELINE = "Berserk"
MIN_ITEMS      = 1

# Delai entre appels Jikan (rate limit : 3/sec)
JIKAN_SLEEP = 1.2

# Poids de source par defaut (sans fichier de configuration de domaine)
DEFAULT_SOURCE_WEIGHTS = {
    "mangadex": 0.92,
    "jikan": 0.88,
    "anilist": 0.93,
}


# -- Fixtures partagees (module-scope) ----------------------------------------
# Un seul appel reseau par classe, evite les 429 Jikan.

@pytest.fixture(scope="module")
def mangadex_items():
    """Items MangaDex pour QUERY_MANGA (module-scope = 1 seul appel)."""
    return _fetch_mangadex(MANGADEX_BASE, QUERY_MANGA, TIMEOUT)


@pytest.fixture(scope="module")
def jikan_items():
    """Items Jikan pour QUERY_MANGA (module-scope = 1 seul appel)."""
    time.sleep(JIKAN_SLEEP)
    return _fetch_jikan(JIKAN_BASE, QUERY_MANGA, TIMEOUT)


@pytest.fixture(scope="module")
def anilist_items():
    """Items AniList pour QUERY_ANIME (module-scope = 1 seul appel)."""
    return _fetch_anilist(ANILIST_URL, QUERY_ANIME, TIMEOUT)


@pytest.fixture(scope="module")
def pipeline_items():
    """
    Collecte directe via fetchers MangaDex + Jikan pour tests pipeline.
    Utilise les fetchers directement, sans SourceLoader ni fichier de configuration
    de sources specifique au domaine (trusted_sources.yml).
    Pour le pipeline complet avec SourceLoader, voir le depot de domaine.
    """
    items = []
    items.extend(_fetch_mangadex(MANGADEX_BASE, QUERY_PIPELINE, TIMEOUT))
    time.sleep(JIKAN_SLEEP)
    items.extend(_fetch_jikan(JIKAN_BASE, QUERY_PIPELINE, TIMEOUT))
    return items


# -- MangaDex -----------------------------------------------------------------

@pytest.mark.live
class TestMangaDexLive:

    def test_search_returns_results(self, mangadex_items):
        assert len(mangadex_items) >= MIN_ITEMS, \
            "MangaDex: 0 resultat pour '{}'".format(QUERY_MANGA)

    def test_item_structure(self, mangadex_items):
        assert mangadex_items, "MangaDex: aucun item"
        for item in mangadex_items:
            assert item.get("source") == "mangadex"
            assert item.get("source_url", "").startswith("https://mangadex.org/title/")
            assert "title" in item
            assert "id" in item

    def test_first_result_is_target(self, mangadex_items):
        assert mangadex_items, "MangaDex: aucun item"
        titles = [str(i.get("title", "")).lower() for i in mangadex_items[:5]]
        assert any("piece" in t or "one" in t for t in titles), \
            "Aucun titre attendu dans: {}".format(titles)

    def test_status_field_present(self, mangadex_items):
        assert mangadex_items, "MangaDex: aucun item"
        valid = {"ongoing", "completed", "hiatus", "cancelled", None}
        for item in mangadex_items:
            assert item.get("status") in valid, \
                "Status inattendu: {}".format(item.get("status"))

    def test_tags_are_list(self, mangadex_items):
        assert mangadex_items, "MangaDex: aucun item"
        for item in mangadex_items:
            assert isinstance(item.get("tags", []), list)

    def test_different_queries_return_different_results(self, mangadex_items):
        time.sleep(0.5)
        items_alt = _fetch_mangadex(MANGADEX_BASE, "Dragon Ball", TIMEOUT)
        ids_op = {i.get("id") for i in mangadex_items}
        ids_alt = {i.get("id") for i in items_alt}
        assert ids_op != ids_alt, "Les deux requetes retournent les memes IDs"


# -- Jikan (MyAnimeList) ------------------------------------------------------

@pytest.mark.live
class TestJikanLive:

    def test_search_returns_results(self, jikan_items):
        assert len(jikan_items) >= MIN_ITEMS, \
            "Jikan: 0 resultat pour '{}'".format(QUERY_MANGA)

    def test_item_structure(self, jikan_items):
        assert jikan_items, "Jikan: aucun item"
        for item in jikan_items[:5]:
            assert item.get("source") == "jikan"
            assert item.get("source_url", "").startswith("https://myanimelist.net/")
            assert "title" in item
            assert "id" in item

    def test_first_result_title(self, jikan_items):
        assert jikan_items, "Jikan: aucun item"
        first = jikan_items[0].get("title", "")
        assert "One Piece" in first or "piece" in first.lower(), \
            "Premier titre inattendu: {}".format(first)

    def test_authors_field(self, jikan_items):
        assert jikan_items, "Jikan: aucun item"
        for item in jikan_items[:5]:
            assert isinstance(item.get("authors", []), list)

    def test_genres_field(self, jikan_items):
        assert jikan_items, "Jikan: aucun item"
        for item in jikan_items[:5]:
            assert isinstance(item.get("genres", []), list)

    def test_score_is_numeric_or_none(self, jikan_items):
        for item in jikan_items[:5]:
            score = item.get("score")
            assert score is None or isinstance(score, (int, float)), \
                "Score non-numerique: {}".format(score)


# -- AniList ------------------------------------------------------------------

@pytest.mark.live
class TestAniListLive:

    def test_search_returns_results(self, anilist_items):
        assert len(anilist_items) >= MIN_ITEMS, \
            "AniList: 0 resultat pour '{}'".format(QUERY_ANIME)

    def test_item_structure(self, anilist_items):
        assert anilist_items, "AniList: aucun item"
        for item in anilist_items[:5]:
            assert item.get("source") == "anilist"
            assert item.get("source_url", "").startswith("https://anilist.co/anime/")
            assert "title" in item
            assert "id" in item

    def test_studios_field(self, anilist_items):
        assert anilist_items, "AniList: aucun item"
        for item in anilist_items[:3]:
            assert isinstance(item.get("studios", []), list)

    def test_score_in_range(self, anilist_items):
        for item in anilist_items[:5]:
            score = item.get("score")
            if score is not None:
                assert 0 <= score <= 100, "Score hors range: {}".format(score)


# -- Pipeline complet ---------------------------------------------------------

@pytest.mark.live
class TestFullPipelineLive:

    def test_collect_returns_items(self, pipeline_items):
        assert len(pipeline_items) >= MIN_ITEMS, \
            "Pipeline: 0 item collecte pour '{}'".format(QUERY_PIPELINE)

    def test_collect_output_contract(self, pipeline_items):
        out = collect_build_output(QUERY_PIPELINE, "manga", pipeline_items, dry_run=False)
        for field in ["status", "skill_name", "skill_version", "timestamp", "output"]:
            assert field in out, "Champ manquant: {}".format(field)
        assert out["status"] == "success"
        assert out["output"]["data"]["total_items"] == len(pipeline_items)

    def test_deduplication_reduces_or_equal(self, pipeline_items):
        dedup = Deduplicator(fuzzy_threshold=0.80)
        deduped = dedup.run(pipeline_items)
        assert len(deduped) <= len(pipeline_items)

    def test_dedup_cross_source_merge(self, pipeline_items):
        sources_in = {i.get("source") for i in pipeline_items}
        if "mangadex" not in sources_in or "jikan" not in sources_in:
            pytest.skip("Les deux sources n'ont pas retourne de resultats")
        dedup = Deduplicator(fuzzy_threshold=0.80)
        deduped = dedup.run(pipeline_items)
        multi_source = [i for i in deduped if len(i.get("all_sources", [])) > 1]
        assert multi_source, "Aucun merge cross-source ({} items)".format(len(deduped))

    def test_scoring_produces_valid_scores(self, pipeline_items):
        if not pipeline_items:
            pytest.skip("Aucun item collecte")
        scored = score_and_filter(pipeline_items, DEFAULT_SOURCE_WEIGHTS, min_score=0.0,
                                   deduplicate_results=False)
        assert scored, "score_and_filter: aucun item"
        for item in scored:
            score = item.get("_reliability_score", -1)
            assert 0.0 <= score <= 1.0
            assert "_reliability_level" in item

    def test_pipeline_filter_by_threshold(self, pipeline_items):
        if not pipeline_items:
            pytest.skip("Aucun item collecte")
        threshold = 0.80
        scored = score_and_filter(pipeline_items, DEFAULT_SOURCE_WEIGHTS, min_score=threshold,
                                   deduplicate_results=True)
        for item in scored:
            assert item["_reliability_score"] >= threshold

    def test_pipeline_score_output_contract(self, pipeline_items):
        if not pipeline_items:
            pytest.skip("Aucun item collecte")
        scored = score_and_filter(pipeline_items, DEFAULT_SOURCE_WEIGHTS, min_score=0.0,
                                   deduplicate_results=True)
        out = score_build_output(scored, 0.0, len(pipeline_items))
        assert out["status"] == "success"
        assert out["output"]["data"]["total_input"] == len(pipeline_items)
        assert out["output"]["data"]["total_scored"] == len(scored)

    def test_pipeline_sorted_desc(self, pipeline_items):
        if not pipeline_items:
            pytest.skip("Aucun item collecte")
        scored = score_and_filter(pipeline_items, DEFAULT_SOURCE_WEIGHTS, min_score=0.0,
                                   deduplicate_results=True)
        if len(scored) < 2:
            pytest.skip("Pas assez d'items")
        scores = [i["_reliability_score"] for i in scored]
        assert scores == sorted(scores, reverse=True)
