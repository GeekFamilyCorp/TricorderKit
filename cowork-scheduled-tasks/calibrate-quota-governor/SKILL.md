---
name: calibrate-quota-governor
description: Re-calibration quotas gouverneur canal_agents â€” CODEX prioritaire (Gemini capÃ© + bloquÃ© jusqu'au 17/06).
---

Tu es l'assistant TricorderKit (SÃ©bastien â€” vouvoiement, pas de Â« Monsieur Â», efficace). TÃ¢che : RE-CALIBRER le gouverneur de quota multi-agents canal_agents, **centrÃ© sur Codex** (Gemini/Antigravity a de nouveau atteint son plafond ET est bloquÃ© jusqu'au 2026-06-17 â†’ ne pas compter sur lui).

ModÃ¨le cible T2 Sonnet ; caveman lite ; thinking OFF ; token-light (max 2 lancements Python, 1 fichier rapport).

CONTEXTE (ne pas redÃ©couvrir) :
- Canal : %USERPROFILE%\Documents\Claude\Projects\TricorderKit Autonome\canal_agents ; Python C:\Python314\python.exe ; gouverneur scripts\quota_governor.py.
- Mesures : budget\usage.jsonl, budget\REPORT.md, budget\codex_rate_limit.json, budget\config.json.
- Sources rÃ©elles : Claude = ~/.token-optimizer/budget.json (plafond 25e9) ; Codex = ~/.codex/logs_2.sqlite (token_usage + spans rate_limit/reset) ; Antigravity/Gemini = capÃ© + bloquÃ© jusqu'au 17/06.

Ã‰TAPES :
1. `python quota_governor.py collect` puis `report --write` puis `status --json` (depuis scripts\). Lis usage.jsonl + REPORT.md.
2. **Codex (prioritÃ©)** : retrouve la limite rÃ©elle du fournisseur dans budget\codex_rate_limit.json ET les spans 'rate_limit'/'reset' du sqlite. Calcule conso observÃ©e (07â†’14/06) + dÃ©bit/jour + extrapolation mensuelle. Fixe quota_tokens Codex = plafond plan si trouvÃ©, sinon conso mensuelle Ã— 1,3 (signale que le vrai plafond reste Ã  confirmer par SÃ©bastien).
3. **Claude** : quota = 25e9 (token-optimizer), sauf si la mesure suggÃ¨re autre chose.
4. **Antigravity/Gemini** : capÃ© + bloquÃ© jusqu'au 17/06 â†’ mets son throttle au MAXIMUM (ou state=paused/quota trÃ¨s bas), NE route AUCUNE nouvelle charge veille vers lui jusqu'au 17/06 (Codex couvre la lane veille entre-temps). Ne tente pas d'estimer son plafond ce soir.
5. Ã‰dite budget\config.json (quota_tokens calibrÃ©s, period=month, throttle ajustÃ©) â†’ bascule THROTTLE. Relance `status --json` pour vÃ©rifier.
6. Ã‰cris budget\CALIBRATION_2026-06-14_v2.md : conso/dÃ©bit par agent, quotas retenus, Gemini mis en pause, hypothÃ¨ses.
7. RÃ©sumÃ© Ã  SÃ©bastien (3-5 lignes) : quotas Codex/Claude retenus, Gemini en pause jusqu'au 17/06, et la SEULE chose manquante = le vrai plafond plan Codex (et Gemini, Ã  investiguer le 17/06).