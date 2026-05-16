#!/usr/bin/env python3
"""
pre_intent_hook — enrichit la requête brute avant l'Intent Router.
Version : 0.2.0
Output : dict JSON-serializable (cf. hook_types.PreIntentOutput)

Améliorations v0.2.0 vs v0.1.0 :
- Détection de domaine étendue à 9 catégories (vs 4)
- Scoring multi-match (chaque mot-clé = +1 point)
- hook_id UUID v4 + timestamp ISO-8601 UTC pour traçabilité Langfuse/Temporal
- Flags cli_hints calculés par domaine
- Validation de l'input (non-str toléré)
- Aucun side-effect (fonctions pures)
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

# ---------------------------------------------------------------------------
# Table domaines → mots-clés (lowercase)
# Ajouter ici de nouveaux domaines sans modifier la logique de scoring.
# ---------------------------------------------------------------------------
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "manga_anime": [
        "one piece", "manga", "anime", "light novel", " ln ", "mangaka",
        "shonen", "seinen", "shoujo", "isekai", "manhua", "manhwa",
        "seiyuu", "seiyū", "voice actor", "studio d'animation",
        "volume", "chapitre", "chapter", "tome", "oricon", "bookwalker",
    ],
    "github": [
        "github", "repo", "pull request", "commit", "branch", "merge",
        "git push", "git pull", "workflow yml", "release", "tag git",
        "fork", "issue github",
    ],
    "deep_research": [
        "research", "synthèse", "rapport", "veille", "source",
        "fiabilité", "scoring", "analyse", "étude", "investigation",
    ],
    "obsidian": [
        "obsidian", "vault", "daily log", "hot_cache", "hot cache",
        "memory-boot", "patch_note", "frontmatter", "note obsidian",
        "patch note",
    ],
    "graph_memory": [
        "neo4j", "graph", "graphify", "qdrant", "vecteur", "embedding",
        "node", "relation", "cypher",
    ],
    "eval": [
        "eval", "evaluation", "eval-lab", "non-régression", "regression",
        "score", "benchmark", "test cli", "pytest", "fixture", "contrat",
    ],
    "security": [
        "semgrep", "trivy", "gitleaks", "security", "sécurité",
        "vulnerability", "audit", "scan", "secret", "cve",
    ],
    "workflow": [
        "temporal", "workflow", "usage_observer", "skill_eval",
        "orchestration", "planification", "activité temporal",
    ],
    "memory_session": [
        "mémoire", "contexte session", "hot cache", "compress context",
        "token budget", "context window",
    ],
}

# CLI / goat probable par domaine principal
CLI_HINTS: Dict[str, str] = {
    "manga_anime":    "may_use_mangatracker_cli",
    "github":         "may_use_github_goat",
    "deep_research":  "may_use_source_watch_goat",
    "obsidian":       "may_use_obsidian_agent_layer",
    "security":       "may_use_security_audit_cli",
    "eval":           "may_use_eval_lab",
}

DEEP_RESEARCH_DOMAINS = {"manga_anime", "deep_research", "graph_memory", "security"}


def run_pre_intent_hook(raw_input: Any) -> Dict[str, Any]:
    """Enrichit la requête utilisateur avec des métadonnées structurées.

    Args:
        raw_input: Texte brut de la requête (str recommandé, autres types tolérés).

    Returns:
        PreIntentOutput : dict JSON-serializable avec hook_id, timestamp, metadata.
        Aucun side-effect — aucun I/O externe.
    """
    if not isinstance(raw_input, str):
        raw_input = str(raw_input)

    text = raw_input.lower()
    hook_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    scores: Dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[domain] = score

    domain = max(scores, key=lambda d: scores[d]) if scores else "other"

    requires_deep_research = domain in DEEP_RESEARCH_DOMAINS
    cli_hints = [CLI_HINTS[domain]] if domain in CLI_HINTS else []

    return {
        "raw_input": raw_input,
        "hook_id": hook_id,
        "timestamp": timestamp,
        "metadata": {
            "domain": domain,
            "domain_scores": scores,
            "requires_deep_research": requires_deep_research,
            "cli_hints": cli_hints,
        },
    }
