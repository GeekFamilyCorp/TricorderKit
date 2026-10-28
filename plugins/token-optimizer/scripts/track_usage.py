#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""track_usage.py - Ingestion de la conso REELLE de tokens depuis les transcripts Cowork/Claude.

Lit les transcripts JSONL (messages assistant portant `message.usage`), totalise la
consommation reelle par modele (Haiku/Sonnet/Opus) et l'injecte dans budget.json via
budget.py log. Source de verite = usage facture par l'API, pas une estimation.

Garde-fous :
- Idempotent : etat par fichier (nb de lignes deja traitees) dans
  ~/.token-optimizer/track_state.json. Une ligne deja comptee ne l'est jamais deux fois.
- Filtre mois courant (UTC) par defaut : ne compte que les messages du mois en cours
  (evite de backfiller des mois passes dans le budget courant).
- Ponderation cache : input effectif = input_tokens + cache_creation_input_tokens
  + CACHE_READ_FACTOR * cache_read_input_tokens (lectures de cache facturees ~0.1x).
- --dry-run : affiche ce qui serait logue, n'ecrit NI le budget NI l'etat.

Usage :
    python track_usage.py --dry-run
    python track_usage.py            # ingestion reelle du mois courant
    python track_usage.py --json
    python track_usage.py --month 2026-06 --root "C:/.../sessions"
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

CACHE_READ_FACTOR = 0.1  # lectures de cache facturees ~0.1x du prix input
HOME = Path(os.path.expanduser("~")) / ".token-optimizer"
STATE_FILE = HOME / "track_state.json"
BUDGET_PY = Path(__file__).resolve().parent / "budget.py"

DEFAULT_ROOTS = [
    Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "Claude" / "local-agent-mode-sessions",
    Path(os.path.expanduser("~")) / ".claude" / "projects",
]


def norm_model(name):
    n = str(name or "").lower()
    if "opus" in n:
        return "opus"
    if "sonnet" in n:
        return "sonnet"
    if "haiku" in n:
        return "haiku"
    return ""


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"files": {}}


def save_state(state):
    HOME.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def find_transcripts(roots):
    files = []
    for r in roots:
        try:
            if r.exists():
                files.extend(str(p) for p in r.rglob("*.jsonl"))
        except Exception:
            continue
    # audit.jsonl = journal d'outils, pas un transcript de messages -> exclu
    seen, out = set(), []
    for f in files:
        if os.path.basename(f).lower() == "audit.jsonl":
            continue
        if f in seen:
            continue
        seen.add(f)
        out.append(f)
    return out


def month_of(ts):
    try:
        return str(ts)[:7]
    except Exception:
        return ""


def extract_usage(obj):
    msg = obj.get("message") if isinstance(obj, dict) else None
    if not isinstance(msg, dict):
        return None
    usage = msg.get("usage")
    if not isinstance(usage, dict):
        return None
    model = norm_model(msg.get("model"))
    if not model:
        return None
    inp = int(usage.get("input_tokens") or 0)
    cc = int(usage.get("cache_creation_input_tokens") or 0)
    cr = int(usage.get("cache_read_input_tokens") or 0)
    out = int(usage.get("output_tokens") or 0)
    eff_in = inp + cc + int(round(CACHE_READ_FACTOR * cr))
    return model, eff_in, out


def main():
    ap = argparse.ArgumentParser(description="Ingestion conso reelle depuis transcripts.")
    ap.add_argument("--dry-run", action="store_true", help="N'ecrit rien (budget + etat).")
    ap.add_argument("--month", default=datetime.now(timezone.utc).strftime("%Y-%m"),
                    help="Mois cible YYYY-MM (defaut : mois courant UTC).")
    ap.add_argument("--root", action="append", help="Racine(s) transcripts (override).")
    ap.add_argument("--all-months", action="store_true", help="Ignorer le filtre mois.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    roots = [Path(r) for r in args.root] if args.root else DEFAULT_ROOTS
    state = load_state()
    files_state = state.setdefault("files", {})
    totals = {m: {"in": 0, "out": 0} for m in ("haiku", "sonnet", "opus")}
    n_msgs = 0
    scanned = 0

    for f in find_transcripts(roots):
        scanned += 1
        start = int(files_state.get(f, {}).get("lines", 0))
        try:
            with open(f, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
        except Exception:
            continue
        for line in lines[start:]:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("type") != "assistant":
                continue
            if not args.all_months:
                m = month_of(obj.get("timestamp") or "")
                if m and m != args.month:
                    continue
            u = extract_usage(obj)
            if not u:
                continue
            model, eff_in, out = u
            if eff_in == 0 and out == 0:
                continue
            totals[model]["in"] += eff_in
            totals[model]["out"] += out
            n_msgs += 1
        if not args.dry_run:
            files_state[f] = {"lines": len(lines)}

    logged = []
    if not args.dry_run:
        for model, d in totals.items():
            if d["in"] == 0 and d["out"] == 0:
                continue
            cmd = [sys.executable, str(BUDGET_PY), "log", "--model", model,
                   "--input", str(d["in"]), "--output", str(d["out"])]
            try:
                subprocess.run(cmd, check=False, capture_output=True)
                logged.append(model)
            except Exception:
                pass
        save_state(state)

    result = {
        "month": args.month, "messages": n_msgs, "files_scanned": scanned,
        "totals": totals, "logged_models": logged, "dry_run": args.dry_run,
        "cache_read_factor": CACHE_READ_FACTOR,
    }
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        tag = " [DRY-RUN]" if args.dry_run else ""
        print(f"=== track_usage ({args.month}){tag} ===")
        print(f"Transcripts scannes : {scanned} | messages comptes : {n_msgs}")
        for model, d in totals.items():
            print(f"  {model:6s} : +{d['in']:,} in / +{d['out']:,} out")
        if not args.dry_run:
            print(f"Modeles logues : {', '.join(logged) or 'aucun'}")


if __name__ == "__main__":
    main()
