"""
index_qdrant.py — TricorderKit deep-research-core
Indexation des findings dans Qdrant.

Pipeline attendu :
    collect_sources.py | deduplicate_findings.py | score_reliability.py | index_qdrant.py

Usage :
    python score_reliability.py --input findings.json | python index_qdrant.py
    python index_qdrant.py --input scored.json --collection manga_knowledge
    python index_qdrant.py --input scored.json --dry-run
    python index_qdrant.py --input scored.json --embedder hash   # sans GPU, sans ML

Backends d'embedding :
  auto        — Essaie sentence-transformers puis hash (defaut)
  sentence    — sentence-transformers all-MiniLM-L6-v2 (384-dim, local, recommande)
  hash        — Hachage numpy deterministique 384-dim (tests / dry-run / sans ML lib)

Version : 0.1.0 — 15/05/2026
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# -- Logging -----------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    stream=sys.stderr,
)
log = logging.getLogger("index_qdrant")

# -- Constantes --------------------------------------------------------------
DEFAULT_COLLECTION = "manga_knowledge"
DEFAULT_QDRANT_URL = "http://localhost:6333"
VECTOR_SIZE = 384           # Compatible all-MiniLM-L6-v2 et hash fallback
DEFAULT_BATCH_SIZE = 64
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Namespace UUID pour IDs deterministes (RFC 4122 v5)
_UUID_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace


# -- Embedders ----------------------------------------------------------------

class HashEmbedder:
    """
    Embedder deterministique base sur feature hashing (numpy pur).
    Produit des vecteurs 384-dim L2-normalises depuis du texte.
    Pas semantique mais stable, rapide, sans dependance ML.
    """

    def __init__(self, n_features: int = VECTOR_SIZE) -> None:
        self.n_features = n_features

    def _text_to_ngrams(self, text: str, n: int = 3) -> list[str]:
        text = text.lower()
        return [text[i:i+n] for i in range(max(0, len(text) - n + 1))]

    def encode(self, texts: list[str], batch_size: int = 64, show_progress_bar: bool = False) -> np.ndarray:
        result = np.zeros((len(texts), self.n_features), dtype=np.float32)
        for idx, text in enumerate(texts):
            vec = np.zeros(self.n_features, dtype=np.float32)
            ngrams = self._text_to_ngrams(text)
            if not ngrams:
                h = int(hashlib.sha256(b"").hexdigest(), 16)
                vec[h % self.n_features] = 1.0
            else:
                for gram in ngrams:
                    h = int(hashlib.sha256(gram.encode()).hexdigest()[:8], 16)
                    pos = h % self.n_features
                    sign = 1.0 if (h >> 8) & 1 else -1.0
                    vec[pos] += sign
            # L2-normalisation
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            result[idx] = vec
        return result


def _load_sentence_embedder(model_name: str = EMBEDDING_MODEL):
    """Charge SentenceTransformer si disponible, sinon leve ImportError."""
    from sentence_transformers import SentenceTransformer  # noqa: PLC0415
    log.info("Chargement embedder sentence-transformers : %s", model_name)
    return SentenceTransformer(model_name)


def get_embedder(mode: str = "auto"):
    """Retourne (embedder, backend_name) selon le mode."""
    if mode == "hash":
        log.info("Embedder : hash (deterministique numpy)")
        return HashEmbedder(), "hash"
    if mode == "sentence":
        emb = _load_sentence_embedder()
        return emb, "sentence-transformers"
    # mode == "auto"
    try:
        emb = _load_sentence_embedder()
        return emb, "sentence-transformers"
    except ImportError:
        log.warning("sentence-transformers non disponible — fallback hash embedder")
        return HashEmbedder(), "hash"


# -- Construction du texte d'embedding ---------------------------------------

def build_embedding_text(item: dict) -> str:
    parts: list[str] = []
    title = str(item.get("title") or "")
    if title:
        parts.append(title)
        parts.append(title)
    title_ja = str(item.get("title_japanese") or item.get("title_native") or "")
    if title_ja and title_ja != title:
        parts.append(title_ja)
    for field in ["genres", "tags"]:
        val = item.get(field)
        if isinstance(val, list):
            parts.append(" ".join(str(v) for v in val[:10] if v))
        elif val:
            parts.append(str(val))
    for field in ["authors", "studios"]:
        val = item.get(field)
        if isinstance(val, list):
            parts.append(" ".join(str(v) for v in val[:5] if v))
        elif val:
            parts.append(str(val))
    desc = str(item.get("description") or "")
    if desc:
        parts.append(desc[:300])
    return " | ".join(p for p in parts if p.strip())


# -- UUID5 deterministe -------------------------------------------------------

def item_to_point_id(item: dict, domain: str) -> str:
    title = str(item.get("title") or item.get("id") or "unknown").lower().strip()
    seed = "{}:{}".format(domain, title)
    return str(uuid.uuid5(_UUID_NAMESPACE, seed))


# -- Construction du payload -------------------------------------------------

def build_payload(item: dict, domain: str, embedding_text: str) -> dict:
    return {
        "domain": domain,
        "source": str(item.get("source") or "unknown"),
        "reliability_score": float(item.get("_reliability_score") or 0.0),
        "reliability_level": str(item.get("_reliability_level") or "Incomplet"),
        "title": str(item.get("title") or ""),
        "title_japanese": str(item.get("title_japanese") or item.get("title_native") or ""),
        "year": int(item["year"]) if item.get("year") and str(item["year"]).isdigit() else None,
        "status": str(item.get("status") or ""),
        "authors": item.get("authors") or [],
        "genres": item.get("genres") or item.get("tags") or [],
        "studios": item.get("studios") or [],
        "score": float(item["score"]) if item.get("score") else None,
        "all_sources": item.get("all_sources") or [{"source": item.get("source", ""), "source_url": item.get("source_url", "")}],
        "source_url": str(item.get("source_url") or ""),
        "embedding_text_preview": embedding_text[:200],
        "indexed_at": datetime.now(timezone.utc).isoformat(),
    }


# -- Gestion de la collection ------------------------------------------------

def ensure_collection(client, collection_name: str, vector_size: int = VECTOR_SIZE) -> bool:
    from qdrant_client.models import (
        Distance, VectorParams,
        PayloadSchemaType, TextIndexParams, TokenizerType,
    )
    existing = [c.name for c in client.get_collections().collections]
    if collection_name in existing:
        info = client.get_collection(collection_name)
        existing_size = info.config.params.vectors.size
        if existing_size != vector_size:
            raise ValueError(
                "Collection '{}' existe avec vector_size={}, attendu {}.".format(
                    collection_name, existing_size, vector_size))
        log.info("Collection '%s' existante — reuse", collection_name)
        return False
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    try:
        client.create_payload_index(collection_name, "domain", PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name, "source", PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name, "reliability_level", PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name, "reliability_score", PayloadSchemaType.FLOAT)
        client.create_payload_index(collection_name, "status", PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name, "year", PayloadSchemaType.INTEGER)
        client.create_payload_index(
            collection_name, "title",
            field_schema=TextIndexParams(type="text", tokenizer=TokenizerType.WORD, lowercase=True),
        )
    except Exception as exc:
        log.warning("Certains index payload ont echoue (non bloquant) : %s", exc)
    return True


# -- Upsert en batch ---------------------------------------------------------

def upsert_batch(client, collection_name: str, points: list, batch_size: int = DEFAULT_BATCH_SIZE) -> dict:
    from qdrant_client.models import PointStruct
    total = len(points)
    success = 0
    failed = 0
    for start in range(0, total, batch_size):
        batch = points[start:start + batch_size]
        try:
            client.upsert(collection_name=collection_name, points=batch)
            success += len(batch)
        except Exception as exc:
            failed += len(batch)
            log.error("Upsert batch echec : %s", exc)
    return {"total": total, "success": success, "failed": failed}


# -- Pipeline principal ------------------------------------------------------

def run_indexation(items, domain, collection_name, qdrant_url, embedder_mode, batch_size, dry_run):
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct
    client = QdrantClient(url=qdrant_url, timeout=10)
    if not dry_run:
        try:
            client.get_collections()
        except Exception as exc:
            raise ConnectionError("Impossible de joindre Qdrant ({}) : {}".format(qdrant_url, exc)) from exc
    embedder, backend_name = get_embedder(embedder_mode)
    vector_size = VECTOR_SIZE
    collection_created = None if dry_run else ensure_collection(client, collection_name, vector_size)
    embedding_texts = [build_embedding_text(item) for item in items]
    point_ids = [item_to_point_id(item, domain) for item in items]
    vectors = embedder.encode(embedding_texts, batch_size=batch_size, show_progress_bar=False)
    points = []
    for item, vec, pid, emb_text in zip(items, vectors, point_ids, embedding_texts):
        payload = build_payload(item, domain, emb_text)
        points.append(PointStruct(id=pid, vector=vec.tolist(), payload=payload))
    if dry_run:
        sample = [{"id": p.id, "title": p.payload.get("title"), "vector_preview": p.vector[:5]} for p in points[:3]]
        return {"mode": "dry_run", "would_index": len(points), "collection": collection_name,
                "qdrant_url": qdrant_url, "embedder": backend_name, "vector_size": vector_size, "sample_points": sample}
    upsert_stats = upsert_batch(client, collection_name, points, batch_size)
    col_info = client.get_collection(collection_name)
    return {"mode": "indexation", "collection": collection_name, "qdrant_url": qdrant_url,
            "embedder": backend_name, "vector_size": vector_size, "collection_created": collection_created,
            "upsert_stats": upsert_stats, "collection_total_vectors": col_info.vectors_count or 0}


# -- Output contract ---------------------------------------------------------

def build_output(run_result, items_count, dry_run):
    if dry_run:
        summary = "[DRY-RUN] {} items seraient indexes dans '{}'".format(
            run_result["would_index"], run_result["collection"])
    else:
        stats = run_result.get("upsert_stats", {})
        summary = "{}/{} items indexes dans '{}'".format(
            stats.get("success", 0), items_count, run_result["collection"])
    return {
        "status": "dry_run" if dry_run else "success",
        "skill_name": "deep-research-core:index_qdrant",
        "skill_version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output": {"summary": summary, "data": run_result, "next_steps": []},
    }


# -- CLI ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Indexation Qdrant — TricorderKit")
    parser.add_argument("--input", "-i")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    parser.add_argument("--embedder", default="auto", choices=["auto", "sentence", "hash"])
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--domain", default="manga", choices=["manga", "anime", "github", "publishers"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default="json", choices=["json", "table"])
    args = parser.parse_args()
    if args.input:
        with open(args.input, encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raw = json.load(sys.stdin)
    if isinstance(raw, list):
        items = raw
        domain = args.domain
    elif isinstance(raw, dict) and "output" in raw:
        items = raw["output"]["data"].get("items", [])
        domain = raw["output"]["data"].get("domain", args.domain)
    else:
        log.error("Format d'entree non reconnu")
        sys.exit(1)
    if not items:
        sys.exit(0)
    try:
        run_result = run_indexation(items, domain, args.collection, args.qdrant_url,
                                     args.embedder, args.batch_size, args.dry_run)
    except (ConnectionError, ValueError) as exc:
        log.error("%s", exc)
        sys.exit(2)
    output = build_output(run_result, len(items), args.dry_run)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
