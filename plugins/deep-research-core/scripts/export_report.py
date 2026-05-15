"""
export_report.py — TricorderKit deep-research-core
Generateur de rapport Markdown / Obsidian depuis scored findings.

Pipeline attendu :
    collect_sources.py | deduplicate_findings.py | score_reliability.py | export_report.py

Usage :
    python score_reliability.py --input findings.json | python export_report.py
    python export_report.py --input scored.json --format obsidian --output rapport.md
    python export_report.py --input scored.json --format markdown --title "One Piece — Recherche"

Formats :
  markdown  — Markdown pur, tables GitHub Flavored, pas de frontmatter
  obsidian  — Markdown + YAML frontmatter compatible Obsidian (tags, aliases, date)

Version : 0.1.0 — 15/05/2026
"""

from __future__ import annotations

import argparse
import json
import logging
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
log = logging.getLogger("export_report")

# -- Constantes --------------------------------------------------------------
RELIABILITY_ORDER = [
    "Confirme",
    "Probable",
    "A verifier",
    "Incomplet",
]

# Correspondance entre emoji-label et label ASCII (pour tri et frontmatter)
LEVEL_ASCII = {
    "Confirme": "confirme",
    "Probable": "probable",
    "A verifier": "a_verifier",
    "Incomplet": "incomplet",
}

# Icone par niveau
LEVEL_ICON = {
    "Confirme": "green_circle",
    "Probable": "yellow_circle",
    "A verifier": "orange_circle",
    "Incomplet": "red_circle",
}


# -- Normalisation du niveau -------------------------------------------------

def normalize_level(raw_level: str) -> str:
    """
    Convertit les labels emoji (score_reliability) en labels ASCII simples.
    Exemples :
        "Confirme" -> "Confirme"
        "Probable" -> "Probable"
    """
    if not raw_level:
        return "Incomplet"
    for key in RELIABILITY_ORDER:
        if key.lower().replace(" ", "") in raw_level.lower().replace(" ", ""):
            return key
    return "Incomplet"


# -- Formatage des cellules --------------------------------------------------

def _cell(value: Any, max_len: int = 40) -> str:
    if value is None:
        return "—"
    s = str(value)
    if isinstance(value, list):
        s = ", ".join(str(v) for v in value[:3])
        if len(value) > 3:
            s += "…"
    return s[:max_len] if len(s) > max_len else s


def _sources_cell(item: dict) -> str:
    """Formate la colonne sources avec liens Markdown."""
    all_sources = item.get("all_sources", [])
    if not all_sources:
        src = item.get("source", "")
        url = item.get("source_url", "")
        if url:
            return "[{}]({})".format(src, url)
        return src or "—"
    parts = []
    for s in all_sources[:3]:
        name = s.get("source", "")
        url = s.get("source_url", "")
        parts.append("[{}]({})".format(name, url) if url else name)
    if len(all_sources) > 3:
        parts.append("+{}".format(len(all_sources) - 3))
    return " · ".join(parts)


# -- Generateur Markdown pur -------------------------------------------------

def generate_markdown(
    items: list[dict],
    query: str,
    domain: str,
    title: str,
    original_count: int,
    min_score: float,
) -> str:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines: list[str] = []

    lines.append("# {}".format(title))
    lines.append("")
    lines.append("> **Domaine** : {}  |  **Requete** : `{}`  |  **Date** : {}".format(
        domain, query, now_str))
    lines.append("> {} items retenus / {} en entree (seuil fiabilite : {:.0%})".format(
        len(items), original_count, min_score))
    lines.append("")

    # Grouper par niveau de fiabilite
    groups: dict[str, list[dict]] = {lvl: [] for lvl in RELIABILITY_ORDER}
    for item in items:
        raw = item.get("_reliability_level", "Incomplet")
        lvl = normalize_level(raw)
        groups[lvl].append(item)

    for lvl in RELIABILITY_ORDER:
        group = groups[lvl]
        if not group:
            continue
        lines.append("## {} {} ({})".format(
            raw_icon_for_level(lvl), lvl, len(group)))
        lines.append("")
        lines.append("| Titre | Auteurs/Studios | Score | Sources |")
        lines.append("|---|---|---:|---|")
        for item in group:
            title_cell = _cell(item.get("title") or item.get("id"), 45)
            creators = (
                item.get("authors")
                or item.get("studios")
                or item.get("description", "")
            )
            creators_cell = _cell(creators, 35)
            score_val = item.get("_reliability_score")
            score_cell = "{:.3f}".format(score_val) if score_val is not None else "—"
            sources_cell = _sources_cell(item)
            lines.append("| {} | {} | {} | {} |".format(
                title_cell, creators_cell, score_cell, sources_cell))
        lines.append("")

    lines.append("---")
    lines.append("*Rapport genere par `deep-research-core:export_report` v0.1.0*")
    lines.append("")

    return "\n".join(lines)


