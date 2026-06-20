---
name: budget-analyzer
description: >
  Analyse la consommation de tokens et propose des economies. Lit ~/.token-optimizer/budget.json
  (alimente par budget-tracker) et produit tendances, projection fin de mois, detection de
  gaspillage et opportunites d'economie chiffrees. Mots-cles : "analyse mon budget", "ou partent
  mes tokens", "rapport d'optimisation", "comment economiser des tokens", "projection budget",
  "gaspillage tokens", "audit conso".
---

# Budget Analyzer

Moteur d'analyse du budget tokens (Lot 1 du systeme d'auto-optimisation). Complementaire de `budget-tracker` (qui logue) : ici on **analyse et on recommande**.

## Quand declencher

- L'utilisateur demande une analyse, un rapport ou des pistes d'economie.
- En amont d'une decision de routage agressif (le model-router peut le consulter).
- Sur planification (rapport quotidien/hebdomadaire).

## Procedure

Executer le script et restituer une synthese :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget_analyzer.py            # rapport humain
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget_analyzer.py --json     # pour optimizer/dashboard
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget_analyzer.py --recommend
```

## Ce que produit l'analyse

- **Repartition** par modele/tier en equivalents-Haiku (calibres par `calibration_factor`).
- **Tendance** : conso/jour, projection fin de mois, ETA des seuils 50/80/95 %.
- **Gaspillages** (heuristiques sur `events[]`) :
  - `opus_sous_utilise` : petites taches routees en Opus ;
  - `sortie_longue_sans_compression` : sorties longues T1/T2 sans caveman ;
  - `taches_repetitives_offload_local` : taches Haiku repetitives -> candidates offload local.
- **Recommandations** separees en **auto-applicables** (consommees par `optimizer` au Lot 2) et **a proposer** (validation requise).

## Interpretation

- `ratio` = part du budget mensuel consommee (calibree).
- `projected_ratio` > 1.0 = depassement prevu en fin de mois au rythme actuel.
- `est_saving_equiv` = economie estimee en tokens equivalents-Haiku si l'optimisation est appliquee.

## Limites

- Chiffres **estimes** (hook + estimation `classify.py`), pas la facturation exacte. Ajuster `calibration_factor` via `budget.py set-budget --calibration X` apres comparaison avec l'usage reel.
- L'analyse de gaspillage s'affine avec le volume d'`events[]` (peu fiable < ~20 evenements).

## Reference

- Plan complet : `docs/AUTO_BUDGET_PLAN.md`.
