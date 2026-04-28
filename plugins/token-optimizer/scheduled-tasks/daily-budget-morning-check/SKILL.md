---
name: daily-budget-morning-check
description: Notification matinale du statut budget tokens — rappel quotidien à 8h30
---

Tu es Claude en mode Cowork pour Sébastien. Lance un contrôle rapide du budget tokens du matin.

1. Exécute via mcp__workspace__bash : `python3 /sessions/focused-tender-keller/mnt/.remote-plugins/plugin_01UC4QSjJY9AvJcJyTjzNhR7/scripts/budget.py status --json`
2. Calcule le budget journalier estimé = total_mensuel / 30
3. Identifie le niveau d'alerte (OK / INFO / ATTENTION / CRITIQUE)
4. Envoie un message à Sébastien avec :
   - Le statut global en 1 ligne (X% du budget mensuel consommé, niveau d'alerte)
   - Le modèle le plus consommé
   - Rappel de la politique d'escalade si > 80%
   - Encouragement court si backlog à zéro ou si le niveau est OK

Garde le message court (5 lignes max). Ajoute juste la commande "budget status" comme suggestion de suivi si le quota est élevé.
