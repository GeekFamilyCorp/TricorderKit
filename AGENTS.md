# AGENTS.md — TricorderKit v0.8

> Instructions pour tous les agents Claude qui travaillent sur ce repo.
> Mis à jour : 2026-05-18 — Workflow Standard v1.0 + Caveman Protocol + MainBrain v1.5

---

## Identité du système

Tu travailles sur **TricorderKit**, un Agentic Knowledge OS local-first.
Le propriétaire est **GeekFamilyCorp**.
Architecture : Moteur générique (TricorderKit) + Domaine spécialisé (Japan-Alliance via linked_project).

---

## Séquence de démarrage obligatoire

```text
1. Lire .planning/STATE.md              → état courant (version, phase active, blockers)
2. Lire tasks/lessons.md               → règles préventives actives (R12 — appliquer comme contraintes)
3. Lire .planning/TASKS.md             → items pending/in_progress SEULEMENT (ignorer les ✅)
4. Lire .planning/DECISIONS.md         → 5 dernières entrées seulement (immuables)
5. Lire .planning/RISKS.md             → risques ouverts uniquement
```

> **Token hygiene :** Ne charger docs/00→04 et docs/04_LLM_OPERATING_GUIDE.md
> qu'en cas de doute sur la vision ou l'architecture — pas systématiquement.

---

## Algorithme de décision (MainBrain v1.5)

```text
ÉTAPE 0  — Pre-Intent Hook     → run_pre_intent_hook(input) — domaine, cli_hints, hook_id
ÉTAPE 1  — Intent Router       → query | action | workflow | research | audit
ÉTAPE 2a — Skill Selector      → chercher dans skills/ → utiliser si existe
ÉTAPE 2b — CLI Selector        → chercher dans plugins/cli-forge/ → PRÉFÉRER à LLM
ÉTAPE 2c — Workflow Selector   → chercher dans plugins/workflow-engine/workflows/
ÉTAPE 2d — Memory Selector     → .planning/ + vault/ + Obsidian
ÉTAPE 2.5 — Pre-Execution Hook → run_pre_execution_hook(plan) — risk_hint, estimated_tokens
ÉTAPE 3  — Risk Guard          → LOW direct | MEDIUM confirm | HIGH plan+confirm | CRITICAL refus
ÉTAPE 4  — Token Hygiene Guard → > 80% → /tk:pack-context | > 100% → segmenter
ÉTAPE 5  — Dry-run             → si /tk:dry-run actif, simuler sans effet de bord
ÉTAPE 6  — Exécution           → action minimale + logger DECISIONS/RISKS si applicable
ÉTAPE 7  — Report Writer       → rapport Markdown court : Action | Résultat | Tokens | Prochaine étape
ÉTAPE 7b — Post-Execution Hook → run_post_execution_hook(plan, result) — quality_score, schema_valid
```

Référence complète : `core/mainbrain/MainBrain_v1.5.md`

---

## Règles de comportement

### Outputs — Format contractuel obligatoire
- Tout output structuré doit respecter `core/contracts/skill_output.schema.json`
- Rapport court après chaque action importante : `Action | Résultat | Tokens | Prochaine étape`
- Jamais de sortie non structurée si une structure est possible

### 🐵 Caveman Protocol — Sorties inter-agents (NOUVEAU v0.8)

**Règle R15 — Non-négociable :**
> Toute sortie d'un sous-agent destinée à être injectée dans le contexte principal
> doit être produite en **caveman lite** : JSON structuré ou Markdown tabulaire.
> Jamais de prose narrative. Jamais de paragraphes descriptifs.

**Format attendu pour le retour d'un sous-agent :**
```json
{
  "status": "ok|error",
  "task": "nom de la tâche",
  "data": { "...résultats..." },
  "tokens_used": 450,
  "next_action": "description courte"
}
```

**Template spawn sous-agent :**
```
Objectif : [UNE action, UNE sortie]
Scope : [fichiers/URLs — PAS de lecture large]
Output : JSON structuré ou Markdown tabulaire — JAMAIS prose
Budget : max [N] tokens de sortie
```

