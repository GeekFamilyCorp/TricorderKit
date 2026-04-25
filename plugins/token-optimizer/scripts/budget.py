#!/usr/bin/env python3
"""
budget.py — Suivi du budget mensuel de tokens pour token-optimizer.

Stocke la conso dans ~/.token-optimizer/budget.json.
Sous-commandes : status, log, set-budget, reset, prune-history.

Usage:
    python3 budget.py status
    python3 budget.py status --json
    python3 budget.py log --model sonnet --input 3200 --output 1800
    python3 budget.py set-budget --total 30000000 --haiku 0.7 --sonnet 0.25 --opus 0.05
    python3 budget.py reset
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_HOME = Path(os.path.expanduser("~")) / ".token-optimizer"
DEFAULT_FILE = DEFAULT_HOME / "budget.json"
HISTORY_DIR = DEFAULT_HOME / "history"

WEIGHTS = {
    "haiku":  {"input": 1,  "output": 1},
    "sonnet": {"input": 3,  "output": 5},
    "opus":   {"input": 15, "output": 25},
}

DEFAULT_CONFIG = {
    "version": "1.0",
    "month": datetime.utcnow().strftime("%Y-%m"),
    "config": {
        "total_monthly_tokens": 20_000_000,
        "allocation": {"haiku": 0.60, "sonnet": 0.30, "opus": 0.10},
        "alerts": [0.50, 0.80, 0.95],
    },
    "consumption": {
        "haiku":  {"input": 0, "output": 0},
        "sonnet": {"input": 0, "output": 0},
        "opus":   {"input": 0, "output": 0},
    },
}


def ensure_dirs():
    DEFAULT_HOME.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load() -> dict:
    ensure_dirs()
    if not DEFAULT_FILE.exists():
        save(DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))
    with open(DEFAULT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Auto-reset si nouveau mois
    current = datetime.utcnow().strftime("%Y-%m")
    if data.get("month") != current:
        archive = HISTORY_DIR / f"{data.get('month', 'unknown')}.json"
        shutil.copy(DEFAULT_FILE, archive)
        data["month"] = current
        data["consumption"] = {
            m: {"input": 0, "output": 0} for m in WEIGHTS
        }
        save(data)
    return data


def save(data: dict):
    ensure_dirs()
    with open(DEFAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def to_equivalent(data: dict) -> dict:
    """Convertit la conso en tokens equivalents (poids appliques)."""
    out = {}
    for model, cons in data["consumption"].items():
        eq = cons["input"] * WEIGHTS[model]["input"] + cons["output"] * WEIGHTS[model]["output"]
        out[model] = {
            "raw_input": cons["input"],
            "raw_output": cons["output"],
            "equivalent": eq,
        }
    out["total_equivalent"] = sum(v["equivalent"] for v in out.values())
    return out


def alert_level(ratio: float, thresholds: list) -> str:
    if ratio >= 1.0:
        return "BLOCKED"
    if ratio >= thresholds[2]:
        return "CRITICAL"
    if ratio >= thresholds[1]:
        return "WARNING"
    if ratio >= thresholds[0]:
        return "INFO"
    return "OK"


def escalation_policy(ratio: float, thresholds: list) -> str:
    if ratio >= thresholds[2]:
        return "force_haiku"
    if ratio >= thresholds[1]:
        return "downgrade_one_tier"
    return "normal"


def cmd_status(args):
    data = load()
    eq = to_equivalent(data)
    total_budget = data["config"]["total_monthly_tokens"]
    thresholds = data["config"]["alerts"]
    total_used = eq["total_equivalent"]
    ratio = total_used / total_budget if total_budget else 0

    per_model_budgets = {
        m: int(total_budget * alloc)
        for m, alloc in data["config"]["allocation"].items()
    }

    result = {
        "month": data["month"],
        "total_budget_tokens": total_budget,
        "total_used_equivalent": total_used,
        "total_ratio": round(ratio, 4),
        "alert": alert_level(ratio, thresholds),
        "escalation_policy": escalation_policy(ratio, thresholds),
        "per_model": {},
    }

    for m in WEIGHTS:
        used = eq[m]["equivalent"]
        budget_m = per_model_budgets[m]
        r = used / budget_m if budget_m else 0
        result["per_model"][m] = {
            "used_equivalent": used,
            "budget": budget_m,
            "ratio": round(r, 4),
            "alert": alert_level(r, thresholds),
            "raw_input": eq[m]["raw_input"],
            "raw_output": eq[m]["raw_output"],
        }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print(f"=== Budget {data['month']} ===")
    print(f"Total : {total_used:,} / {total_budget:,} tokens eq  ({ratio*100:.1f}%)  [{result['alert']}]")
    for m, d in result["per_model"].items():
        print(f"  {m:6s} : {d['used_equivalent']:,} / {d['budget']:,} ({d['ratio']*100:.1f}%)  [{d['alert']}]  "
              f"[in={d['raw_input']:,} out={d['raw_output']:,}]")
    print(f"Policy : {result['escalation_policy']}")


def cmd_log(args):
    data = load()
    m = args.model.lower()
    if m not in WEIGHTS:
        sys.exit(f"model doit etre un de {list(WEIGHTS.keys())}")
    data["consumption"][m]["input"] += args.input
    data["consumption"][m]["output"] += args.output
    save(data)
    print(f"OK : +{args.input} input / +{args.output} output sur {m}")


def cmd_set_budget(args):
    data = load()
    if args.total:
        data["config"]["total_monthly_tokens"] = args.total
    alloc = data["config"]["allocation"]
    if args.haiku is not None:
        alloc["haiku"] = args.haiku
    if args.sonnet is not None:
        alloc["sonnet"] = args.sonnet
    if args.opus is not None:
        alloc["opus"] = args.opus
    total = alloc["haiku"] + alloc["sonnet"] + alloc["opus"]
    if abs(total - 1.0) > 0.01:
        sys.exit(f"Allocation doit sommer a 1.0 (actuel : {total})")
    save(data)
    print("Budget mis a jour :", json.dumps(data["config"], indent=2))


def cmd_reset(args):
    data = load()
    archive = HISTORY_DIR / f"{data['month']}.json"
    shutil.copy(DEFAULT_FILE, archive)
    data["consumption"] = {m: {"input": 0, "output": 0} for m in WEIGHTS}
    data["month"] = datetime.utcnow().strftime("%Y-%m")
    save(data)
    print(f"Reset effectue. Ancien budget archive dans {archive}")


def cmd_prune_history(args):
    ensure_dirs()
    keep = args.keep_months
    files = sorted(HISTORY_DIR.glob("*.json"))
    if len(files) <= keep:
        print(f"Rien a supprimer ({len(files)} fichiers, garde {keep})")
        return
    to_remove = files[:-keep]
    for f in to_remove:
        f.unlink()
    print(f"Supprime {len(to_remove)} fichier(s) d'historique")


def cmd_log_from_task(args):
    """Hook PostToolUse : lit stdin JSON et log la conso."""
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    model_raw = payload.get("model", "")
    if "opus" in model_raw:
        m = "opus"
    elif "sonnet" in model_raw:
        m = "sonnet"
    elif "haiku" in model_raw:
        m = "haiku"
    else:
        return
    inp = payload.get("usage", {}).get("input_tokens", 0)
    out = payload.get("usage", {}).get("output_tokens", 0)
    if not inp and not out:
        return
    data = load()
    data["consumption"][m]["input"] += inp
    data["consumption"][m]["output"] += out
    save(data)


def main():
    parser = argparse.ArgumentParser(description="Budget tracker pour token-optimizer.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status"); p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("log")
    p.add_argument("--model", required=True, choices=list(WEIGHTS))
    p.add_argument("--input", type=int, default=0)
    p.add_argument("--output", type=int, default=0)
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("set-budget")
    p.add_argument("--total", type=int)
    p.add_argument("--haiku", type=float)
    p.add_argument("--sonnet", type=float)
    p.add_argument("--opus", type=float)
    p.set_defaults(func=cmd_set_budget)

    p = sub.add_parser("reset"); p.set_defaults(func=cmd_reset)

    p = sub.add_parser("prune-history")
    p.add_argument("--keep-months", type=int, default=12)
    p.set_defaults(func=cmd_prune_history)

    p = sub.add_parser("log-from-task"); p.set_defaults(func=cmd_log_from_task)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
