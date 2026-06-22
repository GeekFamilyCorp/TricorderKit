#!/usr/bin/env python3
"""
experiments/temporal_memory — PoC #3 (god-mode) : mémoire temporelle (Graphiti/Zep-inspirée).

PoC ISOLÉ, hors-ligne, sans dépendance lourde. Ne touche pas au cœur, n'écrit aucun vault.
Objectif : prouver qu'une couche de mémoire BI-TEMPORELLE (faits datés valid_from/valid_to)
répond mieux aux questions "que savait-on à l'instant T ?" qu'un simple full-context,
et à moindre coût en tokens.

Deux moteurs (même esprit que ragas_eval.py) :
  - memory (défaut) : store bi-temporel pur-Python, déterministe, tourne tout de suite.
  - neo4j (optionnel) : même schéma sur Neo4j si NEO4J_URL est défini (repli sur memory sinon).

Schéma d'un fait : (entity, attribute, value, valid_from, valid_to, recorded_at, source).
Quand un nouveau fait (entity, attribute) arrive à valid_from=t, il CLÔTURE le fait courant
précédent (valid_to=t). Une requête as_of(entity, attribute, t) renvoie la valeur valide à t.

Métriques :
  - temporal_accuracy : fraction de requêtes du benchmark dont la valeur as-of est correcte.
  - token_proxy : coût estimé (≈ chars/4) du contexte envoyé au LLM, store temporel
    (slice pertinent) vs full-context (tous les épisodes concaténés). On reporte le gain.

Usage :
    python temporal_memory.py --selftest
    python temporal_memory.py --dataset sample_episodes.jsonl
    python temporal_memory.py --dataset sample_episodes.jsonl --engine neo4j

Format JSONL d'entrée (deux types de lignes) :
    {"type":"episode","entity":"X","attribute":"role","value":"...","valid_from":"2026-01-01","source":"..."}
    {"type":"query","entity":"X","attribute":"role","as_of":"2026-03-01","expected":"..."}
Réf. : Awesome-Agent-Memory (TeleAI-UAGI), comparatifs Zep/Graphiti/Mem0 2026 — cf. radar.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from bisect import bisect_right
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

INF_DATE = "9999-12-31"


def _parse_day(s: str) -> date:
    """Tolérant : accepte YYYY-MM-DD ou ISO datetime."""
    s = (s or "").strip()
    if not s:
        raise ValueError("date vide")
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return datetime.fromisoformat(s).date()


def estimate_tokens(text: str) -> int:
    """Proxy hors-ligne du coût en tokens : ~4 caractères par token."""
    return max(1, len(text) // 4)


@dataclass
class Fact:
    entity: str
    attribute: str
    value: str
    valid_from: date
    valid_to: date
    source: str = ""
    recorded_at: Optional[date] = None

    def text(self) -> str:
        end = "" if self.valid_to.isoformat() == INF_DATE else self.valid_to.isoformat()
        return (f"{self.entity}.{self.attribute} = {self.value} "
                f"[{self.valid_from.isoformat()}..{end or 'now'}] ({self.source})")


@dataclass
class MemoryEngine:
    """Store bi-temporel pur-Python. Faits indexés par (entity, attribute), triés par valid_from."""
    _by_key: dict = field(default_factory=dict)
    _episodes_raw: list = field(default_factory=list)

    def add_episode(self, entity: str, attribute: str, value: str,
                    valid_from: str, source: str = "") -> None:
        vf = _parse_day(valid_from)
        key = (entity, attribute)
        facts = self._by_key.setdefault(key, [])
        # Clôture le fait courant ouvert qui précède : son valid_to devient vf.
        for f in facts:
            if f.valid_from <= vf and f.valid_to == _parse_day(INF_DATE):
                f.valid_to = vf
        facts.append(Fact(entity, attribute, value, vf, _parse_day(INF_DATE), source, vf))
        facts.sort(key=lambda f: f.valid_from)
        self._episodes_raw.append(
            f"[{valid_from}] {entity}.{attribute} := {value} (source: {source})")

    def as_of(self, entity: str, attribute: str, as_of: str) -> Optional[Fact]:
        """Renvoie le fait valide à la date 'as_of' (valid_from <= t < valid_to)."""
        t = _parse_day(as_of)
        facts = self._by_key.get((entity, attribute), [])
        starts = [f.valid_from for f in facts]
        idx = bisect_right(starts, t) - 1
        if idx < 0:
            return None
        f = facts[idx]
        return f if f.valid_from <= t < f.valid_to else None

    def context_for(self, entity: str, attribute: str, as_of: str) -> str:
        """Contexte TEMPOREL minimal : le seul fait pertinent (ou rien)."""
        f = self.as_of(entity, attribute, as_of)
        return f.text() if f else ""

    def full_context(self) -> str:
        """Contexte NAÏF : tous les épisodes concaténés (baseline coûteuse)."""
        return "\n".join(self._episodes_raw)


def build_neo4j_engine():
    """Optionnel : même API que MemoryEngine via Neo4j. Repli silencieux sur memory."""
    url = os.environ.get("NEO4J_URL")
    if not url:
        return None
    try:
        from neo4j import GraphDatabase  # noqa: F401
    except Exception:
        print("[temporal_memory] neo4j non installé -> repli moteur 'memory'.", file=sys.stderr)
        return None
    # NB : le schéma Cypher (noeud :Fact {valid_from, valid_to, source}) est documenté dans
    # README.md. Pour ce PoC isolé, on conserve la logique de référence en mémoire ; le
    # backend Neo4j sera branché lors d'une promotion (DEC), une fois la mesure validée.
    print("[temporal_memory] NEO4J_URL détecté mais backend non encore câblé "
          "(PoC isolé) -> repli moteur 'memory'.", file=sys.stderr)
    return None


def load_dataset(path: str):
    episodes, queries = [], []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = json.loads(line)
            if row.get("type") == "query":
                queries.append(row)
            else:
                episodes.append(row)
    return episodes, queries


def run(engine: MemoryEngine, episodes: list, queries: list) -> dict:
    for ep in episodes:
        engine.add_episode(ep["entity"], ep["attribute"], str(ep["value"]),
                           ep["valid_from"], ep.get("source", ""))

    correct = 0
    temporal_tokens = 0
    details = []
    for q in queries:
        f = engine.as_of(q["entity"], q["attribute"], q["as_of"])
        got = f.value if f else None
        exp = None if q.get("expected") in (None, "", "None") else str(q["expected"])
        ok = (got == exp)
        correct += int(ok)
        temporal_tokens += estimate_tokens(engine.context_for(
            q["entity"], q["attribute"], q["as_of"]))
        details.append({"q": f"{q['entity']}.{q['attribute']} @ {q['as_of']}",
                        "expected": exp, "got": got, "ok": ok})

    n = max(1, len(queries))
    full_ctx = engine.full_context()
    # Baseline full-context : on renvoie TOUT le contexte à chaque requête.
    full_tokens = estimate_tokens(full_ctx) * len(queries)
    saving = 0.0 if full_tokens == 0 else (1 - temporal_tokens / full_tokens)
    return {
        "temporal_accuracy": correct / n,
        "queries": len(queries),
        "correct": correct,
        "tokens_temporal": temporal_tokens,
        "tokens_full_context": full_tokens,
        "token_saving_ratio": round(saving, 3),
        "details": details,
    }


# --- Jeu de selftest embarqué : faits à validité changeante dans le temps -------------------
_SELFTEST_EPISODES = [
    {"entity": "projet_alpha", "attribute": "lead", "value": "Ada",
     "valid_from": "2026-01-01", "source": "kickoff"},
    {"entity": "projet_alpha", "attribute": "lead", "value": "Bel",
     "valid_from": "2026-04-01", "source": "réorg Q2"},
    {"entity": "projet_alpha", "attribute": "status", "value": "design",
     "valid_from": "2026-01-01", "source": "kickoff"},
    {"entity": "projet_alpha", "attribute": "status", "value": "build",
     "valid_from": "2026-03-15", "source": "revue"},
    {"entity": "projet_alpha", "attribute": "status", "value": "ship",
     "valid_from": "2026-06-01", "source": "go-live"},
]
_SELFTEST_QUERIES = [
    {"entity": "projet_alpha", "attribute": "lead", "as_of": "2026-02-01", "expected": "Ada"},
    {"entity": "projet_alpha", "attribute": "lead", "as_of": "2026-05-01", "expected": "Bel"},
    {"entity": "projet_alpha", "attribute": "status", "as_of": "2026-01-10", "expected": "design"},
    {"entity": "projet_alpha", "attribute": "status", "as_of": "2026-04-01", "expected": "build"},
    {"entity": "projet_alpha", "attribute": "status", "as_of": "2026-06-10", "expected": "ship"},
    {"entity": "projet_alpha", "attribute": "lead", "as_of": "2025-12-01", "expected": None},
]


def selftest() -> int:
    res = run(MemoryEngine(), list(_SELFTEST_EPISODES), list(_SELFTEST_QUERIES))
    print(json.dumps({k: v for k, v in res.items() if k != "details"},
                     ensure_ascii=False, indent=2))
    for d in res["details"]:
        flag = "OK " if d["ok"] else "XX "
        print(f"  {flag} {d['q']}: attendu={d['expected']!r} obtenu={d['got']!r}")
    ok_acc = res["temporal_accuracy"] == 1.0
    ok_saving = res["token_saving_ratio"] > 0.0  # le slice temporel doit coûter moins cher
    if ok_acc and ok_saving:
        print(f"\n[selftest] OK — exactitude temporelle 100%, "
              f"économie tokens {res['token_saving_ratio']*100:.0f}% vs full-context.")
        return 0
    print("\n[selftest] ÉCHEC — vérifier la logique bi-temporelle.", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="PoC #3 mémoire temporelle (god-mode).")
    ap.add_argument("--selftest", action="store_true", help="jeu embarqué + assertions")
    ap.add_argument("--dataset", help="JSONL d'épisodes + requêtes")
    ap.add_argument("--engine", choices=["memory", "neo4j"], default="memory")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.dataset:
        ap.print_help()
        return 2

    engine = None
    if args.engine == "neo4j":
        engine = build_neo4j_engine()
    if engine is None:
        engine = MemoryEngine()

    episodes, queries = load_dataset(args.dataset)
    res = run(engine, episodes, queries)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
