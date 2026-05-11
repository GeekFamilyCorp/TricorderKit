# SKILL — graphify

## Declencheurs
- Stocker des concepts, decisions, entites dans le graph
- Recuperer des concepts lies via traversal ou recherche semantique
- Requetes "lie a X", "decisions reliees a Y"
- Indexer les outputs de deep-research-core
- Boucles LangGraph research->extract->store->reflect

## Outils MCP (quand graph-server actif)
- graphify_store(node_type, title, content, relationships[])
- graphify_retrieve(query, mode="hybrid", limit=10)
- graphify_relate(from_id, rel_type, to_id)
- graphify_ping()

## Integration LangGraph state
- Concept  -> state["knowledge"]
- Task     -> state["tasks"]
- Decision -> state["context"]
- Source   -> state["sources"]

## Dependances
- Neo4j sur port 7687 : docker compose up -d neo4j
- Qdrant sur port 6333 : docker compose up -d qdrant
- NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, QDRANT_URL dans .env

## Non implemente (v0.1 scaffold)
Ce descripteur est fourni pour la planification. Implementation Phase 3.
