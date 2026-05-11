# TricorderKit

> CLI-first Agentic Knowledge Operating System — local-first

[![Version](https://img.shields.io/badge/version-0.7-blue)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/phase-2%20CLI--first-orange)](/.planning/STATE.md)
[![Stack](https://img.shields.io/badge/stack-Claude%20%2B%20Temporal%20%2B%20Neo4j%20%2B%20Qdrant-purple)](docker-compose.yml)

---

## What is TricorderKit?

TricorderKit is an **Agentic Knowledge OS** — a local-first system that transforms user intentions into traceable, auditable, and reusable workflows.

```
v0.6 definition : memory + skills + token hygiene + observability
v0.7 definition : CLI-first Agentic OS + Temporal workflows + skill registry + deep research + Obsidian knowledge layer
```

It takes inspiration from the Star Trek tricorder — a tool that scans, analyzes, and synthesizes information on demand.

---

## Stack

| Layer | Technology | Purpose |
|---|---|---|
| Agent | Claude Code (Anthropic) | Main reasoning agent |
| Knowledge | Obsidian (local vault) | Local-first knowledge base |
| Connectors | MCP servers | Service integrations |
| Graph DB | Neo4j 5.18 | Relational knowledge graph |
| Vector DB | Qdrant v1.8.4 | Semantic search / RAG |
| Workflows | Temporal 1.23 | Persistent workflow engine |
| Observability | Langfuse 2 | Token tracing + cost tracking |
| Infrastructure | Docker Compose | Local infra |
| CLIs | cli-forge (custom) | Deterministic API wrappers |

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/GeekFamilyCorp/TricorderKit.git
cd TricorderKit

# 2. Copy and fill environment variables
cp .env.example .env

# 3. Start infrastructure (optional — Phase 3+)
docker compose up -d

# 4. Boot the agent session
/tk:boot
```

---

## CLI Usage

TricorderKit ships with deterministic CLIs via the `cli-forge` plugin. These replace raw API calls with structured, cacheable commands. Add your own domain CLIs in `tools/`.

### github-goat — GitHub API CLI (example)

```bash
# List repos
python tools/github-goat/github_goat.py list-repos <owner>

# Search repositories
python tools/github-goat/github_goat.py search-repos "agentic OS"

# List issues
python tools/github-goat/github_goat.py list-issues <owner> <repo>

# Dry-run (simulate without side effects)
python tools/github-goat/github_goat.py --dry-run list-repos <owner>
```

### your-scraper — Generic Web Scraper (example scaffold)

```bash
# Fetch and parse an RSS feed
python tools/your-scraper/scraper.py rss --url https://example.com/feed.xml --output table

# Scrape a web page (trafilatura)
python tools/your-scraper/scraper.py web --url https://example.com/article

# Dry-run any command
python tools/your-scraper/scraper.py --dry-run rss --url https://example.com/feed.xml
```

> **Windows encoding tip:** Set `PYTHONUTF8=1` before running scripts to handle non-ASCII characters correctly.

---

## Agent Commands

```text
/tk:boot              → load state + memory + context
/tk:status            → current system state
/tk:plan              → display .planning/TASKS.md
/tk:pack-context      → compress context for handoff
/tk:token-hygiene     → token budget audit
/tk:audit-skills      → verify skill registry
/tk:eval-skill <name> → run non-regression eval
/tk:cli-forge <svc>   → generate CLI for a service
/tk:cli-audit <name>  → security audit a CLI
/tk:deep-research <q> → autonomous structured research
/tk:vault-audit       → audit Obsidian vault coherence
/tk:workflow-start <w>→ start a Temporal workflow
/tk:workflow-status   → status of active workflows
/tk:security-scan     → security audit
/tk:report            → structured Markdown report
/tk:health            → system health dashboard
/tk:dry-run <cmd>     → simulate command without side effects
/tk:changelog         → auto-generate CHANGELOG entry
```

---

## Repo Structure

```text
TricorderKit/
├── README.md               ← this file
├── README_FIRST.md         ← read before anything else
├── AGENTS.md               ← instructions for Claude agents
├── CLAUDE.md               ← Claude Code configuration
├── CHANGELOG.md            ← version history
├── docker-compose.yml      ← local infrastructure (DEV only — see file header)
├── .env.example            ← environment variables template
│
├── tools/                  ← your domain CLIs (add your own here)
│   ├── github-goat/        ← GitHub API CLI (example)
│   └── your-scraper/       ← generic web scraper scaffold (RSS/HTTP/trafilatura)
│
├── core/
│   ├── mainbrain/          ← MainBrain v1.4 decision algorithm
│   └── contracts/          ← JSON schemas (skill output contract)
│
├── plugins/
│   ├── cli-forge/          ← deterministic CLI generator & scaffolding
│   │   └── scripts/        ← manifest validator
│   ├── workflow-engine/    ← Temporal workflows
│   └── deep-research-core/ ← autonomous research pipelines (generic)
│
├── skills/
│   └── tk-boot/            ← /tk:boot skill
│
├── scripts/
│   ├── validate_repo.py    ← repo structure validator
│   └── health_check.py     ← system health dashboard
│
├── tests/
│   └── cli_contracts/      ← CLI contract tests (dry-run)
│
└── .planning/
    ├── STATE.md            ← current project state
    ├── TASKS.md            ← active backlog
    ├── DECISIONS.md        ← architectural decisions log
    ├── RISKS.md            ← risk register
    └── ROADMAP_v0.7.md     ← 5-phase roadmap
```

---

## Health Check

```bash
# Repo structure validation
python scripts/validate_repo.py

# List placeholder stubs created by --fix
python scripts/validate_repo.py --show-stubs

# System health dashboard (services + CLIs + planning)
python scripts/health_check.py

# HTML report
python scripts/health_check.py --output html

# CLI contract tests (add your own alongside)
python tests/cli_contracts/test_github_goat.py
```

---

## v0.7 — What's New vs v0.6

See [CHANGELOG.md](CHANGELOG.md) for the full entry. Key additions:

- **MainBrain v1.4** — upgraded routing engine with Risk Guard, CLI Selector, Token Hygiene Guard, and Dry-run mode
- **cli-forge plugin** — generates deterministic CLIs for any domain (github-goat included as example), with SQLite cache and dry-run support
- **workflow-engine plugin** — Temporal-based persistent workflows with token budget guard and pause/resume signals
- **deep-research-core plugin** — autonomous local-first research engine (configurable sources: RSS, web scraping, GitHub, custom APIs)
- **Contract testing** — `skill_output.schema.json` mandatory for all skills
- **Rate limiting** — `token_budget` per workflow with `pause_and_notify`
- **docker-compose.yml** — Neo4j + Qdrant + Temporal + Langfuse local stack
- **5-phase roadmap** with milestone dates in `.planning/ROADMAP_v0.7.md`

---

## Phase Roadmap (v0.7)

| Phase | Name | Status | Target |
|---|---|---|---|
| 1 | Foundations | ✅ Complete | 10/05/2026 |
| 2 | CLI-first (cli-forge) | 🔶 In progress | 17/05/2026 |
| 3 | Persistent workflows (Temporal) | 🔲 Pending | 07/06/2026 |
| 4 | Deep Research | 🔲 Pending | 21/06/2026 |
| 5 | Quality loop (eval-lab, security) | 🔲 Pending | 05/07/2026 |

---

## Contributing

This is a personal/research project. If you fork it, please respect the atomic knowledge rule:

> **1 idea = 1 node (100–500 tokens)**

---

*TricorderKit v0.7 — GeekFamilyCorp — 2026*  
*"What a tricorder does for the body, TricorderKit does for knowledge."*
