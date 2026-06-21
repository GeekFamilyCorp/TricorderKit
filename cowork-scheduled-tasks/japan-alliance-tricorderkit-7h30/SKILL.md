---
name: japan-alliance-tricorderkit-7h30
description: Rapport matinal 07h30 (T1/Haiku) â€” lecture dÃ©lÃ©guÃ©e Ã  Ollama local (qwen:1.8b) : script PowerShell lit le vault + rÃ©dige, Claude lance et relaie (lecture seule)
---

ROUTAGE : T1/Haiku, lecture seule, Extended Thinking OFF. Le vault est lu par un script PowerShell local + Ollama (qwen:1.8b) â€” zÃ©ro token API d'analyse. Ton rÃ´le : LANCER et RELAYER, jamais lire le vault toi-mÃªme.

1. Lance via Desktop Commander start_process (shell powershell par dÃ©faut, NE PAS prÃ©fixer "powershell") : & "%USERPROFILE%\Documents\obsidian\Japan-Alliance\scripts\ollama_read_report.ps1" 2>$null. Le modÃ¨le peut charger 30-90s : si l'affichage time-out, NE PAS relancer â€” attendre puis passer Ã  l'Ã©tape 2. Au besoin, lancement dÃ©tachÃ© : Start-Process powershell.exe -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','<script>' -WindowStyle Hidden, puis sonder.
2. Lis (read_file, chemin Windows rÃ©el) : %USERPROFILE%\Documents\obsidian\Japan-Alliance\00_System\03_Manifestes_Migration\TRICORDERKIT_RAPPORTS\RAPPORT_MATIN_<AAAA-MM-JJ>.md. Absent aprÃ¨s ~90s â†’ signaler "Rapport matin Ollama non gÃ©nÃ©rÃ© â€” vÃ©rifier le serveur (Get-Process ollama) et le script" et TERMINER.
3. Relaie Ã  SÃ©bastien (vouvoiement), â‰¤120 mots, ton direct et motivant : la ligne Chiffres (Total + delta J-1 + ventilation MA+LN / AN / PC / IS / LC â€” chiffres DÃ‰TERMINISTES PowerShell : ne jamais recalculer ni inventer) ; la synthÃ¨se Ollama si exploitable, sinon 1 phrase de constat Ã  toi ; termine par "â†’ [UNE ACTION CONCRÃˆTE POUR CE MATIN]" (prioritÃ© MA/LN puis AN).

RÃ¨gles : lecture seule â€” jamais enrichir/modifier fiche ou index ; ne jamais citer les JV (en pause) ; SO = dÃ©lÃ©guÃ© (run nuit 02h + bus), ne pas retraiter. Pas de notification si tout est nominal.