# MainBrain v1.4 — TricorderKit Agentic Knowledge OS

> Upgrade de MainBrain v1.3 — 10/05/2026  
> Nouveautés : Risk Guard, CLI Selector, Token Hygiene Guard, Dry-run mode

---

## Vision

TricorderKit v1.4 est un **Agentic Knowledge Operating System CLI-first**.

```text
Intentions utilisateur
        ↓
MainBrain v1.4
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
MainBrain v1.4
├── Intent Router          ← comprend et classe la demande
├── Skill Selector         ← cherche skill documentée existante
├── CLI Selector           ← cherche CLI déterministe (cli-forge)  [NOUVEAU]
├── Workflow Selector      ← cherche workflow Temporal existant
├── Memory Selector        ← cherche mémoire projet / Obsidian
├── Risk Guard             ← évalue niveau de risque avant exécution  [NOUVEAU]
├── Token Hygiene Guard    ← évalue budget tokens avant exécution  [AMÉLIORÉ]
├── Dry-run Mode           ← simule sans effet de bord  [NOUVEAU]
└── Report Writer          ← produit rapport Markdown court
```

---

## Algorithme de décision (v1.4)

```text
ÉTAPE 1 — Intent Router
  → Comprendre la demande
  → Classifier : query | action | workflow | research | audit
  → Identifier : domaine, entités, urgence

ÉTAPE 2 — Sélection de l'outil
  2a. Skill Selector
      → Chercher dans skills/
      → Si skill documentée existe → sélectionner
  2b. CLI Selector  [NOUVEAU]
      → Chercher dans plugins/cli-forge/generated/
      → Si CLI déterministe existe → préférer à une requête LLM
  2c. Workflow Selector
      → Chercher dans plugins/workflow-engine/workflows/
      → Si workflow Temporal existe → déclencher
  2d. Memory Selector
      → Chercher dans .planning/ + vault/ + Obsidian
      → Si mémoire pertinente existe → consulter avant toute action

ÉTAPE 3 — Risk Guard  [NOUVEAU]
  → Évaluer le niveau de risque : LOW | MEDIUM | HIGH | CRITICAL
  → LOW    → exécuter directement
  → MEDIUM → confirmation courte
  → HIGH   → plan détaillé + confirmation
  → CRITICAL → refus + escalade

ÉTAPE 4 — Token Hygiene Guard  [AMÉLIORÉ]
  → Estimer le coût tokens de l'action
  → Vérifier budget disponible
  → Si > 80% budget → proposer /tk:pack-context
  → Si > 100% budget → refuser et segmenter

ÉTAPE 5 — Dry-run Mode  [NOUVEAU]
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
```

---

## Les 5 piliers (hérités v1.3, enrichis)

### 1. Agentic OS

Structure :
- domaines
- tâches
- skills
- automatisations

**Nouveau v1.4 :** CLI-first layer entre skills et automations.

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
- **cli** ← NOUVEAU
- **workflow_template** ← NOUVEAU

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
- **generates** ← NOUVEAU (cli génère output)
- **audited_by** ← NOUVEAU (skill audité par eval)

### 5. Hybrid Retrieval

```text
Graph (Neo4j) + Vector (Qdrant) + Metadata + CLI cache (SQLite)
```

---

## Pipeline Cognitif v1.4

```text
Raw Data / Intention utilisateur
        ↓
Intent Router
        ↓
Sélection outil (Skill → CLI → Workflow → Mémoire)
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
```

---

## Objectif Final

Construire :
- un OS cognitif local-first
- une mémoire relationnelle (Neo4j + Obsidian)
- un graphe knowledge manga/anime first-class
- des workflows persistants et récupérables (Temporal)
- une architecture IA transmissible, auditable et économe

---

*MainBrain v1.4 — 10/05/2026*  
*Précédente version : MainBrain v1.3 (pipeline cognitif sans CLI Selector ni Risk Guard)*
