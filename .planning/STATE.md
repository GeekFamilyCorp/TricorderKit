# TricorderKit v0.7 — State

**Date:** 2026-05-11  
**Phase:** 2 (CLI-first active) — repo neutralized  
**Status:** Public generic framework ✅

---

## Current state

TricorderKit is now a **public, domain-agnostic agentic OS framework**.

All Japan-Alliance / MangaTracker-specific content has been migrated to the private `MangaTracker` repository.

---

## Installed components

### CLI tools (examples — replace with your domain CLIs)
- `tools/your-cli/` — generic domain CLI scaffold
- `tools/your-scraper/` — open-source web scraper (RSS/HTTP/trafilatura)

### Claude Code integrations
- `.claude/hooks/` — 4 hooks active (token budget, vault manifest, secret guard, full-vault-read guard)
- `.claude/agents/` — 5 agents (token-budget, vault-audit, vault-optimizer, vault-structure, web-scraper)
- `.claude/commands/` — 8 commands (vault-analyze/audit/delta/optimize/sync, token-check, scraper-audit/scan)
- `.claude/skills/` — vault-token-optimizer + open-source-web-scraper

### Plugins
- `plugins/deep-research-core/` — autonomous research engine (generic stub)
- `plugins/cli-forge/` — CLI scaffolding
- `plugins/memory-boot/` — session memory boot
- `plugins/token-optimizer/` — token optimization
- `plugins/workflow-engine/` — workflow orchestration

### Vault optimizer
- `scripts/vault_optimizer/` — 5 scripts (analyzer, manifest, delta, router, summarizer)

---

## Architecture

```text
TricorderKit (public) — generic framework
    └── any domain CLI (tools/)
    └── web scraper (tools/)
    └── Claude integrations (.claude/)
    └── deep-research-core (plugins/)

MangaTracker (private) — Japan-Alliance instance
    └── tools/mangatracker-cli/ (18 JP sources)
    └── tools/jp-scraper/ (5 JP sources)
    └── plugins/deep-research-core/ (JP pipelines + sources)
    └── .mcp.json (kintone config)
    └── .claude/ (JP-specific agents/commands/skills)
```

---

## Next steps

1. Implement actual CLI parsers for your domain
2. Configure your MCP service in `.env`
3. Test the scraper with your sources
4. Build Phase 3 — RAG / Qdrant integration
