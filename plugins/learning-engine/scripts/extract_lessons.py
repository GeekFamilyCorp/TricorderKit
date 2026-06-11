#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_lessons.py — Étape 3 de la boucle learning-engine (DEC-046, Lot A).

Transforme des experience cards (optionnellement un strategy_variant) en leçons
opérationnelles falsifiables (lesson.schema.json).

  ExperienceCards [+ StrategyVariant] --> Lessons (observation + action + confiance)

Garde-fou : `human_review_required: true` par défaut sur toute leçon ; status
initial = "observed". Le seuil de confiance est paramétrable (--min-confidence) :
les leçons sous le seuil sont écartées (non écrites), pas promues silencieusement.

Sortie : enveloppe skill_output (--format json|md).

Exemple :
  python extract_lessons.py --task-type scraping_jp --cards-dir runs/learning \
      --min-confidence 0.6
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import _common as C
from compare_strategies import card_score  # réutilise le scoring d'une carte

SKILL = "learning-extract-lessons"
DEFAULT_CARDS = C.PLUGIN_ROOT / "runs" / "learning"
DEFAULT_OUT = C.PLUGIN_ROOT / "runs" / "learning" / "lessons"


def _confidence(scores: list[float], n: int) -> float:
    """Confiance = (volume de preuves) x (consistance). 0-1."""
    if not scores:
        return 0.0
    volume = min(1.0, n / 5.0)  # plateau à 5 runs
    if len(scores) >= 2:
        consistency = 1.0 - min(1.0, statistics.pstdev(scores) * 2.0)
    else:
        consistency = 0.5  # un seul run = consistance inconnue
    return round(max(0.0, min(1.0, 0.5 * volume + 0.5 * consistency)), 4)


def build_lessons(task_type: str, cards: list[dict], seq_start: int = 1) -> list[dict]:
    """Une leçon par stratégie ayant assez de preuves + une leçon comparative si ≥2."""
    by_strategy: dict[str, list[dict]] = {}
    for c in cards:
        by_strategy.setdefault(c.get("strategy_used", "unknown"), []).append(c)

    lessons = []
    seq = seq_start
    strat_means: dict[str, float] = {}
    for strat, cs in by_strategy.items():
        scores = [s for s in (card_score(c) for c in cs) if s is not None]
        if not scores:
            continue
        mean = statistics.fmean(scores)
        strat_means[strat] = mean
        conf = _confidence(scores, len(cs))
        run_ids = sorted({rid for c in cs for rid in c.get("run_ids", [])})
        evidence = run_ids or [c["experience_card_id"] for c in cs]
        verdict = ("performe bien" if mean >= 0.7
                   else "donne des résultats moyens" if mean >= 0.5
                   else "sous-performe")
        lessons.append({
            "lesson_id": f"{_slug(task_type)}_{strat_slug(strat)}_{seq:03d}",
            "date": C.today(),
            "task_type": task_type,
            "observation": (f"Sur {len(cs)} run(s) de '{task_type}', la stratégie "
                            f"'{strat}' {verdict} (score moyen {mean:.2f})."),
            "action": (f"Conserver '{strat}' comme stratégie de référence pour ce task_type."
                       if mean >= 0.7 else
                       f"Réviser ou remplacer '{strat}' : tester une variante alternative."),
            "confidence": conf,
            "evidence": evidence,
            "source_runs": run_ids,
            "quality": {
                "evidence_strength": round(min(100.0, len(cs) * 20.0), 2),
                "repeatability": round(conf * 100.0, 2),
            },
            "status": "observed",
            "human_review_required": True,
        })
        seq += 1

    # Leçon comparative si au moins deux stratégies mesurées
    if len(strat_means) >= 2:
        ranked = sorted(strat_means.items(), key=lambda kv: kv[1], reverse=True)
        best, worst = ranked[0], ranked[-1]
        margin = best[1] - worst[1]
        if margin >= 0.05:
            all_cards = [c for cs in by_strategy.values() for c in cs]
            all_runs = sorted({rid for c in all_cards for rid in c.get("run_ids", [])})
            lessons.append({
                "lesson_id": f"{_slug(task_type)}_compare_{seq:03d}",
                "date": C.today(),
                "task_type": task_type,
                "observation": (f"'{best[0]}' surclasse '{worst[0]}' sur '{task_type}' "
                                f"(écart {margin:.2f} sur le score moyen)."),
                "action": f"Router ce task_type vers '{best[0]}' par défaut.",
                "confidence": round(min(1.0, margin * 2 + 0.3), 4),
                "evidence": all_runs or [c["experience_card_id"] for c in all_cards],
                "source_runs": all_runs,
                "quality": {"evidence_strength": round(min(100.0, len(all_cards) * 15.0), 2),
                            "regression_risk": 30.0},
                "status": "observed",
                "human_review_required": True,
            })
    return lessons


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_") or "task"


