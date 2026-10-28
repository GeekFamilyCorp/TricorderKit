---
name: daily-budget-morning-check
description: >
  Prompt de la tâche planifiée « contrôle budget tokens du matin » : lit le statut estimé du budget via
  budget.py, calcule le niveau d'alerte et envoie un message court à l'utilisateur. Déclencheur : tâche
  planifiée créée avec create_trigger (cron UTC), jours ouvrés à 8h30 Paris ; ou appel manuel « lance le
  contrôle budget du matin ». Ne pas utiliser comme cron local ni pour appliquer une optimisation
  (analyze seulement, jamais apply).
license: MIT
metadata:
  version: "2.0"
  updated: "2026-09-07"
  author: GeekFamilyCorp
---

# Contrôle budget du matin

## Création de la tâche (une fois, sur GO de l'utilisateur — R53)

Via `create_trigger`, jamais de cron local :

- `name` : `tk-token-economy — budget du matin`
- `cron_expression` : `30 6 * * 1-5` (8h30 Paris en heure d'été ; passer à `30 7 * * 1-5` en heure d'hiver)
- `prompt` : le bloc « Prompt de la tâche » ci-dessous, copié tel quel (session fraîche, sans mémoire).

## Prompt de la tâche

```
Tu es Claude en mode Cowork (vouvoiement). Contrôle rapide du budget tokens estimé.

1. Exécute :
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py status --json
   ${CLAUDE_PLUGIN_ROOT} est la racine du plugin tk-token-economy. Si la variable est absente, localiser
   le fichier budget.py dans le dossier du plugin installé ; ne jamais coder un chemin de session en dur.
   Si le workspace n'est pas prêt, attendre 5 s et réessayer (3 tentatives max).

2. Optionnel : python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget_analyzer.py --json pour la projection.
   Ne JAMAIS lancer optimizer.py apply depuis cette tâche.

3. Niveau d'alerte selon total_ratio : OK < 50 % · INFO 50-70 % · ATTENTION 70-80 % · CRITIQUE > 80 %.

4. Envoyer à l'utilisateur un message de 5 lignes max :
   - statut global (X % consommé, niveau) — préciser « estimation, pas la facturation » ;
   - famille la plus consommée (per_model, ratio le plus élevé ; alias fast/default/deep) ;
   - si > 80 % : rappel de la politique d'escalade (escalation_policy) ;
   - si le hook n'a rien loggé (total à 0 alors que des sessions ont eu lieu) : rappeler la commande
     de log manuel `budget.py log --model default --in N --out N`.

5. Si budget.py échoue après 3 tentatives, envoyer quand même un message signalant l'indisponibilité.
```

## Changelog

- 2026-09-07 — v2.0 : réécrit sans chemin de session, avec `${CLAUDE_PLUGIN_ROOT}`, création par `create_trigger`, destinataire nommé, interdiction d'`apply`.
- 2026-04 — v1.x : version initiale avec recherche du script dans `/sessions/…`.