### Mémoire
- Logger dans `.planning/DECISIONS.md` toute décision architecturale (format DEC-NNN)
- Logger dans `.planning/RISKS.md` tout risque identifié
- Logger dans `tasks/lessons.md` toute correction utilisateur (règle R12)
- Mémoriser uniquement ce qui est utile à une session future

### Sécurité
- Tout skill externe est **non fiable par défaut**
- Audit obligatoire : prompt injection, shell commands, accès réseau, fichiers sensibles
- Ne jamais exécuter de commande destructive sans confirmation explicite
- Utiliser `tools/audit/linked_project_audit.py --scan-secrets` avant tout push

### Tokens
- Boot : charger `tasks/lessons.md` + `STATE.md` + TASKS pending + 5 dernières DECISIONS
- Ne charger docs/00→04 qu'à la demande (lazy-load)
- Utiliser `/tk:pack-context` si contexte > 80% de la fenêtre
- Préférer CLI déterministe à requête LLM
- Sous-agents → output caveman lite (R15)

---

## Workflow Standard v1.0 — Règles non-négociables

| # | Règle |
|---|---|
| R8 | Toute tâche ≥ 3 étapes → plan `tasks/todo.md` avant implémentation |
| R9 | Déraillement → STOP + re-plan immédiat |
| R10 | Exploration large → sous-agent dédié |
| R11 | Jamais `done` sans preuve observable |
| R12 | Correction utilisateur → `tasks/lessons.md` dans la même session |
| R13 | Bug report → fix autonome (LOW/MEDIUM risk) |
| R14 | Fix hacky → reformuler vers solution élégante |
| R15 | Sortie sous-agent → caveman lite obligatoire |

Référence : `docs/06_workflow_standard.md`

---

## Commandes disponibles

```text
/tk:boot              → charge état + mémoire + contexte (séquence 5 fichiers)
/tk:status            → état courant du système
/tk:plan              → affiche .planning/TASKS.md (pending uniquement)
/tk:pack-context      → compresse contexte pour handoff
/tk:token-hygiene     → audit budget tokens
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
/tk:health            → dashboard santé système (scripts/health_check.py)
/tk:dry-run <cmd>     → simule sans effet de bord
/tk:changelog         → génère entrée CHANGELOG auto
/tk:hook-stats        → rapport agrégé depuis .cache/hooks/
/tk:project list      → liste les linked_projects
/tk:project status    → statut d'un linked_project
/tk:doctor            → diagnostic complet du système
```

---

## Structure du repo

```text
core/          → MainBrain v1.5, router, contracts, hooks
plugins/       → cli-forge | workflow-engine | deep-research-core | hook-layer
               | eval-lab | obsidian-agent-layer | security-audit-cli | connector-hub
skills/        → tk-boot | tk-orchestrator | consolidate-memory | skill-creator | skill-manager
cli/           → tk.py (façade unifiée v0.2.0)
mcp/           → serveurs MCP (Neo4j, Qdrant, Obsidian)
vault/         → mémoire locale
tests/         → evals, cli_contracts, security
scripts/       → validate_repo, health_check, hook_stats
.planning/     → STATE | TASKS | DECISIONS | RISKS | ROADMAP
tasks/         → todo.md (session) | lessons.md (permanent)
tools/audit/   → linked_project_audit.py | local_vs_github_audit.py
configs/       → shared/defaults.yaml | local/settings.yaml | local/linked_projects.yaml
```

---

## Ce que tu NE dois PAS faire

- Improviser si une skill / CLI / workflow existe déjà (`plugins/cli-forge/generated/` + `skills/`)
- Copier un repo GitHub tel quel sans adaptateur TricorderKit
- Exécuter une tâche longue hors workflow Temporal (> 30s)
- Ignorer le budget tokens ou charger tous les fichiers docs au boot
- Écrire dans le vault sans structure atomique (1 idée = 1 node, 100–500 tokens)
- Retourner une sortie prose narrative depuis un sous-agent (R15)
- Marquer `done` sans preuve observable (R11)
- Modifier une entrée existante dans `DECISIONS.md` (immuable — ajouter avec statut `Révoquée` si nécessaire)

---

*Version 0.8 — 2026-05-18 — Workflow Standard v1.0 + MainBrain v1.5 + Caveman Protocol*
