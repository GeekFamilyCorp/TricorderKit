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

---

## Obsidian Vault Setup (for memory-boot)

The `memory-boot` plugin stores and retrieves session context from an Obsidian vault connected via the [`obsidian-claude-vault` MCP](https://github.com/bitbonsai/mcpvault). Here is the recommended vault structure and the reasoning behind each folder.

### Recommended Vault Structure

```
claude-vault/
│
├── 00_SYSTEM/                  ← Claude's operating system
│   ├── 05_Hot_Cache/
│   │   └── HOT_CACHE.md        ← ★ Most important file. Read first every session.
│   ├── 06_Successes/           ← Journal of what worked
│   │   ├── SUCCESSES_INDEX.md  ← Master table (skills / plugins / projects)
│   │   ├── skills/             ← One .md per skill created or improved
│   │   ├── plugins/            ← One .md per plugin delivered
│   │   └── projects/           ← One .md per project launched
│   └── MASTER_PROTOCOL.md      ← Rules of engagement (reading order, logging rules)
│
├── 10_INBOX/                   ← Raw daily input, never restructured
│   └── Daily_Logs/
│       └── YYYY-MM-DD.md       ← One log per day, auto-created by memory-boot
│
├── 20_ENTITIES/                ← Structured knowledge base
│   ├── Projects/               ← One .md per active project
│   ├── Concepts/               ← Decisions, ADRs, technical notes
│   └── [your domain folders]   ← e.g. Products/, Clients/, Research/, etc.
│
├── 30_RELATIONS/               ← Maps of Content (MOC) and links
│   └── Maps_of_Content/
│       └── MOC_ACTIVE_PROJECTS.md
│
├── 40_ERRORS/                  ← Error tracking and pattern detection
│   ├── Error_Log/
│   │   └── ERRORS.md           ← Append-only error log (never delete entries)
│   └── Patterns/
│       └── PATTERNS_INDEX.md   ← Recurring error patterns to avoid
│
└── 60_ARCHIVE/                 ← Retired content, snapshots, history
```

### What goes where

**`00_SYSTEM/05_Hot_Cache/HOT_CACHE.md`** — the single most important file. It is Claude's working memory: current projects, last decisions, open tasks, error patterns to avoid. Keep it under 200 lines. Claude reads it first, every session, before anything else.

**`00_SYSTEM/06_Successes/`** — the success journal. Every skill created, every plugin delivered, every project launched gets a line in `SUCCESSES_INDEX.md` and a fiche in the appropriate subfolder. The `rapport` skill reads this to generate status reports.

**`10_INBOX/Daily_Logs/`** — the raw session log. The `memory-boot` skill creates one file per day, appends an entry at session start and at session end. Never restructure these — they are the audit trail.

**`20_ENTITIES/`** — the knowledge base. One file per project, concept, or domain entity. This is where detailed information lives (roadmaps, specs, decisions). HOT_CACHE only holds pointers to these files. Add domain subfolders freely to match your own projects.

**`40_ERRORS/`** — the error memory. `ERRORS.md` is append-only: every mistake gets logged immediately with date, context, correction applied, and whether it's a recurrent pattern. `PATTERNS_INDEX.md` extracts the patterns so Claude avoids repeating them.

### HOT_CACHE design principles

The HOT_CACHE is the key to effective memory. Keep it fast to read and always up to date:

```markdown
---
last_session: YYYY-MM-DD
---

## State
- Last session: [what happened]
- Active projects: [list with links to 20_ENTITIES/Projects/]

## Last Decisions (reverse chronological)
### YYYY-MM-DD — [topic]
- [decision taken and why]

## Open Tasks
- [ ] [task] — context in one line
- [x] ~~[done task]~~ ✅ YYYY-MM-DD

## Error Patterns to Avoid
- Sync with 40_ERRORS/Patterns/PATTERNS_INDEX.md
```

**Rules:**
- Never let HOT_CACHE exceed 200 lines — summarize aggressively
- Update `last_session` and open tasks at **every** session end
- Move detailed context to `20_ENTITIES/` files; HOT_CACHE holds only pointers
- If HOT_CACHE is older than 7 days, Claude will warn before proceeding

### Memory optimization strategy

| Problem | Solution |
|---------|----------|
| Claude forgets between sessions | `boot` at session start → reads HOT_CACHE |
| Context window fills up | `context-compress` → 10-20% of original size |
| Details get lost | Move depth to `20_ENTITIES/`, keep HOT_CACHE as index |
| Mistakes repeat | Log immediately to `40_ERRORS/ERRORS.md` |
| Can't find what was done | `06_Successes/SUCCESSES_INDEX.md` as master log |
| Too many skills slow Claude down | `skill-manager` audit every 2 months |

### MCP Setup (obsidian-claude-vault)

Add to Claude Desktop's `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "obsidian-claude-vault": {
      "command": "npx",
      "args": ["-y", "@bitbonsai/mcpvault", "/absolute/path/to/your/vault"]
    }
  }
}
```

> **Windows + MSIX note:** Claude Desktop (MSIX app) reads from `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`, **not** `%APPDATA%\Claude\`. Always edit the LocalCache path, otherwise the MCP will silently fail.

---

## Requirements

- Claude Cowork or Claude Code
- Python 3.8+ (for `token-optimizer` scripts)
- Obsidian + `obsidian-claude-vault` MCP (for `memory-boot`)
- Node.js / npx (for Context7 MCP in `token-optimizer`)

## Author

[GeekFamilyCorp](https://github.com/GeekFamilyCorp) — Built with Claude Cowork

---

*TricorderKit is named after the Star Trek tricorder — a device that scans, analyzes, and records everything. That's exactly what this toolkit does for Claude's work sessions.*
