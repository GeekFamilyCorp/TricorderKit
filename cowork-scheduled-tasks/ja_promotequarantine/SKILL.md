---
name: ja_promotequarantine
description: [REMPLACÃ‰E par pipeline-quarantaine le 2026-06-20] Promoteur VPS â€” fusionnÃ© dans pipeline-quarantaine (Ã©tape 1). DÃ©sactivÃ©e, supprimable.
---

Tache automatique JA_PromoteQuarantine (promoteur gouverne, zone QUARANTAINE sure et isolee).

Execute EXACTEMENT cette commande via Desktop Commander start_process (shell powershell.exe), puis rapporte sa sortie :

C:\Python314\python.exe %USERPROFILE%\Documents\Agents-Hub\promote_to_vault.py --once

Ce script :
- lit le staging VPS (paramiko, __VPS_TAILNET_IP__, cle ~/.ssh/vps_hostinger) â€” fiches anime/seiyuu status: to_verify ;
- ecrit UNIQUEMENT dans les 2 sous-dossiers _auto_staging du vault (quarantaine a-verifier / a-valider) ;
- ne touche JAMAIS 01_Fiches ni 01_Seiyu (fiches curees) ni state.db ;
- marque les seiyuu internal_only: true ; deduplique contre l'existant curÃ© (possible_doublon) et contre la quarantaine (skip fichier existant) ;
- limite chaque run a 15 anime + 15 seiyuu, et saute ce qui est deja dans %USERPROFILE%\Documents\Agents-Hub\_promote_state.json.

NE FAIS RIEN D'AUTRE : pas d'edition manuelle du vault, pas de LLM, pas d'appel payant. Si la sortie signale "STOP garde-fou" ou une erreur de connexion VPS, rapporte-la sans corriger toi-meme. Rapporte : nb anime/seiyuu crees ce run + total promus dans le state.