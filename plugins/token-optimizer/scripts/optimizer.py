#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
optimizer.py - Boucle d'auto-amelioration du budget tokens (Lot 2).

Autonomie : "auto-applique le sur, propose le reste".
L'auto-application n'ecrit QUE des drapeaux de donnees bornes et reversibles
dans budget.json (cle "auto_state") consommes par le model-router. JAMAIS
d'edition de code ni d'action sur du sensible.

Sous-commandes :
    optimizer.py analyze            # dry-run : ce qui serait applique
    optimizer.py apply              # applique la liste blanche (reversible, journalise)
    optimizer.py status             # etat des optimisations actives
    optimizer.py rollback --last    # annule la derniere application

Etat ecrit dans budget.json["auto_state"] :
    caveman_default : null | "lite" | "full" | "ultra"
    haiku_reroute   : bool
    force_haiku     : bool
    score_bias      : int borne [0..MAX_BIAS] (pousse les taches limites vers le tier inferieur)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import budget_analyzer as BA  # meme dossier

HOME = Path(os.path.expanduser("~")) / ".token-optimizer"
BUDGET_FILE = HOME / "budget.json"
LOG_FILE = HOME / "optimizer-log.jsonl"
ROLLBACK_FILE = HOME / "optimizer-rollback.json"

MAX_BIAS = 10
BIAS_PRESSURE = 5  # bias applique sous pression budget

DEFAULT_STATE = {
    "caveman_default": None,
    "haiku_reroute": False,
    "force_haiku": False,
    "score_bias": 0,
    "updated": None,
    "applied_by": "optimizer",
}


def load_budget():
    if not BUDGET_FILE.exists():
        return None
    try:
        return json.loads(BUDGET_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_budget(data):
    HOME.mkdir(parents=True, exist_ok=True)
    BUDGET_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def current_state(data):
    st = dict(DEFAULT_STATE)
    st.update(data.get("auto_state", {}) or {})
    return st


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def decide_state(analysis):
    """Calcule l'etat cible a partir de l'analyse. Deterministe et borne."""
    ratio = analysis["ratio"]
    proj = analysis["projected_ratio"]
    th = [0.50, 0.80, 0.95]

    st = dict(DEFAULT_STATE)
    st["force_haiku"] = ratio >= th[2]
    st["haiku_reroute"] = ratio >= th[1] or proj > 1.0
    if ratio >= th[2]:
        st["caveman_default"] = "ultra"
    elif ratio >= th[1]:
        st["caveman_default"] = "full"
    elif proj > 1.0:
        st["caveman_default"] = "lite"
    else:
        st["caveman_default"] = None
    pressure = (ratio >= th[1]) or (proj > 1.2)
    st["score_bias"] = clamp(BIAS_PRESSURE if pressure else 0, 0, MAX_BIAS)
    return st


def diff_state(old, new):
    keys = ("caveman_default", "haiku_reroute", "force_haiku", "score_bias")
    return {k: {"from": old.get(k), "to": new.get(k)} for k in keys if old.get(k) != new.get(k)}


def append_log(entry):
    HOME.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def push_rollback(prev_state):
    stack = []
    if ROLLBACK_FILE.exists():
        try:
            stack = json.loads(ROLLBACK_FILE.read_text(encoding="utf-8"))
        except Exception:
            stack = []
    stack.append(prev_state)
    ROLLBACK_FILE.write_text(json.dumps(stack, indent=2, ensure_ascii=False), encoding="utf-8")


def pop_rollback():
    if not ROLLBACK_FILE.exists():
        return None
    try:
        stack = json.loads(ROLLBACK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not stack:
        return None
    prev = stack.pop()
    ROLLBACK_FILE.write_text(json.dumps(stack, indent=2, ensure_ascii=False), encoding="utf-8")
    return prev


def cmd_analyze(args):
    data = load_budget()
    if data is None:
        print("budget.json introuvable. Lance d'abord budget.py status.")
        return
    analysis = BA.analyze(data)
    old = current_state(data)
    target = decide_state(analysis)
    changes = diff_state(old, target)
    print(f"Budget : {analysis['ratio']*100:.1f}% (projete {analysis['projected_ratio']*100:.0f}%)")
    print("Etat actuel  :", {k: old[k] for k in ('caveman_default','haiku_reroute','force_haiku','score_bias')})
    print("Etat cible   :", {k: target[k] for k in ('caveman_default','haiku_reroute','force_haiku','score_bias')})
    if changes:
        print("Changements AUTO (seraient appliques) :")
        for k, v in changes.items():
            print(f"  - {k}: {v['from']} -> {v['to']}")
    else:
        print("Aucun changement auto necessaire.")
    prop = analysis["recommendations"]["propose"]
    if prop:
        print("A PROPOSER (validation requise) :")
        for r in prop:
            print(f"  ? {r}")


def cmd_apply(args):
    data = load_budget()
    if data is None:
        print("budget.json introuvable.")
        return
    analysis = BA.analyze(data)
    old = current_state(data)
    target = decide_state(analysis)
    changes = diff_state(old, target)
    if not changes:
        print("Rien a appliquer (etat deja optimal).")
        return
    push_rollback(old)
    target["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data["auto_state"] = target
    save_budget(data)
    append_log({
        "ts": target["updated"], "action": "apply",
        "ratio": analysis["ratio"], "projected_ratio": analysis["projected_ratio"],
        "changes": changes,
    })
    print("Optimisations AUTO appliquees (reversibles) :")
    for k, v in changes.items():
        print(f"  * {k}: {v['from']} -> {v['to']}")
    prop = analysis["recommendations"]["propose"]
    if prop:
        print("Restent A PROPOSER :")
        for r in prop:
            print(f"  ? {r}")


def cmd_status(args):
    data = load_budget()
    if data is None:
        print("budget.json introuvable.")
        return
    st = current_state(data)
    print("Etat auto-optimisations :")
    for k in ("caveman_default", "haiku_reroute", "force_haiku", "score_bias"):
        print(f"  {k} = {st[k]}")
    print(f"  maj = {st.get('updated')}")
    depth = 0
    if ROLLBACK_FILE.exists():
        try:
            depth = len(json.loads(ROLLBACK_FILE.read_text(encoding="utf-8")))
        except Exception:
            depth = 0
    print(f"Points de rollback disponibles : {depth}")


def cmd_rollback(args):
    data = load_budget()
    if data is None:
        print("budget.json introuvable.")
        return
    prev = pop_rollback()
    if prev is None:
        print("Aucun point de rollback.")
        return
    data["auto_state"] = prev
    save_budget(data)
    append_log({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "action": "rollback", "restored": {k: prev.get(k) for k in
                ('caveman_default','haiku_reroute','force_haiku','score_bias')}})
    print("Rollback effectue. Etat restaure :",
          {k: prev.get(k) for k in ('caveman_default','haiku_reroute','force_haiku','score_bias')})


def main():
    ap = argparse.ArgumentParser(description="Auto-optimiseur budget (token-optimizer).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("analyze").set_defaults(func=cmd_analyze)
    sub.add_parser("apply").set_defaults(func=cmd_apply)
    sub.add_parser("status").set_defaults(func=cmd_status)
    rb = sub.add_parser("rollback"); rb.add_argument("--last", action="store_true"); rb.set_defaults(func=cmd_rollback)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
