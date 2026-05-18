# MainBrain v1.5 — TricorderKit Agentic Knowledge OS

> Upgrade de MainBrain v1.4 — 16/05/2026  
> Nouveautés : Hook Layer (Pre-Intent, Pre-Execution, Post-Execution) — boucle d'auto-amélioration

---

## Vision

TricorderKit v1.5 est un **Agentic Knowledge Operating System CLI-first**.

```text
Intentions utilisateur
        ↓
MainBrain v1.5
        ↓
Execution Layer (Skills → CLIs → Workflows → Mémoire)
        ↓
Storage Layer (Obsidian → Neo4j → Qdrant → Markdown)
        ↓
Observabilité (Langfuse → Usage Observer)
```

---

## Architecture du MainBrain

```text
MainBrain v1.5
├── [NOUVEAU] Hook Layer        ← observe, enrichit et score chaque exécution
│   ├── pre_intent_hook         ← enrichit la requête brute (domaine, flags CLI)
│   ├── pre_execution_hook      ← enrichit le plan (risk_hint, hook_run_id, tokens)
│   └── post_execution_hook     ← score le résultat (quality_score, schema_valid)
├── Intent Router               ← comprend et classe la demande
├── Skill Selector              ← cherche skill documentée existante
├── CLI Selector                ← cherche CLI déterministe (cli-forge)
├── Workflow Selector           ← cherche workflow Temporal existant
├── Memory Selector             ← cherche mémoire projet / Obsidian
├── Risk Guard                  ← évalue niveau de risque avant exécution
├── Token Hygiene Guard         ← évalue budget tokens avant exécution
├── Dry-run Mode                ← simule sans effet de bord
└── Report Writer               ← produit rapport Markdown court
```

---

## Algorithme de décision (v1.5)

```text
ÉTAPE 0 — Pre-Intent Hook  [NOUVEAU v1.5]
  → from core.hooks import run_pre_intent_hook
  → enriched_input = run_pre_intent_hook(raw_user_input)
  → Détecte le domaine (manga_anime | github | deep_research | obsidian |
    graph_memory | eval | security | workflow | memory_session | other)
  → Génère hook_id (UUID v4) + timestamp ISO-8601 UTC
  → Remonte les cli_hints (ex: may_use_mangatracker_cli)
  → Output transmis à l'Intent Router

ÉTAPE 1 — Intent Router
  → Comprendre la demande (en tenant compte du domaine enriched_input.metadata.domain)
  → Classifier : query | action | workflow | research | audit
  → Identifier : domaine, entités, urgence

ÉTAPE 2 — Sélection de l'outil
  2a. Skill Selector
      → Chercher dans skills/
      → Si skill documentée existe → sélectionner
  2b. CLI Selector
      → Chercher dans plugins/cli-forge/generated/
      → Si CLI déterministe existe → préférer à une requête LLM
      → Utiliser les cli_hints du Pre-Intent Hook pour prioriser
  2c. Workflow Selector
      → Chercher dans plugins/workflow-engine/workflows/
      → Si workflow Temporal existe → déclencher
  2d. Memory Selector
      → Chercher dans .planning/ + vault/ + Obsidian
      → Si mémoire pertinente existe → consulter avant toute action

ÉTAPE 2.5 — Pre-Execution Hook  [NOUVEAU v1.5]
  → from core.hooks import run_pre_execution_hook
  → plan = { skill/goat/workflow sélectionné, action_type, input, ... }
  → enriched_plan = run_pre_execution_hook(plan)
  → Injecte : hook_run_id (UUID), hook_timestamp, risk_hint, estimated_tokens
  → risk_hint calculé : LOW | MEDIUM | HIGH | CRITICAL
  → Log JSON-lines dans .cache/hooks/pre_execution.log
  → enriched_plan transmis à Risk Guard + Token Hygiene Guard

ÉTAPE 3 — Risk Guard
  → Lire enriched_plan.hooks.risk_hint (déjà calculé en Étape 2.5)
  → LOW    → exécuter directement
  → MEDIUM → confirmation courte
  → HIGH   → plan détaillé + confirmation
  → CRITICAL → refus + escalade

ÉTAPE 4 — Token Hygiene Guard
  → Lire enriched_plan.hooks.estimated_tokens
  → Vérifier budget disponible
  → Si > 80% budget → proposer /tk:pack-context
  → Si > 100% budget → refuser et segmenter

ÉTAPE 5 — Dry-run Mode
  → Si /tk:dry-run actif → simuler sans effet de bord
  → Afficher : "Ce qui serait exécuté" + "Impact estimé" + "Tokens estimés"

ÉTAPE 6 — Exécution
  → Exécuter l'action minimale
  → Logger dans .planning/DECISIONS.md si décision architecturale
  → Logger dans .planning/RISKS.md si risque identifié

ÉTAPE 7 — Report Writer
  → Produire rapport Markdown court
  → Format : Action | Résultat | Tokens utilisés | Prochaine étape
  → Mémoriser uniquement les décisions utiles à une session future

ÉTAPE 7bis — Post-Execution Hook  [NOUVEAU v1.5]
  → from core.hooks import run_post_execution_hook
  → final_result = run_post_execution_hook(enriched_plan, skill_result)
  → Calcule quality_score (0.0–1.0) sur 4 critères : status, output, sources, reliability
  → Valide contre core/contracts/skill_output.schema.json (dégradé gracieux si absent)
  → Extrait tokens_used réels ou fallback sur estimated_tokens
  → Log JSON-lines dans .cache/hooks/post_execution.log
  → Ces logs alimentent usage_observer.workflow.ts (Temporal) toutes les 6h
```

