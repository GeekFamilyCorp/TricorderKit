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


---

## Gouvernance machine-lisible (DEC-046 / N3)

La politique écrite dans [`README_MCP_POLICY.md`](./README_MCP_POLICY.md) est rendue
**exécutable** et **deny-by-default** :

- `registry_allowlist.yaml` — allowlist déclarative (serveurs + tools + permissions +
  rate limits). Tout ce qui n'y figure pas est **refusé**. Secrets : références
  `${VAR}` uniquement (DEC-039), jamais de valeur en clair dans `.mcp.json`.
- `scripts/mcp_gateway.py` — moteur de décision et d'audit, sortie conforme au
  contrat `core/contracts/skill_output.schema.json`.
- `logs/mcp_calls.jsonl` — journal par appel (gitignoré).

```bash
tk mcp list                                              # serveurs/tools déclarés + configurés
tk mcp audit                                             # .mcp.json confronté à l'allowlist
tk mcp allowlist-check --server graph-server --tool graphify_store
```

Codes retour : `0` autorisé / synchronisé, `1` refusé / violation, `2` erreur d'environnement.
