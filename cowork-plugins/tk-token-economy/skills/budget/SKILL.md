---
name: budget
description: >
  Suit, analyse et optimise la consommation mensuelle de tokens ESTIMÉE par famille de modèle (fast /
  default / deep, voir models.json) à partir d'un fichier local. Trois modes : `status` (consommation et
  seuils 50/80/95 %), `analyze` (tendance, projection fin de mois, gaspillages), `optimize` (drapeaux sûrs
  et réversibles, jamais appliqués sans GO explicite). À utiliser quand l'utilisateur demande « combien j'ai
  consommé », « budget tokens », « où partent mes tokens », « projection budget », « optimise mon budget »,
  « logge cette conso », ou depuis la tâche planifiée du matin. Ce sont des estimations locales, pas la
  facturation Anthropic ; en Cowork le hook PostToolUse ne reçoit pas toujours les tokens, d'où une
  commande de log manuel de repli. Ne pas utiliser pour choisir le modèle d'une tâche (→ model-router)
  ni pour compresser une sortie (→ caveman).
license: MIT
metadata:
  version: "2.0"
  updated: "2026-09-07"
  author: GeekFamilyCorp
---

# Budget (status · analyze · optimize)

Un seul fichier de données : `~/.tk-token-economy/budget.json` (schéma v1.1, archivé chaque mois dans `~/.tk-token-economy/history/`). Trois scripts, trois modes.

**Honnêteté des chiffres** : tout est estimé (poids d'équivalence fast 1/1, default 3/5, deep 15/25 pour input/output). Comparer à l'usage réel et corriger via `--calibration` avant de trancher un arbitrage.

## Alimentation des données

1. **Automatique** — hook `PostToolUse` sur `Task` (`hooks/hooks.json`) → `budget.py log-from-task`. Il ne logge que si le payload contient des compteurs de tokens ; **en Cowork ce n'est pas toujours le cas** : un statut à 0 ne veut pas dire zéro consommation.
2. **Manuel (repli)** — après une exécution significative :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py log --model default --in 3200 --out 1800
```

`--model` accepte les alias `fast` / `default` / `deep` (ou la famille). Les tokens se lisent dans le résumé d'usage de la session ou s'estiment avec `classify.py`.

## Mode `status`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py status          # lisible
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py status --json   # pour model-router / tâche planifiée
```

Seuils et politique d'escalade retournée (`escalation_policy`) :

| Ratio | Alerte | Effet sur model-router |
|---|---|---|
| < 50 % | OK | rien |
| 50–80 % | INFO | rappel discret |
| 80–95 % | WARNING | `downgrade_one_tier` sauf « critique » |
| ≥ 95 % | CRITICAL | `force_haiku` sauf « critique » / « urgent » |

Configuration : `budget.py set-budget --total N --haiku 0.6 --sonnet 0.3 --opus 0.1 --calibration 1.0 --alert-mode informative|enforcing`. Détail dans `references/budget-config.md` et `references/alerts.md`. Reset manuel : `budget.py reset` (l'historique est conservé).

## Mode `analyze`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget_analyzer.py              # rapport
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget_analyzer.py --json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget_analyzer.py --recommend
```

Produit : répartition par famille, conso/jour, projection fin de mois, ETA des seuils, gaspillages (`opus_sous_utilise`, `sortie_longue_sans_compression`, `taches_repetitives_offload_local`) et recommandations séparées en *auto-applicables* / *à proposer*. Peu fiable sous ~20 événements : le dire.

## Mode `optimize`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py analyze     # dry-run : toujours commencer ici
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py status
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py apply       # SEULEMENT après GO explicite (R53)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py rollback --last
```

`apply` n'écrit que des drapeaux bornés et réversibles (`haiku_reroute`, `force_haiku`, `caveman_default`, `score_bias`) dans `auto_state`, journalisés avec point de rollback. Règle : en session interactive, présenter le dry-run et attendre le GO de l'utilisateur ; en tâche planifiée, ne jamais lancer `apply`, seulement `analyze` et le remonter. Effet des drapeaux sur le routage : `${CLAUDE_PLUGIN_ROOT}/skills/model-router/references/auto-budget.md`.

Tout le reste (changer le budget total, créer des règles d'offload local, toucher un domaine sensible) reste une proposition.

## Restitution type

```
Budget 2026-09 (estimation) : 12,4 M / 20 M eq (62 %) — INFO
  fast 52 % · default 85 % [WARNING] · deep 57 %
Projection fin de mois : 96 % → seuil 95 % atteint vers le 27
Données : 143 événements (hook) + 2 logs manuels — calibration ×1.0 non vérifiée
```

## Références

- `references/budget-config.md` — schéma de `budget.json`, poids d'équivalence, rétention
- `references/alerts.md` — niveaux d'alerte et overrides
- `${CLAUDE_PLUGIN_ROOT}/references/regles.md` — R53 (GO avant action), R31 (NO-DROP), R54 (doctrine de routage)

## Changelog

- 2026-09-07 — v2.0 : fusion de `budget-tracker` + `budget-analyzer` + `auto-optimize` en un skill à trois modes ; `apply` conditionné au GO explicite ; commande `log --model <alias> --in --out` de repli ; retrait des cibles d'offload Antigravity/Gemini ; chiffres annoncés comme estimations.
- 2026-04 — v1.x : trois skills séparés (lots L1–L3 du plan auto-budget).