---

## Les 5 piliers (hérités v1.4, enrichis)

### 1. Agentic OS

Structure :
- domaines
- tâches
- skills
- automatisations

**Nouveau v1.5 :** Hook Layer entre entrée utilisateur et Intent Router + entre exécution et rapport.

### 2. Atomic Knowledge

Règle :
```text
1 idée = 1 node
```
Taille recommandée : 100 à 500 tokens.

### 3. Typed Nodes

Types :
- decision
- concept
- pattern
- fact
- event
- workflow
- skill
- automation
- entity
- manga
- anime
- publisher
- mangaka
- trend
- cli
- workflow_template
- **hook_run** ← NOUVEAU (trace d'exécution par hook_run_id)
- **usage_stat** ← NOUVEAU (agrégat usage_observer)

### 4. Typed Edges

Relations :
- supports
- contradicts
- depends_on
- related_to
- part_of
- derived_from
- influenced
- adapted_into
- created_by
- generates
- audited_by
- **observed_by** ← NOUVEAU (skill/goat observé par un hook_run)

### 5. Hybrid Retrieval

```text
Graph (Neo4j) + Vector (Qdrant) + Metadata + CLI cache (SQLite) + Hook logs (.cache/hooks/)
```

---

## Pipeline Cognitif v1.5

```text
Raw Data / Intention utilisateur
        ↓
[Étape 0] Pre-Intent Hook  ← domaine, hook_id, cli_hints
        ↓
Intent Router
        ↓
Sélection outil (Skill → CLI → Workflow → Mémoire)
        ↓
[Étape 2.5] Pre-Execution Hook  ← hook_run_id, risk_hint, estimated_tokens
        ↓
Risk Guard + Token Hygiene Guard
        ↓
[Dry-run si activé]
        ↓
Atomic Extraction (si nouveau knowledge)
        ↓
Graph Consolidation (Neo4j)
        ↓
Vector Indexation (Qdrant)
        ↓
Agent Reasoning
        ↓
Outputs (Markdown + DECISIONS.md + RISKS.md)
        ↓
[Étape 7bis] Post-Execution Hook  ← quality_score, tokens_used, schema_valid
        ↓
usage_observer.workflow.ts (Temporal, toutes les 6h)
```

---

## Risk Guard — Niveaux de risque

| Niveau | Critères | Comportement |
|---|---|---|
| LOW | Lecture seule, pas d'effet de bord | Exécuter directement |
| MEDIUM | Écriture fichier local, appel API read | Confirmation courte |
| HIGH | Écriture Obsidian, push GitHub, appel API write | Plan détaillé + confirmation |
| CRITICAL | Suppression, commandes shell destructives, accès prod | Refus + escalade |

---

## Token Hygiene Guard — Seuils

| Budget | Action |
|---|---|
| < 50% | Continuer normalement |
| 50–79% | Warning silencieux, surveiller |
| 80–99% | Proposer /tk:pack-context |
| ≥ 100% | Segmenter obligatoirement |

---

## Hook Layer — Import

```python
from core.hooks import (
    run_pre_intent_hook,     # Étape 0
    run_pre_execution_hook,  # Étape 2.5
    run_post_execution_hook, # Étape 7bis
)

# Flux complet
enriched_input  = run_pre_intent_hook(raw_user_input)
# ... Intent Router, Sélection outil ...
enriched_plan   = run_pre_execution_hook(plan)
# ... Risk Guard, Token Guard, Exécution ...
final_result    = run_post_execution_hook(enriched_plan, skill_result)
```

Tests : `pytest core/hooks/tests/test_hooks.py -v`

---

## Commandes MainBrain

```text
/tk:boot              → charge état + mémoire + contexte
/tk:status            → état courant (plugins, workflows, budget tokens)
/tk:plan              → affiche .planning/TASKS.md
/tk:pack-context      → compresse contexte pour handoff
/tk:token-hygiene     → rapport détaillé budget tokens
/tk:audit-skills      → vérifie registre skills + contrats
/tk:eval-skill <name> → run eval non-régression d'un skill
/tk:cli-forge <svc>   → génère CLI pour un service
/tk:cli-audit <name>  → audit sécurité une CLI
/tk:cli-test <name>   → teste contrats CLI
/tk:cli-register <n>  → enregistre CLI dans registre
/tk:deep-research <q> → recherche autonome structurée
/tk:vault-audit       → audit cohérence vault Obsidian
/tk:workflow-start <w>→ démarre workflow Temporal
/tk:workflow-status   → status workflows actifs
/tk:security-scan     → audit sécurité app/endpoints
/tk:report            → rapport Markdown structuré
/tk:health            → dashboard santé système
/tk:dry-run <cmd>     → simule commande sans effet de bord
/tk:changelog         → génère entrée CHANGELOG automatique
/tk:hook-stats        → rapport agrégé depuis .cache/hooks/  [NOUVEAU]
```

---

## Objectif Final

Construire :
- un OS cognitif local-first
- une mémoire relationnelle (Neo4j + Obsidian)
- un graphe knowledge manga/anime first-class
- des workflows persistants et récupérables (Temporal)
- une architecture IA transmissible, auditable et économe
- **une boucle d'auto-amélioration traçable (Hook Layer + usage_observer)**

---

*MainBrain v1.5 — 16/05/2026*  
*Précédente version : MainBrain v1.4 (Risk Guard, CLI Selector, Token Hygiene Guard)*
