#!/usr/bin/env python3
"""search_vault.py - Recherche semantique sur le RAG vault (G3 / DEC-023).

Recherche dense sur la collection Qdrant 'vault' : embed de la requete via nomic
(prefixe 'search_query: '), puis Top-N. Le texte est lu DEPUIS LE PAYLOAD Qdrant
(decouple de tout index positionnel : corrige la limite de hybrid_rag.py d'origine).

Exposable en tool MCP : appeler search_vault(query, top_n) -> liste de dicts.

Usage CLI :
  python search_vault.py --query "auteur de Vinland Saga" --top-n 5
"""
from __future__ import annotations
import argparse, json, sys, urllib.request

# WIN-002 : forcer UTF-8 sur stdout (cp1252 ne supporte pas les emoji/kanji)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

QUERY_PREFIX = "search_query: "


def _embed(text, ollama, model, keep_alive="30m"):
    body = json.dumps({"model": model, "prompt": text, "keep_alive": keep_alive}).encode("utf-8")
    req = urllib.request.Request(ollama.rstrip("/") + "/api/embeddings", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["embedding"]


def _post(url, body, timeout=30):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def search_vault(query, top_n=5, collection="vault",
                 qdrant="http://localhost:6333", ollama="http://localhost:11434",
                 model="nomic-embed-text"):
    """Renvoie [{score, title, path, kind, text, ...}] pour les Top-N plus proches."""
    vec = _embed(QUERY_PREFIX + str(query), ollama, model)
    # API recente (>=1.10) puis repli sur l'ancienne.
    try:
        res = _post("%s/collections/%s/points/query" % (qdrant, collection),
                    {"query": vec, "limit": top_n, "with_payload": True})
        hits = res["result"]["points"]
    except Exception:
        res = _post("%s/collections/%s/points/search" % (qdrant, collection),
                    {"vector": vec, "limit": top_n, "with_payload": True})
        hits = res["result"]
    out = []
    for h in hits:
        p = h.get("payload") or {}
        out.append({"score": round(h.get("score", 0.0), 4),
                    "title": p.get("title"), "path": p.get("path"),
                    "kind": p.get("kind"), "fiabilite": p.get("fiabilite"),
                    "text": (p.get("text") or "")[:500]})
    return out


def main():
    ap = argparse.ArgumentParser(description="Recherche RAG vault (G3).")
    ap.add_argument("--query", required=True)
    ap.add_argument("--top-n", type=int, default=5)
    ap.add_argument("--collection", default="vault")
    ap.add_argument("--qdrant", default="http://localhost:6333")
    ap.add_argument("--ollama", default="http://localhost:11434")
    ap.add_argument("--model", default="nomic-embed-text")
    args = ap.parse_args()
    try:
        results = search_vault(args.query, args.top_n, args.collection,
                               args.qdrant, args.ollama, args.model)
    except Exception as exc:
        print(json.dumps({"error": str(exc)})); return 1
    print(json.dumps({"query": args.query, "n": len(results), "results": results},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
