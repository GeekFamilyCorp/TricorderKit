#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""budget.py - Suivi du budget mensuel de tokens pour token-optimizer (schema v1.1)."""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for _stream in ("stdout", "stderr", "stdin"):
    try:
        getattr(sys, _stream).reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_HOME = Path(os.path.expanduser("~")) / ".token-optimizer"
DEFAULT_FILE = DEFAULT_HOME / "budget.json"
HISTORY_DIR = DEFAULT_HOME / "history"
EVENTS_MAX = 2000

WEIGHTS = {
    "haiku":  {"input": 1,  "output": 1},
    "sonnet": {"input": 3,  "output": 5},
    "opus":   {"input": 15, "output": 25},
}
OFFLOAD_TARGETS = ("local", "antigravity", "haiku_reroute")

DEFAULT_CONFIG = {
    "version": "1.1",
    "month": datetime.now(timezone.utc).strftime("%Y-%m"),
    "config": {
        "total_monthly_tokens": 20000000,
        "allocation": {"haiku": 0.60, "sonnet": 0.30, "opus": 0.10},
        "alerts": [0.50, 0.80, 0.95],
        "alert_mode": "informative",
        "calibration_factor": 1.0,
    },
    "consumption": {
        "haiku":  {"input": 0, "output": 0},
        "sonnet": {"input": 0, "output": 0},
        "opus":   {"input": 0, "output": 0},
    },
    "offload": {t: {"tasks": 0, "tokens_saved_equiv": 0} for t in OFFLOAD_TARGETS},
    "events": [],
}

TOKEN_IN_KEYS = {"input_tokens", "prompt_tokens"}
TOKEN_OUT_KEYS = {"output_tokens", "completion_tokens"}


def ensure_dirs():
    DEFAULT_HOME.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def fresh_config():
    return json.loads(json.dumps(DEFAULT_CONFIG))


def migrate(data):
    data.setdefault("version", "1.1")
    cfg = data.setdefault("config", {})
    cfg.setdefault("total_monthly_tokens", 20000000)
    cfg.setdefault("allocation", {"haiku": 0.60, "sonnet": 0.30, "opus": 0.10})
    cfg.setdefault("alerts", [0.50, 0.80, 0.95])
    cfg.setdefault("alert_mode", "informative")
    cfg.setdefault("calibration_factor", 1.0)
    cons = data.setdefault("consumption", {})
    for m in WEIGHTS:
        slot = cons.setdefault(m, {"input": 0, "output": 0})
        slot.setdefault("input", 0)
        slot.setdefault("output", 0)
    off = data.setdefault("offload", {})
    for t in OFFLOAD_TARGETS:
        s = off.setdefault(t, {"tasks": 0, "tokens_saved_equiv": 0})
        s.setdefault("tasks", 0)
        s.setdefault("tokens_saved_equiv", 0)
    data.setdefault("events", [])
    return data


