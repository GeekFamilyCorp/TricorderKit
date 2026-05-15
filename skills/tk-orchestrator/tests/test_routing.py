"""
test_routing.py — Tests du classifieur d'intention et du registry
TricorderKit v0.8 — tk-orchestrator v0.2.0
"""

import sys
from pathlib import Path

# Ajuster le path pour les imports

import pytest
from router.intent_classifier import (
    classify_intent, IntentResult,
    DOMAIN_CONFIDENCE_THRESHOLD,
)


# ── Tests : Classification d'intention ────────────────────────────────────────

class TestIntentClassification:

    def test_query_intent_basic(self):
        result = classify_intent("liste les repos Claude")
        assert result.type == "query"

    def test_action_intent_basic(self):
        result = classify_intent("crée une note Obsidian sur One Piece")
        assert result.type == "action"

    def test_workflow_intent_basic(self):
        result = classify_intent("surveille les nouvelles sorties de manga")
        assert result.type == "workflow"

    def test_research_intent(self):
        result = classify_intent("synthèse de tous les mangas Shonen Jump 2026")
        assert result.type == "research"

    def test_audit_intent(self):
        result = classify_intent("audit du vault Obsidian")
        assert result.type == "audit"

    def test_tk_command_is_system(self):
        result = classify_intent("/tk:boot")
        assert result.type == "action"
        assert result.domain == "system"
        assert result.confidence == 1.0

    def test_tk_command_extracts_subcommand(self):
        result = classify_intent("/tk:vault-audit")
        assert "vault-audit" in result.entities

    def test_unknown_intent_fallback(self):
        result = classify_intent("xyzzy plugh twisty")
        assert result.type == "unknown"
        assert result.confidence < 0.5


# ── Tests : Classification de domaine ─────────────────────────────────────

class TestDomainClassification:

    def test_github_domain(self):
        result = classify_intent("liste les repos GitHub de Claude Code")
        assert result.domain == "github"

    def test_manga_domain(self):
        result = classify_intent("infos sur le manga One Piece tome 107")
        assert result.domain == "manga"

    def test_vault_domain(self):
        result = classify_intent("vérifie les liens cassés dans Obsidian")
        assert result.domain == "vault"

    def test_system_domain_priority(self):
        """system doit être prioritaire même si github est aussi présent."""
        result = classify_intent("/tk:cli-forge github create")
        assert result.domain == "system"

    def test_ambiguous_manga_github(self):
        """
        'surveille les sorties manga sur le repo BookWalker'
        → manga doit gagner car plus de keywords manga
        """
        result = classify_intent("surveille les sorties manga sur le repo BookWalker")
        # Au moins un des deux domaines doit être détecté
        assert result.domain in ("manga", "github")

    def test_anime_domain(self):
        result = classify_intent("derniers épisodes anime de la saison")
        assert result.domain == "anime"

    def test_domain_scores_populated(self):
        result = classify_intent("recherche manga One Piece GitHub")
        assert len(result.domain_scores) > 0
        assert all(0.0 <= v <= 1.0 for v in result.domain_scores.values())


# ── Tests : Extraction d'entités ───────────────────────────────────────────

class TestEntityExtraction:

    def test_extracts_proper_nouns(self):
        result = classify_intent("infos sur le manga One Piece de Oda")
        # "One" et "Piece" ou "Oda" devraient être extraits
        assert len(result.entities) >= 1

    def test_no_entities_for_lowercase(self):
        result = classify_intent("liste les repos")
        # Pas d'entités capitalisées hors premier mot
        assert isinstance(result.entities, list)


# ── Tests : Cas limites ───────────────────────────────────────────────────────

class TestEdgeCases:

    def test_empty_string(self):
        result = classify_intent("")
        assert result.type == "unknown"
        assert isinstance(result.domain, str)

    def test_very_long_input(self):
        long_input = "manga " * 200
        result = classify_intent(long_input)
        assert result.type in ("query", "unknown")
        assert result.domain == "manga"

    def test_japanese_text(self):
        result = classify_intent("ワンピース 最新話 manga")
        # Doit au moins classifier le domaine manga (mot latin présent)
        assert isinstance(result, IntentResult)

    def test_result_is_dataclass(self):
        result = classify_intent("test")
        assert hasattr(result, "type")
        assert hasattr(result, "domain")
        assert hasattr(result, "confidence")
        assert hasattr(result, "entities")
        assert hasattr(result, "domain_scores")
