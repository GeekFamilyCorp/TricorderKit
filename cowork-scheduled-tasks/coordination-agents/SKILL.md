---
name: coordination-agents
description: [REMPLACÃ‰E par ops-monitor le 2026-06-20] Coordination bus â€” fusionnÃ©e dans ops-monitor. DÃ©sactivÃ©e, supprimable.
---

ROUTAGE : T1/Haiku, caveman full, Extended Thinking OFF. Souvent no-op. Lecture ciblÃ©e, JAMAIS de scan vault. Max 10 fiches intÃ©grÃ©es/run, max 3 offloads/run.

Battement du bus canal_agents. TOUTE Ã©criture bus passe par : py "%USERPROFILE%\Documents\Claude\Projects\TricorderKit Autonome\canal_agents\scripts\sync_bus.py" <cmd> (read/inbox/tasks/dispatch/done/claim/heartbeat/health ; flags via <cmd> --help ; si UnicodeEncodeError : $env:PYTHONIOENCODING="utf-8"). Jamais Ã  la main, jamais python3.

A) SENSE : read --agent claude --advance ; health ; inbox --agent claude. Partenaire actif = heartbeats rÃ©cents (codex|antigravity). Aucun battement >24h â†’ traiter quand mÃªme les livrables, noter "aucun partenaire actif".
B) INTÃ‰GRATION (sauter si aucun deliverable_ready ni fichier neuf) : fiches en zone R40 `97_A_Trier/05_A_Integrer/Fiches a trier - en attente/` via MCP obsidian-japan-alliance. QA : 2 sources concordantes OU 1 primaire officielle (Wikipedia exclu) ; ID via next-id (R34) ; patch_note/write_note SANS Ã©craser ; archiver l'original (R31, jamais delete) ; conflit â†’ arbitrage SÃ©bastien. Puis done --task <ID> + 1 entrÃ©e Journal (â‰¤3 lignes).
C) OFFLOADS : depuis le dernier RAPPORT_MATIN/BILAN_NUIT (TRICORDERKIT_RAPPORTS). DÃ‰DUP OBLIGATOIRE via tasks + inbox --agent codex â€” jamais 2Ã— la mÃªme tÃ¢che. Routage selon ROUTING.md. âš ï¸ ANTI-FAMINE : si le partenaire enchaÃ®ne les task_failed (â‰¥3 rÃ©cents sans livrable), NE PAS redispatcher â€” signaler et lister pour SÃ©bastien. Arbitrages (conflits, irrÃ©versible) â†’ jamais offloadÃ©s.
D) heartbeat claude --state idle|working. Sortie â‰¤8 lignes : "Coord HH:00 (partenaire: X) â€” integ: N | offloads: A Ã©mis, B skip | arbitrages | conflits" ; tout no-op â†’ 1 ligne.