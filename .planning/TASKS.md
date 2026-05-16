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
- [x] core/mainbrain/MainBrain_v1.4.md → v1.5 (Étapes 0, 2.5, 7bis câblées)
- [ ] **[PRIORITÉ A]** plugins/workflow-engine/activities/usage_observer.activities.ts
- [ ] **[PRIORITÉ A]** plugins/workflow-engine/activities/skill_eval.activities.ts
- [ ] **[PRIORITÉ A]** Lancer Temporal worker → activer boucle d'observation complète
- [ ] /tk:hook-stats — commande rapport agrégé depuis .cache/hooks/

---

## 🔶 Phase 4 Deep Research — En cours

- [x] plugins/deep-research-core/scripts/collect_sources.py (pipeline dry-run validé 2026-05-15)
- [x] plugins/deep-research-core/scripts/score_reliability.py (pipeline dry-run validé 2026-05-15)
- [x] plugins/deep-research-core/sources/japanese_sources.yml
- [x] plugins/deep-research-core/pipelines/github_research.yml
- [x] plugins/deep-research-core/pipelines/anime_staff_research.yml
- [ ] plugins/deep-research-core/scripts/deduplicate_findings.py
- [ ] plugins/deep-research-core/scripts/export_report.py
- [ ] Test live MangaDex + Jikan (appels réseau réels)
- [ ] Indexation Qdrant (collection manga_knowledge)

---

## ✅ Phase 0 — Bootstrap (verified 2026-05-13)

- [x] Arborescence v0.8 scaffoldée
- [x] core/contracts/skill_output.schema.json
- [x] core/mainbrain/MainBrain_v1.4.md → v1.5

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
- [ ] plugins/workflow-engine/workflows/vault_audit.workflow.ts ← pending
- [ ] plugins/workflow-engine/activities/scan_files.activity.ts ← pending
- [ ] plugins/workflow-engine/activities/run_cli.activity.ts ← pending
- [ ] plugins/workflow-engine/scripts/start_worker.ts ← pending (Temporal non lancé)

---

## 🔲 Phase 5 — Quality Loop (pending — après Phase 4)

- [ ] plugins/obsidian-agent-layer/
- [ ] plugins/security-audit-cli/
- [ ] plugins/eval-lab/
- [ ] scripts/health_check.py (scaffold existant à compléter)
- [ ] Dashboard HTML santé système

---

## Backlog — À prioriser

- [ ] KI-003 — Migrer GitHub MCP → `@github/mcp-server@latest`
- [ ] Migrer plugin memory-boot → v0.8
- [ ] Migrer plugin token-hygiene → v0.8
- [ ] Connecteurs APIs manga (AniList, MangaDex, Jikan)
- [ ] Skill /tk:boot — wiring commande `.claude/commands/boot.md`
- [ ] Skill /tk:vault-audit
- [ ] Skill /tk:deep-research
- [ ] Japan Alliance Phase 1 — schéma Supabase
- [ ] Vérifier MCPs Airtable + Filesystem + Hostinger

---

*Dernière mise à jour : 16/05/2026*
