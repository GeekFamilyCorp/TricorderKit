# graph-server — MCP TricorderKit

Serveur MCP stdio exposant le knowledge graph (Neo4j + Qdrant) à Claude Code.

---

## Outils exposés

| Outil | Description |
|---|---|
| `graphify_ping` | Vérifie la connectivité Neo4j + Qdrant |
| `graphify_store` | Écrit un nœud dans Neo4j et Qdrant |
| `graphify_relate` | Crée une relation entre deux nœuds dans Neo4j |
| `graphify_retrieve` | Requête hybride : graph traversal + vector search |

---

## Prérequis

```bash
# Services Docker
docker compose up -d neo4j qdrant

# Variables d'environnement (.env)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=           # optionnel en local
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=           # requis si embedding_model = OpenAI
```

---

## Installation

```bash
cd mcp/servers/graph-server
npm install
npm run build
```

---

## Lancement manuel

```bash
npm start
```

---

## Intégration Claude Code (.mcp.json)

```json
{
  "mcpServers": {
    "graph-server": {
      "type": "stdio",
      "command": "node",
      "args": ["mcp/servers/graph-server/dist/index.js"],
      "env": {
        "NEO4J_URI": "${NEO4J_URI}",
        "NEO4J_USER": "${NEO4J_USER}",
        "NEO4J_PASSWORD": "${NEO4J_PASSWORD}",
        "QDRANT_URL": "${QDRANT_URL}",
        "QDRANT_API_KEY": "${QDRANT_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

---

## Ontologie

Voir `core/contracts/graph.schema.json` pour le contrat complet.

- **Nœuds** : Concept, Entity, Task, Skill, Agent, Source, Session, Decision
- **Relations** : RELATES_TO, DEPENDS_ON, PRODUCES, CONSUMES, REFERENCES, DERIVED_FROM, PART_OF, IMPLEMENTS, DISCOVERED_IN

---

*Version 0.1.0 — 13/05/2026*