def load():
    ensure_dirs()
    if not DEFAULT_FILE.exists():
        d = fresh_config()
        save(d)
        return d
    with open(DEFAULT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    current = datetime.now(timezone.utc).strftime("%Y-%m")
    if data.get("month") != current:
        try:
            shutil.copy(DEFAULT_FILE, HISTORY_DIR / (str(data.get("month", "unknown")) + ".json"))
        except Exception:
            pass
        data["month"] = current
        data["consumption"] = {m: {"input": 0, "output": 0} for m in WEIGHTS}
        data["offload"] = {t: {"tasks": 0, "tokens_saved_equiv": 0} for t in OFFLOAD_TARGETS}
        data["events"] = []
        data = migrate(data)
        save(data)
        return data
    return migrate(data)


def save(data):
    ensure_dirs()
    with open(DEFAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def record_event(data, model, inp, out, tier=None, offloaded_to=None):
    ev = data.setdefault("events", [])
    ev.append({
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "type": "task", "tier": tier, "model": model,
        "in": int(inp or 0), "out": int(out or 0),
        "estimated": True, "offloaded_to": offloaded_to,
    })
    if len(ev) > EVENTS_MAX:
        del ev[: len(ev) - EVENTS_MAX]


def to_equivalent(data):
    out = {}
    for model, cons in data["consumption"].items():
        eq = cons["input"] * WEIGHTS[model]["input"] + cons["output"] * WEIGHTS[model]["output"]
        out[model] = {"raw_input": cons["input"], "raw_output": cons["output"], "equivalent": eq}
    out["total_equivalent"] = sum(v["equivalent"] for v in out.values())
    return out


def alert_level(ratio, thresholds):
    if ratio >= 1.0:
        return "BLOCKED"
    if ratio >= thresholds[2]:
        return "CRITICAL"
    if ratio >= thresholds[1]:
        return "WARNING"
    if ratio >= thresholds[0]:
        return "INFO"
    return "OK"


def escalation_policy(ratio, thresholds):
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
    per_model_budgets = {m: int(total_budget * a) for m, a in data["config"]["allocation"].items()}
    result = {
        "month": data["month"], "total_budget_tokens": total_budget,
        "total_used_equivalent": total_used, "total_ratio": round(ratio, 4),
        "alert": alert_level(ratio, thresholds),
        "escalation_policy": escalation_policy(ratio, thresholds),
        "alert_mode": data["config"].get("alert_mode", "informative"), "per_model": {},
    }
    for m in WEIGHTS:
        used = eq[m]["equivalent"]
        budget_m = per_model_budgets[m]
        r = used / budget_m if budget_m else 0
        result["per_model"][m] = {
            "used_equivalent": used, "budget": budget_m, "ratio": round(r, 4),
            "alert": alert_level(r, thresholds),
            "raw_input": eq[m]["raw_input"], "raw_output": eq[m]["raw_output"],
        }
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    print("=== Budget " + str(data["month"]) + " ===")
    print(f"Total : {total_used:,} / {total_budget:,} tokens eq  ({ratio*100:.1f}%)  [{result['alert']}]")
    for m, d in result["per_model"].items():
        print(f"  {m:6s} : {d['used_equivalent']:,} / {d['budget']:,} ({d['ratio']*100:.1f}%)  [{d['alert']}]")
    off = data.get("offload", {})
    saved = sum(off.get(t, {}).get("tokens_saved_equiv", 0) for t in OFFLOAD_TARGETS)
    if saved:
        print(f"Economies offload : {saved:,} tokens eq")
    print(f"Policy : {result['escalation_policy']}  | mode alerte : {result['alert_mode']}")


def cmd_log(args):
    data = load()
    m = args.model.lower()
    if m not in WEIGHTS:
        sys.exit("model invalide")
    data["consumption"][m]["input"] += args.input
    data["consumption"][m]["output"] += args.output
    record_event(data, m, args.input, args.output, tier=args.tier)
    save(data)
    print(f"OK : +{args.input} in / +{args.output} out sur {m}")


def cmd_set_budget(args):
    data = load()
    cfg = data["config"]
    if args.total:
        cfg["total_monthly_tokens"] = args.total
    alloc = cfg["allocation"]
    if args.haiku is not None:
        alloc["haiku"] = args.haiku
    if args.sonnet is not None:
        alloc["sonnet"] = args.sonnet
    if args.opus is not None:
        alloc["opus"] = args.opus
    total = alloc["haiku"] + alloc["sonnet"] + alloc["opus"]
    if abs(total - 1.0) > 0.01:
        sys.exit("Allocation doit sommer a 1.0 (actuel : " + str(total) + ")")
    if args.calibration is not None:
        cfg["calibration_factor"] = args.calibration
    if args.alert_mode is not None:
        cfg["alert_mode"] = args.alert_mode
    save(data)
    print("Budget mis a jour :", json.dumps(cfg, ensure_ascii=False))


def cmd_reset(args):
    data = load()
    try:
        shutil.copy(DEFAULT_FILE, HISTORY_DIR / (str(data["month"]) + ".json"))
    except Exception:
        pass
    data["consumption"] = {m: {"input": 0, "output": 0} for m in WEIGHTS}
    data["offload"] = {t: {"tasks": 0, "tokens_saved_equiv": 0} for t in OFFLOAD_TARGETS}
    data["events"] = []
    data["month"] = datetime.now(timezone.utc).strftime("%Y-%m")
    save(data)
    print("Reset effectue pour " + str(data["month"]))


def cmd_prune_history(args):
    ensure_dirs()
    keep = args.keep_months
    files = sorted(HISTORY_DIR.glob("*.json"))
    if len(files) <= keep:
        print(f"Rien a supprimer ({len(files)} fichiers)")
        return
    for f in files[:-keep]:
        try:
            f.unlink()
        except Exception:
            pass
    print(f"Historique purge (garde {keep} mois).")


def cmd_log_offload(args):
    data = load()
    t = args.target
    if t == "haiku":
        t = "haiku_reroute"
    if t not in OFFLOAD_TARGETS:
        sys.exit("target invalide")
    data["offload"][t]["tasks"] += args.tasks
    data["offload"][t]["tokens_saved_equiv"] += args.saved
    save(data)
    print(f"OK : offload {t} +{args.tasks} tache(s), +{args.saved} eq")


def norm_model(name):
    n = str(name).lower() if name else ""
    if "opus" in n:
        return "opus"
    if "sonnet" in n:
        return "sonnet"
    if "haiku" in n:
        return "haiku"
    return ""


def find_tokens(obj):
    c = {"in": 0, "out": 0, "found": False}

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                kl = str(k).lower().replace("-", "_")
                if isinstance(v, bool):
                    continue
                if isinstance(v, (int, float)):
                    if kl in TOKEN_IN_KEYS:
                        c["in"] += int(v); c["found"] = True
                    elif kl in TOKEN_OUT_KEYS:
                        c["out"] += int(v); c["found"] = True
                else:
                    walk(v)
        elif isinstance(o, list):
            for it in o:
                walk(it)
    walk(obj)
    return c["in"], c["out"], c["found"]


def cmd_log_from_task(args):
    try:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
    except Exception:
        return
    if not raw or not raw.strip():
        return
    try:
        payload = json.loads(raw)
    except Exception:
        return
    try:
        if not isinstance(payload, dict):
            return
        ti = payload.get("tool_input")
        if not isinstance(ti, dict):
            ti = {}
        m = norm_model(ti.get("subagent_type") or ti.get("model"))
        if not m:
            m = norm_model(payload.get("model"))
        if not m:
            tr = payload.get("tool_response")
            if isinstance(tr, dict):
                m = norm_model(tr.get("model"))
        inp, out, found = find_tokens(payload)
        if not found or (inp == 0 and out == 0):
            return
        if not m:
            return
        data = load()
        data["consumption"][m]["input"] += int(inp)
        data["consumption"][m]["output"] += int(out)
        record_event(data, m, inp, out)
        save(data)
    except Exception:
        return


def main():
    parser = argparse.ArgumentParser(description="Budget tracker token-optimizer v1.1.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("status"); p.add_argument("--json", action="store_true"); p.set_defaults(func=cmd_status)
    p = sub.add_parser("log")
    p.add_argument("--model", required=True, choices=list(WEIGHTS))
    p.add_argument("--input", type=int, default=0); p.add_argument("--output", type=int, default=0)
    p.add_argument("--tier", default=None); p.set_defaults(func=cmd_log)
    p = sub.add_parser("set-budget")
    p.add_argument("--total", type=int); p.add_argument("--haiku", type=float)
    p.add_argument("--sonnet", type=float); p.add_argument("--opus", type=float)
    p.add_argument("--calibration", type=float)
    p.add_argument("--alert-mode", dest="alert_mode", choices=["informative", "enforcing"])
    p.set_defaults(func=cmd_set_budget)
    p = sub.add_parser("reset"); p.set_defaults(func=cmd_reset)
    p = sub.add_parser("prune-history"); p.add_argument("--keep-months", type=int, default=12); p.set_defaults(func=cmd_prune_history)
    p = sub.add_parser("log-offload")
    p.add_argument("--target", required=True, choices=["local", "antigravity", "haiku"])
    p.add_argument("--saved", type=int, default=0); p.add_argument("--tasks", type=int, default=1)
    p.set_defaults(func=cmd_log_offload)
    p = sub.add_parser("log-from-task"); p.set_defaults(func=cmd_log_from_task)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    is_hook = len(sys.argv) > 1 and sys.argv[1] == "log-from-task"
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        if is_hook:
            sys.exit(0)
        raise
