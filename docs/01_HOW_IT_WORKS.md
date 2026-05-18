# TricorderKit — Comment ça fonctionne ?

> Version 0.8 — 2026-05-18

---

## Vue d'ensemble

```text
Intention utilisateur
        ↓
[Étape 0] Pre-Intent Hook     → domaine, hook_id, cli_hints
        ↓
MainBrain v1.5 — Intent Router → classify: query|action|workflow|research|audit
        ↓
Sélection outil
  ├── Skill Selector           → skills/ (tk-boot, tk-orchestrator, ...)
  ├── CLI Selector             → plugins/cli-forge/generated/ (github-goat, ...)
  ├── Workflow Selector        → plugins/workflow-engine/workflows/ (Temporal)
  └── Memory Selector          → .planning/ + vault/ + Obsidian
        ↓
[Étape 2.5] Pre-Execution Hook → risk_hint, estimated_tokens, hook_run_id
        ↓
Risk Guard + Token Hygiene Guard
        ↓
Exécution (dry-run si activé)
        ↓
[Étape 7bis] Post-Execution Hook → quality_score, schema_valid, tokens_used
        ↓
Rapport Markdown + Logging DECISIONS/RISKS/lessons
        ↓
usage_observer.workflow.ts (Temporal, agrégation toutes les 6h)
```

---

## Composants clés

### MainBrain v1.5

Algorithme de décision central en 8 étapes (0, 1, 2a/b/c/d, 2.5, 3, 4, 5, 6, 7, 7bis).
Référence : `core/mainbrain/MainBrain_v1.5.md`

### Hook Layer v0.2.0

Trois hooks Python câblés dans le MainBrain :
- `pre_intent_hook` : enrichit l'intention (domaine, cli_hints, hook_id UUID)
- `pre_execution_hook` : enrichit le plan (risk_hint, estimated_tokens, hook_run_id)
- `post_execution_hook` : évalue le résultat (quality_score 0.0–1.0, schema_valid)
- Logs JSON-lines : `.cache/hooks/pre_execution.log` + `.cache/hooks/post_execution.log`

### CLI Goats (cli-forge pattern)

```text
Caractéristiques d'un bon goat :
  ✅ Output JSON déterministe
  ✅ Cache SQLite local (évite les appels répétitifs)
  ✅ Mode --dry-run disponible
  ✅ Tests de contrat dans tests/cli_contracts/
  ✅ Enregistré dans plugins/cli-forge/registry.yml
```

Goat de référence : `tools/github-goat/github_goat.py`

### Temporal Workflows

- Worker actif sur `tricorderkit-hooks`
- Workflows déclarés : `usageObserver`, `skillEval`
- Activités : `readHookLogs`, `aggregateStats`, `writeUsageStats`, `runCliContracts`, `runEvalLabScenarios`
- Tous les workflows > 30s → Temporal (DEC-001)
- Workflows < 30s avec état agentique → LangGraph (DEC-008)

### Storage Layer

| Store | Usage | Tech |
|---|---|---|
| Obsidian vault | Notes atomiques, mémoire inter-session | local Markdown |
| Neo4j | Graphe de connaissance (traversal, liens) | Docker |
| Qdrant | Recherche sémantique (similarité) | Docker |
| SQLite | Cache CLI goats | local |
| JSON-lines | Hook logs | .cache/hooks/ |

### Linked Projects (DEC-010)

```text
TricorderKit  = moteur générique (repo public)
Japan-Alliance = linked_project domaine manga/anime (repo privé)
```

Configuration locale : `configs/local/linked_projects.yaml` (non versionné)
Template : `configs/local/linked_projects.example.yaml`
CLI : `tk project list|status|audit`

---

## Risk Guard — Niveaux

| Niveau | Critère | Comportement |
|---|---|---|
| LOW | Lecture seule, no side effects | Exécution directe |
| MEDIUM | Écriture fichier local, API read | Confirmation courte |
| HIGH | Écriture Obsidian, push GitHub, API write | Plan + confirmation |
| CRITICAL | Suppression, shell destructif, prod | Refus + escalade |

---

## Token Hygiene Guard — Seuils

| Budget | Action |
|---|---|
| < 50% | Continuer normalement |
| 50–79% | Warning silencieux |
| 80–99% | Proposer /tk:pack-context |
| ≥ 100% | Segmenter obligatoirement |

---

*TricorderKit v0.8 — GeekFamilyCorp — 2026-05-18*
