#!/usr/bin/env python3
"""
experiments/dedup_embeddings — PoC #2 (god-mode) : blocking par embeddings pour la dédup.

PoC ISOLÉ, hors-ligne, sans dépendance lourde. Ne touche pas au cœur, n'écrit aucun vault.
Objectif : prouver que l'état de l'art entity-resolution = pipeline HYBRIDE
  (1) BLOCKING par embeddings (top-k plus proches voisins) pour ne garder que des paires candidates,
  (2) étage FUZZY existant (lexical) sur ces seules paires → décision finale,
et qu'à budget de comparaisons réduit on conserve (voire améliore) le rappel face au fuzzy exhaustif.

Deux moteurs (même esprit que ragas_eval.py / temporal_memory.py) :
  - proxy (défaut) : embedding par n-grammes de caractères (hashing), déterministe, hors-ligne.
    Démontre la MÉCANIQUE blocking→fuzzy et la mesure ; bon pour les variantes lexicales.
  - nomic (optionnel) : vrais embeddings (nomic-embed-text via EMBED_URL, convention Ollama/gateway).
    Requis pour le rappel SÉMANTIQUE / cross-script (ex. romaji ↔ kana) — repli proxy si indispo.

Métriques : recall / precision / F1 et NOMBRE DE COMPARAISONS fuzzy, pour :
  (a) baseline fuzzy EXHAUSTIF (toutes les paires, O(n²)),
  (b) blocking embeddings + fuzzy (paires candidates seulement).

Usage :
    python dedup_embeddings.py --selftest
    python dedup_embeddings.py --dataset sample_titles.jsonl
    python dedup_embeddings.py --dataset sample_titles.jsonl --engine nomic --topk 5 --block 0.45

Format JSONL : {"type":"title","id":1,"text":"..."} et {"type":"dupe","a":1,"b":2} (vérité terrain).
Réf. : BlockingPy (arXiv 2504.04266), record linkage w/ embeddings (Cambridge) — cf. radar.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import zlib
from itertools import combinations
from typing import Optional

# ----------------------------------------------------------------------------- normalisation
def normalize(text: str) -> str:
    return " ".join(text.lower().replace("-", " ").replace("_", " ").split())


# ----------------------------------------------------------------------------- embedding proxy
_DIM = 256


def char_ngram_embedding(text: str, n_values=(2, 3)) -> list:
    """Embedding déterministe hors-ligne : n-grammes de caractères -> vecteur creux hashé, L2-normalisé."""
    vec = [0.0] * _DIM
    t = f" {normalize(text)} "
    for n in n_values:
        for i in range(len(t) - n + 1):
            gram = t[i:i + n]
            vec[zlib.crc32(gram.encode("utf-8")) % _DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm else vec


def cosine(a: list, b: list) -> float:
    return sum(x * y for x, y in zip(a, b))


def build_nomic_embedder():
    """Optionnel : embeddings nomic via EMBED_URL (Ollama/gateway). Repli proxy si indispo."""
    url = os.environ.get("EMBED_URL")
    if not url:
        return None
    try:
        import urllib.request  # noqa: F401
    except Exception:
        return None
    print("[dedup_embeddings] EMBED_URL détecté mais client non câblé dans ce PoC isolé "
          "-> repli embedding proxy (n-grammes).", file=sys.stderr)
    return None  # câblage réel = sur promotion (DEC), après validation de la mesure.


# ----------------------------------------------------------------------------- étage fuzzy
def levenshtein_ratio(a: str, b: str) -> float:
    """Ratio de similarité [0..1] basé sur la distance de Levenshtein (substitut RapidFuzz, hors-ligne)."""
    a, b = normalize(a), normalize(b)
    if not a and not b:
        return 1.0
    la, lb = len(a), len(b)
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    dist = prev[lb]
    return 1.0 - dist / max(la, lb) if max(la, lb) else 1.0


# ----------------------------------------------------------------------------- pipeline
def load_dataset(path: str):
    titles, dupes = {}, set()
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = json.loads(line)
            if row.get("type") == "dupe":
                dupes.add(frozenset((row["a"], row["b"])))
            else:
                titles[row["id"]] = row["text"]
    return titles, dupes


def fuzzy_decide(titles: dict, pairs, fuzzy_threshold: float):
    """Applique l'étage fuzzy aux paires candidates -> ensemble de doublons prédits."""
    predicted = set()
    for i, j in pairs:
        if levenshtein_ratio(titles[i], titles[j]) >= fuzzy_threshold:
            predicted.add(frozenset((i, j)))
    return predicted


