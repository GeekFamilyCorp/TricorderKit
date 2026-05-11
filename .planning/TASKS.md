# TricorderKit v0.7 — Tasks

**Updated:** 2026-05-11

---

## Phase 1 — COMPLETED

- [x] Scaffolding v0.7 on GitHub
- [x] Core files (PLAN_MASTER, architecture, plugins)
- [x] CLI tools: validate_repo.py + health_check.py
- [x] Claude Vault memory updated
- [x] source-watch-goat built
- [x] Push v0.7 to GitHub

## Phase 2 — COMPLETED

- [x] Install 3 packs (mangatracker-cli, jp-scraper, vault-optimizer)
- [x] Push infrastructure + CLI tools + Claude integrations to GitHub
- [x] Create private MangaTracker repo
- [x] Migrate all JP-specific content to MangaTracker
- [x] Neutralize TricorderKit — replace all JP content with generic stubs

## Phase 3 — TODO

- [ ] Implement actual domain CLI parsers (replace stubs with real sources)
- [ ] Configure and test MCP service integration
- [ ] Build RAG pipeline — Qdrant integration
- [ ] Neo4j knowledge graph integration
- [ ] Temporal workflow engine integration
- [ ] Phase 3 launch: `tk boot` + full agent workflow

## Backlog

- [ ] Add more pipeline types to deep-research-core
- [ ] Build CLI forge — automated CLI scaffolding
- [ ] Workflow engine — Temporal adapters
- [ ] Write tests for vault_optimizer scripts
