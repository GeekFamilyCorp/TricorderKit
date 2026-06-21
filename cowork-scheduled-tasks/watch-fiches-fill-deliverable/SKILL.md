---
name: watch-fiches-fill-deliverable
description: Surveille le bus canal_agents (horaire) et prÃ©vient SÃ©bastien au deliverable_ready (ou task_failed quota) de la tÃ¢che T-2026-06-20-FICHES-FILL. Ã€ dÃ©sactiver une fois la tÃ¢che terminÃ©e.
---

Tu surveilles la tÃ¢che bus T-2026-06-20-FICHES-FILL (remplissage/correction des 67 fiches manga, lane remplissage-correction : Codex â†’ Antigravity â†’ Claude).

Ã‰TAPES (dÃ©terministe, zÃ©ro Ã©criture vault) :
1. Lis le journal du bus : fichier `%USERPROFILE%\Documents\Claude\Projects\TricorderKit Autonome\canal_agents\bus\events.jsonl` (1 event JSON par ligne).
2. Ã‰tat anti-doublon : lis/Ã©cris `%USERPROFILE%\Documents\Agents-Hub\_watch_fiches_fill.json` (clÃ© `last_seq_notifie`, dÃ©faut 0).
3. Cherche les events dont `task` == "T-2026-06-20-FICHES-FILL" ET `seq` > last_seq_notifie ET `type` âˆˆ {deliverable_ready, task_failed, task_done}.
4. S'il y en a :
   - **deliverable_ready / task_done** : ouvre le livrable citÃ© dans le payload (ex. `outbox/codex/...dryrun.json` ou `outbox/<agent>/...`), rÃ©sume : agent Ã©metteur, nb fiches traitÃ©es/`done`, nb `to_verify`, ISBN corrigÃ©s, points Ã  arbitrer. Puis NOTIFIE SÃ©bastien : Â« Livrable fiches-fill prÃªt (agent X) â€” synthÃ¨se + je peux faire la QA et classer. Â»
   - **task_failed raison quota** : NOTIFIE : Â« Quota <agent> atteint sur fiches-fill â€” coller le prompt Antigravity (`canal_agents/PROMPT_FICHES_FILL_relais.md`) pour le relais. Â»
   - Mets Ã  jour `last_seq_notifie` = plus grand seq traitÃ©.
5. **Si aucun nouvel event qualifiant : ne produis AUCUNE notification** (reste silencieux, termine sans bruit).

Utilise Python `C:\Python314\python.exe` pour lire les fichiers si besoin (encodage utf-8). Ne rÃ©clame pas la tÃ¢che, ne la traite pas toi-mÃªme : tu observes et tu prÃ©viens uniquement.