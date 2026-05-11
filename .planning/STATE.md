# TricorderKit v0.7 — State

**Date:** 2026-05-11
**Phase:** 3 (RAG/Knowledge Graph — en cours)
**Status:** Public generic framework OK

## Current state
TricorderKit est un framework agentique public et domain-agnostic.
Phase 2 (CLI-first) terminee. Phase 3 (RAG + Graphify) active.

## Plugins installes
- plugins/deep-research-core/ — research engine (stub)
- plugins/cli-forge/ — CLI scaffolding
- plugins/memory-boot/ — session memory boot
- plugins/token-optimizer/ — token optimization
- plugins/workflow-engine/ — Temporal + LangGraph (DEC-008)
- plugins/graphify/ — Neo4j + Qdrant hybrid (DEC-009) [v0.1 scaffold]

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
3. OK validate_repo.py — stub detection
4. OK docker-compose.yml — DEV ONLY warning
5. OK .env.example — secure placeholders
6. OK DECISIONS.md — DEC-001 a DEC-009
7. OK plugins/graphify — v0.1 scaffold
