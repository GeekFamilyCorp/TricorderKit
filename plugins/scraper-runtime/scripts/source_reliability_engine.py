#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
source_reliability_engine.py — Moteur de fiabilite des sources (TricorderKit,
DEC-046 / N6).

Calcule un score de fiabilite par source a partir de l'historique des runs de
scraping, et PROPOSE une mise a jour du registre normalise — en DRY-RUN STRICT.

  * Lecture seule : n'ecrit JAMAIS dans le vault ni dans aucun registre.
  * La promotion effective (ecriture) est deleguee au writer du projet aval
    (routage DEC-016), qui applique l'archivage R31 avant toute modification.
  * Sortie conforme a core/contracts/skill_output.schema.json (status=dry_run).

Entree : un dossier de "source observations" (JSON) ou un tableau JSON via
--input / stdin. Chaque observation decrit le resultat d'un run pour une source :

  {
    "source": "aggregator-a",       # identifiant de source (generique)
    "official": true,                # source officielle (editeur) ou non
    "pages_fetched": 40,
    "items_extracted": 30,
    "duplicates": 2,
    "errors": 0,
    "fetched_at": "2026-06-11T03:00:00Z",
    "latest_item_date": "2026-06-10"  # date du contenu le plus recent vu
  }

Sous-composantes du score (0..100), moyenne ponderee transparente :
  officiality, freshness, extractability, dedup_quality, reliability.

Usage :
  python source_reliability_engine.py --input runs/                 # dossier
  python source_reliability_engine.py --input obs.json --format md
  cat obs.json | python source_reliability_engine.py               # stdin
  python source_reliability_engine.py --input runs/ --registry reg.yaml  # deltas
"""
from __future__ import annotations

import argparse
import datetime as _dt
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

SKILL_NAME = "source-reliability-engine"
SKILL_VERSION = "0.1.0"

# Ponderation des sous-scores (somme = 1.0). Transparente et ajustable.
WEIGHTS = {
    "officiality": 0.30,
    "reliability": 0.25,
    "freshness": 0.20,
    "extractability": 0.15,
    "dedup_quality": 0.10,
}

FRESHNESS_FULL_DAYS = 2     # <= 2 jours : 100
FRESHNESS_ZERO_DAYS = 30    # >= 30 jours : 0


# ── Encodage (PATTERN-WIN-ENCODING) ─────────────────────────────────────────────
def setup_utf8() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            continue
        if (getattr(stream, "encoding", "") or "").lower().startswith("utf"):
            continue
        rec = getattr(stream, "reconfigure", None)
        if callable(rec):
            try:
                rec(encoding="utf-8", errors="replace")
                continue
            except Exception:
                pass
        buf = getattr(stream, "buffer", None)
        if buf is not None:
            try:
                setattr(sys, name, io.TextIOWrapper(buf, encoding="utf-8", errors="replace"))
            except Exception:
                pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _parse_date(value: str | None) -> _dt.date | None:
    if not value:
        return None
    s = str(value).strip().replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return _dt.datetime.strptime(s[: len(fmt) + 2] if "T" in fmt else s[:10], fmt).date()
        except ValueError:
            continue
    try:
        return _dt.date.fromisoformat(s[:10])
    except ValueError:
        return None


# ── Sous-scores ─────────────────────────────────────────────────────────────────
def freshness_score(latest: _dt.date | None, ref: _dt.date) -> float:
    if latest is None:
        return 0.0
    age = (ref - latest).days
    if age <= FRESHNESS_FULL_DAYS:
        return 100.0
    if age >= FRESHNESS_ZERO_DAYS:
        return 0.0
    span = FRESHNESS_ZERO_DAYS - FRESHNESS_FULL_DAYS
    return _clamp(100.0 * (1 - (age - FRESHNESS_FULL_DAYS) / span))


def extractability_score(items: int, pages: int) -> float:
    if pages <= 0:
        return 0.0 if items <= 0 else 50.0
    return _clamp(100.0 * min(1.0, items / pages))


def dedup_score(items: int, duplicates: int) -> float:
    total = items + duplicates
    if total <= 0:
        return 100.0
    return _clamp(100.0 * (1 - duplicates / total))


def reliability_score(items: int, errors: int) -> float:
    total = items + errors
    if total <= 0:
        return 100.0 if errors == 0 else 0.0
    return _clamp(100.0 * (1 - errors / total))


# ── Agregation par source ───────────────────────────────────────────────────────
def score_source(observations: list[dict], ref: _dt.date) -> dict:
    """Calcule le score composite d'une source a partir de ses observations."""
    n = len(observations)
    pages = sum(int(o.get("pages_fetched", 0) or 0) for o in observations)
    items = sum(int(o.get("items_extracted", 0) or 0) for o in observations)
    dups = sum(int(o.get("duplicates", 0) or 0) for o in observations)
    errs = sum(int(o.get("errors", 0) or 0) for o in observations)
    official_ratio = sum(1 for o in observations if o.get("official")) / n if n else 0.0
    latest_dates = [d for d in (_parse_date(o.get("latest_item_date")) for o in observations) if d]
    latest = max(latest_dates) if latest_dates else None

    sub = {
        "officiality": round(100.0 * official_ratio, 1),
        "reliability": round(reliability_score(items, errs), 1),
        "freshness": round(freshness_score(latest, ref), 1),
        "extractability": round(extractability_score(items, pages), 1),
        "dedup_quality": round(dedup_score(items, dups), 1),
    }
    composite = round(sum(sub[k] * w for k, w in WEIGHTS.items()), 1)
    return {
        "sub_scores": sub,
        "reliability_score": composite,
        "sample_size": n,
        "totals": {"pages_fetched": pages, "items_extracted": items,
                   "duplicates": dups, "errors": errs},
        "latest_item_date": latest.isoformat() if latest else None,
    }


