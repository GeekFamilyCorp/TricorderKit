# TricorderKit

> CLI-first Agentic Knowledge Operating System — local-first

[![Version](https://img.shields.io/badge/version-0.9-blue)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/phase-9%20public--ready-green)](/.planning/STATE.md)
[![Stack](https://img.shields.io/badge/stack-Claude%20%2B%20Temporal%20%2B%20Neo4j%20%2B%20Qdrant-purple)](docker-compose.yml)

---

## What is TricorderKit?

TricorderKit is an **Agentic Knowledge OS** — a local-first system that transforms user intentions into traceable, auditable, and reusable workflows.

```
v0.6 definition : memory + skills + token hygiene + observability
v0.7 definition : CLI-first Agentic OS + Temporal workflows + skill registry + deep research + Obsidian knowledge layer
v0.8 definition : linked_project architecture + hook layer + quality loop + CLI tk + audit tools
v0.9 definition : Supabase layer + Langfuse observability + obsidian-agent-layer + tk doctor + public-ready documentation
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
├── cli/
│   └── tk.py               ← unified CLI (tk status/health/skill/workflow/vault/research/project)
│
├── tools/                  ← domain CLIs (add your own here)
│   ├── github-goat/        ← GitHub API CLI (example)
│   ├── your-scraper/       ← generic web scraper scaffold (RSS/HTTP/trafilatura)
│   └── audit/              ← linked_project_audit.py + local_vs_github_audit.py
│
├── configs/
│   ├── shared/defaults.yaml       ← defaults (versioned)
│   ├── local/                     ← local overrides (gitignored)
│   └── vps/                       ← VPS overrides (gitignored, future)
│
├── templates/
│   └── linked_project_template/   ← reproducible linked_project template
│
├── docs/
│   └── linked_projects.md         ← linked_project convention
│
├── reports/                ← generated audit + research reports
│
├── core/
│   ├── mainbrain/          ← MainBrain v1.5 decision algorithm
│   └── contracts/          ← JSON schemas (skill output contract)
│
├── plugins/
│   ├── cli-forge/          ← deterministic CLI generator & scaffolding
│   ├── workflow-engine/    ← Temporal workflows + activities + worker
│   ├── deep-research-core/ ← autonomous research pipelines (generic)
│   ├── hook-layer/         ← Pre-Intent / Pre-Execution / Post-Execution hooks
│   ├── eval-lab/           ← quality loop — eval runner + regression checker
│   ├── obsidian-agent-layer/ ← vault router + note builder
│   └── security-audit-cli/ ← security runner (audit, secrets, anon-check)
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
    ├── DECISIONS.md        ← architectural decisions log (DEC-001 → DEC-011)
    ├── RISKS.md            ← risk register
    └── ROADMAP_v0.7.md     ← 6-phase roadmap
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

## v0.9 — What's New vs v0.8

See [CHANGELOG.md](CHANGELOG.md) for the full entry. Key additions:

- **Supabase layer** — PostgreSQL schema for structured domain data (7 tables, RLS, seed data); replaces raw Obsidian-only storage for relational entities
- **Langfuse observability** — end-to-end token tracing via hooks (pre_intent → trace, pre/post_execution → span); no SDK dependency, REST-direct, Python 3.14 compatible
- **obsidian-agent-layer** — `obsidian_runner.py` + `tk obsidian` commands; vault router + note builder with 34 tests
- **security-audit-cli** — `security_runner.py` + `tk security`; secrets scan, anonymization check, dependency audit (16 tests)
- **tk doctor** — unified health check: 14 checks (Python, Docker, 4 services, `.env`, 4 dirs, modules, linked_projects, secrets); `[OK]` / `[WARN]` / `[FAIL]` output
- **tk rapport** — CLI status report from `BOOT_SUMMARY.md` + `STATUS.md` → `reports/status/latest_status.md` (JSON flag supported)
- **Public-ready docs** — `INSTALL.md`, `examples/linked-project-template/`, `docs/linked_projects.md`, `docs/anonymization.md`, `ROADMAP.md`
- **485 tests passing** — 0 FAIL (up from 174 at v0.9 M1)

---

## v0.8 — What's New vs v0.7

See [CHANGELOG.md](CHANGELOG.md) for the full entry. Key additions:

- **linked_project architecture** — TricorderKit is now a generic engine; domain-specific content lives in separate private linked_projects (see `examples/linked-project-template/`)
- **Hook layer v0.2** — Pre-Intent, Pre-Execution, Post-Execution hooks wired into MainBrain; 25 tests
- **Quality loop** — eval-lab (eval_runner + baseline_store + regression_checker), security-audit-cli, obsidian-agent-layer
- **CLI `tk`** — unified entrypoint: `tk status`, `tk health`, `tk skill list`, `tk workflow list`, `tk vault scan`, `tk research run --dry-run`, `tk project *`, `--format json|markdown` everywhere
- **Audit tools** — `tools/audit/linked_project_audit.py` + `tools/audit/local_vs_github_audit.py`
- **Template** — `templates/linked_project_template/` reproductible (9 subdirs + configs)
- **Config layers** — `configs/shared/defaults.yaml` (versioned) + local + vps overrides (gitignored)
- **GitHub MCP migration** — `@modelcontextprotocol/server-github` → `ghcr.io/github/github-mcp-server` (Docker, official)

## v0.7 — What's New vs v0.6

- **MainBrain v1.4** — Risk Guard, CLI Selector, Token Hygiene Guard, Dry-run mode
- **cli-forge plugin** — deterministic CLI generator (github-goat example), SQLite cache
- **workflow-engine plugin** — Temporal persistent workflows with token budget guard
- **deep-research-core plugin** — autonomous local-first research engine (RSS, web, APIs)
- **Contract testing** — `skill_output.schema.json` mandatory for all skills
- **docker-compose.yml** — Neo4j + Qdrant + Temporal + Langfuse local stack

---

## Phase Roadmap

See [ROADMAP.md](ROADMAP.md) for full details.

| Phase | Name | Status | Completed |
|---|---|---|---|
| 1 | Foundations | ✅ Complete | 10/05/2026 |
| 2 | CLI-first (cli-forge) | ✅ Complete | 17/05/2026 |
| 3 | Persistent workflows (Temporal) | ✅ Complete | 15/05/2026 |
| 4 | Deep Research | ✅ Complete | 16/05/2026 |
| 5 | Quality loop (eval-lab, security) | ✅ Complete | 16/05/2026 |
| 6 | Linked project architecture | ✅ Complete | 17/05/2026 |
| 7 | v0.9 — Orchestration + observability | ✅ Complete | 22/05/2026 |
| 8 | v0.9 — Public-ready (docs, install, security) | ✅ Complete | 22/05/2026 |
| 9 | VPS deployment (optional) | 🔲 Planned | — |
| 10 | Multi-linked-project support | 🔲 Planned | — |
| 11 | Plugin marketplace / registry | 🔲 Planned | — |
| 12 | Community release | 🔲 Planned | — |

---

## Contributing

This is a personal/research project. If you fork it, please respect the atomic knowledge rule:

> **1 idea = 1 node (100–500 tokens)**

---

*TricorderKit v0.9 — GeekFamilyCorp — 2026*  
*"What a tricorder does for the body, TricorderKit does for knowledge."*
