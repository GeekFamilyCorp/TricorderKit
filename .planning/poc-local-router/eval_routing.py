#!/usr/bin/env python3
# Eval harness du routage (G2). ASCII-only volontairement (robustesse mount).
# Mesure la justesse du routage sur un jeu de prompts etiquetes.
#
# Deux classifieurs:
#   - "keyword" (defaut): reference deterministe SANS LLM. Score chaque profil par
#     recouvrement de mots-cles de son champ "when". Sert de baseline + regression.
#   - "ollama": branche le vrai SLM via local_router.route() si Ollama est dispo.
#
# Usage:
#   python3 eval_routing.py                      # baseline keyword sur le set fourni
#   python3 eval_routing.py --classifier ollama  # via SLM local (si installe)
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
STOP = {"de", "la", "le", "les", "des", "du", "un", "une", "et", "ou", "a", "au",
        "aux", "en", "sur", "dans", "pour", "ce", "cette", "mes", "ma", "mon"}


def _load_router():
    spec = importlib.util.spec_from_file_location("local_router", HERE / "local_router.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tokenize(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 2}


def keyword_classifier(prompt: str, profiles: dict) -> str:
    """Baseline deterministe : profil dont le 'when' recouvre le plus le prompt."""
    p_tokens = tokenize(prompt)
    best, best_score = profiles["default_profile"], -1
    for key, prof in profiles["profiles"].items():
        score = len(p_tokens & tokenize(prof.get("when", "")))
        if score > best_score:
            best, best_score = key, score
    return best


def run_eval(eval_set: list, profiles: dict, classify) -> dict:
    rows, ok = [], 0
    for case in eval_set:
        got = classify(case["prompt"], profiles)
        hit = got == case["expected"]
        ok += hit
        rows.append({"prompt": case["prompt"], "expected": case["expected"], "got": got, "ok": hit})
    return {"total": len(eval_set), "passed": ok,
            "accuracy": round(ok / len(eval_set), 3) if eval_set else 0.0, "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description="Eval du routage (G2).")
    ap.add_argument("--profiles", default=str(HERE / "profiles.json"))
    ap.add_argument("--set", default=str(HERE / "routing_eval_set.json"))
    ap.add_argument("--classifier", choices=["keyword", "ollama"], default="keyword")
    args = ap.parse_args()

    lr = _load_router()
    profiles = lr.load_profiles(Path(args.profiles))
    eval_set = json.loads(Path(args.set).read_text(encoding="utf-8"))

    if args.classifier == "ollama":
        def classify(prompt, profs):
            return lr.route(prompt, profs, lr.DEFAULT_MODEL)["profile"]
    else:
        classify = keyword_classifier

    report = run_eval(eval_set, profiles, classify)
    print(f"[eval] classifieur={args.classifier} · {report['passed']}/{report['total']} "
          f"· accuracy={report['accuracy']}")
    for r in report["rows"]:
        mark = "OK " if r["ok"] else "XX "
        print(f"  {mark}{r['got']:<9} (attendu {r['expected']:<9}) :: {r['prompt'][:60]}")
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