def score(predicted, truth) -> dict:
    tp = len(predicted & truth)
    fp = len(predicted - truth)
    fn = len(truth - predicted)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}


def run(titles: dict, truth, embedder, topk: int, block_threshold: float,
        fuzzy_threshold: float) -> dict:
    ids = list(titles)

    # (a) Baseline : fuzzy exhaustif sur toutes les paires.
    all_pairs = list(combinations(ids, 2))
    base_pred = fuzzy_decide(titles, all_pairs, fuzzy_threshold)
    base = score(base_pred, truth)
    base["comparisons"] = len(all_pairs)

    # (b) Blocking embeddings : top-k voisins par cosinus >= seuil -> paires candidates.
    vecs = {i: embedder(titles[i]) for i in ids}
    cand = set()
    for i in ids:
        sims = sorted(((cosine(vecs[i], vecs[j]), j) for j in ids if j != i), reverse=True)
        for sim, j in sims[:topk]:
            if sim >= block_threshold:
                cand.add(frozenset((i, j)))
    cand_pairs = [tuple(p) for p in cand]
    blk_pred = fuzzy_decide(titles, cand_pairs, fuzzy_threshold)
    blk = score(blk_pred, truth)
    blk["comparisons"] = len(cand_pairs)

    reduction = 0.0 if not all_pairs else (1 - len(cand_pairs) / len(all_pairs))
    return {
        "n_titles": len(ids),
        "n_truth_dupes": len(truth),
        "baseline_fuzzy_exhaustif": base,
        "blocking_embeddings_plus_fuzzy": blk,
        "comparison_reduction_ratio": round(reduction, 3),
    }


# ----------------------------------------------------------------------------- selftest
_SELFTEST_TITLES = {
    1: "Tokyo Revengers",
    2: "Tokyo Rebengers",          # faute de frappe -> doublon de 1
    3: "Toukyou Revengers",        # variante romaji -> doublon de 1
    4: "One Piece",
    5: "One   Piece!",             # ponctuation/espaces -> doublon de 4
    6: "Naruto",
    7: "Bleach",
    8: "Blaech",                   # faute -> doublon de 7
}
_SELFTEST_DUPES = {frozenset((1, 2)), frozenset((1, 3)), frozenset((4, 5)), frozenset((7, 8))}


def selftest() -> int:
    res = run(_SELFTEST_TITLES, _SELFTEST_DUPES, char_ngram_embedding,
              topk=4, block_threshold=0.35, fuzzy_threshold=0.7)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    blk = res["blocking_embeddings_plus_fuzzy"]
    base = res["baseline_fuzzy_exhaustif"]
    # Revendication mesurée : le blocking atteint LA MÊME qualité que le fuzzy exhaustif
    # (rappel + F1 identiques) pour une fraction des comparaisons. La variante romaji
    # (1,3) reste hors de portée du lexical hors-ligne -> motive le moteur sémantique `nomic`.
    ok_recall = abs(blk["recall"] - base["recall"]) < 1e-9
    ok_f1 = abs(blk["f1"] - base["f1"]) < 1e-9
    ok_reduction = res["comparison_reduction_ratio"] > 0.5
    if ok_recall and ok_f1 and ok_reduction:
        print(f"\n[selftest] OK — qualité égale au fuzzy exhaustif "
              f"(rappel={blk['recall']}, F1={blk['f1']}) pour "
              f"-{res['comparison_reduction_ratio']*100:.0f}% de comparaisons. "
              f"NB : variante romaji non captée par le proxy lexical -> moteur `nomic`.")
        return 0
    print("\n[selftest] ÉCHEC — vérifier blocking/seuils.", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="PoC #2 dédup par embeddings (god-mode).")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dataset", help="JSONL titres + paires vérité-terrain")
    ap.add_argument("--engine", choices=["proxy", "nomic"], default="proxy")
    ap.add_argument("--topk", type=int, default=4)
    ap.add_argument("--block", type=float, default=0.35, help="seuil cosinus blocking")
    ap.add_argument("--fuzzy", type=float, default=0.7, help="seuil ratio fuzzy")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.dataset:
        ap.print_help()
        return 2

    embedder = char_ngram_embedding
    if args.engine == "nomic":
        nomic = build_nomic_embedder()
        if nomic is not None:
            embedder = nomic

    titles, truth = load_dataset(args.dataset)
    res = run(titles, truth, embedder, args.topk, args.block, args.fuzzy)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
