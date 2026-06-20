# Cas de test Arbor — Audit GitHub

## Objectif
Comparer plusieurs dépôts GitHub et produire un scoring TricorderKit (INTEGRER / PROTOTYPER /
SURVEILLER / REJETER), via un arbre d'hypothèses Arbor.

## Entrée
- Liste de dépôts candidats (URLs).
- Critères : pertinence, maturité, licence, activité, recoupement avec l'existant.

## Sortie attendue
- Arbre d'hypothèses lisible (branches explorées + rejetées avec justification).
- `reports/benchmarks/arbor_github_audit_test.md`.

## Critères de réussite
- Décision argumentée par dépôt.
- Branches rejetées conservées.
- Aucune écriture hors `experiments/` et `reports/benchmarks/`.
