---
name: backlog-japan-alliance-4h
description: [REMPLACÃ‰E par pipeline-quarantaine le 2026-06-20] ModÃ©ration quarantaine â€” fusionnÃ©e dans pipeline-quarantaine (Ã©tape 2). DÃ©sactivÃ©e, supprimable.
---

ROUTAGE : T2/Sonnet, caveman lite, Extended Thinking OFF. Veille de MODÃ‰RATION des fiches produites par le VPS â€” aucune production de fiche neuve. UNE passe ciblÃ©e par run, â‰¤10 fiches. Vouvoyer SÃ©bastien.

Mission /8h : modÃ©rer la quarantaine alimentÃ©e par le pipeline VPS (feedâ†’promote) pour prÃ©parer la graduation. Vault = MCP obsidian-japan-alliance (PÃ‰RIMÃˆTRE STRICT : %USERPROFILE%\Documents\obsidian\Japan-Alliance). JAMAIS toucher 01_Fiches / 01_Seiyu (curÃ©), ni state.db / data_sources.db.

Zones :
- Anime : 02_Anime & Production\99_A_Verifier_Doublons\_auto_staging\
- Seiyuu : 03_Personnes_Culture\02_Seiyu_Agences\03_A_Valider\_auto_staging\

Ã‰TAPES (lot â‰¤10 non encore modÃ©rÃ©es) :
1. DÃ‰DOUBLONNAGE : search_notes (romaji + JP) contre le canon â†’ si doublon, marquer possible_doublon + cible canonique (ne pas fusionner ici : signaler pour l'intÃ©gration de 12h).
2. LICENCE : vÃ©rifier license_status (libre|a_verifier) + free_sources ; absence â†’ laisser tel quel et signaler (le freecheck VPS repassera la nuit).
3. FRONTMATTER (anti double-bloc) : un seul `---`. Si le collecteur VPS a Ã©crit du YAML invalide (valeur avec `:` non quotÃ©e, ex. sources_echec), normaliser en UN bloc valide via update_frontmatter (merge) â€” jamais un 2e bloc. Remonter la cause racine Ã  SÃ©bastien (le collecteur VPS devrait quoter ces valeurs).
4. COMPLÃ‰TUDE : champs clÃ©s prÃ©sents â†’ marquer graduate: true UNIQUEMENT les fiches propres + license_status: libre + non-doublon. Les autres RESTENT en quarantaine (NO-DROP).
5. Ne JAMAIS crÃ©er de fiche, ne jamais enrichir le contenu (rÃ´le gratuit du VPS).

Rapport â‰¤6 lignes : lot traitÃ© (N), prÃªtes graduate:true (M), doublons signalÃ©s (X), licences manquantes (Y), anomalies frontmatter corrigÃ©es (Z), causes racines VPS Ã  remonter. Vouvoyer SÃ©bastien.