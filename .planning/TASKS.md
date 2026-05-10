# TASKS.md — TricorderKit v0.7

> Backlog vivant. Mettre à jour après chaque session.

---

## En cours

- [ ] Valider manifest cli-forge (validate_cli_manifest.py --all)
- [ ] Tester source-watch-goat live (trending-manga --output table)

---

## Phase 1 — Fondations ✅ Complétée

- [x] README_FIRST.md
- [x] AGENTS.md
- [x] CLAUDE.md
- [x] .planning/STATE.md
- [x] .planning/DECISIONS.md
- [x] .planning/RISKS.md
- [x] .planning/TASKS.md (ce fichier)
- [x] .planning/ROADMAP_v0.7.md
- [x] CHANGELOG.md
- [x] core/mainbrain/MainBrain_v1.4.md
- [x] core/contracts/skill_output.schema.json

---

## Phase 2 — CLI-first 🔶 En cours

- [x] plugins/cli-forge/cli_manifest.schema.json
- [x] plugins/cli-forge/registry.yml
- [x] plugins/cli-forge/scripts/validate_cli_manifest.py
- [x] plugins/cli-forge/generated/github-goat/ (dry-run validé)
- [x] plugins/cli-forge/generated/source-watch-goat/ (en cours)
- [x] tests/cli_contracts/test_github_goat.py
- [x] tests/cli_contracts/test_source_watch_goat.py
- [ ] plugins/cli-forge/generated/github-goat/manifest.yml
- [ ] plugins/cli-forge/generated/source-watch-goat/manifest.yml
- [ ] plugins/cli-forge/templates/cli_template.md
- [ ] skills/tk-cli-forge/SKILL.md

---

## Phase 3 — Workflows 🔲 Pending

- [x] plugins/workflow-engine/workflows/source_watch.workflow.ts
- [ ] plugins/workflow-engine/README.md
- [ ] plugins/workflow-engine/workflows/vault_audit.workflow.ts
- [ ] plugins/workflow-engine/workflows/skill_eval.workflow.ts
- [ ] plugins/workflow-engine/activities/scan_files.activity.ts
- [ ] plugins/workflow-engine/activities/run_cli.activity.ts
- [ ] plugins/workflow-engine/scripts/start_worker.ts
- [x] docker-compose.yml (Neo4j + Qdrant + Temporal + Langfuse)

---

## Phase 4 — Deep Research 🔲 Pending

- [x] plugins/deep-research-core/manifest.yml
- [x] plugins/deep-research-core/sources/trusted_sources.yml
- [x] plugins/deep-research-core/pipelines/manga_sources_research.yml
- [ ] plugins/deep-research-core/README.md
- [ ] plugins/deep-research-core/sources/japanese_sources.yml
- [ ] plugins/deep-research-core/pipelines/github_research.yml
- [ ] plugins/deep-research-core/pipelines/anime_staff_research.yml
- [ ] plugins/deep-research-core/scripts/collect_sources.py
- [ ] plugins/deep-research-core/scripts/score_reliability.py

---

## Phase 5 — Qualité 🔲 Pending

- [ ] plugins/obsidian-agent-layer/
- [ ] plugins/security-audit-cli/
- [ ] plugins/eval-lab/
- [x] scripts/health_check.py
- [x] scripts/validate_repo.py
- [ ] Dashboard HTML santé système

---

## Backlog — À prioriser

- [ ] MCP serveur Neo4j (mcp/servers/graph-server/)
- [ ] MCP serveur Qdrant (mcp/servers/vector-server/)
- [ ] Connecteurs APIs manga (AniList, MangaDex, Jikan)
- [ ] Skill /tk:vault-audit
- [ ] Skill dependency graph (visualisation)
- [ ] Notion/Airtable bridge (export knowledge graph)

---

*Dernière mise à jour : 10/05/2026*
