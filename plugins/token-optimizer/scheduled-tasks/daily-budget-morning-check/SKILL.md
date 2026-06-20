---
name: daily-budget-morning-check
description: Notification matinale du statut budget tokens — rappel quotidien à 8h30
---

Tu es Claude en mode Cowork pour [votre nom]. Lance un contrôle rapide du budget tokens du matin.

## Instructions

1. Localise le script budget via mcp__workspace__bash (chemin local à la session courante) :
   ```bash
   find /sessions/$(basename $(ls -d /sessions/*/mnt/outputs 2>/dev/null | head -1 | sed 's|/mnt/outputs||')) -name "budget.py" 2>/dev/null | head -1
   ```
   Si le workspace retourne "Workspace still starting" ou "unavailable", attends 5 secondes et réessaie (max 3 tentatives).
   En dernier recours, utilise le chemin direct :
   `/sessions/<session-courante>/mnt/.remote-plugins/plugin_01UC4QSjJY9AvJcJyTjzNhR7/scripts/budget.py`

2. Exécute ensuite :
   ```bash
   python3 <chemin_trouvé> status --json
   ```

3. Calcule le budget journalier estimé = total_budget_tokens / 30.

4. Identifie le niveau d'alerte selon `total_ratio` :
   - ✅ OK : < 50%
   - ℹ️ INFO : 50–70%
   - ⚠️ ATTENTION : 70–80%
   - 🚨 CRITIQUE : > 80%

5. Envoie un message DM Slack à [votre nom] avec :
   - Le statut global en 1 ligne (X% consommé, niveau d'alerte)
   - Le modèle le plus consommé (`per_model` → ratio le plus élevé)
   - Rappel de la politique d'escalade si > 80%
   - Encouragement court si niveau OK

Garde le message court (5 lignes max). Ajoute la commande `budget status` comme suggestion de suivi si le quota est élevé.

## Notes techniques
- Ne jamais hardcoder le nom de session (`/sessions/<nom>/`) — il change à chaque ouverture Cowork.
- Les autres sessions dans `/sessions/` sont en permission refusée — chercher uniquement dans la session courante.
- En cas d'échec workspace après 3 tentatives, envoyer quand même un message Slack signalant l'indisponibilité.