def raw_icon_for_level(lvl: str) -> str:
    icons = {
        "Confirme": "✅",
        "Probable": "🟡",
        "A verifier": "🟠",
        "Incomplet": "🔴",
    }
    return icons.get(lvl, "❓")


# -- Generateur Obsidian (frontmatter YAML + Markdown) -----------------------

def generate_obsidian(
    items: list[dict],
    query: str,
    domain: str,
    title: str,
    original_count: int,
    min_score: float,
) -> str:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_iso = datetime.now(timezone.utc).isoformat()

    # Tags automatiques depuis les items
    all_genres: list[str] = []
    for item in items[:20]:
        for g in (item.get("genres") or item.get("tags") or []):
            if isinstance(g, str) and g:
                tag = g.lower().replace(" ", "-").replace("/", "-")
                if tag not in all_genres:
                    all_genres.append(tag)
    tags = ["deep-research", domain] + all_genres[:5]

    # Frontmatter YAML
    fm_lines = ["---"]
    fm_lines.append("title: \"{}\"".format(title.replace('"', "'")))
    fm_lines.append("date: {}".format(now_str))
    fm_lines.append("domain: {}".format(domain))
    fm_lines.append("query: \"{}\"".format(query.replace('"', "'")))
    fm_lines.append("source: deep-research-core")
    fm_lines.append("version: 0.1.0")
    fm_lines.append("items_total: {}".format(len(items)))
    fm_lines.append("items_input: {}".format(original_count))
    fm_lines.append("min_score: {}".format(min_score))
    fm_lines.append("generated_at: {}".format(now_iso))
    fm_lines.append("tags:")
    for tag in tags:
        fm_lines.append("  - {}".format(tag))
    fm_lines.append("---")
    fm_lines.append("")

    body = generate_markdown(items, query, domain, title, original_count, min_score)
    return "\n".join(fm_lines) + body


# -- Extraction des metadonnees depuis skill_output --------------------------

def extract_metadata(raw: dict) -> tuple[str, str, int, float]:
    """Retourne (query, domain, original_count, min_score) depuis un skill_output."""
    data = raw.get("output", {}).get("data", {})
    query = data.get("query", "unknown")
    domain = data.get("domain", "unknown")
    original_count = data.get("total_input", len(data.get("items", [])))
    min_score = data.get("min_score_threshold", 0.70)
    return query, domain, original_count, min_score


# -- Output contract ---------------------------------------------------------

def build_output(
    report_content: str,
    output_file: str | None,
    report_format: str,
    items_count: int,
) -> dict:
    written_to = output_file or "(stdout)"
    return {
        "status": "success",
        "skill_name": "deep-research-core:export_report",
        "skill_version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output": {
            "summary": "{} items exportes au format {} vers {}".format(
                items_count, report_format, written_to),
            "data": {
                "format": report_format,
                "output_file": written_to,
                "items_exported": items_count,
                "report_size_chars": len(report_content),
            },
            "next_steps": ["Indexation Qdrant (collection manga_knowledge)"],
        },
    }


# -- CLI ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Export rapport Markdown TricorderKit")
    parser.add_argument("--input", "-i", help="Fichier JSON en entree (sinon stdin)")
    parser.add_argument(
        "--format", "-f", default="obsidian", choices=["markdown", "obsidian"],
        help="Format de sortie (defaut : obsidian)",
    )
    parser.add_argument("--output", "-o", help="Fichier .md de destination (sinon stdout)")
    parser.add_argument("--title", help="Titre du rapport (defaut : auto depuis query+domain)")
    parser.add_argument("--emit-json", action="store_true",
                        help="Ecrire le rapport .md ET emettre un skill_output JSON sur stdout")
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
        query, domain, original_count, min_score = "unknown", "unknown", len(raw), 0.70
    elif isinstance(raw, dict) and "output" in raw:
        items = raw["output"]["data"].get("items", [])
        query, domain, original_count, min_score = extract_metadata(raw)
    else:
        log.error("Format d'entree non reconnu")
        sys.exit(1)

    log.info("%d items en entree pour le rapport", len(items))

    # Titre auto si non fourni
    report_title = args.title or "Recherche {} — {}".format(domain.capitalize(), query)

    # Generation
    if args.format == "obsidian":
        content = generate_obsidian(items, query, domain, report_title, original_count, min_score)
    else:
        content = generate_markdown(items, query, domain, report_title, original_count, min_score)

    # Ecriture
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        log.info("Rapport ecrit : %s (%d chars)", args.output, len(content))

    # Sortie
    if args.emit_json or not args.output:
        if args.emit_json and args.output:
            # JSON sur stdout, rapport dans le fichier
            skill_out = build_output(content, args.output, args.format, len(items))
            print(json.dumps(skill_out, ensure_ascii=False, indent=2))
        else:
            # Rapport Markdown sur stdout
            print(content)


if __name__ == "__main__":
    main()
