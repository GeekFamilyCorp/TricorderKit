"""
intent_classifier.py — Classifieur d'intention multi-domaine
TricorderKit v0.8 — tk-orchestrator v0.2.0

Stratégie : pattern matching pondéré + scoring multi-domaine.
Aucune dépendance LLM — déterministe et instantané.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ── Types ────────────────────────────────────────────────────────────────────

@dataclass
class IntentResult:
    type: str           # query | action | workflow | research | audit | unknown
    domain: str         # manga | github | vault | system | anime | ln | general
    confidence: float   # 0.0 → 1.0
    entities: List[str] = field(default_factory=list)
    domain_scores: Dict[str, float] = field(default_factory=dict)


# ── Patterns d'intention ──────────────────────────────────────────────────────

INTENT_PATTERNS: Dict[str, List[str]] = {
    "query": [
        "quelles", "quels", "liste", "trouve", "search", "get", "affiche",
        "montre", "donne", "c'est quoi", "qu'est-ce", "info", "infos",
        "quel est", "qui est", "combien", "show", "list", "find", "fetch",
    ],
    "action": [
        "crée", "écris", "créer", "écrire", "update", "push", "save",
        "sauvegarde", "modifie", "ajoute", "supprime", "envoie", "génère",
        "create", "write", "add", "delete", "send", "generate", "build",
    ],
    "workflow": [
        "surveille", "automatise", "boucle", "workflow", "planifie",
        "déclenche", "programme", "répète", "monitor", "schedule",
        "watch", "automate", "loop", "trigger",
    ],
    "research": [
        "synthèse", "analyse", "recherche", "deep", "compare", "synthétise",
        "résume", "étudie", "explore", "investigate", "summarize", "research",
        "study", "report", "rapport",
    ],
    "audit": [
        "audit", "health", "check", "validate", "vérifie", "contrôle",
        "teste", "diagnostique", "inspect", "review", "test", "diagnose",
        "status", "état",
    ],
}

# Poids des patterns selon leur position dans la phrase
# (début = intention plus marquée)
INTENT_WEIGHTS = {
    "query": 1.0,
    "action": 1.2,    # Les actions sont souvent plus explicites
    "workflow": 1.3,
    "research": 1.1,
    "audit": 1.1,
}


# ── Patterns de domaine ─────────────────────────────────────────────────────

DOMAIN_PATTERNS: Dict[str, List[str]] = {
    "manga": [
        "manga", "mangaka", "chapitre", "chapter", "tome", "volume",
        "one piece", "naruto", "dragon ball", "shonen", "shojo", "seinen",
        "seinen", "jump", "weekly shonen", "oricon", "bookwalker", "comic",
        "bd japonaise", "scantrad", "tankōbon", "tankobón",
    ],
    "anime": [
        "anime", "animé", "épisode", "episode", "saison", "season",
        "anilist", "myanimelist", "mal", "crunchyroll", "netflix anime",
        "studio", "réalisateur", "director", "opening", "ending",
        "seiyū", "seiyuu", "doublage", "vostfr",
    ],
    "ln": [
        "light novel", "ln", "light-novel", "roman léger", "novel",
        "narou", "kakuyomu", "bookwalker ln", "isekai", "web novel",
        "webnovel",
    ],
    "github": [
        "github", "repo", "repository", "repos", "commit", "pull request",
        "pr", "issue", "branch", "code", "git", "push", "merge",
        "claude code", "api", "sdk",
    ],
    "vault": [
        "obsidian", "vault", "note", "notes", "lien", "link", "tag",
        "template", "fichier", "file", "frontmatter", "markdown",
        "kb", "knowledge base", "base de connaissance",
    ],
    "system": [
        "tricorderkit", "tk:", "/tk:", "orchestrat", "skill", "plugin",
        "workflow-engine", "cli-forge", "état", "state", "phase",
        "boot", "budget", "token", "planning", "decision",
    ],
}

# Priorité des domaines en cas d'égalité ou ambiguïté
DOMAIN_PRIORITY = ["system", "vault", "github", "anime", "ln", "manga"]

# Seuil de confiance minimal pour sélectionner un domaine
DOMAIN_CONFIDENCE_THRESHOLD = 0.6


# ── Extracteur d'entités (noms propres simples) ────────────────────────────────

def extract_entities(text: str) -> List[str]:
    """Extraction naïve d'entités : mots capitalisés hors début de phrase."""
    words = text.split()
    entities = []
    for i, word in enumerate(words):
        clean = word.strip('.,!?;:"\"()[]')
        if (
            len(clean) > 2
            and clean[0].isupper()
            and i > 0  # pas le premier mot (souvent une commande)
            and clean.lower() not in {
                "le", "la", "les", "de", "du", "des", "un", "une",
                "et", "ou", "pour", "sur", "dans", "avec",
            }
        ):
            entities.append(clean)
    return list(dict.fromkeys(entities))  # dédupliqué, ordre préservé


