# graphify — TricorderKit Knowledge Graph Engine

Plugin v0.1 scaffold — Phase 3
Architecture : Neo4j (graph traversal) + Qdrant (semantic search) + LangGraph (agent loops)

## Ontologie Neo4j

Node types : Concept | Entity | Task | Skill | Agent | Source | Session | Decision

Relation types : RELATES_TO | DEPENDS_ON | PRODUCES | CONSUMES | REFERENCES | DERIVED_FROM | PART_OF | IMPLEMENTS | DISCOVERED_IN

## Integration LangGraph
- Concept  -> state["knowledge"]
- Task     -> state["tasks"]
- Decision -> state["context"]
- Source   -> state["sources"]

Boucle agentique cible : research -> extract -> store(graphify) -> reflect -> research...

## Status v0.1
Scaffold uniquement. Implementation en Phase 3.
Utiliser validate_repo.py --show-stubs pour tracker la progression.
