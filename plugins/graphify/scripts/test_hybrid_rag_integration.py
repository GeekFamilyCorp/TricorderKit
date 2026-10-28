"""Test d'INTÉGRATION du pipeline RAG hybride (G3) — exécution réelle.

Exerce réellement : Qdrant en mémoire (recherche dense vectorielle) + BM25 (sparse)
+ RRF + re-ranking. L'embedding dense et le re-ranker sont des STAND-INS déterministes
(sac-de-mots haché) pour éviter torch/HuggingFace en CI : on valide le CÂBLAGE complet
et la pertinence, pas la qualité d'un modèle particulier.

Skippe proprement si qdrant-client n'est pas installé.
"""
import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

qdrant = pytest.importorskip("qdrant_client")
pytest.importorskip("rank_bm25")

spec = importlib.util.spec_from_file_location("hybrid_rag", Path(__file__).with_name("hybrid_rag.py"))
hr = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = hr
spec.loader.exec_module(hr)

DIM = 64
DOCS = [
    "La pièce de rechange pour le moteur X500 porte la référence REF-9942.",
    "Le guide de dépannage recommande de redémarrer le système en cas d'erreur 404.",
    "La politique de l'entreprise stipule que les mots de passe doivent faire 12 caractères.",
    "Le moteur de recherche utilise des vecteurs denses pour comprendre l'intention.",
    "Pour réparer le moteur X500, vérifiez d'abord la référence REF-9942 avant de commander.",
]


class _BagEmbed:
    """Embedding déterministe : chaque mot incrémente une dimension hachée. Sans torch."""

    def encode(self, text):
        import numpy as np
        vec = np.zeros(DIM, dtype="float32")
        for tok in str(text).lower().split():
            vec[int(hashlib.md5(tok.encode()).hexdigest(), 16) % DIM] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec


class _OverlapReranker:
    """Re-ranker stand-in : score = nombre de mots de la requête présents dans le doc."""

    def predict(self, pairs):
        out = []
        for query, doc in pairs:
            q = set(query.lower().split())
            out.append(float(sum(1 for w in q if w in doc.lower())))
        return out


def _build_rag():
    from qdrant_client.models import Distance, VectorParams

    rag = hr.HybridRAG(documents=list(DOCS))
    rag._dense = _BagEmbed()
    rag._rerank = _OverlapReranker()
    client = qdrant.QdrantClient(":memory:")
    client.create_collection("knowledge_base", VectorParams(size=DIM, distance=Distance.COSINE))
    client.upload_collection(
        collection_name="knowledge_base",
        vectors=[rag._dense.encode(d).tolist() for d in DOCS],
        payload=[{"text": d} for d in DOCS],
        ids=list(range(len(DOCS))),
    )
    rag._qdrant = client
    return rag


def test_end_to_end_keyword_query_ranks_reference_docs_first():
    rag = _build_rag()
    results = rag.retrieve("référence pour le moteur X500", top_n=2)
    assert results, "le pipeline doit renvoyer des résultats"
    top_texts = " ".join(doc for doc, _ in results)
    # Les deux docs pertinents mentionnent X500 + REF-9942 → doivent remonter.
    assert "REF-9942" in top_texts
    assert "X500" in top_texts


def test_end_to_end_excludes_irrelevant_doc():
    rag = _build_rag()
    results = rag.retrieve("référence moteur X500", top_n=2)
    top_texts = " ".join(doc for doc, _ in results)
    assert "mots de passe" not in top_texts  # doc hors-sujet écarté
