# STATE.md — TricorderKit v0.9

> État courant du projet. Mettre à jour à chaque session.

---

## Version courante

- **Version** : 0.9 M4
- **Date** : 2026-05-22
- **Phase active** : M5 — Tests security-audit-cli + couverture obsidian-agent-layer

---

## Statut des phases

| Phase | Nom | Statut | Vérifié |
|---|---|---|---|
| 0 | Bootstrap | ✅ Verified | 2026-05-13 |
| 1 | Fondations (fichiers fondateurs) | ✅ Verified | 2026-05-10 |
| 2 | CLI-Forge | ✅ Verified | 2026-05-13 |
| 2.5 | QualityGuard | ✅ Verified | 2026-05-15 |
| 3 | Workflows persistants (Temporal) | ✅ Verified | 2026-05-15 |
| 3.5 | Hook Layer | ✅ Complet | 2026-05-16 |
| 4 | Deep Research | ✅ Complet — **B3 tests live PASS 24/24** | 2026-05-22 |
| 5 | Quality Loop | ✅ Complet | 2026-05-16 |
| 6 | Séparation linked_project | ✅ Migration Japan-Alliance effectuée | 2026-05-17 |
| 6.5 | Restructuration Japan-Alliance → vault pur | ✅ MangaTracker = agent CLI | 2026-05-17 |
| M1 | Orchestration + budget_guard T1/T2/T3 | ✅ Complet | 2026-05-18 |
| M2 | Japan-Alliance Phase 1 + Supabase | ✅ Complet | 2026-05-18 |
| M3 | Pipeline rtk→docmancer live + observabilité Langfuse | ✅ Complet | 2026-05-22 |
| M4 | Token hygiene + boot ≤ 500 tokens + 435 tests | ✅ Complet | 2026-05-22 |

---

## Hook Layer — v0.2.0 COMPLET (2026-05-16)

**Tous les composants déployés sur GitHub :**

| Fichier | Commit | Description |
|---|---|---|
| `core/hooks/__init__.py` | `4e1a18a` | Exports propres |
| `core/hooks/hook_types.py` | `d1647da` | TypedDict partagés |
| `core/hooks/pre_intent_hook.py` | `5fffd74` | 9 domaines, scoring multi-match, hook_id UUID, timestamp ISO-8601 |
| `core/hooks/pre_execution_hook.py` | `9b8782d` | risk_hint calculé, estimated_tokens (1.3 token/char) |
| `core/hooks/post_execution_hook.py` | `275b8a6` | quality_score 4 critères, schema validation optionnelle |
| `core/hooks/tests/test_hooks.py` | `300ee04` | 25 tests pytest |
| `usage_observer.workflow.ts` | `5f9c57b` | Signal TERMINATE, max_runs, return structuré |
| `skill_eval.workflow.ts` | `0f4d883` | eval-lab Phase 5, EvalSummary, budget par phase |
| `activities/usage_observer.activities.ts` | `eee49eb` | readHookLogs (checkpoint), aggregateStats, writeUsageStats |
| `activities/skill_eval.activities.ts` | `9fd035c` | runCliContracts, runEvalLabScenarios, writeEvalResults |
| `activities/index.ts` | `be0b762` | Barrel exports (sans types fantômes) |
| `scripts/start_worker.ts` | `6152ac8` | Temporal worker — enregistre tous workflows et activities |
| `scripts/hook_stats.py` | `9749338` | CLI /tk:hook-stats — tableau Markdown agrégé |
| `tsconfig.json` | `41a36e9` | CommonJS — résout ESM/ts-node conflict |
| `workflows/index.ts` | `8b0616d` | Barrel obligatoire pour workflowsPath |
| **docker-compose.yml** | `8b0616d` | postgres12 + temporal-db + tags fixés |
| **MainBrain v1.5** | `c1017e4` | Étapes 0 (Pre-Intent), 2.5 (Pre-Execution), 7bis (Post-Execution) câblées |

**KI-004 RÉSOLU (2026-05-16)** : Worker Temporal confirmé RUNNING en local.

```
state: RUNNING | taskQueue: tricorderkit-hooks | activities: 6
```

---

## Statut des plugins

