# TASKS.md — TricorderKit v0.8

> Backlog vivant. Mettre à jour après chaque session.

---

## ✅ Phase 3.5 — Hook Layer (deployed 2026-05-16)

- [x] core/hooks/__init__.py — exports propres
- [x] core/hooks/hook_types.py — TypedDict partagés (0 dépendance externe)
- [x] core/hooks/pre_intent_hook.py — 9 domaines, scoring multi-match, hook_id UUID
- [x] core/hooks/pre_execution_hook.py — risk_hint calculé, estimated_tokens
- [x] core/hooks/post_execution_hook.py — quality_score, schema validation
- [x] core/hooks/tests/test_hooks.py — 25 tests pytest
- [x] plugins/workflow-engine/workflows/usage_observer.workflow.ts v0.2.0
- [x] plugins/workflow-engine/workflows/skill_eval.workflow.ts v0.2.0
- [x] core/mainbrain/MainBrain_v1.5.md → v1.5 (Étapes 0, 2.5, 7bis câblées)
- [x] plugins/workflow-engine/activities/usage_observer.activities.ts — readHookLogs, aggregateStats, writeUsageStats (commit eee49eb)
- [x] plugins/workflow-engine/activities/skill_eval.activities.ts — runCliContracts, runEvalLabScenarios, writeEvalResults (commit 9fd035c)
- [x] plugins/workflow-engine/activities/index.ts — barrel exports + Activities union type (commit 92b7f86)
- [x] plugins/workflow-engine/scripts/start_worker.ts — Temporal worker enregistrant tous les workflows et activities (commit 6152ac8)
- [x] scripts/hook_stats.py — CLI /tk:hook-stats, tableau Markdown agrégé depuis .cache/hooks/ (commit 9749338)
- [ ] **[KI-004]** Lancer Temporal worker sur la machine hôte → activer boucle d'observation complète
  - Prérequis : `npm install @temporalio/worker` dans plugins/workflow-engine/
  - Commande : `OBSIDIAN_VAULT_PATH=/chemin/vault npx ts-node plugins/workflow-engine/scripts/start_worker.ts`

---

## ✅ Phase 4 Deep Research — COMPLÈTE (tests live B3 PASS 2026-05-22)

- [x] plugins/deep-research-core/scripts/collect_sources.py (pipeline dry-run validé 2026-05-15)
- [x] plugins/deep-research-core/scripts/score_reliability.py (pipeline dry-run validé 2026-05-15)
- [x] plugins/deep-research-core/sources/japanese_sources.yml
- [x] plugins/deep-research-core/pipelines/github_research.yml
- [x] plugins/deep-research-core/pipelines/anime_staff_research.yml
- [x] plugins/deep-research-core/scripts/deduplicate_findings.py (Deduplicator 2 passes : exact + fuzzy Jaccard, merge cross-source, all_sources[] — 16/05/2026)
- [x] plugins/deep-research-core/scripts/export_report.py (formats markdown + obsidian, frontmatter YAML auto, --emit-json — 16/05/2026)
- [x] **[B3 DONE 2026-05-22]** Tests live MangaDex + Jikan + AniList + Pipeline — **24/24 PASS** — `pytest tests/test_live_sources.py --live` (Japan-Alliance)
- [x] plugins/deep-research-core/scripts/index_qdrant.py (HashEmbedder + sentence-transformers fallback, UUID5, upsert batch, indexes payload complets — 16/05/2026)
- [x] plugins/deep-research-core/tests/test_live_sources.py (7 classes pytest live : MangaDex, Jikan, AniList, pipeline complet — 16/05/2026)

---

## ✅ Phase 0 — Bootstrap (verified 2026-05-13)

- [x] Arborescence v0.8 scaffoldée
- [x] core/contracts/skill_output.schema.json
- [x] core/mainbrain/MainBrain_v1.5.md → v1.5

---

## ✅ Phase 1 — Fondations (verified 2026-05-10)

- [x] README_FIRST.md
- [x] AGENTS.md
- [x] CLAUDE.md
- [x] .planning/STATE.md
- [x] .planning/DECISIONS.md
- [x] .planning/RISKS.md
- [x] .planning/TASKS.md
- [ ] .planning/ROADMAP_v0.8.md ← à créer

---

## ✅ Phase 2 — CLI-Forge (verified 2026-05-13)

- [x] plugins/cli-forge/README.md
- [x] plugins/cli-forge/manifest.yml
- [x] plugins/cli-forge/cli_manifest.schema.json
- [x] plugins/cli-forge/registry.yml
- [x] plugins/cli-forge/generated/github-goat/ (dry_run_validated)
- [x] plugins/cli-forge/generated/source-watch-goat/ (dry_run_validated)
- [x] plugins/cli-forge/scripts/validate_cli_manifest.py
- [ ] plugins/cli-forge/generated/obsidian-goat/ ← pending
- [ ] plugins/cli-forge/scripts/test_cli_contract.py ← pending
- [ ] tests/cli_contracts/github-goat.test.ts ← pending

---

## ✅ Phase 2.5 — QualityGuard (verified 2026-05-15)

