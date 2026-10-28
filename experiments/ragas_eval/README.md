# experiments/ragas_eval — PoC #1 (god-mode) : évaluation RAG

> Issu du radar god-mode 2026-06-22 (candidat #1, score ~82). **PoC isolé** : mesure objective de la
> qualité du RAG (graphify) — le maillon manquant pour arbitrer toute évolution RAG de façon data-driven.
> N'écrit pas le vault, ne touche pas au cœur. Promotion vers `eval-lab` = sur DEC, après mesure.

## Pourquoi
graphify a un pipeline RAG (Qdrant + BM25 + RRF + reranker, DEC-023) mais **aucune métrique objective**.
RAGAS (open-source, sans ground-truth, LLM-as-judge, compatible Claude) fournit faithfulness /
answer_relevancy / context_precision. Sources : voir `claude-vault/70_ROADMAP/GODMODE_RADAR_2026-06-22.md`.

## Deux moteurs
- **proxy** (défaut) : métriques déterministes par overlap lexical, **hors-ligne, sans dépendance** —
  baseline + garde-fou + selftest. Tourne tout de suite.
- **ragas** : vrai RAGAS (LLM-as-judge). Requiert `pip install ragas datasets` + un LLM-juge
  (`REFLECTION_LLM_URL`/`MODEL`, même convention que `reflection.py` — Ollama local ou gateway).

## Usage
```
python ragas_eval.py --selftest
python ragas_eval.py --dataset sample_qa.jsonl                 # proxy (offline)
python ragas_eval.py --dataset sample_qa.jsonl --engine ragas  # vrai RAGAS si dispo (sinon repli proxy)
```
Entrée JSONL : `{"question","contexts":[...],"answer","ground_truth"(optionnel)}`.

## Prochaines étapes (vers la promotion eval-lab)
1. Construire un jeu Q/R réel (20-50) à partir du vault → mesurer le score de base du RAG actuel.
2. Brancher un LLM-juge (Ollama `qwen`/gateway) pour le moteur `ragas`.
3. Re-mesurer après chaque changement RAG (reranker, GraphRAG…) → comparer.
4. Si concluant → DEC + intégrer comme commande `tk eval rag` dans `eval-lab`.

## Garde-fous
Exemples `sample_qa.jsonl` génériques (aucun contenu métier privé). 100 % mesure, zéro écriture vault.
