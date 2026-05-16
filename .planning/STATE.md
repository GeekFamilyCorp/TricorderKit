# STATE.md — TricorderKit v0.8

> État courant du projet. Mettre à jour à chaque session.

---

## Version courante

- **Version** : 0.8
- **Date** : 16/05/2026
- **Phase active** : Phase 4 — Deep Research *(complète, tests live en attente)*

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
| 5 | Quality Loop | 🔲 Pending | Débloqué après 2.5 + 4 |

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

## Deep Research — Pipeline COMPLET (2026-05-16)

| Script | Description |
|---|---|
| `collect_sources.py` | Collecte multi-source parallèle (MangaDex, Jikan, AniList, GitHub) + cache SQLite |
| `deduplicate_findings.py` | 2 passes : exact (hash MD5) + fuzzy (Jaccard bigrammes), merge `all_sources[]` |
| `score_reliability.py` | Score composite 0–1.0, filtrage par seuil, 4 niveaux fiabilité |
| `export_report.py` | Rapports markdown + obsidian, frontmatter YAML auto, `--emit-json` |
| `index_qdrant.py` | HashEmbedder numpy + sentence-transformers fallback, UUID5, upsert batch, indexes payload |
| `test_live_sources.py` | 7 classes pytest `@pytest.mark.live` — prêts, EN ATTENTE activation |

```bash
# Pipeline complet (dry-run, sans ML ni Qdrant) :
python collect_sources.py --query "One Piece" --domain manga --dry-run \
  | python deduplicate_findings.py \
  | python score_reliability.py \
  | python export_report.py --format obsidian --output rapport.md

# Avec Qdrant actif :
python index_qdrant.py --input scored.json --collection manga_knowledge --embedder hash

# Tests live :
pytest tests/ --live -v
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
| eval-lab | 🔲 À créer (Phase 5) | A |
| obsidian-agent-layer | 🔲 À créer (Phase 5) | B |
| security-audit-cli | 🔲 À créer (Phase 5) | B |

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
Phase 5 — Quality Loop (débloquée) :
  ⬜ plugins/obsidian-agent-layer/
  ⬜ plugins/security-audit-cli/
  ⬜ plugins/eval-lab/
  ⬜ scripts/health_check.py
  ⬜ Dashboard HTML santé système

Actions manuelles en parallèle :
  ⏸ Tests live : pytest tests/ --live (nécessite accès réseau)
  ⏸ KI-004 : lancer Temporal worker (cd plugins/workflow-engine && npm install ...)
```

---

*Dernière mise à jour : 16/05/2026 — Phase 4 COMPLÈTE — Phase 5 Quality Loop débloquée*
