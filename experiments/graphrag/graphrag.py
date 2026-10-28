#!/usr/bin/env python3
"""
experiments/graphrag — PoC #4 (god-mode) : récupération entité-relation (GraphRAG).

PoC ISOLÉ, hors-ligne, sans dépendance lourde. Ne touche pas au cœur, n'écrit aucun vault.
Objectif : prouver que sur les questions RELATIONNELLES / multi-sauts (« qui a fondé le studio qui
maintient le fork X ? »), une récupération par TRAVERSÉE DE GRAPHE (sous-graphe pertinent autour
de l'entité-amorce) couvre la passage-support que le RAG VECTORIEL PLAT rate, car la passage-cible
(2 sauts plus loin) ne ressemble pas lexicalement à la question.

Deux moteurs comparés à BUDGET ÉGAL (même nombre de passages récupérés) :
  - flat   : RAG vectoriel plat — top-k passages par similarité cosinus à la question.
  - graph  : GraphRAG — BFS k-sauts depuis l'entité-amorce -> passages du sous-graphe.

Métrique : answer_coverage = fraction des questions dont la passage-support (entité `answer`)
figure dans l'ensemble récupéré. C'est le rappel de récupération, prérequis d'une bonne réponse.

Usage :
    python graphrag.py --selftest
    python graphrag.py --dataset sample_graph.jsonl

Format JSONL :
    {"type":"entity","id":"...","label":"...","passage":"..."}
    {"type":"edge","s":"...","r":"relation","o":"..."}
    {"type":"query","question":"...","seed":"...","answer":"...","hops":2}
Réf. : MS GraphRAG + variantes locales, patterns RAG 2026 — cf. radar.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import zlib
from collections import deque

_DIM = 512


def normalize(text: str) -> str:
    out = []
    for ch in text.lower():
        out.append(ch if ch.isalnum() or ch.isspace() else " ")
    return " ".join("".join(out).split())


def embed(text: str, n_values=(3, 4)) -> list:
    """Embedding déterministe hors-ligne : n-grammes de caractères -> vecteur hashé L2-normalisé."""
    vec = [0.0] * _DIM
    t = f" {normalize(text)} "
    for n in n_values:
        for i in range(len(t) - n + 1):
            vec[zlib.crc32(t[i:i + n].encode("utf-8")) % _DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm else vec


def cosine(a: list, b: list) -> float:
    return sum(x * y for x, y in zip(a, b))


class Graph:
    def __init__(self):
        self.passages = {}              # id -> passage text
        self.labels = {}                # id -> label
        self.adj = {}                   # id -> list[(relation, neighbour_id)]

    def add_entity(self, eid, label, passage):
        self.passages[eid] = passage
        self.labels[eid] = label
        self.adj.setdefault(eid, [])

    def add_edge(self, s, r, o):
        self.adj.setdefault(s, []).append((r, o))
        self.adj.setdefault(o, [])      # garantit que la cible existe comme nœud

    def subgraph(self, seed, hops):
        """BFS borné : ensemble des entités à <= 'hops' sauts de l'amorce (amorce incluse)."""
        seen = {seed}
        frontier = deque([(seed, 0)])
        while frontier:
            node, d = frontier.popleft()
            if d >= hops:
                continue
            for _, nb in self.adj.get(node, []):
                if nb not in seen:
                    seen.add(nb)
                    frontier.append((nb, d + 1))
        return seen


def load_dataset(path: str):
    g = Graph()
    queries = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = json.loads(line)
            t = row.get("type")
            if t == "entity":
                g.add_entity(row["id"], row.get("label", row["id"]), row.get("passage", ""))
            elif t == "edge":
                g.add_edge(row["s"], row["r"], row["o"])
            elif t == "query":
                queries.append(row)
    return g, queries


def flat_retrieve(g: Graph, question: str, k: int):
    """RAG plat : top-k passages les plus proches de la question par cosinus."""
    q = embed(question)
    scored = sorted(((cosine(q, embed(g.passages[eid])), eid) for eid in g.passages),
                    reverse=True)
    return {eid for _, eid in scored[:k]}


