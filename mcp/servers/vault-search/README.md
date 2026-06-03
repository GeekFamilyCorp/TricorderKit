# vault-search — serveur MCP RAG (G3 / DEC-023)

Expose la recherche semantique du vault (`search_vault`) en tool MCP. Wrappe
`plugins/graphify/scripts/search_vault.py` : embeddings `nomic-embed-text` via Ollama +
collection Qdrant `vault`. Decouple du `graph-server` Node (Neo4j + OpenAI).

## Pre-requis
- `pip install mcp` (SDK MCP Python / FastMCP).
- Ollama (`nomic-embed-text`) + Qdrant up, collection `vault` peuplee par l'indexeur
  (`index_vault.py --incremental`, run nocturne 03:00).

## Variables d'environnement (optionnelles)
| Var | Defaut |
|---|---|
| `TK_QDRANT_URL` | `http://localhost:6333` |
| `TK_OLLAMA_URL` | `http://localhost:11434` |
| `TK_VAULT_COLLECTION` | `vault` |
| `TK_EMBED_MODEL` | `nomic-embed-text` |

## Enregistrement (a faire APRES verification e2e post-index)
Ajouter dans `.mcp.json` -> `mcpServers` :

```json
"vault-search": {
  "type": "stdio",
  "command": "python",
  "args": ["mcp/servers/vault-search/server.py"],
  "description": "Recherche semantique RAG du vault (Qdrant 'vault' + nomic) — tool search_vault"
}
```

## Test rapide (CLI, sans MCP)
```
python plugins/graphify/scripts/search_vault.py --query "votre requete" --top-n 5
```

> Statut 2026-06-01 : code pret. Enregistrement + test e2e planifies APRES le 1er index nocturne
> (collection `vault` vide jusque-la).
