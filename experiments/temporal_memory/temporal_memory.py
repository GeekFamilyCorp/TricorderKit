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


class SqliteEngine:
    """Backend RÉEL persistant (stdlib sqlite3, zéro dépendance). Même API que MemoryEngine.

    Choisi pour la portabilité : tourne à l'identique sur le poste ET sur le VPS
    (qui utilise déjà SQLite : state.db / paperclip_state.json), sans nouvelle infra.
    Les dates sont stockées en ISO (YYYY-MM-DD) -> comparaison lexicale = ordre chronologique.
    """

    def __init__(self, db_path: str = ":memory:"):
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS temporal_facts (
                entity TEXT, attribute TEXT, value TEXT,
                valid_from TEXT, valid_to TEXT, source TEXT, recorded_at TEXT
            )""")
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tf ON temporal_facts(entity, attribute, valid_from)")
        self.conn.commit()

    def add_episode(self, entity, attribute, value, valid_from, source=""):
        vf = _parse_day(valid_from).isoformat()
        # Clôture le fait courant ouvert qui précède : valid_to <- vf.
        self.conn.execute(
            "UPDATE temporal_facts SET valid_to=? "
            "WHERE entity=? AND attribute=? AND valid_to=? AND valid_from<=?",
            (vf, entity, attribute, INF_DATE, vf))
        self.conn.execute(
            "INSERT INTO temporal_facts VALUES (?,?,?,?,?,?,?)",
            (entity, attribute, str(value), vf, INF_DATE, source, vf))
        self.conn.commit()

    def as_of(self, entity, attribute, as_of) -> Optional[Fact]:
        t = _parse_day(as_of).isoformat()
        row = self.conn.execute(
            "SELECT entity, attribute, value, valid_from, valid_to, source, recorded_at "
            "FROM temporal_facts WHERE entity=? AND attribute=? AND valid_from<=? AND valid_to>? "
            "ORDER BY valid_from DESC LIMIT 1",
            (entity, attribute, t, t)).fetchone()
        if not row:
            return None
        return Fact(row[0], row[1], row[2], _parse_day(row[3]), _parse_day(row[4]),
                    row[5] or "", _parse_day(row[6]) if row[6] else None)

    def context_for(self, entity, attribute, as_of) -> str:
        f = self.as_of(entity, attribute, as_of)
        return f.text() if f else ""

    def full_context(self) -> str:
        rows = self.conn.execute(
            "SELECT valid_from, entity, attribute, value, source FROM temporal_facts "
            "ORDER BY valid_from").fetchall()
        return "\n".join(f"[{r[0]}] {r[1]}.{r[2]} := {r[3]} (source: {r[4]})" for r in rows)


def build_neo4j_engine():
    """Option FUTURE (non prioritaire) : même API via Neo4j si NEO4J_URL est défini.

    Conservé pour mémoire : sur la cible VPS (Hermes/Paperclip) il n'y a PAS de Neo4j,
    donc le backend réel recommandé est SqliteEngine. Repli silencieux ici.
    """
    if not os.environ.get("NEO4J_URL"):
        return None
    print("[temporal_memory] Neo4j non retenu pour la cible VPS -> utiliser --engine sqlite.",
          file=sys.stderr)
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

    # Parité moteur RÉEL : SqliteEngine (en mémoire) doit donner exactement le même résultat.
    res_sql = run(SqliteEngine(":memory:"), list(_SELFTEST_EPISODES), list(_SELFTEST_QUERIES))
    ok_parity = (res_sql["temporal_accuracy"] == res["temporal_accuracy"]
                 and res_sql["correct"] == res["correct"])

    # Persistance : ré-ouvrir un fichier .db et relire un fait passé doit fonctionner.
    import tempfile
    import os as _os
    tmp = _os.path.join(tempfile.gettempdir(), "tk_temporal_selftest.db")
    if _os.path.exists(tmp):
        _os.remove(tmp)
    e1 = SqliteEngine(tmp)
    for ep in _SELFTEST_EPISODES:
        e1.add_episode(ep["entity"], ep["attribute"], ep["value"], ep["valid_from"],
                       ep.get("source", ""))
    e1.conn.close()
    e2 = SqliteEngine(tmp)  # ré-ouverture
    f = e2.as_of("projet_alpha", "lead", "2026-02-01")
    ok_persist = (f is not None and f.value == "Ada")
    e2.conn.close()
    _os.remove(tmp)

    if ok_acc and ok_saving and ok_parity and ok_persist:
        print(f"\n[selftest] OK — exactitude temporelle 100%, "
              f"économie tokens {res['token_saving_ratio']*100:.0f}% vs full-context ; "
              f"parité moteur sqlite OK ; persistance disque OK.")
        return 0
    print(f"\n[selftest] ÉCHEC — acc={ok_acc} saving={ok_saving} "
          f"parite_sqlite={ok_parity} persist={ok_persist}.", file=sys.stderr)
    return 1


def make_engine(name: str, db_path: str):
    if name == "sqlite":
        return SqliteEngine(db_path or ":memory:")
    if name == "neo4j":
        eng = build_neo4j_engine()
        if eng is not None:
            return eng
        print("[temporal_memory] repli moteur 'memory'.", file=sys.stderr)
    return MemoryEngine()


def main() -> int:
    ap = argparse.ArgumentParser(description="PoC #3 mémoire temporelle (god-mode).")
    ap.add_argument("--selftest", action="store_true", help="jeu embarqué + assertions")
    ap.add_argument("--dataset", help="JSONL d'épisodes + requêtes")
    ap.add_argument("--engine", choices=["memory", "sqlite", "neo4j"], default="memory")
    ap.add_argument("--db", default=":memory:", help="chemin .db pour --engine sqlite")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.dataset:
        ap.print_help()
        return 2

    engine = make_engine(args.engine, args.db)
    episodes, queries = load_dataset(args.dataset)
    res = run(engine, episodes, queries)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
