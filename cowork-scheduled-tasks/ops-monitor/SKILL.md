---
name: ops-monitor
description: Sonde ops /6h (T1/Haiku, caveman full) â€” FUSION coordination-agents + dispatch-task-monitor : battement bus canal_agents (sense/intÃ©gration/dispatch/heartbeat) PUIS scan sessions Cowork â†’ TASK_MONITOR.md. Souvent no-op.
---

ROUTAGE : T1/Haiku, caveman full, Extended Thinking OFF. Sonde ops FUSIONNÃ‰E (bus canal_agents + sessions Cowork). Souvent no-op. Lecture ciblÃ©e, JAMAIS de scan vault. Max 10 fiches intÃ©grÃ©es/run, max 3 offloads/run.

==================== PARTIE A â€” BUS canal_agents ====================
TOUTE Ã©criture bus passe par : py "%USERPROFILE%\Documents\Claude\Projects\TricorderKit Autonome\canal_agents\scripts\sync_bus.py" <cmd> (read/inbox/tasks/dispatch/done/claim/heartbeat/health ; flags via <cmd> --help ; si UnicodeEncodeError : $env:PYTHONIOENCODING="utf-8"). Jamais Ã  la main, jamais python3.

A) SENSE : read --agent claude --advance ; health ; inbox --agent claude. Partenaire actif = heartbeats rÃ©cents (codex|antigravity). Aucun battement >24h â†’ traiter quand mÃªme les livrables, noter "aucun partenaire actif".
B) INTÃ‰GRATION (sauter si aucun deliverable_ready ni fichier neuf) : fiches en zone R40 `97_A_Trier/05_A_Integrer/Fiches a trier - en attente/` via MCP obsidian-japan-alliance. QA : 2 sources concordantes OU 1 primaire officielle (Wikipedia exclu) ; ID via next-id (R34) ; patch_note/write_note SANS Ã©craser ; archiver l'original (R31, jamais delete) ; conflit â†’ arbitrage SÃ©bastien. Puis done --task <ID> + 1 entrÃ©e Journal (â‰¤3 lignes).
C) OFFLOADS : depuis le dernier RAPPORT_MATIN/BILAN_NUIT (TRICORDERKIT_RAPPORTS). DÃ‰DUP OBLIGATOIRE via tasks + inbox --agent codex â€” jamais 2Ã— la mÃªme tÃ¢che. Routage selon ROUTING.md. âš ï¸ ANTI-FAMINE : si le partenaire enchaÃ®ne les task_failed (â‰¥3 rÃ©cents sans livrable), NE PAS redispatcher â€” signaler et lister pour SÃ©bastien. Arbitrages (conflits, irrÃ©versible) â†’ jamais offloadÃ©s.
D) heartbeat claude --state idle|working.

==================== PARTIE B â€” TASK MONITOR sessions Cowork ====================
1. Appelle list_sessions avec limit=50 â†’ sÃ©pare running vs idle.
2. Pour les 5 sessions idle les plus rÃ©centes, appelle read_transcript (max 3 turns) â†’ extrais la derniÃ¨re action rÃ©alisÃ©e.
3. Ã‰cris "00_SYSTEM/05_Hot_Cache/TASK_MONITOR.md" via obsidian-claude-vault (mode overwrite) :
```
---
last_check: YYYY-MM-DD HH:MM
running: N
idle: N
---
# ðŸ” Task Monitor â€” YYYY-MM-DD HH:MM

## ðŸŸ¢ Running (N)
| Titre | Session ID |
|---|---|

## ðŸŸ¡ Idle â€” relances possibles (N)
| Titre | DerniÃ¨re action | Relancer ? |
|---|---|---|

## ðŸ“Š Stats
Total: N | Running: N | Idle: N
ðŸ¤– Auto â€” ops-monitor
```
Lecture seule sur les transcripts (jamais relancer une session toi-mÃªme) ; Ã©criture uniquement dans TASK_MONITOR.md.

==================== SORTIE ====================
â‰¤10 lignes combinÃ©es : "Ops HH:30 â€” BUS (partenaire: X) integ:N offloads:A/B skip arbitrages:Z | SESSIONS running:N idle:N relances:N". Tout no-op â†’ 1 ligne. Vouvoyer SÃ©bastien, pas de notification si tout est nominal.