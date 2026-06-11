#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
record_experience.py — Étape 1 de la boucle learning-engine (DEC-046, Lot A).

Ingère un run (JSON conforme run_experience.schema.json) et produit une
experience card validée (experience_card.schema.json) dans runs/learning/.

  Run --> [Trace/Score déjà dans le run] --> ExperienceCard

Le run ne porte pas de `task_type` ni de `project_scope` (ce sont des dimensions
d'analyse) : ils sont fournis par l'appelant. Les scores qualité du run (0-100)
sont projetés sur l'échelle 0-1 de la carte.

Sortie : enveloppe skill_output (--format json|md). Dry-run = aucune écriture.

Exemples :
  python record_experience.py --run run.json --task-type scraping \
      --project-scope project-a
  cat run.json | python record_experience.py --run - --task-type veille --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import _common as C

SKILL = "learning-record-experience"
DEFAULT_OUT = C.PLUGIN_ROOT / "runs" / "learning"

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    return _SLUG_RE.sub("_", text.lower()).strip("_") or "task"


def _pct_to_unit(value, default=None):
    """Projette un score 0-100 vers 0-1 (None si absent)."""
    if value is None:
        return default
    return round(max(0.0, min(100.0, float(value))) / 100.0, 4)


def build_card(run: dict, task_type: str, project_scope: str,
               card_date: str | None = None) -> dict:
    date = card_date or (run.get("started_at", "")[:10]) or C.today()
    run_id = run.get("run_id", "")
    strat_for_id = _slug((run.get("strategy_used", {}) or {}).get("id", "x"))
    # Unicité : date + task + stratégie + suffixe run_id (évite la collision
    # de deux runs du même task_type/jour qui écraseraient la même carte).
    card_id = f"exp_{date.replace('-', '_')}_{_slug(task_type)}_{strat_for_id}"
    rid_suffix = _slug(run_id.split('_')[-1]) if run_id else ""
    if rid_suffix:
        card_id = f"{card_id}_{rid_suffix}"

    q = run.get("quality", {}) or {}
    metrics = run.get("metrics", {}) or {}
    dupes = metrics.get("duplicates_detected")
    items = metrics.get("items_extracted")
    duplicate_rate = None
    if dupes is not None and items not in (None, 0):
        duplicate_rate = round(min(1.0, dupes / (items + dupes)), 4)
    elif q.get("score_dedup") is not None:
        # score_dedup haut = peu de doublons ; on dérive un taux complémentaire
        duplicate_rate = round(1.0 - _pct_to_unit(q.get("score_dedup"), 0.0), 4)

    quality = {}
    rel = _pct_to_unit(q.get("score_global"))
    if rel is not None:
        quality["relevance_score"] = rel
    for src_key, dst_key in (
        ("score_source_reliability", "source_reliability_score"),
        ("score_completeness", "completeness_score"),
        ("score_freshness", "freshness_score"),
    ):
        v = _pct_to_unit(q.get(src_key))
        if v is not None:
            quality[dst_key] = v
    if duplicate_rate is not None:
        quality["duplicate_rate"] = duplicate_rate
    # cost_score : moins de tokens = mieux ; borné, informatif seulement
    tok = metrics.get("token_cost_estimate")
    if tok is not None:
        quality["cost_score"] = round(1.0 / (1.0 + float(tok) / 10000.0), 4)

    strategy = (run.get("strategy_used", {}) or {}).get("id", "unknown")

    results = {}
    outputs = run.get("outputs", {}) or {}
    for k in ("db_rows_created", "db_rows_updated"):
        if outputs.get(k) is not None:
            results[k] = outputs[k]
    for k in ("items_extracted", "official_sources_found", "pages_fetched"):
        if metrics.get(k) is not None:
            results[k] = metrics[k]

    card = {
        "experience_card_id": card_id,
        "date": date,
        "task_type": task_type,
        "project_scope": project_scope,
        "strategy_used": strategy,
        "run_ids": [run_id] if run_id else [],
        "tools_used": [],
        "sources_used": [s.get("name") for s in (run.get("inputs", {}) or {})
                         .get("sources", []) if s.get("name")],
        "results": results,
        "quality": quality,
        "status": "proposed",
        "human_review_required": True,
    }
    # Erreurs reprises telles quelles (même sous-schéma)
    if run.get("errors"):
        card["errors"] = run["errors"]
    return card


def main(argv=None) -> int:
    C.setup_utf8()
    ap = argparse.ArgumentParser(description="Ingère un run -> experience card validée.")
    ap.add_argument("--run", default="-", help="Chemin du run JSON ('-' = stdin)")
    ap.add_argument("--task-type", required=True, help="Type de tâche (dimension d'analyse)")
    ap.add_argument("--project-scope", required=True,
                    help="Scope projet (chaîne libre, ex. project-a) — moteur générique")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT), help="Répertoire des cartes")
    ap.add_argument("--dry-run", action="store_true", help="Simuler sans écrire")
    C.add_format_arg(ap)
    args = ap.parse_args(argv)

    try:
        run = C.read_json_stdin_or_path(args.run)
    except Exception as e:  # noqa: BLE001
        return C.fail(SKILL, "ERR_INPUT", f"Lecture du run impossible: {e}", fmt=args.format)

    run_errors = C.validate(run, "run_experience")
    if run_errors:
        return C.fail(SKILL, "ERR_SCHEMA_RUN",
                      "Run non conforme: " + " | ".join(run_errors[:5]), fmt=args.format)

    card = build_card(run, args.task_type, args.project_scope)
    card_errors = C.validate(card, "experience_card")
    if card_errors:
        return C.fail(SKILL, "ERR_SCHEMA_CARD",
                      "Carte générée non conforme: " + " | ".join(card_errors[:5]),
                      fmt=args.format)

    out_path = Path(args.out_dir) / f"{card['experience_card_id']}.json"

    if args.dry_run:
        C.emit(C.skill_output(
            skill_name=SKILL, status="dry_run",
            summary=f"Carte {card['experience_card_id']} prête (validée, non écrite).",
            data={"experience_card": card},
            dry_run_report={
                "actions_that_would_run": [f"write {out_path}"],
                "risk_level": "LOW",
            },
        ), args.format)
        return 0

    written = C.write_json(out_path, card)
    C.emit(C.skill_output(
        skill_name=SKILL, status="success",
        summary=f"Experience card {card['experience_card_id']} écrite et validée.",
        data={"experience_card_id": card["experience_card_id"],
              "strategy_used": card["strategy_used"], "quality": card["quality"]},
        files_created=[str(written)],
        next_steps=["compare_strategies.py sur ce task_type",
                    "extract_lessons.py quand ≥ 3 cartes accumulées"],
    ), args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
