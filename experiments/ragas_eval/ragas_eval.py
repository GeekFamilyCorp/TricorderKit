#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ragas_eval.py — PoC #1 (god-mode radar) : évaluation RAG pour eval-lab.

Mesure objective de la qualité RAG, SANS ground-truth obligatoire :
  - faithfulness   : la réponse est-elle ancrée dans les contextes récupérés ?
  - answer_relevancy : la réponse répond-elle à la question ?
  - context_precision : les contextes récupérés sont-ils pertinents ?

Deux moteurs :
  - `--engine ragas`  : vrai RAGAS (LLM-as-judge) si `pip install ragas` + LLM configuré
                        (env REFLECTION_LLM_URL/MODEL, convention reflection.py). Lazy-import.
  - `--engine proxy`  : proxy DÉTERMINISTE stdlib (overlap lexical), tourne hors-ligne, sans dépendance.
                        Sert de garde-fou/baseline + selftest. (défaut)

Entrée : JSONL, 1 objet/ligne : {"question","contexts":[...],"answer","ground_truth"(optionnel)}.
Sortie : rapport JSON + résumé console. ISOLÉ (experiments/) — n'écrit pas le vault, ne touche pas au cœur.

Usage :
    python ragas_eval.py --selftest
    python ragas_eval.py --dataset sample_qa.jsonl                 # proxy
    python ragas_eval.py --dataset sample_qa.jsonl --engine ragas  # vrai RAGAS si dispo
"""
from __future__ import annotations
import argparse, json, os, re, sys
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for _s in ("stdout", "stderr"):
    try: getattr(sys, _s).reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

HERE = Path(__file__).resolve().parent
_WORD = re.compile(r"\w+", re.UNICODE)


def toks(s: str) -> set:
    return {w.lower() for w in _WORD.findall(s or "") if len(w) > 2}


def overlap(a: str, b: str) -> float:
    """Jaccard-lite : part des tokens de `a` couverts par `b`."""
    ta, tb = toks(a), toks(b)
    if not ta:
        return 0.0
    return round(len(ta & tb) / len(ta), 3)


def proxy_metrics(item: dict) -> dict:
    q = item.get("question", "")
    ctx = " ".join(item.get("contexts", []) or [])
    ans = item.get("answer", "")
    # faithfulness ~ part de la reponse couverte par les contextes
    faith = overlap(ans, ctx)
    # answer_relevancy ~ part de la question couverte par la reponse
    rel = overlap(q, ans)
    # context_precision ~ part des contextes utiles a la reponse
    cp = overlap(ctx, ans + " " + q)
    return {"faithfulness": faith, "answer_relevancy": rel, "context_precision": cp}


def run_proxy(items: list) -> dict:
    rows = [{**proxy_metrics(it), "question": it.get("question", "")[:80]} for it in items]
    keys = ("faithfulness", "answer_relevancy", "context_precision")
    agg = {k: round(sum(r[k] for r in rows) / max(len(rows), 1), 3) for k in keys}
    return {"engine": "proxy", "n": len(rows), "aggregate": agg, "rows": rows}


def run_ragas(items: list) -> dict:
    """Vrai RAGAS si installe + LLM configure. Sinon lève une exception explicite."""
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision
    except Exception as e:
        raise RuntimeError(f"RAGAS indisponible ({e}). `pip install ragas datasets` + configurer un LLM-juge.")
    url = os.environ.get("REFLECTION_LLM_URL")
    if not url:
        raise RuntimeError("LLM-juge non configuré (REFLECTION_LLM_URL). Voir reflection.py (Ollama/gateway).")
    ds = Dataset.from_list([{
        "question": it.get("question", ""),
        "contexts": it.get("contexts", []) or [],
        "answer": it.get("answer", ""),
        "ground_truth": it.get("ground_truth", ""),
    } for it in items])
    res = evaluate(ds, metrics=[faithfulness, answer_relevancy, context_precision])
    return {"engine": "ragas", "n": len(items), "aggregate": dict(res), "rows": None}


def load_jsonl(p: Path) -> list:
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def selftest() -> int:
    sample = [
        {"question": "Quel editeur publie Chainsaw Man ?",
         "contexts": ["Chainsaw Man est publie par Shueisha dans le Weekly Shonen Jump."],
         "answer": "Chainsaw Man est publie par Shueisha."},
        {"question": "Capitale du Japon ?",
         "contexts": ["Le Japon est un archipel."],
         "answer": "La capitale est Tokyo."},  # contexte non pertinent -> faithfulness basse
    ]
    r = run_proxy(sample)
    assert r["n"] == 2 and set(r["aggregate"]) == {"faithfulness", "answer_relevancy", "context_precision"}
    assert r["rows"][0]["faithfulness"] > r["rows"][1]["faithfulness"], "le cas ancre doit scorer plus haut"
    print("[selftest] OK — proxy déterministe, faithfulness discrimine ancré vs non-ancré.")
    print(json.dumps(r["aggregate"], ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Éval RAG (RAGAS ou proxy déterministe) — PoC eval-lab.")
    ap.add_argument("--dataset", type=str, help="JSONL question/contexts/answer")
    ap.add_argument("--engine", choices=["proxy", "ragas"], default="proxy")
    ap.add_argument("--out", type=str, default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.dataset:
        print("--dataset requis (ou --selftest)."); return 2
    items = load_jsonl(Path(a.dataset))
    try:
        report = run_ragas(items) if a.engine == "ragas" else run_proxy(items)
    except RuntimeError as e:
        print(f"[ragas indisponible] repli proxy. Détail: {e}")
        report = run_proxy(items)
    out = Path(a.out) if a.out else HERE / "ragas_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] {report['engine']} sur {report['n']} items -> {report['aggregate']}")
    print(f"     rapport: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