# ── Scoring ───────────────────────────────────────────────────────────────

def _score_intent(text_lower: str) -> Tuple[str, float]:
    scores: Dict[str, float] = {k: 0.0 for k in INTENT_PATTERNS}
    words = text_lower.split()

    for intent, keywords in INTENT_PATTERNS.items():
        for kw in keywords:
            if kw in text_lower:
                # Bonus si en début de phrase
                position_bonus = 1.5 if any(
                    w.startswith(kw) for w in words[:3]
                ) else 1.0
                scores[intent] += INTENT_WEIGHTS[intent] * position_bonus

    best = max(scores, key=lambda k: scores[k])
    total = sum(scores.values()) or 1.0
    confidence = min(scores[best] / total * 2, 1.0)  # normalisation

    if scores[best] == 0.0:
        return "unknown", 0.3
    return best, round(confidence, 2)


def _score_domains(text_lower: str) -> Dict[str, float]:
    scores: Dict[str, float] = {k: 0.0 for k in DOMAIN_PATTERNS}

    for domain, keywords in DOMAIN_PATTERNS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[domain] += 1.0

    # Normaliser sur le maximum
    max_score = max(scores.values()) if any(scores.values()) else 1.0
    if max_score > 0:
        scores = {k: round(v / max_score, 2) for k, v in scores.items()}

    return scores


def _select_domain(domain_scores: Dict[str, float]) -> Tuple[str, float]:
    """Sélectionne le domaine gagnant selon le score et la priorité."""
    # Filtrer au-dessus du seuil
    candidates = {
        k: v for k, v in domain_scores.items()
        if v >= DOMAIN_CONFIDENCE_THRESHOLD
    }

    if not candidates:
        # Aucun domaine clair → prendre le meilleur avec confiance réduite
        best = max(domain_scores, key=lambda k: domain_scores[k])
        return best, round(domain_scores[best] * 0.5, 2)

    if len(candidates) == 1:
        k = list(candidates.keys())[0]
        return k, candidates[k]

    # Plusieurs candidats → appliquer la règle de priorité
    for domain in DOMAIN_PRIORITY:
        if domain in candidates:
            return domain, candidates[domain]

    # Fallback : le meilleur score
    best = max(candidates, key=lambda k: candidates[k])
    return best, candidates[best]


# ── Interface publique ─────────────────────────────────────────────────────────

def classify_intent(user_input: str) -> IntentResult:
    """
    Classifie l'intention et le domaine d'une requête utilisateur.

    Args:
        user_input: La requête en langage naturel ou commande /tk:*

    Returns:
        IntentResult avec type, domain, confidence, entities, domain_scores
    """
    text_lower = user_input.lower().strip()

    # Cas spécial : commande /tk: explicite
    if text_lower.startswith("/tk:"):
        cmd = text_lower[4:].split()[0] if len(text_lower) > 4 else "unknown"
        return IntentResult(
            type="action",
            domain="system",
            confidence=1.0,
            entities=[cmd],
            domain_scores={"system": 1.0},
        )

    intent_type, intent_conf = _score_intent(text_lower)
    domain_scores = _score_domains(text_lower)
    domain, domain_conf = _select_domain(domain_scores)
    entities = extract_entities(user_input)

    # Confiance globale = moyenne pondérée
    overall_conf = round((intent_conf * 0.6 + domain_conf * 0.4), 2)

    return IntentResult(
        type=intent_type,
        domain=domain,
        confidence=overall_conf,
        entities=entities,
        domain_scores={k: v for k, v in domain_scores.items() if v > 0},
    )
