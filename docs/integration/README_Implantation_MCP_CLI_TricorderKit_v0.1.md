# README — CLI + MCP Integration in TricorderKit

Version: v0.1  
Date: 2026-05-10  
Audience: Claude / Claude Code  
Project: TricorderKit — generic agentic OS framework  
Objective: reduce token consumption by moving extraction, scraping, normalization and export into local CLIs, reserving MCPs for structured external access, controlled actions, and orchestration.

---

## 1. Executive summary for Claude

Integrate your domain CLI pack under `tools/` as a local tooling layer.

Core principle:

```text
Do not use a conversational agent to scrape, list, parse, or compare large volumes.
Use CLIs for repetitive and high-volume tasks.
Use MCPs only to access structured external systems or trigger controlled commands.
```

The CLI should produce short, consumable Markdown / JSON / log files. Claude then reads only the final outputs, not the full source pages.

Goal: transform TricorderKit into a lean agentic system:

```text
domain source
→ domain CLI
→ short normalized file
→ local cache
→ Obsidian / JSON export
→ read by Claude
→ synthesis / decision / correction
```

---

## 2. CLI-first principle

| Use case | Tool | Reason |
|---|---|---|
| Scrape a web page | CLI | Avoids copying large pages into context |
| Batch-scan multiple sources | CLI | Reduces agentic calls |
| Normalize results | CLI | Deterministic processing |
| Read a short synthesis | Claude | Model value-add |
| Update a validated record | Claude or controlled MCP | Targeted action |
| Access back-office service | MCP | Structured access |
| Export to Obsidian | CLI | Stable files |
| Editorial decision | Claude | Human/editorial reasoning |

---

## 3. Available CLI modules (example — adapt to your domain)

```text
your-cli content scan-new --source your_source --type new
your-cli content scan-ranking --source your_ranking_source
your-cli sync obsidian --vault ./exports
your-cli sync service --table sources
your-cli audit sources
```

---

## 4. MCP project configuration

`.mcp.json` at root — your service via environment variables.  
Secrets in `.env` (never committed).  
Variables: `SERVICE_BASE_URL`, `SERVICE_API_TOKEN`.

---

## 5. Security

- Strict CLI whitelist in `mcp/README_MCP_POLICY.md`
- Mandatory dry-run for bulk modifications
- Claude Code hooks: `validate_no_secret_commit.py`, `token_budget_guard.py`
- No secrets in Git
