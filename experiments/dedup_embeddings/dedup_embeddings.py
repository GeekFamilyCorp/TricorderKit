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
    """Vrais embeddings via Ollama (nomic-embed-text). Repli proxy (None) si indisponible.

    EMBED_URL (defaut http://localhost:11434) + EMBED_MODEL (defaut nomic-embed-text).
    Sonde la connectivite une fois ; renvoie un embedder L2-normalise (meme interface que le proxy).
    """
    import urllib.request
    base = os.environ.get("EMBED_URL", "http://localhost:11434").rstrip("/")
    model = os.environ.get("EMBED_MODEL", "nomic-embed-text")
    cache = {}

    def _embed(text):
        if text in cache:
            return cache[text]
        body = json.dumps({"model": model, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(base + "/api/embeddings", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            v = json.loads(r.read().decode("utf-8"))["embedding"]
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        v = [x / norm for x in v]
        cache[text] = v
        return v

    try:
        _embed("probe")          # sonde
    except Exception as exc:
        print(f"[dedup_embeddings] nomic indisponible ({base}, {model}) -> repli proxy : {exc!r}",
              file=sys.stderr)
        return None
    return _embed


# ----------------------------------------------------------------------------- décision sémantique
def run_semantic(titles, truth, embedder, topk, block_threshold, sem_threshold) -> dict:
    """Blocking par cosinus PUIS décision SÉMANTIQUE (cosinus >= seuil) — capte le cross-script
    là où la décision lexicale (Levenshtein) échoue (ex. romaji/kana vs kanji)."""
    ids = list(titles)
    vecs = {i: embedder(titles[i]) for i in ids}
    cand = set()
    for i in ids:
        sims = sorted(((cosine(vecs[i], vecs[j]), j) for j in ids if j != i), reverse=True)
        for sim, j in sims[:topk]:
            if sim >= block_threshold:
                cand.add(frozenset((i, j)))
    predicted = {p for p in cand
                 if cosine(vecs[tuple(p)[0]], vecs[tuple(p)[1]]) >= sem_threshold}
    m = score(predicted, truth)
    m["candidates"] = len(cand)
    m["_predicted"] = predicted
    return m


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
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # JP/kana dans la sortie (consoles cp1252)
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="PoC #2 dédup par embeddings (god-mode).")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dataset", help="JSONL titres + paires vérité-terrain")
    ap.add_argument("--engine", choices=["proxy", "nomic"], default="proxy")
    ap.add_argument("--topk", type=int, default=4)
    ap.add_argument("--block", type=float, default=0.35, help="seuil cosinus blocking")
    ap.add_argument("--fuzzy", type=float, default=0.7, help="seuil ratio fuzzy")
    ap.add_argument("--sem", type=float, default=0.6, help="seuil cosinus décision sémantique (nomic)")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.dataset:
        ap.print_help()
        return 2

    titles, truth = load_dataset(args.dataset)

    if args.engine == "nomic":
        nomic = build_nomic_embedder()
        if nomic is None:
            print("[dedup_embeddings] moteur nomic indisponible — lancer Ollama (nomic-embed-text) "
                  "ou définir EMBED_URL.", file=sys.stderr)
            return 3
        # baseline = proxy LEXICAL (char n-grammes + fuzzy), pour mesurer l'apport sémantique.
        lex = run(titles, truth, char_ngram_embedding, args.topk, 0.2, 0.85)["blocking_embeddings_plus_fuzzy"]
        # nomic = embeddings réels + décision SÉMANTIQUE (cosinus).
        sem = run_semantic(titles, truth, nomic, args.topk, max(0.0, args.block - 0.05), args.sem)
        # Reconstruit l'ensemble prédit du proxy lexical pour le diff (paires gagnées par nomic).
        ids = list(titles)
        lex_set = set()
        vecsp = {i: char_ngram_embedding(titles[i]) for i in ids}
        candp = set()
        for i in ids:
            sims = sorted(((cosine(vecsp[i], vecsp[j]), j) for j in ids if j != i), reverse=True)
            for s, j in sims[:args.topk]:
                if s >= 0.2:
                    candp.add(frozenset((i, j)))
        for p in candp:
            a, b = tuple(p)
            if levenshtein_ratio(titles[a], titles[b]) >= 0.85:
                lex_set.add(p)
        gained = [(titles[tuple(p)[0]], titles[tuple(p)[1]])
                  for p in (sem["_predicted"] & truth) - lex_set]
        out = {
            "n_titles": len(titles), "n_truth_dupes": len(truth),
            "lexical_proxy": {k: lex[k] for k in ("recall", "precision", "f1")},
            "nomic_semantic": {k: sem[k] for k in ("recall", "precision", "f1", "candidates")},
            "pairs_recovered_by_nomic_only": gained,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    res = run(titles, truth, char_ngram_embedding, args.topk, args.block, args.fuzzy)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
