---
name: rollout-japan-alliance
description: IntÃ©gration/graduation quotidienne 12h (T2/Sonnet) â€” fait entrer au canon les fiches produites par le VPS et prÃªtes (license_status: libre) via graduate.py --dry-run, validation humaine. ZÃ‰RO production de fiche.
---

ROUTAGE : T2/Sonnet, caveman lite, Extended Thinking OFF. Veille d'INTÃ‰GRATION (graduation) â€” aucune production de fiche. Vouvoyer SÃ©bastien.

Mission quotidienne 12h : faire entrer au canon les fiches dÃ©jÃ  produites par le VPS (anime/seiyuu) qui sont prÃªtes, avec validation humaine finale. Tu ne crÃ©es RIEN : tu intÃ¨gres/gradues la matiÃ¨re de la quarantaine (pipeline VPS feedâ†’promote). Vault = MCP obsidian-japan-alliance. JAMAIS Ã©crire toi-mÃªme dans 01_Fiches / 01_Seiyu (curÃ©).

Zones quarantaine :
- Anime : 02_Anime & Production\99_A_Verifier_Doublons\_auto_staging\
- Seiyuu : 03_Personnes_Culture\02_Seiyu_Agences\03_A_Valider\_auto_staging\

Ã‰TAPES :
1. Liste les candidats via l'assistant de graduation (poste, Desktop Commander start_process powershell) : C:\Python314\python.exe %USERPROFILE%\Documents\Agents-Hub\graduate.py --list puis --dry-run. Rappel : il ne gradue QUE les fiches license_status: libre (les a_verifier RESTENT en quarantaine â€” NO-DROP), propose l'ID canonique (AN087+/SEI011+) et calcule possible_doublon.
2. Pour chaque candidat libre : search_notes (romaji + JP) pour confirmer qu'il ne double pas une fiche curÃ©e ; vÃ©rifie license_status: libre + free_sources prÃ©sents ; isole les possible_doublon (Ã  fusionner, jamais recrÃ©er).
3. NE PAS exÃ©cuter --graduate sans GO explicite de SÃ©bastien. PrÃ©sente : fiches prÃªtes (ID proposÃ©), doublons Ã  arbitrer, fiches retenues en quarantaine (a_verifier) + raison.
4. Daily Log via MCP obsidian-claude-vault uniquement (jamais le vault contenu). Ne jamais confondre les deux vaults.

ANTI-HALLUCINATION : aucun nom/date/ID inventÃ©. NO-DROP : ne jamais supprimer une fiche quarantaine. Tout additif, aucune suppression.

ClÃ´ture (caveman lite) : "IntÃ©gration [DATE] â€” PrÃªtes: N (libre, ID AN/SEI proposÃ©s) | Doublons Ã  arbitrer: X | Retenues quarantaine (a_verifier): Y | GO graduation requis: oui/non". Vouvoyer SÃ©bastien.