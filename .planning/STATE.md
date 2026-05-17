# STATE.md — TricorderKit v0.8

> État courant du projet. Mettre à jour à chaque session.

---

## Version courante

- **Version** : 0.8
- **Date** : 17/05/2026
- **Phase active** : Phase 6 — Séparation linked_project *(complète)*

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
| 4 | Deep Research | ✅ Complet (tests live EN ATTENTE) | 2026-05-16 |
| 5 | Quality Loop | ✅ Complet | 2026-05-16 |
| 6 | Séparation linked_project | ✅ Migration japan-alliance effectuée | 2026-05-17 |

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
| deep-research-core | ✅ Pipeline complet validé : collect+dedup+score+export+index_qdrant — tests live prêts | S |
| hook-layer | ✅ v0.2.0 COMPLET — core/hooks/ (7 fichiers, 25 tests) + activities (2 fichiers) + worker + hook_stats | S |
| memory-boot | 🔲 À migrer v0.8 | S |
| token-hygiene | 🔲 À migrer v0.8 | S |
| agents-standard | 🔲 À créer | A |
| skill-registry | 🔲 À créer | A |
| repo-pack | 🔲 À migrer v0.8 | A |
| usage-observer | ✅ v0.2.0 — activities implémentées, worker RUNNING | A |
| eval-lab | ✅ Phase 5 — eval_runner Typer complet + baseline_store + regression_checker + tests | A |
| obsidian-agent-layer | ✅ Phase 5 — vault_router + note_builder + obsidian_client | B |
| security-audit-cli | ✅ Phase 5 — security_runner Typer complet (audit, check-anon, scan-secrets) | B |

---

## Infrastructure

| Service | Statut |
|---|---|
| Neo4j | ✅ Actif via Docker Compose |
| Qdrant | ✅ Actif via Docker Compose |
| Langfuse | ✅ Actif sur :3001 (3000 réservé Docker Desktop — résolu commit 0fae3ed) |
| Temporal | ✅ RUNNING — worker actif sur tricorderkit-hooks |
| graph-server MCP | ✅ ping / store / relate / retrieve opérationnels |
| QualityGuard | ✅ Semgrep 1.162.0 + Trivy 0.70.0 + Gitleaks 8.30.1 |
| error_memory SQLite | ✅ SHA-256 + block-check actif |
| Hook logs | ✅ .cache/hooks/pre_execution.log + post_execution.log (JSON-lines) |

---

## Blockers actifs

| ID | Description | Niveau |
|---|---|---|
| KI-003 | GitHub MCP deprecated → migration vers `@github/mcp-server@latest` manuelle requise | Moyen |

---

## Bugs résolus récents

| ID | Description | Commit | Date |
|---|---|---|---|
| ERR-T-001 | UUID Qdrant invalide (chars non-hex) → SHA-1 hex pur | — | 2026-05-13 |
| ERR-T-002 | `${CLAUDE_PLUGIN_ROOT}` → chemin absolu + `datetime.utcnow()` → `datetime.now(timezone.utc)` | `40d3166` | 2026-05-15 |
| KI-004 | Temporal worker : tsconfig CommonJS + DB postgres12 + workflows/index.ts barrel + docker rm containers orphelins | `8b0616d` | 2026-05-16 |

---

## Architecture linked_project (Phase 6 — 2026-05-17)

```text
TricorderKit  = moteur générique anonymisé
Japan-Alliance = linked_project privé spécialisé (GeekFamilyCorp/Japan-Alliance)

Fichiers migrés vers GeekFamilyCorp/Japan-Alliance :
  tools/mangatracker-cli/    → japan-alliance/tools/mangatracker-cli/
  tools/jp-scraper/          → japan-alliance/tools/jp-scraper/
  deep-research-core/sources/japanese_sources.yml → japan-alliance/pipelines/sources/
  deep-research-core/pipelines/anime_staff_research.yml → japan-alliance/pipelines/
  deep-research-core/tests/test_live_sources.py → japan-alliance/tests/deep_research/

Lien local déclaré dans :
  configs/local/linked_projects.yaml (non versionné — chemins réels)
  configs/local/linked_projects.example.yaml (versionné — template)

Règle d'or :
  TricorderKit exécute. Japan-Alliance spécialise. VPS = extension optionnelle.
```

## Prochaine action recommandée

```text
Phase 6 COMPLÈTE — Architecture linked_project opérationnelle.

Actions restantes :
  ✅ Migration japan-alliance effectuée (2026-05-17)
  ⏸ Tests live deep-research : pytest plugins/deep-research-core/tests/ --live
  ⏸ Langfuse : port 3000 en conflit — changer port ou libérer
  ⬜ CLI tk minimal : tk status, tk doctor, tk project list/status
  ⬜ KI-003 : migration GitHub MCP vers @github/mcp-server@latest
  ⬜ Cloner Japan-Alliance localement + créer configs/local/linked_projects.yaml
```

---

*Dernière mise à jour : 17/05/2026 — Phase 6 COMPLÈTE — Migration linked_project japan-alliance effectuée*
