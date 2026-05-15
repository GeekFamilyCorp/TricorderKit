"""
deduplicate_findings.py — TricorderKit deep-research-core
Deduplication cross-source avec merge enrichi et fuzzy title matching.

Pipeline attendu :
    collect_sources.py | deduplicate_findings.py | score_reliability.py

Usage :
    python collect_sources.py --query "One Piece" --domain manga | python deduplicate_findings.py
    python deduplicate_findings.py --input results.json
    python deduplicate_findings.py --input results.json --threshold 0.80 --output table

Differ de la dedup integree dans score_reliability :
  - Merge cross-source : "One Piece" vu par MangaDex + Jikan => 1 item avec all_sources[]
  - Fuzzy title matching : "Berserk" ~ "Berserk (2016)" via distance normalisee
  - Rapport de merge : quels items ont ete fusionnes et depuis quelles sources
  - Standalone : peut s'inserer avant OU apres scoring

Version : 0.1.0 — 15/05/2026
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# -- Logging -----------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    stream=sys.stderr,
)
log = logging.getLogger("deduplicate_findings")

# -- Constantes --------------------------------------------------------------
DEFAULT_FUZZY_THRESHOLD = 0.80   # similarite minimale pour considerer deux titres identiques
MAX_ITEMS_REPORT = 100           # cap pour la sortie table


# -- Normalisation de titre --------------------------------------------------

def normalize_title(title: str) -> str:
    """
    Normalisation aggressive pour comparaison :
    - minuscules
    - suppression des articles (the, a, an, le, la, les, un, une)
    - suppression des subtitles entre parentheses : "Berserk (2016)" -> "Berserk"
    - suppression de la ponctuation
    - collapse des espaces
    """
    s = title.lower().strip()
    # Enlever les parentheses et leur contenu
    s = re.sub(r"\([^)]*\)", "", s)
    # Enlever les crochets et leur contenu
    s = re.sub(r"\[[^\]]*\]", "", s)
    # Enlever les articles de debut
    for article in ["the ", "a ", "an ", "le ", "la ", "les ", "un ", "une ", "l'"]:
        if s.startswith(article):
            s = s[len(article):]
    # Enlever la ponctuation
    s = re.sub(r"[^\w\s]", " ", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def title_key(title: str) -> str:
    """Hash MD5 du titre normalise pour bucket exact."""
    return hashlib.md5(normalize_title(title).encode()).hexdigest()


# -- Similarite de Jaccard sur bigrammes -------------------------------------

def bigrams(s: str) -> set[str]:
    """Ensemble de bigrammes d'un string."""
    if len(s) < 2:
        return {s}
    return {s[i:i+2] for i in range(len(s) - 1)}


def jaccard_similarity(a: str, b: str) -> float:
    """Similarite de Jaccard sur bigrammes de caracteres."""
    na, nb = normalize_title(a), normalize_title(b)
    if na == nb:
        return 1.0
    if not na or not nb:
        return 0.0
    ba, bb = bigrams(na), bigrams(nb)
    intersection = len(ba & bb)
    union = len(ba | bb)
    return intersection / union if union > 0 else 0.0


# -- Merge d'items -----------------------------------------------------------

def merge_items(primary: dict, secondary: dict) -> dict:
    """
    Fusionne secondary dans primary :
    - Cumule all_sources (liste de {source, source_url})
    - Enrichit les champs manquants dans primary avec ceux de secondary
    - Conserve le _merge_count pour tracer les fusions
    """
    merged = dict(primary)

    # Initialiser all_sources si absent
    if "all_sources" not in merged:
        merged["all_sources"] = [{
            "source": primary.get("source", "unknown"),
            "source_url": primary.get("source_url", ""),
        }]

    # Ajouter la source secondaire si pas deja presente
    sec_entry = {
        "source": secondary.get("source", "unknown"),
        "source_url": secondary.get("source_url", ""),
    }
    existing_sources = {e["source"] for e in merged["all_sources"]}
    if sec_entry["source"] not in existing_sources:
        merged["all_sources"].append(sec_entry)

    # Enrichir les champs manquants
    enrichment_fields = [
        "title_japanese", "year", "status", "authors", "genres",
        "score", "rank", "studios", "season", "episodes", "tags",
        "description", "language", "topics", "stars",
    ]
    for field in enrichment_fields:
        if not merged.get(field) and secondary.get(field):
            merged[field] = secondary[field]

    # Choisir le meilleur titre (priorite : titre non-vide le plus court sans parentheses)
    if secondary.get("title") and not primary.get("title"):
        merged["title"] = secondary["title"]

    # Compteur de fusions
    merged["_merge_count"] = merged.get("_merge_count", 1) + 1

    return merged


