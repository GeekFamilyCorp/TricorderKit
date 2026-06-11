#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare_strategies.py — Étape 2 de la boucle learning-engine (DEC-046, Lot A).

Agrège les experience cards d'un même task_type par stratégie utilisée et produit :
  - un objet strategy_variant validé (strategy_variant.schema.json)
  - un rapport Markdown dans reports/learning/

  ExperienceCards --> [group by strategy] --> StrategyVariant (classement)

Le score d'une carte = moyenne des scores qualité présents (relevance, fiabilité,
complétude, fraîcheur, cost) moins le duplicate_rate (pénalité). Le classement
remonte la stratégie au meilleur score moyen comme `winning_variant`.

Sortie : enveloppe skill_output (--format json|md).

Exemple :
  python compare_strategies.py --task-type scraping_jp --cards-dir runs/learning
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import _common as C

SKILL = "learning-compare-strategies"
DEFAULT_CARDS = C.PLUGIN_ROOT / "runs" / "learning"
DEFAULT_REPORTS = C.PLUGIN_ROOT / "reports" / "learning"

_POSITIVE = ("relevance_score", "source_reliability_score", "completeness_score",
             "freshness_score", "cost_score")


def card_score(card: dict) -> float | None:
    q = card.get("quality", {}) or {}
    pos = [q[k] for k in _POSITIVE if isinstance(q.get(k), (int, float))]
    if not pos:
        return None
    score = statistics.fmean(pos)
    if isinstance(q.get("duplicate_rate"), (int, float)):
        score -= q["duplicate_rate"]  # pénalité doublons
    return round(max(0.0, min(1.0, score)), 4)


def build_variant(task_type: str, cards: list[dict],
                  project_scope: str | None) -> tuple[dict, dict]:
    """Retourne (strategy_variant, stats_par_strategie)."""
    by_strategy: dict[str, list[float]] = {}
    last_run: dict[str, str] = {}
    for c in cards:
        s = card_score(c)
        if s is None:
            continue
        strat = c.get("strategy_used", "unknown")
        by_strategy.setdefault(strat, []).append(s)
        d = c.get("date", "")
        if d > last_run.get(strat, ""):
            last_run[strat] = d

    variants = []
    for strat, scores in sorted(by_strategy.items(),
                                key=lambda kv: statistics.fmean(kv[1]), reverse=True):
        avg = round(statistics.fmean(scores), 4)
        variants.append({
            "id": strat if strat.replace("_", "").isalnum() else "unknown",
            "description": f"Stratégie « {strat} » — {len(scores)} run(s) agrégé(s).",
            "score_average": avg,
            "runs_count": len(scores),
            "last_run": last_run.get(strat, C.today()),
            "status": "candidate",
        })

    variant_obj: dict = {"task_type": task_type, "variants": variants}
    if project_scope:
        variant_obj["project_scope"] = project_scope

    if len(variants) >= 2:
        winner = variants[0]
        runner = variants[1]
        margin = winner["score_average"] - runner["score_average"]
        action = ("promouvoir comme défaut" if margin >= 0.05
                  else "écart faible — accumuler plus de runs avant décision")
        variant_obj["decision"] = {
            "winning_variant": winner["id"],
            "action": action,
            "risk": "LOW" if margin >= 0.05 else "MEDIUM",
            "decided_at": C.today(),
            "decided_by": "learning-engine/compare_strategies",
        }
    stats = {v["id"]: {"score_average": v["score_average"],
                       "runs_count": v["runs_count"]} for v in variants}
    return variant_obj, stats


def render_md(variant_obj: dict) -> str:
    lines = [f"# Classement de stratégies — {variant_obj['task_type']}",
             f"\n> Généré le {C.today()} par learning-engine/compare_strategies\n",
             "| Rang | Variante | Score moyen | Runs | Dernier run | Statut |",
             "|---|---|---|---|---|---|"]
    for i, v in enumerate(variant_obj.get("variants", []), 1):
        lines.append(f"| {i} | `{v['id']}` | {v['score_average']:.3f} | "
                     f"{v['runs_count']} | {v.get('last_run', '—')} | {v['status']} |")
    dec = variant_obj.get("decision")
    if dec:
        lines += ["", "## Décision proposée",
                  f"- **Gagnante** : `{dec['winning_variant']}`",
                  f"- **Action** : {dec['action']}",
                  f"- **Risque** : {dec['risk']}"]
    else:
        lines += ["", "> Moins de 2 variantes comparables — pas de décision (besoin de diversité de stratégies)."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    C.setup_utf8()
    ap = argparse.ArgumentParser(description="Compare les stratégies d'un task_type.")
    ap.add_argument("--task-type", required=True)
    ap.add_argument("--cards-dir", default=str(DEFAULT_CARDS))
    ap.add_argument("--reports-dir", default=str(DEFAULT_REPORTS))
    ap.add_argument("--dry-run", action="store_true", help="Ne pas écrire le rapport/objet")
    C.add_format_arg(ap)
    args = ap.parse_args(argv)

    cards = []
    for p in C.iter_json_files(args.cards_dir, prefix="exp_"):
        try:
            c = C.read_json(p)
        except Exception:  # noqa: BLE001
            continue
        if c.get("task_type") == args.task_type:
            cards.append(c)

    if not cards:
        return C.fail(SKILL, "ERR_NO_CARDS",
                      f"Aucune carte pour task_type='{args.task_type}' dans {args.cards_dir}",
                      fmt=args.format)

    scope = cards[0].get("project_scope")
    variant_obj, stats = build_variant(args.task_type, cards, scope)

    errs = C.validate(variant_obj, "strategy_variant")
    partial = False
    if errs:
        # < 2 variantes => schéma exige minItems:2 ; on dégrade en partial sans écrire l'objet
        partial = True

    out_json = Path(args.reports_dir) / f"strategy_{args.task_type}.json"
    out_md = Path(args.reports_dir) / f"strategy_{args.task_type}.md"
    md = render_md(variant_obj)

    if args.dry_run:
        C.emit(C.skill_output(
            skill_name=SKILL, status="dry_run",
            summary=f"{len(variant_obj['variants'])} variante(s) pour {args.task_type} "
                    f"({len(cards)} cartes).",
            data={"strategy_variant": variant_obj, "stats": stats},
            dry_run_report={"actions_that_would_run": [f"write {out_json}", f"write {out_md}"],
                            "risk_level": "LOW"},
        ), args.format)
        return 0

    files = []
    Path(args.reports_dir).mkdir(parents=True, exist_ok=True)
    out_md.write_text(md, encoding="utf-8")
    files.append(str(out_md))
    if not partial:
        C.write_json(out_json, variant_obj)
        files.append(str(out_json))

    C.emit(C.skill_output(
        skill_name=SKILL, status="partial" if partial else "success",
        summary=(f"Classement {args.task_type} : "
                 + (variant_obj.get("decision", {}).get("winning_variant", "—")
                    if not partial else "1 seule variante (pas de comparaison)")
                 + f" sur {len(cards)} cartes."),
        data={"strategy_variant": variant_obj, "stats": stats,
              "schema_note": ("strategy_variant exige ≥2 variantes : objet JSON non écrit"
                              if partial else "validé")},
        files_created=files,
        next_steps=(["extract_lessons.py --task-type " + args.task_type]
                    if not partial else
                    ["Accumuler des runs avec une 2e stratégie pour comparer"]),
    ), args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
