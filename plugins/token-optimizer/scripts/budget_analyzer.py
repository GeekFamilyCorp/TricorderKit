#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
budget_analyzer.py — Moteur d'analyse du budget tokens (Lot 1).

Lit ~/.token-optimizer/budget.json (+ history/) et produit :
- repartition par modele (equivalents-Haiku, calibres)
- tendance : conso/jour, projection fin de mois, ETA des seuils 50/80/95%
- detection de gaspillage (heuristiques sur events[])
- opportunites d'economie chiffrees (offload local / reroute Haiku)
- recommandations (auto-applicables vs a proposer)

Usage:
    python3 budget_analyzer.py                 # rapport humain
    python3 budget_analyzer.py --json          # sortie machine (optimizer/dashboard)
    python3 budget_analyzer.py --recommend     # uniquement les recommandations
"""

import argparse
import calendar
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

HOME = Path(os.path.expanduser("~")) / ".token-optimizer"
BUDGET_FILE = HOME / "budget.json"
HISTORY_DIR = HOME / "history"

WEIGHTS = {
    "haiku":  {"input": 1,  "output": 1},
    "sonnet": {"input": 3,  "output": 5},
    "opus":   {"input": 15, "output": 25},
}
TIER_OF = {"haiku": "T1", "sonnet": "T2", "opus": "T3"}


def equiv(model, inp, out):
    w = WEIGHTS.get(model, WEIGHTS["sonnet"])
    return inp * w["input"] + out * w["output"]


def load_budget():
    if not BUDGET_FILE.exists():
        return None
    try:
        return json.loads(BUDGET_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def total_equiv(consumption):
    return sum(equiv(m, c.get("input", 0), c.get("output", 0)) for m, c in consumption.items())


def analyze(data: dict) -> dict:
    cfg = data.get("config", {})
    cal = float(cfg.get("calibration_factor", 1.0) or 1.0)
    budget = int(cfg.get("total_monthly_tokens", 20_000_000))
    thresholds = cfg.get("alerts", [0.50, 0.80, 0.95])
    consumption = data.get("consumption", {})
    events = data.get("events", [])
    offload = data.get("offload", {})

    used_raw = total_equiv(consumption)
    used = used_raw * cal
    ratio = used / budget if budget else 0.0

    # --- Tendance / projection ---
    now = datetime.now(timezone.utc)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    elapsed = now.day - 1 + (now.hour / 24.0)
    elapsed = max(elapsed, 0.01)
    daily_rate = used / elapsed
    projected_eom = daily_rate * days_in_month
    projected_ratio = projected_eom / budget if budget else 0.0

    def eta_days(th):
        target = th * budget
        if used >= target:
            return 0
        if daily_rate <= 0:
            return None
        return round((target - used) / daily_rate, 1)

    eta = {f"{int(t*100)}%": eta_days(t) for t in thresholds}

    # --- Repartition par modele / tier ---
    by_model = {}
    for m in WEIGHTS:
        c = consumption.get(m, {})
        e = equiv(m, c.get("input", 0), c.get("output", 0)) * cal
        by_model[m] = {"tier": TIER_OF[m], "equivalent": round(e),
                       "share": round(e / used, 3) if used else 0.0,
                       "raw_input": c.get("input", 0), "raw_output": c.get("output", 0)}

    # --- Heuristiques de gaspillage (sur events) ---
    waste = []
    opus_small = [e for e in events if e.get("model") == "opus"
                  and (e.get("in", 0) + e.get("out", 0)) < 4000]
    if opus_small:
        waste.append({
            "type": "opus_sous_utilise",
            "count": len(opus_small),
            "detail": "Taches Opus de petite taille (<4k tokens) potentiellement faisables en Sonnet/Haiku.",
            "est_saving_equiv": round(sum(equiv("opus", e.get("in", 0), e.get("out", 0))
                                          - equiv("sonnet", e.get("in", 0), e.get("out", 0))
                                          for e in opus_small) * cal),
        })

    big_out = [e for e in events if e.get("model") in ("haiku", "sonnet") and e.get("out", 0) > 3000]
    if big_out:
        waste.append({
            "type": "sortie_longue_sans_compression",
            "count": len(big_out),
            "detail": "Sorties longues (>3k tokens out) sur T1/T2 : candidates au mode caveman.",
            "est_saving_equiv": round(sum(equiv(e["model"], 0, int(e.get("out", 0) * 0.5))
                                          for e in big_out) * cal),
        })

    # Taches repetitives (meme model + taille arrondie) -> offload local
    buckets = defaultdict(list)
    for e in events:
        if e.get("model") == "haiku":
            key = (e.get("model"), round((e.get("in", 0) + e.get("out", 0)) / 500))
            buckets[key].append(e)
    repetitive = [v for v in buckets.values() if len(v) >= 5]
    if repetitive:
        n = sum(len(v) for v in repetitive)
        saved = round(sum(equiv("haiku", e.get("in", 0), e.get("out", 0))
                          for v in repetitive for e in v) * cal)
        waste.append({
            "type": "taches_repetitives_offload_local",
            "count": n,
            "detail": "Taches Haiku repetitives : candidates a l'offload local (Hermes/Ollama), cout Claude ~0.",
            "est_saving_equiv": saved,
        })

    # --- Recommandations (auto-applicables vs propose) ---
    recommendations = {"auto": [], "propose": []}
    if ratio >= thresholds[1]:
        recommendations["auto"].append("Activer le reroute Haiku agressif (budget > 80%).")
    if ratio >= thresholds[2]:
        recommendations["auto"].append("Forcer Haiku + caveman ultra (budget > 95%).")
    if projected_ratio > 1.0 and ratio < thresholds[1]:
        recommendations["auto"].append(
            f"Projection fin de mois {projected_ratio*100:.0f}% du budget : activer caveman par defaut sur T1/T2.")
    if any(w["type"] == "taches_repetitives_offload_local" for w in waste):
        recommendations["propose"].append("Mettre en place l'offload local (Lot 4) pour les taches Haiku repetitives.")
    if any(w["type"] == "opus_sous_utilise" for w in waste):
        recommendations["propose"].append("Resserrer le seuil T3 (Opus) : trop de petites taches routees en Opus.")

    return {
        "month": data.get("month"),
        "calibration_factor": cal,
        "budget": budget,
        "used_equiv": round(used),
        "used_equiv_raw": round(used_raw),
        "ratio": round(ratio, 4),
        "alert_mode": cfg.get("alert_mode", "informative"),
        "daily_rate_equiv": round(daily_rate),
        "projected_eom_equiv": round(projected_eom),
        "projected_ratio": round(projected_ratio, 4),
        "eta_days_to_threshold": eta,
        "by_model": by_model,
        "events_count": len(events),
        "offload": offload,
        "waste": waste,
        "recommendations": recommendations,
    }


def print_human(a: dict):
    print(f"=== Analyse budget {a['month']} (calibration x{a['calibration_factor']}) ===")
    print(f"Consomme : {a['used_equiv']:,} / {a['budget']:,} eq  ({a['ratio']*100:.1f}%)  [mode: {a['alert_mode']}]")
    print(f"Rythme   : {a['daily_rate_equiv']:,}/jour  ->  projection fin de mois {a['projected_eom_equiv']:,} "
          f"({a['projected_ratio']*100:.0f}% du budget)")
    eta = a["eta_days_to_threshold"]
    eta_txt = ", ".join(f"{k} dans {v}j" if v not in (None, 0) else (f"{k} atteint" if v == 0 else f"{k} n/a")
                        for k, v in eta.items())
    print(f"Seuils   : {eta_txt}")
    print("Repartition :")
    for m, d in a["by_model"].items():
        print(f"  {m:6s} ({d['tier']}): {d['equivalent']:,} eq  ({d['share']*100:.0f}%)")
    off = a.get("offload", {})
    saved = sum(off.get(t, {}).get("tokens_saved_equiv", 0) for t in off)
    if saved:
        print(f"Economies offload deja realisees : {saved:,} eq")
    if a["waste"]:
        print("Gaspillages detectes :")
        for w in a["waste"]:
            print(f"  - [{w['type']}] x{w['count']} -> ~{w['est_saving_equiv']:,} eq economisables. {w['detail']}")
    else:
        print("Gaspillages detectes : aucun (peu de donnees ou conso saine).")
    rec = a["recommendations"]
    if rec["auto"]:
        print("Recommandations AUTO-APPLICABLES :")
        for r in rec["auto"]:
            print(f"  * {r}")
    if rec["propose"]:
        print("Recommandations A PROPOSER :")
        for r in rec["propose"]:
            print(f"  ? {r}")
    if a["events_count"] < 10:
        print(f"\n(Note : seulement {a['events_count']} evenements enregistres — "
              f"l'analyse s'affinera avec l'usage. Calibre apres ~2 semaines.)")


def main():
    ap = argparse.ArgumentParser(description="Analyseur de budget tokens (token-optimizer).")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--recommend", action="store_true", help="N'affiche que les recommandations")
    args = ap.parse_args()

    data = load_budget()
    if data is None:
        msg = {"error": "budget.json introuvable ou illisible. Lance d'abord budget.py status."}
        print(json.dumps(msg) if args.json else msg["error"])
        return

    a = analyze(data)
    if args.json:
        print(json.dumps(a, indent=2, ensure_ascii=False))
    elif args.recommend:
        print(json.dumps(a["recommendations"], indent=2, ensure_ascii=False))
    else:
        print_human(a)


if __name__ == "__main__":
    main()