- [x] Semgrep 1.162.0 intégré (scan pipeline validé)
- [x] Trivy 0.70.0 intégré
- [x] Gitleaks 8.30.1 intégré
- [x] data/quality_guard/error_memory.sqlite (SHA-256 + block-check)
- [x] ERR-T-002 résolu — commit 40d3166

---

## ✅ Phase 3 — Workflows (verified 2026-05-15)

- [x] plugins/workflow-engine/README.md
- [x] plugins/workflow-engine/manifest.yml
- [x] plugins/workflow-engine/workflows/source_watch.workflow.ts
- [x] docker-compose.yml (Neo4j + Qdrant + Langfuse actifs)
- [x] graph-server MCP opérationnel (ping / store / relate / retrieve)
- [x] plugins/workflow-engine/scripts/start_worker.ts (commit 6152ac8)
- [ ] plugins/workflow-engine/workflows/vault_audit.workflow.ts ← pending
- [ ] plugins/workflow-engine/activities/scan_files.activity.ts ← pending
- [ ] plugins/workflow-engine/activities/run_cli.activity.ts ← pending

---

## ✅ Phase 5 — Quality Loop (COMPLÈTE — 16/05/2026)

- [x] plugins/obsidian-agent-layer/ — vault_router (routing claude-vault/notes-vault), note_builder, obsidian_client
- [x] plugins/security-audit-cli/ — security_runner Typer : audit, check-anon, scan-secrets, check-patterns, dry-run
- [x] plugins/eval-lab/ — eval_runner Typer : eval, validate-schema, report, dry-run + baseline_store + regression_checker + tests/
- [x] scripts/health_check.py — v0.8, check_services/plugins/planning/docker, generate_html dark-theme (fix utcnow → now(timezone.utc))
- [x] Dashboard HTML santé système — `python health_check.py --output html` → vault/reports/health_{ts}.html

---

## ✅ Rang A — Complétés (2026-05-17)

- [x] configs/shared/defaults.yaml + configs/local/settings.yaml + configs/vps/settings.yaml (PENDING)
- [x] .planning/DECISIONS.md — DEC-010 (linked_project pattern) + DEC-011 (VPS optionnel)
- [x] reports/local_first_audit_2026-05-17.md — premier audit système complet
- [x] KI-003 — migration GitHub MCP → `ghcr.io/github/github-mcp-server` (Docker officiel) ✅ get_me = GeekFamilyCorp
- [x] README.md v0.8 badges + What's New
- [x] CHANGELOG.md — entrée [0.8.0] complète

## ✅ Rang B — Complétés (2026-05-17, commit 3c154d2)

- [x] tests/test_cli_local.py — **36/36 tests PASS** (CLI tk subprocess, JSON contract, encoding)
- [x] tests/test_linked_project.py — **42/42 tests PASS** (linked_project_audit + local_vs_github_audit)
- [x] plugins/connector-hub/ v0.1.0 — hub passif multi-sources (list/status/dispatch, 19 sources, routing CLI)

---

## ✅ Corrections v0.9 (2026-05-22)

- [x] **[FIX-CONF]** Fix conftest conflit eval-lab / tk-orchestrator — root cause : version "0.8" hardcodée dans `tests/test_cli_local.py` alors que STATE.md retourne "0.9 M2". Fix : bump version dans test + `cli/tk.py --version`. **359 PASS, 0 FAIL** depuis la racine.

---

## ✅ M3-LIVE — Pipeline rtk→docmancer test live (2026-05-22)

- [x] **[M3-LIVE]** `pipeline_rtk_docmancer.py --query "Chainsaw Man" --no-dry-run` → note réelle créée
  - Chemin : `japan-alliance_vault/Mangas/Chainsaw Man/Chainsaw-Man.md`
  - Titre ✅ `Chainsaw Man` · Auteur ✅ `Fujimoto, Tatsuki` · Titre JP ✅ `チェンソーマン` · Statut ✅ `completed`
  - Fix collect parser : `output.data.items` (was looking for `findings` key)
  - Fix write_obsidian : filesystem direct via `linked_projects.yaml` (ObsidianClient MCP-only)
  - Fix field normalization : `authors[]→author`, `title_japanese→title_jp`
  - Fix title selection : exact-match first (`_best_finding`), merge fields from all exact matches
  - Publisher/volumes : non retournés par Jikan search — enhancement future

---

## Backlog v0.9 — À prioriser

- [ ] Wiring Temporal → connector_hub.dispatch (source_watch.workflow.ts déclenché par hub)
- [ ] cli-forge — obsidian-goat CLI (accès vault depuis subprocess)
- [ ] Skill /tk:boot — wiring `.claude/commands/boot.md`
- [ ] Skill /tk:vault-audit
- [ ] Skill /tk:deep-research
- [ ] Migrer plugin memory-boot → v0.8
- [ ] Migrer plugin token-hygiene → v0.8
- [ ] Japan-Alliance Phase 1 — schéma Supabase (tables manga, anime, mangaka)
- [ ] .planning/ROADMAP_v0.9.md — définir prochaines phases
- [ ] KI-004 — Temporal worker monitoring continu (hook boucle complète en prod)

---

*Dernière mise à jour : 2026-05-22 — FIX-CONF ✅ + M3-LIVE ✅ — 359 tests, 0 FAIL depuis racine*
