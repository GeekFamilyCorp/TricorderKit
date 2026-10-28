#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registry.py — CLI du registre de modeles (models/model_registry.yaml).

Abstraction Ollama/LiteLLM : liste les modeles, resout le modele d'un tier
(local prefere = gratuit, sinon distant). Sortie JSON. Aucun secret, aucun appel reseau.

Usage :
  python models/registry.py list
  python models/registry.py resolve --tier T2 [--prefer local|remote]
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

REG = Path(__file__).resolve().parent / "model_registry.yaml"


def _load() -> dict:
    try:
        import yaml  # type: ignore
        return yaml.safe_load(REG.read_text(encoding="utf-8-sig")) or {}
    except Exception as e:  # pas de PyYAML -> parse minimal degrade
        return {"_error": "PyYAML requis (pip install pyyaml): %s" % e}


def cmd_list(reg: dict) -> dict:
    return {"tiers": reg.get("tiers", {}),
            "local_models": [m.get("name") for m in reg.get("local_models", [])],
            "gateway": reg.get("gateway", {})}


def cmd_resolve(reg: dict, tier: str, prefer: str | None) -> dict:
    t = (reg.get("tiers") or {}).get(tier)
    if not t:
        return {"status": "error", "detail": "tier inconnu: %s" % tier}
    pref = prefer or t.get("prefer", "remote")
    chosen = t.get(pref) or t.get("remote") or t.get("local")
    return {"status": "ok", "tier": tier, "prefer": pref, "model": chosen,
            "local": t.get("local"), "remote": t.get("remote"),
            "gateway_url_env": (reg.get("gateway") or {}).get("base_url_env")}


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # R19
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="model-registry")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    rp = sub.add_parser("resolve")
    rp.add_argument("--tier", required=True)
    rp.add_argument("--prefer", choices=["local", "remote"], default=None)
    a = ap.parse_args(argv)
    reg = _load()
    if "_error" in reg:
        print(json.dumps({"status": "error", "detail": reg["_error"]}, ensure_ascii=False))
        return 1
    out = cmd_list(reg) if a.cmd == "list" else cmd_resolve(reg, a.tier, a.prefer)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
