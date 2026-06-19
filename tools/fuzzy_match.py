#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fuzzy_match.py — appariement flou rapide (RapidFuzz). Generique, leger, zero modele/GPU.

Quick-win dedup (tool-scout 2026-06-19) : remplace FuzzyWuzzy ; matching romaji/titres,
detection de doublons. C++ sous le capot -> rapide, faible empreinte.

Usage :
  python tools/fuzzy_match.py match --query "One Piece" --choices "one piece,naruto" [--threshold 85]
  python tools/fuzzy_match.py --selftest

API : best_match(query, choices, threshold) -> {match, score} | None
      dedup(items, threshold) -> [[doublons...]]
Pre-requis : pip install rapidfuzz
"""
from __future__ import annotations
import argparse, json, re, sys, unicodedata

try:
    from rapidfuzz import fuzz, process
    HAVE = True
except Exception:
    HAVE = False


def norm(s) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower()).strip()


def best_match(query, choices, threshold: float = 85.0):
    if not HAVE:
        return None
    nmap = {norm(c): c for c in choices}
    r = process.extractOne(norm(query), list(nmap.keys()), scorer=fuzz.token_sort_ratio)
    if r and r[1] >= threshold:
        return {"match": nmap[r[0]], "score": round(r[1], 1)}
    return None


def dedup(items, threshold: float = 90.0):
    """Groupes de doublons probables (par token_sort_ratio)."""
    if not HAVE:
        return []
    n = [norm(x) for x in items]
    seen, groups = set(), []
    for i in range(len(items)):
        if i in seen:
            continue
        grp = [items[i]]
        for j in range(i + 1, len(items)):
            if j not in seen and fuzz.token_sort_ratio(n[i], n[j]) >= threshold:
                grp.append(items[j]); seen.add(j)
        if len(grp) > 1:
            groups.append(grp)
    return groups


def _selftest() -> int:
    assert HAVE, "rapidfuzz absent (pip install rapidfuzz)"
    assert best_match("One Piece", ["one piece", "naruto"])["match"] == "one piece"
    assert best_match("Eiichiro Oda", ["Oda Eiichiro", "Akira Toriyama"], 70) is not None
    assert any(len(g) == 2 for g in dedup(["Chainsaw Man", "chainsaw  man", "Naruto"]))
    print(json.dumps({"ok": True, "rapidfuzz": True, "tests": "passed"}))
    return 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="fuzzy-match")
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    m = sub.add_parser("match")
    m.add_argument("--query", required=True)
    m.add_argument("--choices", required=True, help="liste separee par des virgules")
    m.add_argument("--threshold", type=float, default=85.0)
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not HAVE:
        print(json.dumps({"status": "error", "detail": "pip install rapidfuzz"})); return 1
    if a.cmd == "match":
        choices = [c for c in a.choices.split(",") if c.strip()]
        print(json.dumps(best_match(a.query, choices, a.threshold) or {"match": None}, ensure_ascii=False))
        return 0
    ap.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
