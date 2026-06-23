#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search_baseline.py — optimiseur DÉTERMINISTE hors-ligne (proxy de l'évolution OpenEvolve).

Démontre la boucle « propose -> mesure -> garde le meilleur » SANS dépendance ni LLM : il balaie
les paramètres du bloc EVOLVE d'`initial_program.py` et garde ceux qui maximisent le F1 (via le même
évaluateur). C'est la preuve hors-ligne que le harness est prêt ; OpenEvolve remplacera ce balayage
par une vraie évolution LLM (MAP-Elites) capable AUSSI de réécrire la logique, pas seulement les seuils.

Usage :
    python search_baseline.py --selftest
    python search_baseline.py            # rapport complet (baseline vs meilleur trouvé)
"""
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_DEDUP = os.path.join(HERE, "..", "dedup_embeddings")
sys.path.insert(0, _DEDUP)
from dedup_embeddings import load_dataset, score  # noqa: E402

import initial_program as prog  # noqa: E402

DATASET = os.path.join(_DEDUP, "sample_titles.jsonl")
BLOCKS = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
FUZZIES = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]
TOPKS = [2, 3, 4, 5]


def f1_at(titles, truth, block, fuzzy, topk) -> dict:
    prog.BLOCK_THRESHOLD, prog.FUZZY_THRESHOLD, prog.TOPK = block, fuzzy, topk
    return score(prog.predict(titles), truth)


def search():
    titles, truth = load_dataset(DATASET)
    base = f1_at(titles, truth, 0.35, 0.70, 4)  # defaults du bloc EVOLVE
    best = {"f1": -1}
    best_params = None
    evals = 0
    for b in BLOCKS:
        for f in FUZZIES:
            for k in TOPKS:
                evals += 1
                m = f1_at(titles, truth, b, f, k)
                if (m["f1"], m["recall"]) > (best["f1"], best.get("recall", 0)):
                    best, best_params = m, {"BLOCK_THRESHOLD": b, "FUZZY_THRESHOLD": f, "TOPK": k}
    return base, best, best_params, evals


def main() -> int:
    base, best, best_params, evals = search()
    report = {"baseline_default": base, "best_found": best,
              "best_params": best_params, "evaluations": evals}
    selftest = "--selftest" in sys.argv
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if selftest:
        ok = (best["f1"] >= base["f1"] - 1e-9 and best["f1"] >= 0.9 and best_params is not None)
        if ok:
            print(f"\n[selftest] OK — boucle propose/mesure/garde fonctionnelle : "
                  f"meilleur F1={best['f1']} (baseline {base['f1']}) en {evals} évaluations. "
                  f"Harness prêt pour OpenEvolve.")
            return 0
        print("\n[selftest] ÉCHEC — vérifier evaluator/initial_program.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
