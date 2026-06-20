---
name: auto-optimize
description: >
  Boucle d'auto-amelioration du budget tokens : applique automatiquement les optimisations
  SURES (reroute Haiku, caveman par defaut, biais de score) et propose le reste. Mots-cles :
  "auto-optimise", "optimise mon budget automatiquement", "applique les economies", "active les
  optimisations", "rollback optimisation", "etat des optimisations".
---

# Auto-Optimize (Lot 2)

Applique la boucle d'auto-amelioration au-dessus de `budget-analyzer`. Autonomie : **auto-applique le sur, propose le reste**. L'auto-application n'ecrit que des **drapeaux de donnees bornes et reversibles** (`auto_state` dans `budget.json`) ; jamais d'edition de code ni d'action sur du sensible.

## Commandes

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py analyze        # dry-run
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py apply          # applique le sur (reversible)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py status         # etat actif
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py rollback --last
```

## Liste blanche (auto-appliquee)

| Drapeau | Declencheur | Effet (lu par model-router) |
|---------|-------------|------------------------------|
| `haiku_reroute` | budget >= 80% ou projection > 100% | pousse les T2 non critiques vers Haiku |
| `force_haiku` | budget >= 95% | force Haiku sauf "critique"/"urgent" |
| `caveman_default` | 80% -> full, 95% -> ultra, projection>100% -> lite | active le mode caveman par defaut |
| `score_bias` | pression budget -> 5 (borne 0..10) | abaisse le score de classement (taches limites -> tier inferieur) |

## A proposer (validation requise)

Tout le reste : creation/modif de skills, regles d'offload local/Antigravity, changement d'allocation/total budget, toute action sur un domaine sensible. Ces points sont restitues par `optimizer.py analyze` sous "A PROPOSER".

## Garde-fous

- Chaque `apply` journalise (avant/apres) dans `~/.token-optimizer/optimizer-log.jsonl` et empile un point de rollback.
- `rollback --last` restaure l'etat precedent en un geste.
- Reversibilite totale : aucune action destructive, uniquement des drapeaux de donnees bornes.

## Quand l'utiliser

- Sur demande ("auto-optimise mon budget").
- En tache planifiee (quotidienne) : `apply` puis inclure le resume dans le rapport budget.
- Avant une session lourde, pour activer caveman/reroute si le budget est tendu.