| Plugin | Statut | Priorité |
|---|---|---|
| cli-forge | ✅ Scaffold + github-goat + source-watch-goat (dry_run_validated) | S |
| workflow-engine | ✅ Scaffold + source_watch + usage_observer v0.2.0 + skill_eval v0.2.0 + activities + worker RUNNING | S |
| deep-research-core | ✅ Pipeline complet validé : collect+dedup+score+export+index_qdrant — tests live PASS | S |
| hook-layer | ✅ v0.2.0 COMPLET — core/hooks/ (7 fichiers, 25 tests) + activities (2 fichiers) + worker + hook_stats | S |
| memory-boot | ✅ Migré v0.8 — 21 tests | S |
| token-optimizer | ✅ Migré v0.8 — 31 tests | S |
| tk-orchestrator | ✅ budget_guard T1/T2/T3 — 25 tests | S |
| agents-standard | 🔲 À créer | A |
| skill-registry | 🔲 À créer | A |
| repo-pack | 🔲 À migrer v0.8 | A |
| usage-observer | ✅ v0.2.0 — activities implémentées, worker RUNNING | A |
| eval-lab | ✅ Phase 5 — eval_runner Typer complet + baseline_store + regression_checker + tests | A |
| obsidian-agent-layer | ✅ Phase 5 — vault_router + note_builder + obsidian_client | B |
| security-audit-cli | ✅ Phase 5 + tests v0.9 — 16 tests pytest (secret_scanner, anonymization_checker, pattern_checker, security_runner) | B |
| connector-hub | ✅ v0.1.0 — list/status/dispatch, 19 sources | B |

---

## Infrastructure

| Service | Statut |
|---|---|
| Neo4j | ✅ Actif via Docker Compose |
| Qdrant | ✅ Actif via Docker Compose |
| Langfuse | ✅ Actif sur :3001 — traces live vérifiées M4 |
| Temporal | ✅ RUNNING — worker actif sur tricorderkit-hooks |
| graph-server MCP | ✅ ping / store / relate / retrieve opérationnels |
| QualityGuard | ✅ Semgrep 1.162.0 + Trivy 0.70.0 + Gitleaks 8.30.1 |
| error_memory SQLite | ✅ SHA-256 + block-check actif |
| Hook logs | ✅ .cache/hooks/pre_execution.log + post_execution.log (JSON-lines) |

---

## Tests

| Suite | Résultat | Date |
|---|---|---|
| Suite complète (racine) | **451 PASS**, 0 FAIL | 2026-05-22 |
| test_hooks.py | 25/25 ✅ | 2026-05-16 |
| test_cli_local.py | 36/36 ✅ | 2026-05-17 |
| test_linked_project.py | 42/42 ✅ | 2026-05-17 |
| test_observability.py | 20/20 ✅ | 2026-05-22 |
| test_security_audit.py | 16/16 ✅ | 2026-05-22 |
| test_live_sources.py (--live) | 24/24 ✅ | 2026-05-22 |

---

## Blockers actifs

*Aucun blocker actif.*

---

## Bugs résolus récents

| ID | Description | Commit | Date |
|---|---|---|---|
| ERR-T-001 | UUID Qdrant invalide (chars non-hex) → SHA-1 hex pur | — | 2026-05-13 |
| ERR-T-002 | `${CLAUDE_PLUGIN_ROOT}` → chemin absolu + `datetime.utcnow()` → `datetime.now(timezone.utc)` | `40d3166` | 2026-05-15 |
| KI-004 | Temporal worker : tsconfig CommonJS + DB postgres12 + workflows/index.ts barrel + docker rm containers orphelins | `8b0616d` | 2026-05-16 |
| KI-003 | GitHub MCP déprécié → migration `ghcr.io/github/github-mcp-server` (Docker officiel) — `get_me` ✅ | — | 2026-05-17 |
| FIX-CONF | Version "0.8" hardcodée dans test_cli_local.py → bumped to 0.9, 359 PASS | — | 2026-05-22 |
| db_connection_string | Pattern `{10,}` trop restrictif sur username (ex: `admin`) → à corriger (passer à `{3,}`) | ac6bd3d note | 2026-05-22 |

---

## Architecture linked_projects (Phase 6 + 6.5 — 2026-05-17)

```text
TricorderKit    = moteur générique anonymisé
MangaTracker    = linked_project assistant IA (GeekFamilyCorp/MangaTracker — privé)
                  → CLIs Python, pipelines, skills, agents, workflows
Japan-Alliance  = vault Obsidian pur (GeekFamilyCorp/Japan-Alliance — privé)
                  → Données uniquement, pas de code exécutable
                  → Accessible en lecture aux LLMs via token GitHub
```

**Règle d'or :** TricorderKit exécute. MangaTracker spécialise. Japan-Alliance stocke.

---

## Pending — Phase 3 (Temporal)

```text
[ ] plugins/workflow-engine/workflows/vault_audit.workflow.ts
[ ] plugins/workflow-engine/activities/scan_files.activity.ts
[ ] plugins/workflow-engine/activities/run_cli.activity.ts
```

## Pending — Backlog v0.9

```text
[ ] Skill /tk:vault-audit
[ ] Skill /tk:deep-research
[ ] Migrer plugin repo-pack → v0.8
[ ] .planning/ROADMAP_v0.9.md — définir prochaines phases
[ ] Fix db_connection_string pattern : {10,} → {3,} sur username
[ ] agents-standard → À créer
[ ] skill-registry → À créer
```

---

*Dernière mise à jour : 2026-05-22 — v0.9 M4 COMPLET — 451 tests (435 + 16 security-audit) — 0 FAIL*
