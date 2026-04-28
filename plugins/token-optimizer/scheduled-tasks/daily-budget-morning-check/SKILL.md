---
name: daily-budget-morning-check
description: Notification matinale du statut budget tokens — rappel quotidien à 8h30
---

Tu es Claude en mode Cowork pour [votre nom]. Lance un contrôle rapide du budget tokens du matin.

## Instructions

1. Localise dynamiquement le script budget (chemin de session variable à chaque démarrage) via mcp__workspace__bash :
   ```bash
   find /sessions -maxdepth 5 -name "budget.py" -path "*/plugin_01UC4QSjJY9AvJcJyTjzNhR7/*" 2>/dev/null | head -1
   ```
   Si le workspace retourne "Workspace still starting" ou "unavailable", attends 5 secondes et réessaie (max 3 tentatives).

2. Exécute ensuite :
   ```bash
   python3 <chemin_trouvé> status --json
   ```

3. Calcule le budget journalier estimé = total_mensuel / 30.

4. Identifie le niveau d'alerte :
   - ✅ OK : < 50% du mensuel consommé
   - ℹ️ INFO : 50–70%
   - ⚠️ ATTENTION : 70–80%
   - 🚨 CRITIQUE : > 80%

5. Envoie un message DM Slack à [votre nom] avec :
   - Le statut global en 1 ligne (X% du budget mensuel consommé, niveau d'alerte)
   - Le modèle le plus consommé
   - Rappel de la politique d'escalade si > 80%
   - Encouragement court si le niveau est OK

Garde le message court (5 lignes max). Ajoute la commande `budget status` comme suggestion de suivi si le quota est élevé.

## Notes techniques
- Le chemin `/sessions/<nom-session>/` change à chaque nouvelle session Cowork — ne jamais le hardcoder.
- En cas d'échec du workspace après 3 tentatives, envoyer quand même un message Slack signalant l'indisponibilité du workspace.
