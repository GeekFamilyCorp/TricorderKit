# graphify -- TricorderKit Knowledge Graph Engine

Plugin v0.1 -- Phase 3 TricorderKit
Architecture : Neo4j (graph traversal) + Qdrant (semantic search) + LangGraph (agent loops)

## What is graphify?

graphify is the knowledge graph engine of TricorderKit. It provides a hybrid retrieval interface combining:
- Neo4j -- structural traversal: "what entities are connected to X?"
- Qdrant -- semantic search: "what entities are similar to X?"
- LangGraph -- agentic loops: research -> extract -> store -> reflect

Every write triggers a dual-index: one node in Neo4j, one vector in Qdrant.

## Ontology (Neo4j)

Node types:
| Label | Description | Key properties |
|---|---|---|
| Concept | Abstract idea or domain knowledge | id, title, content, source, created_at |
| Entity | Named real-world thing | id, name, type, url |
| Task | Actionable item or workflow step | id, title, status, priority, due |
| Skill | Claude skill or capability | id, name, trigger, path |
| Agent | Autonomous agent definition | id, name, role, model |
| Source | Data origin (URL, file, API) | id, url, type, last_fetched |
| Session | Claude conversation session | id, date, summary, tokens_used |
| Decision | Architectural decision record | id, code, title, status, date |

Relationship types:
RELATES_TO | DEPENDS_ON | PRODUCES | CONSUMES | REFERENCES | DERIVED_FROM | PART_OF | IMPLEMENTS | DISCOVERED_IN

## Directory structure

plugins/graphify/
  README.md
  manifest.yml
  .claude-plugin/plugin.json
  skills/graphify/SKILL.md
  schema/
    ontology.cypher    (Neo4j constraints + indexes)
    graph.schema.json  (JSON schema for graph objects)
  src/
    indexer.py         (dual-write Neo4j + Qdrant)
    retriever.py       (hybrid query interface)
    embedder.py        (text to vector)
    langgraph_adapter.py (LangGraph state <-> graph nodes)
  mcp/
    graph-server/      (Neo4j MCP server)
    vector-server/     (Qdrant MCP server)
  tests/
    test_graphify.py

## Quick start

  docker compose up -d neo4j qdrant
  python plugins/graphify/src/retriever.py --ping
  python plugins/graphify/src/indexer.py --node-type Concept --title "LangGraph" --content "..."

## LangGraph integration

  Concept  -> state["knowledge"]
  Task     -> state["tasks"]
  Decision -> state["context"]
  Source   -> state["sources"]

  Agentic loop: research -> extract -> store(graphify) -> reflect -> research...

## Status v0.1

Ontology definition  : DONE
schema/              : TODO
src/                 : TODO
mcp/                 : TODO
tests/               : TODO

v0.1 = scaffold + architecture. Implementation in Phase 3.
TricorderKit v0.7 -- Phase 3
