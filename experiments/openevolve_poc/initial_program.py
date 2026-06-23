#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
initial_program.py — programme ÉVOLUABLE (PoC OpenEvolve / autoresearch pour TricorderKit).

C'est le fichier que l'agent évolutionnaire (OpenEvolve) édite pour MAXIMISER le F1 de dédup,
exactement comme `train.py` dans karpathy/autoresearch — mais sur du CPU, sans GPU, et sur une
métrique de dédup au lieu du val_bpb. La logique lourde (embeddings, fuzzy) est réutilisée depuis
`experiments/dedup_embeddings/` (pas de duplication). Seuls les PARAMÈTRES (et, si l'agent le veut,
la logique de `predict`) sont dans le bloc EVOLVE ci-dessous.
"""
import os
import sys

# Réutilise la mécanique déjà testée du PoC #2 (blocking embeddings + fuzzy).
_DEDUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dedup_embeddings")
sys.path.insert(0, _DEDUP)
from dedup_embeddings import (char_ngram_embedding, cosine,  # noqa: E402
                              levenshtein_ratio)

# EVOLVE-BLOCK-START
# Paramètres que l'optimiseur fait varier (valeurs de départ = baseline manuelle du PoC #2).
BLOCK_THRESHOLD = 0.35   # seuil cosinus du blocking embeddings
FUZZY_THRESHOLD = 0.70   # seuil du ratio fuzzy (Levenshtein) pour décider d'un doublon
TOPK = 4                 # nb de voisins candidats par titre
# EVOLVE-BLOCK-END


def predict(titles: dict):
    """Pipeline dédup hybride -> ensemble des paires de doublons prédites (frozenset d'ids)."""
    ids = list(titles)
    vecs = {i: char_ngram_embedding(titles[i]) for i in ids}
    cand = set()
    for i in ids:
        sims = sorted(((cosine(vecs[i], vecs[j]), j) for j in ids if j != i), reverse=True)
        for sim, j in sims[:TOPK]:
            if sim >= BLOCK_THRESHOLD:
                cand.add(frozenset((i, j)))
    predicted = set()
    for pair in cand:
        a, b = tuple(pair)
        if levenshtein_ratio(titles[a], titles[b]) >= FUZZY_THRESHOLD:
            predicted.add(pair)
    return predicted
