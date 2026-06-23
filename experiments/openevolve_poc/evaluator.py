#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluator.py — évaluateur OpenEvolve (PoC autoresearch pour TricorderKit).

OpenEvolve appelle `evaluate(program_path)` après chaque mutation et lit les métriques renvoyées :
il fait évoluer `initial_program.py` pour MAXIMISER `combined_score` (= F1 de dédup).
Même rôle que la mesure `val_bpb` d'autoresearch, mais sur une métrique métier, sur CPU.

L'évaluateur est aussi utilisable hors OpenEvolve (cf. search_baseline.py) : c'est la brique
déterministe qui rend la boucle « propose -> mesure -> garde/jette » possible sans GPU ni LLM.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_DEDUP = os.path.join(HERE, "..", "dedup_embeddings")
sys.path.insert(0, _DEDUP)
from dedup_embeddings import load_dataset, score  # noqa: E402

DATASET = os.path.join(_DEDUP, "sample_titles.jsonl")


def _load_program(program_path: str):
    spec = importlib.util.spec_from_file_location("evolved_program", program_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def evaluate(program_path: str) -> dict:
    """Contrat OpenEvolve : renvoie un dict de métriques (dont combined_score à maximiser)."""
    titles, truth = load_dataset(DATASET)
    try:
        program = _load_program(program_path)
        predicted = program.predict(titles)
    except Exception as exc:  # un programme cassé = score nul (l'évolution l'écarte)
        return {"combined_score": 0.0, "error": repr(exc)}
    m = score(predicted, truth)
    # combined_score = F1 (objectif). On expose aussi recall/precision comme dimensions.
    return {"combined_score": m["f1"], "f1": m["f1"],
            "recall": m["recall"], "precision": m["precision"],
            "n_predicted": len(predicted), "n_truth": len(truth)}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "initial_program.py")
    import json
    print(json.dumps(evaluate(path), ensure_ascii=False, indent=2))
