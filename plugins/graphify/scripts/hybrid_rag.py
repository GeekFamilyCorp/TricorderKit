#!/usr/bin/env python3
"""
hybrid_rag.py — Pipeline RAG hybride (G3, fichier 04).

Dense (Qdrant + embeddings) + Sparse (BM25) -> fusion RRF -> re-ranking cross-encoder.
N'injecte que le Top-N re-rangé (évite « lost in the middle » et coupe les tokens).

Conçu pour brancher sur le Qdrant déjà actif de TricorderKit (:6333) et réutiliser
l'embedding local d'Ollama (mutualisé avec G2). Les dépendances lourdes sont importées
tardivement : ce module reste importable et testable SANS qdrant/sentence-transformers,
ce qui permet de valider la logique pure (RRF) en CI.

Dépendances runtime :
    pip install qdrant-client sentence-transformers rank_bm25 numpy

Usage (CLI) :
    python3 hybrid_rag.py --query "référence moteur X500" --top-n 3
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field


# ----------------------------------------------------------------------------
# Logique pure — testable sans aucune dépendance externe
# ----------------------------------------------------------------------------
def reciprocal_rank_fusion(dense_ids: list, sparse_ids: list, k: int = 60) -> list[tuple]:
    """Fusion RRF de deux listes de doc_ids classés. Renvoie [(doc_id, score)] décroissant."""
    scores: dict = {}
    for ranking in (dense_ids, sparse_ids):
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


class OllamaEmbedder:
    """Embeddings denses via Ollama (nomic-embed-text par défaut). REST urllib, zéro torch.
    Validé en réel 2026-06-01 : nomic-embed-text -> 768 dims, retrieval pertinent."""

    def __init__(self, base="http://localhost:11434", model="nomic-embed-text"):
        self.base, self.model = base, model

    def encode(self, text):
        import urllib.request

        class _Vec(list):  # expose .tolist() pour rester compatible avec l'appelant
            def tolist(self):
                return list(self)

        payload = json.dumps({"model": self.model, "prompt": str(text)}).encode("utf-8")
        req = urllib.request.Request(self.base.rstrip("/") + "/api/embeddings", data=payload,
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            return _Vec(json.loads(r.read())["embedding"])


@dataclass
class HybridRAG:
    """Pipeline hybride. Les modèles/clients sont chargés à la demande (lazy)."""

    collection: str = "knowledge_base"
    qdrant_url: str = "http://localhost:6333"
    # Backend d'embeddings : "ollama" (défaut, zéro torch, validé) ou "sentence-transformers".
    embed_backend: str = "ollama"
    ollama_base: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"
    dense_model_name: str = "all-MiniLM-L6-v2"
    rerank_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    documents: list[str] = field(default_factory=list)
    _dense=None
    _rerank=None
    _bm25=None
    _qdrant=None

    # -- chargements paresseux -------------------------------------------------
    def _ensure_dense(self):
        if self._dense is None:
            if self.embed_backend == "ollama":
                self._dense = OllamaEmbedder(self.ollama_base, self.ollama_embed_model)
            else:
                from sentence_transformers import SentenceTransformer
                self._dense = SentenceTransformer(self.dense_model_name)
        return self._dense

    def _ensure_rerank(self):
        if self._rerank is None:
            from sentence_transformers import CrossEncoder
            self._rerank = CrossEncoder(self.rerank_model_name)
        return self._rerank

    def _ensure_bm25(self):
        if self._bm25 is None:
            from rank_bm25 import BM25Okapi
            self._bm25 = BM25Okapi([d.lower().split(" ") for d in self.documents])
        return self._bm25

    def _ensure_qdrant(self):
        if self._qdrant is None:
            from qdrant_client import QdrantClient
            self._qdrant = QdrantClient(url=self.qdrant_url)
        return self._qdrant

    # -- recherche -------------------------------------------------------------
    def _dense_ids(self, query: str, limit: int) -> list:
        client = self._ensure_qdrant()
        vec = self._ensure_dense().encode(query).tolist()
        # API récente (query_points) avec repli sur l'ancienne (search).
        if hasattr(client, "query_points"):
            res = client.query_points(collection_name=self.collection, query=vec, limit=limit)
            hits = res.points
        else:  # qdrant-client < 1.10
            hits = client.search(collection_name=self.collection, query_vector=vec, limit=limit)
        return [h.id for h in hits]

    def _sparse_ids(self, query: str) -> list:
        import numpy as np
        scores = self._ensure_bm25().get_scores(query.lower().split(" "))
        return np.argsort(scores)[::-1].tolist()

    def retrieve(self, query: str, top_n: int = 3, dense_limit: int = 5) -> list[tuple]:
        """Renvoie le Top-N final [(texte, score_rerank)] après hybride + re-ranking."""
        fused = reciprocal_rank_fusion(self._dense_ids(query, dense_limit), self._sparse_ids(query))
        candidates = [self.documents[doc_id] for doc_id, _ in fused if doc_id < len(self.documents)]
        if not candidates:
            return []
        pairs = [[query, doc] for doc in candidates]
        rerank_scores = self._ensure_rerank().predict(pairs)
        ranked = sorted(zip(candidates, rerank_scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_n]


def main() -> int:
    ap = argparse.ArgumentParser(description="Pipeline RAG hybride (G3).")
    ap.add_argument("--query", required=True)
    ap.add_argument("--top-n", type=int, default=3)
    ap.add_argument("--collection", default="knowledge_base")
    ap.add_argument("--qdrant-url", default="http://localhost:6333")
    args = ap.parse_args()

    rag = HybridRAG(collection=args.collection, qdrant_url=args.qdrant_url)
    try:
        results = rag.retrieve(args.query, top_n=args.top_n)
    except Exception as exc:  # dépendances/infra absentes : message clair, pas de crash brut
        print(f"[hybrid-rag] infra requise (qdrant/sentence-transformers) : {exc}")
        return 1
    for i, (doc, score) in enumerate(results, 1):
        print(f"[{i}] {score:.4f} | {doc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
