#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_source_registry.py — Génère source_registry.yaml depuis un registre normalisé
(DEC-046, Phase 2 / N2).

Principe (Règle « registre généré, jamais écrit à la main ») : on lit un registre
normalisé en **lecture seule** (markdown avec un tableau de sources) et on produit
un `source_registry.yaml` déterministe. Générique : aucun nom de projet/source codé
en dur — le chemin d'entrée et le scope sont des paramètres.

Format d'entrée attendu (markdown) : un tableau dont l'en-tête contient au moins
les colonnes `name` et `url` (insensible à la casse). Colonnes optionnelles
reconnues : `type`, `official` (oui/non/true/false), `profile`.

  python gen_source_registry.py --in 35_Normalized_Registry.md --out source_registry.yaml
  python gen_source_registry.py --in reg.md --format json   # aperçu sans écrire (dry-run)

Sortie : YAML (ou JSON avec --format json). Dry-run par défaut (n'écrit que si --out).
Zéro dépendance pip (pas de PyYAML) : sérialiseur YAML minimal interne.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VALID_PROFILES = {"static_html", "markdown_rag", "dynamic_browser"}
_TRUE = {"oui", "yes", "true", "1", "✅", "officiel", "official"}


def parse_markdown_table(text: str) -> list[dict]:
    """Extrait les lignes du premier tableau markdown contenant 'name' et 'url'."""
    rows: list[dict] = []
    header: list[str] | None = None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if re.fullmatch(r"[\s:|-]+", s):  # ligne de séparation ---|---
            continue
        low = [c.lower() for c in cells]
        if header is None:
            if "name" in low and "url" in low:
                header = low
            continue
        row = dict(zip(header, cells))
        if row.get("name") and row.get("url"):
            rows.append(row)
    return rows


def normalize(rows: list[dict]) -> list[dict]:
    out = []
    seen = set()
    for r in rows:
        url = r["url"].strip().strip("<>")
        if url in seen:
            continue
        seen.add(url)
        prof = (r.get("profile") or "").strip().lower()
        entry = {"name": r["name"].strip(), "url": url}
        if r.get("type"):
            entry["type"] = r["type"].strip()
        if "official" in r:
            entry["official"] = r["official"].strip().lower() in _TRUE
        if prof in VALID_PROFILES:
            entry["profile"] = prof
        out.append(entry)
    return out


def _yaml_scalar(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    if s == "" or re.search(r"[:#\[\]{}&*!|>'\"%@`]", s) or s != s.strip():
        return '"' + s.replace('"', '\\"') + '"'
    return s


def to_yaml(entries: list[dict], scope: str | None) -> str:
    lines = ["# source_registry.yaml — GÉNÉRÉ par gen_source_registry.py (ne pas éditer à la main)",
             "# DEC-046 / N2 — regénérer depuis le registre normalisé."]
    if scope:
        lines.append(f"project_scope: {_yaml_scalar(scope)}")
    lines.append(f"count: {len(entries)}")
    lines.append("sources:")
    for e in entries:
        lines.append(f"  - name: {_yaml_scalar(e['name'])}")
        lines.append(f"    url: {_yaml_scalar(e['url'])}")
        for k in ("type", "official", "profile"):
            if k in e:
                lines.append(f"    {k}: {_yaml_scalar(e[k])}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Génère source_registry.yaml depuis un registre normalisé (lecture seule).")
    ap.add_argument("--in", dest="inp", required=True, help="Registre normalisé (markdown, lecture seule)")
    ap.add_argument("--out", default=None, help="Fichier de sortie (sinon: aperçu stdout = dry-run)")
    ap.add_argument("--project-scope", default=None, help="Scope projet (chaîne libre, optionnel)")
    ap.add_argument("--format", choices=["yaml", "json"], default="yaml")
    args = ap.parse_args(argv)

    src = Path(args.inp)
    if not src.exists():
        print(f"[ERR] introuvable: {src}", file=sys.stderr)
        return 2
    rows = parse_markdown_table(src.read_text(encoding="utf-8", errors="replace"))
    entries = normalize(rows)
    if not entries:
        print("[ERR] aucune source (name+url) trouvée dans le registre", file=sys.stderr)
        return 1

    if args.format == "json":
        import json
        payload = {"project_scope": args.project_scope, "count": len(entries), "sources": entries}
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        rendered = to_yaml(entries, args.project_scope)

    if args.out:
        Path(args.out).write_text(rendered, encoding="utf-8")
        print(f"[OK] {len(entries)} sources -> {args.out}")
    else:
        print(rendered)  # dry-run: aperçu seulement
    return 0


if __name__ == "__main__":
    sys.exit(main())
