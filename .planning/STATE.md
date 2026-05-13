# TricorderKit v0.7 — State

**Date:** 2026-05-11
**Phase:** 3 (RAG/Knowledge Graph — en cours)
**Status:** Public generic framework OK

## Current state

TricorderKit est un framework agentique public et domain-agnostic.
Phase 2 (CLI-first) terminee. Phase 3 (RAG + Graphify) active.

## Plugins installes

* plugins/deep-research-core/ — research engine (stub)
* plugins/cli-forge/ — CLI scaffolding
* plugins/memory-boot/ — session memory boot
* plugins/token-optimizer/ — token optimization
* plugins/workflow-engine/ — Temporal + LangGraph (DEC-008)
* plugins/graphify/ — Neo4j + Qdrant hybrid (DEC-009) \[v0.1 scaffold]

## Architecture

TricorderKit (public)
tools/             (domain CLIs)
plugins/graphify/  <- NEW Phase 3
Neo4j (graph traversal)
Qdrant (semantic search)
LangGraph (agent loops)
MangaTracker (private) — Japan-Alliance instance

## Phase 3 Roadmap

1. core/contracts/graph.schema.json (ontologie Neo4j)
2. mcp/servers/graph-server/ (Neo4j MCP)
3. mcp/servers/vector-server/ (Qdrant MCP)
4. graphify dual-write (Neo4j + Qdrant sync)
5. LangGraph agent loops via graphify state API
6. Gitleaks pre-commit + CI (Priority S)
7. cli-printing-press dans cli-forge (Priority S)

## Etapes completees

1. OK Phase 2 CLI-first
2. OK Framework neutralise (Manga/Anime retire)
3. OK validate\_repo.py — stub detection
4. OK docker-compose.yml — DEV ONLY warning
5. OK .env.example — secure placeholders
6. OK DECISIONS.md — DEC-001 a DEC-009
7. OK plugins/graphify — v0.1 scaffold



\---



\## Phase 2 consolidation — 2026-05-13



Phase 2 cli-forge avait été marquée "terminée" en v0.7 sans standard

d'implémentation Typer ni tests CliRunner. Consolidation appliquée le

13/05/2026 :



\- `docs/cli\_forge\_typer\_standard.md` — standard Typer documenté

\- `plugins/cli-forge/templates/{typer\_cli,typer\_test}.py.j2` — templates Jinja2

\- `plugins/cli-forge/SKILL.md` et `manifest.yml` — gouvernance plugin

\- `tools/tk\_installer/tk\_installer.py` — première CLI Typer de référence

&#x20; (commandes status + diagnose, conforme `skill\_output.schema.json`)

\- `tests/cli\_contracts/test\_tk\_installer.py` — 27 tests CliRunner verts

\- `.tricorderkit/{state,phase\_gates,install\_profile,known\_errors}.yml` —

&#x20; orchestration v0.8



Le travail Phase 3 RAG/Graphify reste prioritaire et non bloqué par cette

consolidation. Le tag `framework: argparse\_legacy` est appliqué aux CLIs

existantes (`github-goat`, `source-watch-goat`) en attendant migration via

PRs dédiées.



Référence : DEC-010 — adoption standard Typer pour les nouvelles CLIs.

