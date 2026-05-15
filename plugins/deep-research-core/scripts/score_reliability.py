"""
score_reliability.py -- TricorderKit deep-research-core
Score de fiabilite composite (0.0 -> 1.0) + deduplication par hash titre.

Usage:
    python collect_sources.py --query "One Piece" --domain manga | python score_reliability.py
    python score_reliability.py --input results.json --output table

Version : 0.1.0 -- 15/05/2026
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

PLUGIN_DIR = Path(__file__).parent.parent
SOURCES_FILE = PLUGIN_DIR / "sources" / "trusted_sources.yml"

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO, stream=sys.stderr)
log = logging.getLogger("score_reliability")

RELIABILITY_LEVELS = [
    (0.90, "Confirme"),
    (0.75, "Probable"),
    (0.60, "A verifier"),
    (0.00, "Incomplet"),
]


def load_source_weights(sources_file: Path) -> dict:
    with open(sources_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    weights: dict = {}
    scoring_weights = data.get("scoring_weights", {})
    for domain_sources in data.values():
        if not isinstance(domain_sources, list):
            continue
        for source in domain_sources:
            if not isinstance(source, dict):
                continue
            key = source.get("name", "").lower().replace(" ", "_").replace("(", "").replace(")", "")
            reliability = source.get("reliability", 0.7)
            weights[key] = reliability
            if "mangadex" in key:
                weights["mangadex"] = reliability
            elif "jikan" in key:
                weights["jikan"] = reliability
            elif "anilist" in key:
                weights["anilist"] = reliability
            elif "oricon" in key:
                weights["oricon"] = reliability
            elif "github" in key:
                weights["github"] = reliability
    weights["_fallback_unknown"] = scoring_weights.get("unknown", 0.20)
    return weights


def get_source_reliability(source_key: str, weights: dict) -> float:
    normalized = source_key.lower().replace(" ", "_").replace("(", "").replace(")", "")
    if normalized in weights:
        return weights[normalized]
    for k, v in weights.items():
        if k in normalized or normalized in k:
            return v
    return weights.get("_fallback_unknown", 0.20)


def compute_score(item: dict, weights: dict) -> float:
    source_key = str(item.get("source", "unknown"))
    source_reliability = get_source_reliability(source_key, weights)
    useful_fields = ["title", "id", "source_url"]
    bonus_fields = ["authors", "genres", "score", "year", "status", "description", "studios"]
    required_present = sum(1 for f in useful_fields if item.get(f))
    bonus_present = sum(1 for f in bonus_fields if item.get(f))
    completeness = (required_present / len(useful_fields)) * 0.7 + (min(bonus_present, len(bonus_fields)) / len(bonus_fields)) * 0.3
    has_user_score = bool(item.get("score") and str(item["score"]).replace(".", "").isdigit())
    user_score_bonus = 0.05 if has_user_score else 0.0
    composite = (source_reliability * 0.60) + (completeness * 0.35) + user_score_bonus
    return round(min(composite, 1.0), 4)


def reliability_level(score: float) -> str:
    for threshold, label in RELIABILITY_LEVELS:
        if score >= threshold:
            return label
    return "Incomplet"


def _title_hash(title: str) -> str:
    normalized = title.lower().strip()
    for token in ["the ", "a ", "an ", "le ", "la ", "les ", "un ", "une "]:
        normalized = normalized.replace(token, "")
    normalized = "".join(c for c in normalized if c.isalnum() or c.isspace()).strip()
    return hashlib.md5(normalized.encode()).hexdigest()


def deduplicate(items: list) -> list:
    seen: dict = {}
    for item in items:
        title = str(item.get("title") or item.get("id") or "")
        if not title:
            continue
        h = _title_hash(title)
        if h not in seen:
            seen[h] = item
        else:
            if item.get("_reliability_score", 0.0) > seen[h].get("_reliability_score", 0.0):
                seen[h] = item
    return list(seen.values())


def score_and_filter(items: list, weights: dict, min_score: float = 0.70, deduplicate_results: bool = True) -> list:
    scored = []
    for item in items:
        score = compute_score(item, weights)
        scored.append({**item, "_reliability_score": score, "_reliability_level": reliability_level(score)})
    log.info("Scoring : %d items scores", len(scored))
    if deduplicate_results:
        before = len(scored)
        scored = deduplicate(scored)
        log.info("Deduplication : %d -> %d items", before, len(scored))
    filtered = [i for i in scored if i["_reliability_score"] >= min_score]
    log.info("Filtrage (min=%.2f) : %d -> %d items", min_score, len(scored), len(filtered))
    filtered.sort(key=lambda x: x["_reliability_score"], reverse=True)
    return filtered


def build_output(items: list, min_score: float, original_count: int) -> dict:
    levels: dict = {}
    for item in items:
        lvl = item.get("_reliability_level", "Incomplet")
        levels[lvl] = levels.get(lvl, 0) + 1
    return {
        "status": "success",
        "skill_name": "deep-research-core:score_reliability",
        "skill_version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output": {
            "summary": f"{len(items)} items retenus / {original_count} en entree (seuil={min_score})",
            "data": {
                "total_input": original_count,
                "total_scored": len(items),
                "min_score_threshold": min_score,
                "distribution": levels,
                "items": items,
            },
            "next_steps": ["export_report.py"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Scoring fiabilite TricorderKit")
    parser.add_argument("--input", "-i", help="Fichier JSON (sinon stdin)")
    parser.add_argument("--min-score", type=float, default=0.70)
    parser.add_argument("--no-dedup", action="store_true")
    parser.add_argument("--output", default="json", choices=["json", "table"])
    args = parser.parse_args()

    raw = json.load(open(args.input, encoding="utf-8")) if args.input else json.load(sys.stdin)
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict) and "output" in raw:
        items = raw["output"]["data"].get("items", [])
    else:
        log.error("Format non reconnu")
        sys.exit(1)

    original_count = len(items)
    log.info("%d items en entree", original_count)
    weights = load_source_weights(SOURCES_FILE)
    scored = score_and_filter(items, weights, min_score=args.min_score, deduplicate_results=not args.no_dedup)
    output = build_output(scored, args.min_score, original_count)

    if args.output == "table":
        print(f"\n{'TITRE':<48} {'SOURCE':<14} {'SCORE':>6}  NIVEAU")
        print("-" * 80)
        for item in scored:
            print(f"{str(item.get('title',''))[:47]:<48} {str(item.get('source',''))[:13]:<14} {item['_reliability_score']:>6.4f}  {item['_reliability_level']}")
        print(f"\nTotal : {len(scored)} / {original_count}")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
