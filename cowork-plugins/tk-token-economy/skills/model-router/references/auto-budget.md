# Auto-optimisation budget — drapeaux lus par model-router

Écrits par `${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py` (skill `budget`, mode `optimize`) dans
`~/.tk-token-economy/budget.json` sous la clé `auto_state`. Ce sont des **drapeaux de données bornés et
réversibles**, jamais du code. Ils ne sont posés qu'après GO explicite (`optimizer.py apply`).

## Lecture

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py status
```

## Application dans model-router

| Drapeau | Valeur | Effet sur le routage |
|---|---|---|
| `score_bias` | 0..10 | passer `--bias N` à `classify.py` : les tâches limites descendent d'un tier |
| `haiku_reroute` | bool | router les T2 non critiques vers `haiku-executor` (alias fast) |
| `force_haiku` | bool | alias fast pour tout, sauf mention « critique » / « urgent » |
| `caveman_default` | null / lite / full / ultra | proposer ce niveau de caveman par défaut (skill manuel : proposer, pas imposer) |

## Comptage des économies (reroute)

Quand une tâche descend d'un tier pour raison budget (ex. T2 → T1) :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py log-offload --target haiku --saved <equiv_economise>
```

`equiv_economise = equiv(tier_origine) − equiv(fast)` à partir des tokens estimés par `classify.py`,
avec les poids d'équivalence de `budget.py` (fast 1/1, default 3/5, deep 15/25 pour input/output).
Ces économies apparaissent dans `budget.py status` et `budget_analyzer.py`.

## Rollback

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py rollback --last
```

Chaque `apply` journalise avant/après dans `~/.tk-token-economy/optimizer-log.jsonl`.
