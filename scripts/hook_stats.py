#!/usr/bin/env python3
"""
hook_stats.py — CLI pour la commande /tk:hook-stats
TricorderKit v0.7 — Phase 3.5 Hook Layer

Lit .cache/hooks/post_execution.log (JSON-lines) et affiche un tableau
Markdown agrégé par skill/goat avec :
  - Nombre de runs
  - Score de qualité moyen (quality_score)
  - Taux d'échec (quality_score < 0.5)
  - Tokens consommés (avg + total)
  - Domaine détecté (du pre_intent_hook)

Usage :
  python3 scripts/hook_stats.py
  python3 scripts/hook_stats.py --format json
  python3 scripts/hook_stats.py --last 50
  python3 scripts/hook_stats.py --skill my-domain-cli
  python3 scripts/hook_stats.py --domain manga_anime
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# ─── Paths ───────────────────────────────────────────────────────────────────
REPO_ROOT       = Path(__file__).resolve().parent.parent
HOOKS_CACHE_DIR = REPO_ROOT / ".cache" / "hooks"
POST_LOG        = HOOKS_CACHE_DIR / "post_execution.log"
PRE_LOG         = HOOKS_CACHE_DIR / "pre_execution.log"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_jsonl(path: Path, last_n: int | None = None) -> list[dict[str, Any]]:
    """Charge un fichier JSON-lines, optionnellement les N dernières lignes."""
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if last_n is not None:
        lines = lines[-last_n:]
    records: list[dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _skill_key(record: dict[str, Any]) -> str:
    """Extrait le nom du skill / goat / workflow depuis un record post-execution."""
    plan = record.get("plan", {})
    return (
        plan.get("skill")
        or plan.get("goat")
        or plan.get("workflow")
        or record.get("skill_or_goat")
        or "(inconnu)"
    )


def _domain_from_run_id(run_id: str | None, pre_index: dict[str, str]) -> str:
    """Résout le domaine depuis le run_id en cherchant dans le pre_index."""
    if not run_id:
        return "—"
    return pre_index.get(run_id, "—")


# ─── Aggregation ─────────────────────────────────────────────────────────────

def build_pre_index(pre_records: list[dict[str, Any]]) -> dict[str, str]:
    """Construit un index {hook_run_id → domain} depuis les records pre_execution."""
    index: dict[str, str] = {}
    for r in pre_records:
        run_id = r.get("hook_run_id") or r.get("hooks", {}).get("hook_run_id")
        domain = r.get("domain") or r.get("metadata", {}).get("domain", "—")
        if run_id:
            index[run_id] = domain
    return index


def aggregate(
    post_records: list[dict[str, Any]],
    pre_index: dict[str, str],
) -> list[dict[str, Any]]:
    """Agrège les records post-execution par skill/goat."""
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "runs": 0,
        "quality_scores": [],
        "tokens": [],
        "domains": [],
        "failures": 0,
    })

    for r in post_records:
        key = _skill_key(r)
        b   = buckets[key]
        b["runs"] += 1

        qs = r.get("quality_score")
        if qs is not None:
            b["quality_scores"].append(float(qs))
            if float(qs) < 0.5:
                b["failures"] += 1

        tok = (
            r.get("tokens_used")
            or r.get("hooks", {}).get("estimated_tokens")
        )
        if tok is not None:
            b["tokens"].append(int(tok))

        run_id = (
            r.get("hook_run_id")
            or r.get("hooks", {}).get("hook_run_id")
        )
        domain = _domain_from_run_id(run_id, pre_index)
        if domain and domain != "—":
            b["domains"].append(domain)

    rows: list[dict[str, Any]] = []
    for skill, b in sorted(buckets.items(), key=lambda x: -x[1]["runs"]):
        runs = b["runs"]
        scores = b["quality_scores"]
        tokens = b["tokens"]
        domains = b["domains"]

        avg_quality    = round(sum(scores) / len(scores), 2) if scores else None
        failure_rate   = round(b["failures"] / runs * 100, 1) if runs else 0.0
        avg_tokens     = round(sum(tokens) / len(tokens)) if tokens else None
        total_tokens   = sum(tokens) if tokens else 0
        top_domain     = max(set(domains), key=domains.count) if domains else "—"

        rows.append({
            "skill":        skill,
            "runs":         runs,
            "avg_quality":  avg_quality,
            "failure_rate": failure_rate,
            "avg_tokens":   avg_tokens,
            "total_tokens": total_tokens,
            "domain":       top_domain,
        })

    return rows


# ─── Formatters ──────────────────────────────────────────────────────────────

def format_markdown(rows: list[dict[str, Any]]) -> str:
    """Génère un tableau Markdown."""
    if not rows:
        return "_Aucun enregistrement trouvé dans le log post-execution._\n"

    lines = [
        "## 📊 Hook Stats — TricorderKit",
        "",
        "| Skill / Goat | Runs | Qualité moy. | Taux échec | Tokens moy. | Tokens total | Domaine |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        quality  = f"{r['avg_quality']:.2f}" if r["avg_quality"] is not None else "—"
        failure  = f"{r['failure_rate']}%"
        avg_tok  = str(r["avg_tokens"]) if r["avg_tokens"] is not None else "—"
        tot_tok  = str(r["total_tokens"]) if r["total_tokens"] else "—"
        lines.append(
            f"| `{r['skill']}` | {r['runs']} | {quality} | {failure} | {avg_tok} | {tot_tok} | {r['domain']} |"
        )

    lines.append("")
    lines.append(f"_Total : {sum(r['runs'] for r in rows)} runs enregistrés._")
    return "\n".join(lines)


def format_json(rows: list[dict[str, Any]]) -> str:
    """Sortie JSON machine-readable."""
    return json.dumps(rows, ensure_ascii=False, indent=2)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="/tk:hook-stats — Tableau agrégé des runs de hooks TricorderKit"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Format de sortie (défaut: markdown)",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=None,
        metavar="N",
        help="Ne lire que les N dernières entrées du log",
    )
    parser.add_argument(
        "--skill",
        type=str,
        default=None,
        help="Filtrer sur un skill/goat spécifique (sous-chaîne)",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default=None,
        help="Filtrer sur un domaine spécifique (sous-chaîne)",
    )
    parser.add_argument(
        "--log",
        type=str,
        default=None,
        help=f"Chemin alternatif vers le fichier de log (défaut: {POST_LOG})",
    )
    args = parser.parse_args()

    post_path = Path(args.log) if args.log else POST_LOG

    if not post_path.exists():
        print(
            f"[hook_stats] Aucun log trouvé : {post_path}\n"
            f"  Vérifiez que le hook post-execution a bien été exécuté au moins une fois.",
            file=sys.stderr,
        )
        sys.exit(0)

    # Chargement
    post_records = load_jsonl(post_path, last_n=args.last)
    pre_records  = load_jsonl(PRE_LOG, last_n=args.last)
    pre_index    = build_pre_index(pre_records)

    # Agrégation
    rows = aggregate(post_records, pre_index)

    # Filtres
    if args.skill:
        rows = [r for r in rows if args.skill.lower() in r["skill"].lower()]
    if args.domain:
        rows = [r for r in rows if args.domain.lower() in r["domain"].lower()]

    # Sortie
    if args.format == "json":
        print(format_json(rows))
    else:
        print(format_markdown(rows))


if __name__ == "__main__":
    main()
