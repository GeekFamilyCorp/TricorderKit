#!/usr/bin/env python3
"""Serveur MCP dedie : recherche semantique dans le vault RAG (G3 / DEC-023).

Wrappe `search_vault.py` (Qdrant collection 'vault' + embeddings nomic via Ollama).
Decouple du graph-server Node (Neo4j + embeddings OpenAI) : paradigme et backend differents.

Tool expose :
  - search_vault(query, top_n=5) -> liste de dicts {score,title,path,kind,fiabilite,text}

Pre-requis : `pip install mcp` ; Ollama + Qdrant up ; collection 'vault' peuplee (indexeur nocturne).
Config (env) : TK_QDRANT_URL, TK_OLLAMA_URL, TK_VAULT_COLLECTION, TK_EMBED_MODEL.
"""
from __future__ import annotations
import os
import sys

# Import de la logique de recherche (script G3, repo racine -> plugins/graphify/scripts).
_SCRIPTS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "..", "..", "..", "plugins", "graphify", "scripts"))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from search_vault import search_vault as _search_vault  # noqa: E402

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # message clair si le SDK n'est pas installe
    sys.stderr.write("[vault-search] dependance manquante : pip install mcp\n")
    raise

mcp = FastMCP("vault-search")

_QDRANT = os.environ.get("TK_QDRANT_URL", "http://localhost:6333")
_OLLAMA = os.environ.get("TK_OLLAMA_URL", "http://localhost:11434")
_COLL = os.environ.get("TK_VAULT_COLLECTION", "vault")
_MODEL = os.environ.get("TK_EMBED_MODEL", "nomic-embed-text")


@mcp.tool()
def search_vault(query: str, top_n: int = 5) -> list:
    """Recherche semantique dans le vault de connaissance (RAG dense).

    Args:
        query: requete en langage naturel.
        top_n: nombre de resultats (defaut 5).
    Returns:
        Liste de resultats {score, title, path, kind, fiabilite, text} tries par pertinence.
    """
    return _search_vault(query, top_n=top_n, collection=_COLL,
                         qdrant=_QDRANT, ollama=_OLLAMA, model=_MODEL)


if __name__ == "__main__":
    mcp.run()