# -- Algorithme de deduplication principal -----------------------------------

class Deduplicator:
    """
    Deduplication en deux passes :
    1. Passe exacte : bucket par hash(normalize_title)
    2. Passe fuzzy  : comparaison Jaccard sur les buckets uniques
    """

    def __init__(self, fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD) -> None:
        self.fuzzy_threshold = fuzzy_threshold
        self.merge_log: list[dict] = []

    def _exact_pass(self, items: list[dict]) -> dict[str, dict]:
        """
        Passe 1 : regroupe les items par hash de titre normalise.
        Returns : {hash -> merged_item}
        """
        buckets: dict[str, dict] = {}
        for item in items:
            title = str(item.get("title") or item.get("id") or "")
            if not title:
                continue
            h = title_key(title)
            if h not in buckets:
                buckets[h] = dict(item)
                if "all_sources" not in buckets[h]:
                    buckets[h]["all_sources"] = [{
                        "source": item.get("source", "unknown"),
                        "source_url": item.get("source_url", ""),
                    }]
            else:
                before_sources = len(buckets[h].get("all_sources", []))
                buckets[h] = merge_items(buckets[h], item)
                after_sources = len(buckets[h].get("all_sources", []))
                if after_sources > before_sources:
                    self.merge_log.append({
                        "type": "exact",
                        "title": buckets[h].get("title"),
                        "merged_from": item.get("source"),
                        "into_sources": [s["source"] for s in buckets[h]["all_sources"]],
                    })
        return buckets

    def _fuzzy_pass(self, buckets: dict[str, dict]) -> list[dict]:
        """
        Passe 2 : fuzzy merge sur les buckets distincts.
        Compare chaque paire de titres normalises ; si Jaccard >= threshold, fusionne.
        O(n^2) — acceptable jusqu'a ~500 items (contexte deep-research, pas big-data).
        """
        items = list(buckets.values())
        if self.fuzzy_threshold >= 1.0:
            return items   # Pas de fuzzy si seuil = 1.0 (exact seulement)

        merged_indices: set[int] = set()
        result: list[dict] = []

        for i in range(len(items)):
            if i in merged_indices:
                continue
            base = items[i]
            base_title = str(base.get("title") or "")
            for j in range(i + 1, len(items)):
                if j in merged_indices:
                    continue
                candidate = items[j]
                cand_title = str(candidate.get("title") or "")
                if not base_title or not cand_title:
                    continue
                sim = jaccard_similarity(base_title, cand_title)
                if sim >= self.fuzzy_threshold:
                    base = merge_items(base, candidate)
                    merged_indices.add(j)
                    self.merge_log.append({
                        "type": "fuzzy",
                        "similarity": round(sim, 4),
                        "title_a": base_title,
                        "title_b": cand_title,
                        "merged_into": base.get("title"),
                        "result_sources": [s["source"] for s in base.get("all_sources", [])],
                    })
            result.append(base)

        return result

    def run(self, items: list[dict]) -> list[dict]:
        original_count = len(items)
        buckets = self._exact_pass(items)
        after_exact = len(buckets)
        result = self._fuzzy_pass(buckets)
        after_fuzzy = len(result)

        log.info(
            "Dedup : %d -> %d (exact) -> %d (fuzzy, seuil=%.2f) — %d fusions",
            original_count, after_exact, after_fuzzy,
            self.fuzzy_threshold, len(self.merge_log),
        )
        return result


