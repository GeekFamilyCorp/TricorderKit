# SKILL -- graphify

## Trigger conditions

Use this skill when the conversation involves:
- Storing knowledge, concepts, decisions, or entities in the graph
- Retrieving related concepts via graph traversal or semantic search
- Querying "what is connected to X", "what decisions relate to Y"
- Indexing research output from deep-research-core
- Seeding the graph from Obsidian vault notes
- Running a LangGraph research -> extract -> store -> reflect loop

## What graphify does

graphify is a hybrid knowledge graph combining Neo4j (structural) and Qdrant (semantic).

Write path:
1. Receive content (text, metadata, node type)
2. Create/update Neo4j node with relationships
3. Embed content -> Qdrant vector (same ID as Neo4j node)

Read path:
1. Query arrives (natural language or structured)
2. Parallel: Neo4j graph traversal + Qdrant vector search
3. Merge + rank results
4. Return enriched context to caller

## Node types

Concept | Entity | Task | Skill | Agent | Source | Session | Decision

## MCP tools (when graph-server is active)

- graphify_store(node_type, title, content, relationships[])
- graphify_retrieve(query, mode="hybrid", limit=10)
- graphify_relate(from_id, rel_type, to_id)
- graphify_ping()

## LangGraph state mapping

Concept  -> state["knowledge"]
Task     -> state["tasks"]
Decision -> state["context"]
Source   -> state["sources"]

## Dependencies

- Neo4j port 7687 : docker compose up -d neo4j
- Qdrant port 6333 : docker compose up -d qdrant
- NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, QDRANT_URL in .env

## Status

v0.1 scaffold -- planning only. Implementation in Phase 3.
Use validate_repo.py --show-stubs to track progress.
