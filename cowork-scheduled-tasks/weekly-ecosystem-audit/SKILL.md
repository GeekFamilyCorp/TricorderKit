---
name: weekly-ecosystem-audit
description: Grand Audit dimanche 04h (T2/Sonnet, caveman lite) â€” Ã©cosystÃ¨me Claude (skills/plugins/MCPs) + audit dynamique 90_Templates Japan-Alliance
---

ROUTAGE : T2/Sonnet, caveman lite, Extended Thinking OFF. Exploiter le JSON du script â€” ne pas rÃ©inspecter l'Ã©cosystÃ¨me manuellement.

Grand Audit du dimanche, deux parties. Vouvoyer SÃ©bastien.

P1 â€” ECOSYSTEM : lance via PowerShell (-File) : %USERPROFILE%\Documents\Claude\Scheduled\weekly-ecosystem-audit\ecosystem_audit.ps1 -OutputFile "$env:TEMP\ecosystem_audit_data.json", puis lis le JSON (Desktop Commander). Rapport : rÃ©sumÃ© exÃ©cutif (comptages skills/plugins/MCPs, alertes services), tableaux skills/plugins, MCPs connectÃ©s, versions npm vs disponibles, services Neo4j/Qdrant/Langfuse up/down, nouveautÃ©s vs dernier rapport, 3 actions max. POINTS DE VIGILANCE : lire CONTEXT_NOTES.md (mÃªme dossier) â€” token-optimizer/budget, npm fix, graph-server, GitHub MCP, Hermes_Gateway, TricorderKit-Worker, Master Index 01h45.

P1bis â€” ROUTAGE DEC-031 : liste les scheduled-tasks ; vÃ©rifie que chaque prompt a son bloc "ROUTAGE" et un tier cohÃ©rent (7h30/task-monitor/coordination = Haiku ; analyse 02h/rollout 12h/veille QA/news-digest/cet audit = Sonnet). Signale toute dÃ©rive + Opus >40% de la conso mensuelle.

P2 â€” TEMPLATES Japan-Alliance : via MCP obsidian-japan-alliance, lister 90_Templates/00_Core/, 90_Templates/ (racine), 90_Templates/_Exemples/ (si prÃ©sent). Anomalies en 5 catÃ©gories : A fiches-contenu dans 00_Core ; B sans numÃ©rotation TP ; C doublons/redondants ; D exemples mal classÃ©s ; E vierges ambigus (nom gÃ©nÃ©rique). Tableau | CatÃ©gorie | Nombre | Exemples (max 3) |.

RAPPORT : sauver %USERPROFILE%\Documents\Claude\Reports\ecosystem-audit-[YYYY-MM-DD].md (crÃ©er le dossier si absent) + bloc Actions prioritaires globales (â‰¤5, triÃ©es par urgence). RÃ©sumÃ© final â‰¤150 mots : "ðŸ”§ Grand Audit â€” [DATE] / Ecosystem : skills X Â· plugins X Â· MCPs X Â· services Â· routage DEC-031 / Templates : X fichiers Â· A:X B:X C:X D:X E:X / Actions 1-3".