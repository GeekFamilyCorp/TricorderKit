# STATE.md — TricorderKit v0.8

> État courant du projet. Mettre à jour à chaque session.

---

## Version courante

- **Version** : 0.8
- **Date** : 16/05/2026
- **Phase active** : Phase 4 — Deep Research *(débloquée)*

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
| `activities/skill_eval.activities.ts` | `9fd035c` | runCliContracts (pytest), runEvalLabScenarios, writeEvalResults |
| `activities/index.ts` | `92b7f86` | Barrel exports + Activities union type pour proxyActivities |
| `scripts/start_worker.ts` | `6152ac8` | Temporal worker — enregistre tous workflows et activities |
| `scripts/hook_stats.py` | `9749338` | CLI /tk:hook-stats — tableau Markdown agrégé |
| **MainBrain v1.5** | `c1017e4` | Étapes 0 (Pre-Intent), 2.5 (Pre-Execution), 7bis (Post-Execution) câblées |

**Seul blocant restant (KI-004)** : lancer le worker Temporal sur la machine hôte.

```bash
# Prérequis (une seule fois)
cd plugins/workflow-engine && npm install @temporalio/worker ts-node typescript

# Lancement
OBSIDIAN_VAULT_PATH=/chemin/vers/vault \
npx ts-node scripts/start_worker.ts
```

---

## Statut des plugins

| Plugin | Statut | Priorité |
|---|---|---|
| cli-forge | ✅ Scaffold + github-goat + source-watch-goat (dry_run_validated) | S |
| workflow-engine | ✅ Scaffold + source_watch + usage_observer v0.2.0 + skill_eval v0.2.0 + activities + worker | S |
| deep-research-core | ✅ Pipeline complet validé : collect+dedup+score+export+index_qdrant — tests live prêts | S |
| hook-layer | ✅ v0.2.0 COMPLET — core/hooks/ (7 fichiers, 25 tests) + activities (2 fichiers) + worker + hook_stats | S |
| memory-boot | 🔲 À migrer v0.8 | S |
| token-hygiene | 🔲 À migrer v0.8 | S |
| agents-standard | 🔲 À créer | A |
| skill-registry | 🔲 À créer | A |
| repo-pack | 🔲 À migrer v0.8 | A |
| usage-observer | ✅ v0.2.0 — activities implémentées, worker prêt (KI-004 : lancer le worker) | A |
| eval-lab | ✅ Phase 5 — eval_runner Typer complet + baseline_store + regression_checker + tests | A |
| obsidian-agent-layer | ✅ Phase 5 — vault_router + note_builder + obsidian_client | B |
| security-audit-cli | ✅ Phase 5 — security_runner Typer complet (audit, check-anon, scan-secrets) | B |

---

## Infrastructure

| Service | Statut |
|---|---|
| Neo4j | ✅ Actif via Docker Compose |
| Qdrant | ✅ Actif via Docker Compose |
| Langfuse | ✅ Actif via Docker Compose |
| Temporal | 🟡 Worker prêt (start_worker.ts déployé) — à lancer manuellement (KI-004) |
| graph-server MCP | ✅ ping / store / relate / retrieve opérationnels |
| QualityGuard | ✅ Semgrep 1.162.0 + Trivy 0.70.0 + Gitleaks 8.30.1 |
| error_memory SQLite | ✅ SHA-256 + block-check actif |
| Hook logs | ✅ .cache/hooks/pre_execution.log + post_execution.log (JSON-lines) |

---

## Blockers actifs

| ID | Description | Niveau |
|---|---|---|
| KI-003 | GitHub MCP deprecated → migration vers `@github/mcp-server@latest` manuelle requise | Moyen |
| KI-004 | Temporal worker à lancer manuellement — activities déployées, boucle non active | Faible |

---

## Bugs résolus récents

| ID | Description | Commit | Date |
|---|---|---|---|
| ERR-T-001 | UUID Qdrant invalide (chars non-hex) → SHA-1 hex pur | — | 2026-05-13 |
| ERR-T-002 | `${CLAUDE_PLUGIN_ROOT}` → chemin absolu + `datetime.utcnow()` → `datetime.now(timezone.utc)` | `40d3166` | 2026-05-15 |

---

## Prochaine action recommandée

```text
Phases 0→5 toutes COMPLÈTES.

Actions manuelles restantes :
  ⏸ KI-004 : lancer Temporal worker
      cd plugins/workflow-engine && npm install @temporalio/worker ts-node typescript
      OBSIDIAN_VAULT_PATH=/chemin/vault npx ts-node scripts/start_worker.ts
  ⏸ Tests live : pytest plugins/deep-research-core/tests/ --live
  ⬜ Backlog : Japan Alliance Phase 1, obsidian-goat CLI, ROADMAP_v0.8.md
```

---

*Dernière mise à jour : 16/05/2026 — Phase 5 COMPLÈTE — Toutes les phases 0→5 finalisées*
