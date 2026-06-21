---
name: pipeline-quarantaine
description: Pipeline quarantaine /8h (5h30/13h30/20h30, T2/Sonnet) â€” FUSION ja_promotequarantine + backlog : (1) promote VPSâ†’quarantaine via script, puis (2) modÃ©ration QA â‰¤10 fiches â†’ graduate:true. ZÃ‰RO production de fiche, NO-DROP.
---

ROUTAGE : T2/Sonnet, caveman lite, Extended Thinking OFF. Pipeline quarantaine en 2 temps : (1) PROMOTION VPSâ†’quarantaine (script dÃ©terministe, zÃ©ro LLM), puis (2) MODÃ‰RATION QA des fiches (â‰¤10/run). Aucune production de fiche neuve, NO-DROP. Vault = MCP obsidian-japan-alliance (PÃ‰RIMÃˆTRE STRICT : %USERPROFILE%\Documents\obsidian\Japan-Alliance). JAMAIS toucher 01_Fiches / 01_Seiyu (curÃ©), ni state.db / data_sources.db. Vouvoyer SÃ©bastien.

Zones quarantaine :
- Anime : 02_Anime & Production\99_A_Verifier_Doublons\_auto_staging\
- Seiyuu : 03_Personnes_Culture\02_Seiyu_Agences\03_A_Valider\_auto_staging\

==================== Ã‰TAPE 1 â€” PROMOTION (script) ====================
Execute EXACTEMENT cette commande via Desktop Commander start_process (shell powershell.exe), puis rapporte sa sortie :

C:\Python314\python.exe %USERPROFILE%\Documents\Agents-Hub\promote_to_vault.py --once

Ce script : lit le staging VPS (paramiko, __VPS_TAILNET_IP__, cle ~/.ssh/vps_hostinger) â€” fiches anime/seiyuu status: to_verify ; ecrit UNIQUEMENT dans les 2 sous-dossiers _auto_staging (quarantaine a-verifier / a-valider) ; ne touche JAMAIS 01_Fiches ni 01_Seiyu ni state.db ; marque les seiyuu internal_only: true ; deduplique contre l'existant curÃ© (possible_doublon) et la quarantaine ; limite chaque run a 15 anime + 15 seiyuu, saute ce qui est deja dans %USERPROFILE%\Documents\Agents-Hub\_promote_state.json. Si la sortie signale "STOP garde-fou" ou une erreur de connexion VPS, rapporte-la sans corriger toi-meme. Note : nb anime/seiyuu crees ce run + total promus.

==================== Ã‰TAPE 2 â€” MODÃ‰RATION (â‰¤10 fiches non encore modÃ©rÃ©es) ====================
1. DÃ‰DOUBLONNAGE : search_notes (romaji + JP) contre le canon â†’ si doublon, marquer possible_doublon + cible canonique (ne pas fusionner ici : signaler pour la graduation de 12h).
2. LICENCE : vÃ©rifier license_status (libre|a_verifier) + free_sources ; absence â†’ laisser tel quel et signaler (le freecheck VPS repassera la nuit).
3. FRONTMATTER (anti double-bloc) : un seul `---`. Si le collecteur VPS a Ã©crit du YAML invalide (valeur avec `:` non quotÃ©e, ex. sources_echec), normaliser en UN bloc valide via update_frontmatter (merge) â€” jamais un 2e bloc. Remonter la cause racine Ã  SÃ©bastien (le collecteur VPS devrait quoter ces valeurs).
4. COMPLÃ‰TUDE : champs clÃ©s prÃ©sents â†’ marquer graduate: true UNIQUEMENT les fiches propres + license_status: libre + non-doublon. Les autres RESTENT en quarantaine (NO-DROP).
5. Ne JAMAIS crÃ©er de fiche, ne jamais enrichir le contenu (rÃ´le gratuit du VPS).

==================== RAPPORT (â‰¤7 lignes) ====================
"Pipeline quarantaine [DATE HH:30] â€” Promotion: +N anime / +M seiyuu (total promus T) | ModÃ©ration: lot traitÃ© L, prÃªtes graduate:true G, doublons X, licences manquantes Y, frontmatter corrigÃ©s Z | causes racines VPS Ã  remonter". Vouvoyer SÃ©bastien.