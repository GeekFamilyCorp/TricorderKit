# BOOT_SUMMARY — TricorderKit
> Fichier généré automatiquement. Ne pas éditer manuellement.
> Mise à jour : fin de chaque session (skill `rapport` ou `/tk:boot --update-summary`).
> Objectif : remplacer le chargement de ~13 500 tokens par ~500 tokens au boot.

---

## Version & statut

| Champ | Valeur |
|---|---|
| Version | **v0.9** (M1+M2+M3 COMPLETS — M4 ✅) |
| Commit HEAD | `a293b2f` (GitHub sync ✅) |
| Dernière session | 2026-05-22 |
| Tests | **377 PASS** (359+20 observabilité M4), 15 skipped (live) |
| Blockers actifs | Aucun |

---

## Infrastructure Docker

| Service | Port | Statut |
|---|---|---|
| Neo4j | 7474/7687 | ✅ |
| Qdrant | 6333 | ✅ |
| Langfuse | **3001** | ✅ |
| Temporal | 7233 | ✅ Worker RUNNING `tricorderkit-hooks` |

---

## Prochaines tâches (v0.9 M3)

1. `✅` B3 — Tests live deep-research **DONE 2026-05-22** — 24/24 PASS (MangaDex + Jikan + AniList + Pipeline)
2. `✅` M4 — Observabilité bout-en-bout Langfuse **DONE 2026-05-22** — 20/20 tests, traces live dans localhost:3001
3. `✅` Fix conftest conflit eval-lab / tk-orchestrator **DONE 2026-05-22** — 0 FAIL (version bump 0.8→0.9 M2 dans test + CLI)
4. `✅` Pipeline rtk→docmancer test live **DONE 2026-05-22** — `Mangas/Chainsaw Man/Chainsaw-Man.md` créé (title+author+title_jp+status ✅)
5. `✅` Push GitHub TricorderKit v0.9 M2 complet **DONE 2026-05-22** — HEAD `e7cc574`

### Complété session v0.9 M2 ✅ (session 1/2)
- **S1** — connector_hub `--temporal` opérationnel (dry_run ✅, workflow_id déterministe)
- **A2** — Supabase schema Japan-Alliance (29 tests ✅) — 7 tables, RLS complet, seed 10 publishers
- **B1** — Skills token-savior + claude-code-router (19 tests ✅)

### Complété session v0.9 M3+M4 ✅ (2026-05-22)
- **M3-LIVE** — Pipeline rtk→docmancer données réelles : `Mangas/Chainsaw Man/Chainsaw-Man.md` créé (title+author+title_jp+status ✅)
  - Fix collect parser, write_obsidian filesystem, title selection, field normalization
- **M4-OBS** — Observabilité bout-en-bout Langfuse hooks
  - `core/hooks/langfuse_observer.py` : REST API directe, no SDK, Python 3.14 compatible
  - 3 hooks branchés : pre_intent→trace-create · pre_execution/post_execution→span-create
  - Batch HTTP groupé par cycle (1 seul appel) + trace_id partagé
  - Langfuse initialisé : projet TricorderKit, clés dans `.env`
  - `tests/test_observability.py` : 20 tests (init + hooks + no-op + mock HTTP + live)

### Complété session v0.9 M2 ✅ (session 2/2)
- **S2** — tk-orchestrator budget_guard phase 2 (25 tests ✅)
  - `token_tracker.py` : T1/T2/T3 tiers + `guard_action()` + `tier_from_complexity()`
  - CLI `budget-guard` : proceed|pause|abort, tier_detail, context_flags
  - CLI `session-budget` : état session + tasks_remaining_estimate
  - `SESSION_BUDGET_DEFAULT = 30 000` tokens, `SESSION_ALERT_THRESHOLD = 0.80`
- **B2** — Pipeline observabilité hook logs → Obsidian (intégration ✅)
  - `tools/observability/hook_log_to_obsidian.py` : JSON-lines → note ERRORS.md
  - Catégories : HIGH/CRITICAL pre_exec + qualité basse + erreurs post_exec
- **M3** — Pipeline rtk→docmancer wiring (intégration ✅)
  - `tools/pipelines/pipeline_rtk_docmancer.py` : collect→dedup→score→build_note→write_obsidian
  - Test dry-run validé : Chainsaw Man → `Mangas/Chainsaw Man/Chainsaw-Man.md`

### Complété session v0.9 M1 ✅
- memory-boot + token-optimizer migrés v0.8 (52 tests)
- skills rtk + docmancer créés
- obsidian-goat CLI v0.1.0 (19 tests, registry v0.2.0)
- .claude/commands/boot.md → /tk:boot natif
- .planning/ROADMAP_v0.9.md créé

---

## Patterns d'erreurs actifs

| Code | Règle |
|---|---|
| ARCH-001 | Hooks Cowork inertes → comportement auto dans SKILL.md orchestrateur |
| ENV-001 | MSIX paths → utiliser LOCALAPPDATA pour fichiers Claude Desktop externes |
| OPS-001 | Scheduled tasks → prompt ≤ 300 tokens |
| ARCH-002 | System prompt Cowork côté serveur → estimation uniquement |

---

## Dernières décisions

| Code | Résumé |
|---|---|
| DEC-011 | VPS extension optionnelle future — local-first maintenu |
| DEC-010 | linked_project : TricorderKit exécute, Japan-Alliance spécialise |
| DEC-009 | Graphify hybride Neo4j + Qdrant |
| DEC-008 | LangGraph < 30s / Temporal > 30s |

---

## Plugins actifs

`cli-forge` ✅ · `workflow-engine` ✅ · `deep-research-core` ✅ · `hook-layer v0.2.0` ✅
`eval-lab` ✅ · `obsidian-agent-layer` ✅ · `security-audit-cli` ✅ · `connector-hub v0.1.0` ✅
`memory-boot` ✅ v0.8 · `token-optimizer` ✅ v0.8

---

## Pour aller plus loin (lazy-load)

| Besoin | Fichier à charger |
|---|---|
| Vision produit | `docs/00_WHAT_IS_TRICORDERKIT.md` |
| Architecture interne | `docs/01_HOW_IT_WORKS.md` |
| Inventaire opérationnel | `docs/02_WHAT_IS_IN_PLACE.md` |
| Backlog détaillé | `docs/03_WHAT_TO_DO_NEXT.md` |
| Guide LLM complet | `docs/04_LLM_OPERATING_GUIDE.md` |
| Workflow Standard | `docs/06_workflow_standard.md` |
| Règles agents | `AGENTS.md` |
| Toutes les décisions | `.planning/DECISIONS.md` |
| Tous les risques | `.planning/RISKS.md` |

---

## Skills disponibles

`tk-boot` ✅ · `tk-orchestrator` ✅ v0.2.0 · `consolidate-memory` ✅
`rtk` ✅ · `docmancer` ✅ · `token-savior` ✅ NEW · `claude-code-router` ✅ NEW
`skill-creator` ✅ · `skill-manager` ✅

## CLIs enregistrées (cli-forge registry v0.2.0)

`github-goat` ✅ dry_run_validated · `obsidian-goat` ✅ NEW dry_run_validated (19 tests)

---

*Auto-généré — TricorderKit v0.9 M4 — 2026-05-22 (B3 ✅, FIX-CONF ✅, PUSH-M2 ✅, M3-LIVE ✅, M4-OBS ✅) — 377 tests, 0 FAIL*
