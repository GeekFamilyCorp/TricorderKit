"""Tests de la logique pure du pipeline RAG hybride (G3).

Valide la fusion RRF sans aucune dépendance externe (qdrant/sentence-transformers
ne sont PAS requis ici)."""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("hybrid_rag", Path(__file__).with_name("hybrid_rag.py"))
hr = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = hr  # requis pour que @dataclass résolve son module
spec.loader.exec_module(hr)


def test_rrf_basic_ordering():
    # doc 1 bien classé dans les deux listes -> doit dominer.
    dense = [1, 2, 3]
    sparse = [1, 3, 2]
    fused = hr.reciprocal_rank_fusion(dense, sparse)
    assert fused[0][0] == 1
    assert [d for d, _ in fused] == [1, 3, 2] or [d for d, _ in fused][0] == 1


def test_rrf_merges_disjoint_lists():
    fused = dict(hr.reciprocal_rank_fusion([10], [20]))
    assert set(fused) == {10, 20}


def test_rrf_rewards_agreement():
    # Un doc présent en tête des deux listes bat un doc présent dans une seule.
    fused = dict(hr.reciprocal_rank_fusion([1, 2], [1, 3]))
    assert fused[1] > fused[2]
    assert fused[1] > fused[3]


def test_hybridrag_instantiates_without_heavy_deps():
    rag = hr.HybridRAG(documents=["a", "b"])
    assert rag.collection == "knowledge_base"
    assert rag.qdrant_url.endswith(":6333")
