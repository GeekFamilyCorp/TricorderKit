# Configuration du budget

## Structure du fichier `~/.token-optimizer/budget.json`

```json
{
  "version": "1.0",
  "month": "2026-04",
  "config": {
    "total_monthly_tokens": 20000000,
    "allocation": {
      "haiku": 0.60,
      "sonnet": 0.30,
      "opus": 0.10
    },
    "alerts": [0.50, 0.80, 0.95]
  },
  "consumption": {
    "haiku":  { "input": 4100000, "output": 2100000 },
    "sonnet": { "input": 3800000, "output": 1300000 },
    "opus":   { "input":  900000, "output":  250000 }
  },
  "history_path": "~/.token-optimizer/history/"
}
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

## Personnalisation

L'utilisateur peut definir des sous-budgets par projet en editant :

```json
"projects": {
  "client-acme": { "limit": 5000000, "consumed": 1200000 },
  "rd-prototype": { "limit": 2000000, "consumed": 450000 }
}
```

Et ajouter `--project client-acme` aux commandes `log`.

## Reset automatique

Au 1er du mois (UTC+1 Paris), le script detecte un changement et :

1. Copie le fichier courant vers `history/YYYY-MM.json`
2. Reinitialise `consumption` a zero
3. Conserve la `config`

## Retention historique

L'historique est conserve 24 mois par defaut. Purge manuelle :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py prune-history --keep-months 12
```
