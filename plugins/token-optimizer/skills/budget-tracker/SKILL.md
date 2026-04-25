---
name: budget-tracker
description: >
  Suit la consommation mensuelle de tokens par modele (Haiku, Sonnet, Opus) et declenche
  des alertes a 50%, 80% et 95% du budget.
  Mots-cles : "combien j'ai consomme", "budget tokens", "conso du mois", "reset budget",
  "quota restant", "configure budget".
  Alimente aussi le model-router qui desescalade quand le budget est sature.
---

# Budget Tracker

Stocke la conso de tokens dans un fichier JSON local (`~/.token-optimizer/budget.json`) et expose trois commandes : status, log, reset.

## Configuration

Le budget est defini dans `references/budget-config.md`. Valeurs par defaut :

- Budget mensuel total : **20 000 000 tokens** (combine Haiku + Sonnet + Opus)
- Repartition indicative : 60% Haiku, 30% Sonnet, 10% Opus
- Alertes : 50%, 80%, 95%

L'utilisateur peut modifier via :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py set-budget --total 30000000 --haiku 0.7 --sonnet 0.25 --opus 0.05
```

## Commandes

### Consulter le statut

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py status
```

Sortie :

```
=== Budget mensuel avril 2026 ===
Total      : 12 450 000 / 20 000 000 tokens  (62.3%)  [ALERTE 50%]
Haiku 4.5  :  6 200 000 / 12 000 000 tokens  (51.7%)
Sonnet 4.6 :  5 100 000 /  6 000 000 tokens  (85.0%)  [ALERTE 80%]
Opus 4.6   :  1 150 000 /  2 000 000 tokens  (57.5%)
```

### Enregistrer une conso

Apres chaque execution significative :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py log --model sonnet --input 3200 --output 1800
```

### Reset (debut de mois)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py reset
```

Automatique au 1er du mois : le script detecte le changement de mois et archive l'historique dans `~/.token-optimizer/history/YYYY-MM.json`.

## Actions selon seuils

- **< 50%** : rien, route normal
- **50-80%** : afficher un rappel discret dans la decision du router
- **80-95%** : le router desescalade d'un tier par defaut (sauf mention "critique" explicite)
- **>= 95%** : forcer Haiku pour tout sauf urgence declaree, proposer d'augmenter le budget OU d'attendre le reset

## Integration avec model-router

Le router appelle `budget.py status --json` en amont de chaque decision. Si le champ `escalation_policy` vaut `downgrade_one_tier` ou `force_haiku`, le router applique le modificateur.
