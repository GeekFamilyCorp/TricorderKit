# mcp/ — TricorderKit v0.7

Serveurs MCP (Model Context Protocol) pour connecter les agents aux services.

## Serveurs planifiés

| Serveur | Service | Priorité |
|---|---|---|
| `graph-server/` | Neo4j — knowledge graph | A |
| `vector-server/` | Qdrant — vector search | A |
| `obsidian-server/` | Obsidian vault local | B |

## Structure cible

```text
mcp/
├── servers/
│   ├── graph-server/       # MCP Neo4j
│   ├── vector-server/      # MCP Qdrant
│   └── obsidian-server/    # MCP Obsidian
└── manifests/
    ├── neo4j.manifest.json
    ├── qdrant.manifest.json
    └── obsidian.manifest.json
```

*À implémenter en Phase 3 — après Docker Compose up*
