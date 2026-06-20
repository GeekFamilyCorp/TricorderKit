# Cas de test Arbor — Scraping Optimizer

## Objectif
Comparer plusieurs stratégies d'extraction de source (sélecteurs, rendu JS, anti-bot, cadence)
et désigner la plus robuste/économe via un arbre d'hypothèses Arbor.

## Entrée
- 1 source représentative (page liste + page détail).
- Variantes de stratégie à comparer.

## Sortie attendue
- Arbre d'hypothèses + scoring (robustesse, coût, couverture).
- `reports/benchmarks/arbor_scraping_optimizer_test.md`.

## Critères de réussite
- Stratégie gagnante justifiée, variantes rejetées conservées.
- Données externes traitées comme non fiables (validation ≥ 2 sources ou primaire).
- Aucune écriture hors `experiments/` et `reports/benchmarks/`.