def strat_slug(text: str) -> str:
    return _slug(text)


def main(argv=None) -> int:
    C.setup_utf8()
    ap = argparse.ArgumentParser(description="Extrait des leçons depuis les experience cards.")
    ap.add_argument("--task-type", required=True)
    ap.add_argument("--cards-dir", default=str(DEFAULT_CARDS))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--min-confidence", type=float, default=0.5,
                    help="Seuil sous lequel une leçon est écartée (défaut 0.5)")
    ap.add_argument("--dry-run", action="store_true")
    C.add_format_arg(ap)
    args = ap.parse_args(argv)

    cards = [c for p in C.iter_json_files(args.cards_dir, prefix="exp_")
             if (c := _safe_read(p)) and c.get("task_type") == args.task_type]
    if not cards:
        return C.fail(SKILL, "ERR_NO_CARDS",
                      f"Aucune carte pour task_type='{args.task_type}'", fmt=args.format)

    lessons = build_lessons(args.task_type, cards)
    kept, dropped = [], []
    for ls in lessons:
        (kept if ls["confidence"] >= args.min_confidence else dropped).append(ls)

    # Validation schéma de chaque leçon retenue
    for ls in kept:
        errs = C.validate(ls, "lesson")
        if errs:
            return C.fail(SKILL, "ERR_SCHEMA_LESSON",
                          f"Leçon {ls['lesson_id']} non conforme: " + " | ".join(errs[:4]),
                          fmt=args.format)

    if not kept:
        C.emit(C.skill_output(
            skill_name=SKILL, status="partial",
            summary=f"Aucune leçon ≥ seuil {args.min_confidence} ({len(dropped)} écartée(s)).",
            data={"dropped": [{"lesson_id": d["lesson_id"], "confidence": d["confidence"]}
                              for d in dropped]},
            next_steps=["Accumuler plus de runs ou abaisser --min-confidence"],
        ), args.format)
        return 0

    if args.dry_run:
        C.emit(C.skill_output(
            skill_name=SKILL, status="dry_run",
            summary=f"{len(kept)} leçon(s) prêtes (validées, non écrites).",
            data={"lessons": kept},
            dry_run_report={"actions_that_would_run":
                            [f"write {args.out_dir}/{ls['lesson_id']}.json" for ls in kept],
                            "risk_level": "LOW"},
        ), args.format)
        return 0

    files = [str(C.write_json(Path(args.out_dir) / f"{ls['lesson_id']}.json", ls))
             for ls in kept]
    C.emit(C.skill_output(
        skill_name=SKILL, status="success",
        summary=f"{len(kept)} leçon(s) écrites (status=observed, review requise). "
                f"{len(dropped)} écartée(s) sous seuil.",
        data={"lesson_ids": [ls["lesson_id"] for ls in kept]},
        files_created=files,
        next_steps=["Revue humaine des leçons (status observed -> accepted)",
                    "propose_skill_update.py sur les leçons acceptées"],
    ), args.format)
    return 0


def _safe_read(p):
    try:
        return C.read_json(p)
    except Exception:  # noqa: BLE001
        return None


if __name__ == "__main__":
    sys.exit(main())