def load_observations(path: str | None) -> list[dict]:
    """Charge les observations depuis un dossier de JSON, un fichier, ou stdin."""
    if path in (None, "-", ""):
        raw = sys.stdin.read().lstrip("﻿")
        return _as_list(json.loads(raw))
    p = Path(path)
    if p.is_dir():
        out: list[dict] = []
        for f in sorted(p.glob("*.json")):
            out.extend(_as_list(json.loads(f.read_text(encoding="utf-8-sig"))))
        return out
    return _as_list(json.loads(p.read_text(encoding="utf-8-sig")))


def _as_list(obj: Any) -> list[dict]:
    if isinstance(obj, list):
        return [o for o in obj if isinstance(o, dict)]
    if isinstance(obj, dict):
        if isinstance(obj.get("observations"), list):
            return [o for o in obj["observations"] if isinstance(o, dict)]
        return [obj]
    return []


def load_registry(path: str | None) -> dict[str, float]:
    """Lit un registre de scores existants (YAML {source: score}) pour les deltas."""
    if not path:
        return {}
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig")) or {}
    except Exception:
        return {}
    scores = data.get("sources", data) if isinstance(data, dict) else {}
    out: dict[str, float] = {}
    if isinstance(scores, dict):
        for k, v in scores.items():
            if isinstance(v, dict) and "reliability_score" in v:
                out[k] = float(v["reliability_score"])
            elif isinstance(v, (int, float)):
                out[k] = float(v)
    return out


def build_proposals(observations: list[dict], registry: dict[str, float],
                    ref: _dt.date) -> list[dict]:
    by_source: dict[str, list[dict]] = {}
    for o in observations:
        src = str(o.get("source", "")).strip()
        if src:
            by_source.setdefault(src, []).append(o)
    proposals = []
    for src in sorted(by_source):
        scored = score_source(by_source[src], ref)
        old = registry.get(src)
        new = scored["reliability_score"]
        proposals.append({
            "source": src,
            "old_score": old,
            "new_score": new,
            "delta": round(new - old, 1) if old is not None else None,
            **scored,
        })
    return proposals


# ── Contrat de sortie skill_output ──────────────────────────────────────────────
def skill_output_dryrun(proposals: list[dict], summary: str) -> dict:
    return {
        "status": "dry_run",
        "skill_name": SKILL_NAME,
        "skill_version": SKILL_VERSION,
        "timestamp": now_iso(),
        "output": {
            "summary": summary[:500],
            "data": {"proposals": proposals, "count": len(proposals),
                     "weights": WEIGHTS},
            "next_steps": [
                "Revue humaine des deltas (human_review_required)",
                "Promotion via le writer du projet aval (routage DEC-016)",
                "Archivage R31 avant toute ecriture du registre",
            ],
        },
        "dry_run_report": {
            "actions_that_would_run": [
                f"Mettre a jour le score de {p['source']} -> {p['new_score']}"
                for p in proposals
            ][:50],
            "risk_level": "LOW",
        },
    }


def emit(env: dict, fmt: str) -> None:
    if fmt == "md":
        o = env["output"]
        print(f"# {env['skill_name']} — {env['status']}")
        print(f"\n{o['summary']}\n")
        print("| source | ancien | nouveau | delta | n | off | rel | fresh | extr | dedup |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for p in o["data"]["proposals"]:
            s = p["sub_scores"]
            print("| %s | %s | %s | %s | %d | %s | %s | %s | %s | %s |" % (
                p["source"], p["old_score"], p["new_score"], p["delta"], p["sample_size"],
                s["officiality"], s["reliability"], s["freshness"],
                s["extractability"], s["dedup_quality"]))
    else:
        print(json.dumps(env, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    setup_utf8()
    ap = argparse.ArgumentParser(prog="source_reliability_engine",
                                 description="Scoring de fiabilite des sources (dry-run strict, N6)")
    ap.add_argument("--input", default=None,
                    help="Dossier ou fichier JSON d'observations (defaut: stdin)")
    ap.add_argument("--registry", default=None,
                    help="Registre YAML de scores existants (pour calculer les deltas)")
    ap.add_argument("--ref-date", default=None,
                    help="Date de reference pour la fraicheur (defaut: aujourd'hui)")
    ap.add_argument("--format", choices=["json", "md"], default="json")
    args = ap.parse_args(argv)

    ref = _parse_date(args.ref_date) or _dt.date.today()
    try:
        observations = load_observations(args.input)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "skill_name": SKILL_NAME,
                          "skill_version": SKILL_VERSION, "timestamp": now_iso(),
                          "output": {"summary": f"lecture observations impossible: {exc}"},
                          "error": {"code": "INPUT_ERROR", "message": str(exc),
                                    "recoverable": True, "rollback_available": False}},
                         ensure_ascii=False, indent=2))
        return 1

    if not observations:
        emit(skill_output_dryrun([], "Aucune observation — rien a scorer."), args.format)
        return 0

    registry = load_registry(args.registry)
    proposals = build_proposals(observations, registry, ref)
    n_changed = sum(1 for p in proposals if p["delta"] not in (None, 0.0))
    summary = (f"DRY-RUN : {len(proposals)} source(s) scoree(s), "
               f"{n_changed} delta(s) vs registre. Aucune ecriture (lecture seule).")
    emit(skill_output_dryrun(proposals, summary), args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
