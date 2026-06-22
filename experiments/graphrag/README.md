# experiments/graphrag — PoC #4 (god-mode) : GraphRAG (récupération entité-relation)

> Radar god-mode 2026-06-22, candidat #4 (~72, effort le plus élevé → APRÈS RAGAS pour le mesurer).
> **PoC isolé.** GraphRAG remplace les passages plats par une structure **entité-relation** et récupère
> des **sous-graphes résumés** — fort sur les questions relationnelles et les corpus privés.

## Pourquoi TricorderKit
Neo4j est présent mais sert peu à la *récupération*. Le domaine est un graphe naturel
(franchise ↔ manga ↔ mangaka ↔ studio ↔ éditeur ↔ magazine) → GraphRAG valoriserait cet investissement
pour les questions « relationnelles » que le RAG vectoriel plat gère mal.

## Plan (à lancer après PoC #1 RAGAS)
1. Construire un graphe d'entités sur un sous-ensemble (extraction entités+relations depuis fiches).
2. Retrieval : requête → sous-graphe pertinent → résumé → réponse, en parallèle du RAG vectoriel actuel.
3. **Mesurer avec RAGAS** (PoC #1) : GraphRAG vs RAG vectoriel sur un set de questions relationnelles.
4. Si gain sur ce type de question → DEC + ajouter un mode `graph` à `graphify`.

## Livré (PoC exécutable, hors-ligne)
`graphrag.py` — graphe entité-relation in-memory, comparaison à **budget égal** :
`flat` (top-k passages par cosinus à la question) vs `graph` (BFS k-sauts depuis l'entité-amorce
→ passages du sous-graphe). Métrique = `answer_coverage` (la passage-support est-elle récupérée ?).

```
python graphrag.py --selftest
python graphrag.py --dataset sample_graph.jsonl
```

**Résultats mesurés (2026-06-22)** : sur les questions relationnelles multi-sauts, GraphRAG
**couvre 100 %** des passages-support, contre **50–67 %** pour le RAG vectoriel plat à budget égal.
Confirme l'intuition : la passage-cible (2 sauts plus loin) ne ressemble pas lexicalement à la
question → le plat la rate, la traversée de graphe la trouve.

## Prochaines étapes (vers la promotion)
1. Brancher sur Neo4j réel + extraction entités/relations depuis un sous-ensemble de fiches.
2. **Mesurer avec RAGAS (PoC #1)** : GraphRAG vs vectoriel plat sur un set de questions relationnelles.
3. Si gain confirmé → DEC + mode `graph` ajouté à `graphify`.

## Garde-fous
Isolé ; mesuré via eval-lab/RAGAS avant tout engagement ; données d'exemple génériques (aucun
contenu métier privé), zéro écriture vault ; effort de construction du graphe non trivial → PoC ciblé.
Réf. : MS GraphRAG + variantes locales, patterns RAG 2026 — cf. radar.
