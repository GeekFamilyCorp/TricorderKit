#!/usr/bin/env python3
"""
hybrid_query.py — squelette de requête GraphRAG hybride (Qdrant → Neo4j → Ollama), 100 % local.

Usage :
  python3 hybrid_query.py --dry-run "quelles œuvres ressemblent à Mushishi ?"
  python3 hybrid_query.py --top-k 5 --collection fiches "..."

--dry-run n'importe aucune bibliothèque tierce et ne contacte aucun service : il imprime le plan.
Sans --dry-run, les imports sont gardés : chaque bibliothèque manquante donne un message
d'installation clair. Code de sortie 0 uniquement si une réponse a été produite (R71).

Configuration par variables d'environnement (jamais de secret en clair ici) :
  QDRANT_URL      (défaut http://127.0.0.1:6333)
  NEO4J_URI       (défaut bolt://127.0.0.1:7687)
  NEO4J_USERNAME / NEO4J_PASSWORD   (lus par le driver, jamais affichés)
  OLLAMA_HOST     (défaut http://127.0.0.1:11434)
  OLLAMA_MODEL    (génération, ex. un modèle de la famille qwen — lire `ollama list`)
  OLLAMA_EMBED    (embedding, doit correspondre à la dimension de la collection Qdrant)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Requête de voisinage : `node` est le nœud Neo4j apparié à un point Qdrant, `score` la similarité.
# Les labels/relations sont génériques : les remplacer par ceux de `get-schema`.
RETRIEVAL_QUERY = """
OPTIONAL MATCH (node)<-[:AUTEUR_DE]-(p)
OPTIONAL MATCH (node)-[:ADAPTE_EN]->(a)
RETURN node.id_externe AS id,
       coalesce(node.titre_fr, node.titre_jp, node.titre) AS titre,
       collect(DISTINCT p.nom_romaji) AS auteurs,
       collect(DISTINCT a.type) AS adaptations,
       score
"""

PROMPT_TEMPLATE = (
    "Tu réponds en français, uniquement à partir du CONTEXTE ci-dessous. "
    "Chaque affirmation cite l'identifiant entre crochets, ex. [MA0123]. "
    "Si le contexte ne permet pas de répondre, dis-le.\n\n"
    "CONTEXTE :\n{context}\n\nQUESTION : {question}\n"
)


def config() -> dict:
    return {
        "qdrant_url": os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"),
        "neo4j_uri": os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687"),
        "ollama_host": os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
        "ollama_model": os.environ.get("OLLAMA_MODEL", "<à lire dans `ollama list`>"),
        "ollama_embed": os.environ.get("OLLAMA_EMBED", "<modèle d'embedding>"),
        "neo4j_auth_present": bool(os.environ.get("NEO4J_USERNAME")) and bool(os.environ.get("NEO4J_PASSWORD")),
    }


def dry_run(args: argparse.Namespace) -> int:
    cfg = config()
    plan = {
        "mode": "dry-run (aucun service contacté)",
        "question": args.question,
        "etapes": [
            f"1. embedding de la question via Ollama {cfg['ollama_host']} modèle {cfg['ollama_embed']}",
            f"2. Qdrant {cfg['qdrant_url']} collection '{args.collection}' → top-{args.top_k} points, "
            f"payload['{args.id_external}']",
            f"3. Neo4j {cfg['neo4j_uri']} : jointure sur node.{args.id_neo4j}, requête de voisinage ci-dessous",
            f"4. génération Ollama modèle {cfg['ollama_model']} avec le prompt ci-dessous",
            "5. journal JSON (question, top_k, ids, modèle, durée)",
        ],
        "neo4j_auth_present": cfg["neo4j_auth_present"],
        "retrieval_query": RETRIEVAL_QUERY.strip(),
        "prompt_template": PROMPT_TEMPLATE,
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def real_run(args: argparse.Namespace) -> int:
    cfg = config()
    manquants = []
    try:
        import neo4j  # noqa: F401
    except ImportError:
        manquants.append("pip install neo4j")
    try:
        from qdrant_client import QdrantClient  # noqa: F401
    except ImportError:
        manquants.append("pip install qdrant-client")
    try:
        from neo4j_graphrag.retrievers import QdrantNeo4jRetriever  # noqa: F401
        from neo4j_graphrag.generation import GraphRAG  # noqa: F401
        from neo4j_graphrag.embeddings import OllamaEmbeddings  # noqa: F401
        from neo4j_graphrag.llm import OllamaLLM  # noqa: F401
    except ImportError:
        manquants.append('pip install "neo4j-graphrag[qdrant,ollama]"')
    if manquants:
        print("Bibliothèques manquantes — installer :\n  " + "\n  ".join(manquants), file=sys.stderr)
        return 2
    if not cfg["neo4j_auth_present"]:
        print("NEO4J_USERNAME / NEO4J_PASSWORD absents de l'environnement (aucune valeur n'est lue ici).",
              file=sys.stderr)
        return 2

    import neo4j
    from qdrant_client import QdrantClient
    from neo4j_graphrag.retrievers import QdrantNeo4jRetriever
    from neo4j_graphrag.generation import GraphRAG
    from neo4j_graphrag.embeddings import OllamaEmbeddings
    from neo4j_graphrag.llm import OllamaLLM

    t0 = time.time()
    driver = neo4j.GraphDatabase.driver(
        cfg["neo4j_uri"], auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    )
    try:
        # Signatures vérifiées le 2026-09-07 sur la doc API neo4j-graphrag ; les noms d'arguments
        # de host/model_name pour OllamaLLM sont « à vérifier » selon la version installée.
        embedder = OllamaEmbeddings(model_name=cfg["ollama_embed"], host=cfg["ollama_host"])
        retriever = QdrantNeo4jRetriever(
            driver=driver,
            client=QdrantClient(url=cfg["qdrant_url"]),
            collection_name=args.collection,
            id_property_external=args.id_external,
            id_property_neo4j=args.id_neo4j,
            embedder=embedder,
            retrieval_query=RETRIEVAL_QUERY,
        )
        llm = OllamaLLM(model_name=cfg["ollama_model"], host=cfg["ollama_host"])
        rag = GraphRAG(retriever=retriever, llm=llm)
        result = rag.search(query_text=args.question, retriever_config={"top_k": args.top_k})
    finally:
        driver.close()

    answer = getattr(result, "answer", None)
    if not answer:
        print("Aucune réponse produite.", file=sys.stderr)
        return 1
    print(answer)
    print(json.dumps({
        "event": "graphrag_query", "question": args.question, "top_k": args.top_k,
        "collection": args.collection, "model": cfg["ollama_model"],
        "duree_s": round(time.time() - t0, 2),
    }, ensure_ascii=False), file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Requête GraphRAG hybride locale (Qdrant + Neo4j + Ollama).")
    p.add_argument("question")
    p.add_argument("--dry-run", action="store_true", help="imprime le plan, ne contacte aucun service")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--collection", default="fiches")
    p.add_argument("--id-external", default="id", help="champ du payload Qdrant portant l'identifiant")
    p.add_argument("--id-neo4j", default="id_externe", help="propriété du nœud Neo4j portant l'identifiant")
    args = p.parse_args(argv)
    return dry_run(args) if args.dry_run else real_run(args)


if __name__ == "__main__":
    sys.exit(main())
