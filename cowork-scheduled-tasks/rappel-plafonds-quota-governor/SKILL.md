---
name: rappel-plafonds-quota-governor
description: Rappel samedi 13/06 : préparer les plafonds Codex/Gemini avant calibrate-quota-governor (dim 14/06)
---

RAPPEL pour Sébastien — préparation de `calibrate-quota-governor` (tâche planifiée one-time du dimanche 14/06).

Contexte (cap v1.0 « Self-Improving », DEC-046, projet TricorderKit) : la tâche `calibrate-quota-governor` calibre la gouvernance budgétaire des modèles. Elle a besoin des PLAFONDS RÉELS des forfaits avant de tourner. Rappel : écosystème **100% forfait + local, zéro coût à la consommation** — on calibre des QUOTAS et des CADENCES de heartbeat, PAS des montants en dollars.

Produis un message de rappel clair et court à Sébastien, contenant cette checklist de préparation à compléter aujourd'hui ou demain matin :

1. **Codex / ChatGPT+** : relever le quota réel disponible (messages ou requêtes par fenêtre — journalier/hebdomadaire), et l'état actuel de la « famine Codex » au bus (`canal_agents\.watch_state\watcher.log`).
2. **Gemini / Antigravity** : relever le quota réel (requêtes/jour, AI Credits), et confirmer les réglages de sobriété déjà décidés (Fast Mode, `.antigravityignore`, AI Credits OFF, jamais Opus).
3. **Claude (Max)** : rappeler l'allocation cible du model-router — **Haiku 55% / Sonnet 30% / Opus 15%** — et le budget mensuel restant (script `scripts/budget.py status` si disponible).
4. **Local (Ollama)** : confirmer les modèles encore servis (qwen:1.8b rapport matinal + routeur, nomic-embed-text RAG) — capacité « gratuite » à privilégier pour T1/T2.

Termine en rappelant : ces chiffres seront saisis dans `calibrate-quota-governor` dimanche 14/06 ; le runbook d'exploitation est dans `.planning/RUNBOOK_EXPLOITATION_v1.0_2026-06-11.md` du repo TricorderKit (Bloc 3). Si des chiffres manquent, demander à Sébastien de les fournir. Ne rien exécuter d'autre — ceci est uniquement un rappel de préparation.