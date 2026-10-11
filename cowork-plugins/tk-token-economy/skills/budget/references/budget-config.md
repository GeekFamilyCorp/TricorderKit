# Configuration du budget

## Structure du fichier `~/.tk-token-economy/budget.json`

```json
{
  "version": "1.1",
  "month": "2026-04",
  "config": {
    "total_monthly_tokens": 20000000,
    "allocation": {
      "haiku": 0.60,
      "sonnet": 0.30,
      "opus": 0.10
    },
    "alerts": [0.50, 0.80, 0.95],
    "alert_mode": "informative",
    "calibration_factor": 1.0
  },
  "consumption": {
    "haiku":  { "input": 4100000, "output": 2100000 },
    "sonnet": { "input": 3800000, "output": 1300000 },
    "opus":   { "input":  900000, "output":  250000 }
  },
  "offload": { "local": { "tasks": 0, "tokens_saved_equiv": 0 }, "haiku_reroute": { "tasks": 0, "tokens_saved_equiv": 0 } },
  "events": [],
  "auto_state": { "caveman_default": null, "haiku_reroute": false, "force_haiku": false, "score_bias": 0 }
}

Familles `haiku` / `sonnet` / `opus` = alias `fast` / `default` / `deep` de `${CLAUDE_PLUGIN_ROOT}/models.json`.
Toutes les valeurs sont des ESTIMATIONS (hook + `classify.py`), pas la facturation.
```

## Calcul du ratio de consommation

Pour que les tiers soient comparables, on convertit en **tokens equivalents Haiku** via des poids :

- Haiku : poids 1
- Sonnet : poids 3 pour input, 5 pour output
- Opus : poids 15 pour input, 25 pour output

Un budget de 20M tokens equivalents = environ :

- 12M pour Haiku natif
- 2M input + 1.2M output Sonnet
- 130k input + 80k output Opus

Cette conversion permet d'avoir une jauge unique "budget mensuel consomme".

## Reset automatique

Au changement de mois (UTC), le script detecte un changement et :

1. Copie le fichier courant vers `history/YYYY-MM.json`
2. Reinitialise `consumption` a zero
3. Conserve la `config`

## Retention historique

L'historique n'est jamais purge automatiquement (NO-DROP, R31). Purge manuelle :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py prune-history --keep-months 12
```
