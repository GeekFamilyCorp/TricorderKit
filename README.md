# TricorderKit

> Plugin ecosystem for Claude Cowork — Session memory, intelligent model routing, and token optimization.

TricorderKit is a collection of **Claude Cowork plugins and skills** focused on helping Claude work smarter across sessions: remembering context from one conversation to the next, routing tasks to the right model tier (Haiku / Sonnet / Opus), and cutting unnecessary token spend.

## Why TricorderKit?

Three problems it solves:

1. **No memory between sessions** — Claude forgets everything when the conversation ends. `memory-boot` fixes this by persisting context in an Obsidian vault and loading it on demand.
2. **Wrong model for the task** — Using Opus for a typo correction, or Haiku for an architecture decision. `token-optimizer` classifies each request and routes to the appropriate tier automatically.
3. **Token waste** — Long contexts, verbose CLI output, hallucinated API signatures. Three dedicated skills compress these at source.

## Contents

### Plugins (installable in Claude Cowork)

| Plugin | Skills | Description |
|--------|--------|-------------|
| [`memory-boot`](plugins/memory-boot/) | `memory-boot`, `rapport` | Session memory from Obsidian vault. Boot context, daily logs, success tracking. |
| [`token-optimizer`](plugins/token-optimizer/) | `model-router`, `task-classifier`, `budget-tracker`, `context-compress`, `docs-fresh`, `cli-compress` | Intelligent Haiku/Sonnet/Opus routing with context compression, fresh docs injection, and monthly budget tracking. |

### Standalone Skills

| Skill | Description |
|-------|-------------|
| [`skill-manager`](skills/skill-manager/) | Inventory, audit, and conflict detection for all installed skills and plugins. |
| [`skill-creator`](skills/skill-creator/) | Create and iterate on skills with eval/benchmark loops. |
| [`consolidate-memory`](skills/consolidate-memory/) | Reflective pass over memory files — merge duplicates, fix stale facts, prune the index. |

## Quick Start

### memory-boot

**Prerequisites:** `obsidian-claude-vault` MCP connected in Claude Cowork.

1. Install the plugin in Claude Cowork
2. At the start of any session, type: `boot`

Claude will read your HOT_CACHE, error patterns and daily log, then summarize the session context.

To get a status report: type `rapport`

### token-optimizer

1. Install the plugin in Claude Cowork
2. Optionally install `rtk` for CLI compression:
   ```bash
   bash plugins/token-optimizer/scripts/rtk-install.sh
   ```
3. The model router activates automatically on each significant request.

Check budget:
```bash
python3 plugins/token-optimizer/scripts/budget.py status
```

## Architecture

```
Session start
     |
[memory-boot]  <- reads HOT_CACHE + ERRORS + PATTERNS from Obsidian
     |
[model-router] <- [budget-tracker] (monthly token budget)
     |
     |-- [context-compress]  (if context > 60% of window)
     |-- [docs-fresh]        (if a library/framework is mentioned) -> MCP Context7
     |
     T1: haiku-executor   (Haiku 4.5  — score 0-25)
     T2: sonnet-executor  (Sonnet 4.6 — score 26-60)
     T3: opus-executor    (Opus 4.6   — score 61-100)
     |
[cli-compress] <- rtk hook (all bash commands)
     |
  Response + budget log
```

## Model Tiers

| Tier | Model | Score | Use cases |
|------|-------|-------|-----------|
| T1 | Haiku 4.5 | 0–25 | Translations, summaries, reformulations, simple extractions |
| T2 | Sonnet 4.6 | 26–60 | Standard writing, code, analysis, light orchestration |
| T3 | Opus 4.6 | 61–100 | System architecture, security code, multi-step reasoning, production debug |

## Not Included

The following are excluded as domain-specific (Japan Alliance Database project):
- `japan-alliance-lookup` — anime, games, cinema, music, culture, language, places, tech
- `mangatracker-lookup` — manga and light novels

## Requirements

- Claude Cowork or Claude Code
- Python 3.8+ (for `token-optimizer` scripts)
- Obsidian + `obsidian-claude-vault` MCP (for `memory-boot`)
- Node.js / npx (for Context7 MCP in `token-optimizer`)

## Author

[GeekFamilyCorp](https://github.com/GeekFamilyCorp) — Built with Claude Cowork

---

*TricorderKit is named after the Star Trek tricorder — a device that scans, analyzes, and records everything. That's exactly what this toolkit does for Claude's work sessions.*