# -- Output contract ---------------------------------------------------------

def build_output(
    items_out: list[dict],
    original_count: int,
    fuzzy_threshold: float,
    merge_log: list[dict],
) -> dict:
    exact_merges = sum(1 for m in merge_log if m["type"] == "exact")
    fuzzy_merges = sum(1 for m in merge_log if m["type"] == "fuzzy")
    multi_source_count = sum(1 for i in items_out if len(i.get("all_sources", [])) > 1)

    return {
        "status": "success",
        "skill_name": "deep-research-core:deduplicate_findings",
        "skill_version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output": {
            "summary": (
                "{} items uniques / {} en entree "
                "({} fusions exactes, {} fuzzy, {} cross-source)".format(
                    len(items_out), original_count,
                    exact_merges, fuzzy_merges, multi_source_count,
                )
            ),
            "data": {
                "original_count": original_count,
                "deduplicated_count": len(items_out),
                "exact_merges": exact_merges,
                "fuzzy_merges": fuzzy_merges,
                "multi_source_items": multi_source_count,
                "fuzzy_threshold": fuzzy_threshold,
                "merge_log": merge_log[:50],   # cap pour ne pas exploser le JSON
                "items": items_out,
            },
            "next_steps": ["score_reliability.py"],
        },
    }


# -- CLI ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Deduplication cross-source TricorderKit")
    parser.add_argument("--input", "-i", help="Fichier JSON en entree (sinon stdin)")
    parser.add_argument(
        "--threshold", "-t", type=float, default=DEFAULT_FUZZY_THRESHOLD,
        help="Seuil de similarite Jaccard pour fuzzy merge (0.0-1.0, defaut=0.80)",
    )
    parser.add_argument(
        "--no-fuzzy", action="store_true",
        help="Desactiver le fuzzy matching (dedup exacte uniquement)",
    )
    parser.add_argument("--output", default="json", choices=["json", "table"])
    args = parser.parse_args()

    # Lecture input
    if args.input:
        with open(args.input, encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raw = json.load(sys.stdin)

    # Support liste directe ou skill_output enveloppe
    if isinstance(raw, list):
        items: list[dict] = raw
    elif isinstance(raw, dict) and "output" in raw:
        items = raw["output"]["data"].get("items", [])
    else:
        log.error("Format d'entree non reconnu")
        sys.exit(1)

    original_count = len(items)
    log.info("%d items en entree", original_count)

    threshold = 1.0 if args.no_fuzzy else args.threshold
    dedup = Deduplicator(fuzzy_threshold=threshold)
    result_items = dedup.run(items)

    output = build_output(result_items, original_count, threshold, dedup.merge_log)

    if args.output == "table":
        print("\n{:<50} {:<6} {:<30}".format("TITRE", "SRCS", "SOURCES"))
        print("-" * 90)
        for item in result_items[:MAX_ITEMS_REPORT]:
            sources_str = ", ".join(s["source"] for s in item.get("all_sources", [{"source": item.get("source", "?")}]))
            print("{:<50} {:<6} {:<30}".format(
                str(item.get("title", ""))[:49],
                len(item.get("all_sources", [1])),
                sources_str[:29],
            ))
        print("\nTotal : {} items uniques / {} en entree".format(len(result_items), original_count))
        if dedup.merge_log:
            print("\nFusions ({}) :".format(len(dedup.merge_log)))
            for m in dedup.merge_log[:10]:
                if m["type"] == "fuzzy":
                    print("  [fuzzy {:.2f}] '{}' ~ '{}'".format(
                        m["similarity"], m["title_a"][:30], m["title_b"][:30]))
                else:
                    print("  [exact] '{}' <- {}".format(
                        str(m.get("title", ""))[:30], m.get("merged_from", "")))
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