def run(g: Graph, queries: list) -> dict:
    flat_cov = graph_cov = 0
    details = []
    for q in queries:
        seed, ans, hops = q["seed"], q["answer"], int(q.get("hops", 2))
        sub = g.subgraph(seed, hops)              # GraphRAG : sous-graphe k-sauts
        k = len(sub)                              # budget égal pour le RAG plat
        flat = flat_retrieve(g, q["question"], k)
        g_hit = ans in sub
        f_hit = ans in flat
        graph_cov += int(g_hit)
        flat_cov += int(f_hit)
        details.append({
            "question": q["question"],
            "answer": g.labels.get(ans, ans),
            "k": k,
            "graph_hit": g_hit,
            "flat_hit": f_hit,
        })
    n = max(1, len(queries))
    return {
        "n_queries": len(queries),
        "k_budget": "égal (taille du sous-graphe)",
        "flat_vector_coverage": round(flat_cov / n, 3),
        "graphrag_coverage": round(graph_cov / n, 3),
        "details": details,
    }


# ----------------------------------------------------------------------------- selftest
def _build_selftest_graph() -> Graph:
    g = Graph()
    ents = [
        ("project_nebula", "Projet Nebula", "Le projet Nebula regroupe plusieurs logiciels dérivés."),
        ("fork_nebula", "Fork Nebula", "Fork Nebula est une variante serveur tirée du projet Nebula."),
        ("org_lumen", "Lumen Labs", "Lumen Labs est un laboratoire logiciel reconnu."),
        ("person_rivera", "Rivera", "Rivera est une ingénieure vétérane du secteur du logiciel libre."),
        ("paper_nebula", "Article Nebula", "Article Nebula est la publication d'origine du projet."),
        ("conf_comet", "Conférence Comet", "Comet est une conférence annuelle de recherche."),
        ("org_orbit", "Association Orbit", "L'Association Orbit organise plusieurs conférences."),
        ("noise_a", "Œuvre sans rapport A", "Un récit indépendant sans lien avec Nebula."),
        ("noise_b", "Œuvre sans rapport B", "Une autre histoire isolée, thème différent."),
    ]
    for eid, label, passage in ents:
        g.add_entity(eid, label, passage)
    edges = [
        ("project_nebula", "forked_into", "fork_nebula"),
        ("fork_nebula", "maintained_by", "org_lumen"),
        ("org_lumen", "founded_by", "person_rivera"),
        ("project_nebula", "described_in", "paper_nebula"),
        ("paper_nebula", "presented_at", "conf_comet"),
        ("conf_comet", "organized_by", "org_orbit"),
    ]
    for s, r, o in edges:
        g.add_edge(s, r, o)
    return g


_SELFTEST_QUERIES = [
    {"question": "Qui a fondé le laboratoire qui maintient le fork Nebula ?",
     "seed": "fork_nebula", "answer": "person_rivera", "hops": 2},
    {"question": "Quelle association organise la conférence où l'article Nebula a été présenté ?",
     "seed": "paper_nebula", "answer": "org_orbit", "hops": 2},
]


def selftest() -> int:
    res = run(_build_selftest_graph(), list(_SELFTEST_QUERIES))
    print(json.dumps({k: v for k, v in res.items() if k != "details"},
                     ensure_ascii=False, indent=2))
    for d in res["details"]:
        print(f"  graph={'OK' if d['graph_hit'] else 'XX'} "
              f"flat={'OK' if d['flat_hit'] else 'XX'} (k={d['k']}) "
              f"-> {d['question']} [{d['answer']}]")
    # Revendication : sur le multi-sauts, GraphRAG couvre la passage-support,
    # et fait STRICTEMENT mieux que le RAG plat à budget égal.
    if res["graphrag_coverage"] == 1.0 and res["graphrag_coverage"] > res["flat_vector_coverage"]:
        print(f"\n[selftest] OK — GraphRAG {res['graphrag_coverage']} vs plat "
              f"{res['flat_vector_coverage']} (multi-sauts, budget égal).")
        return 0
    print("\n[selftest] ÉCHEC — vérifier traversée/embeddings.", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="PoC #4 GraphRAG (god-mode).")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dataset", help="JSONL entités + arêtes + requêtes")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.dataset:
        ap.print_help()
        return 2

    g, queries = load_dataset(args.dataset)
    res = run(g, queries)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
