---
description: Boot TricorderKit session — charge le contexte, HOT_CACHE, patterns d'erreurs, état du projet. Séquence tier 1/2/3.
allowed-tools: Read, Bash, mcp__obsidian-claude-vault__read_note, mcp__obsidian-claude-vault__patch_note
---

Exécute la séquence de démarrage TricorderKit v0.8.

## Séquence obligatoire

### TIER 1 — Toujours (~500 tokens)
1. Lire `BOOT_SUMMARY.md` — résumé exécutif : version, commit, tests, Docker, prochaines tâches
2. Lire `tasks/lessons.md` — règles préventives actives (LESSON-001 à NNN)

Si TIER 1 + lessons.md suffisent pour la demande → aller directement à l'action.

### TIER 2 — Si TIER 1 insuffisant (~2 500 tokens)
3. Lire `.planning/STATE.md` — état détaillé du projet
4. Lire `.planning/TASKS.md` — pending/in_progress uniquement
5. Lire `.planning/DECISIONS.md` — 5 dernières entrées uniquement

### TIER 3 — À la demande (~10 000 tokens)
6. `docs/00_WHAT_IS_TRICORDERKIT.md`
7. `docs/01_HOW_IT_WORKS.md`
8. `docs/02_WHAT_IS_IN_PLACE.md`
9. `docs/03_WHAT_TO_DO_NEXT.md`
10. `docs/04_LLM_OPERATING_GUIDE.md`
11. `docs/06_workflow_standard.md`

## HOT_CACHE Obsidian (si MCP disponible)
- Lire `00_SYSTEM/05_Hot_Cache/HOT_CACHE.md` dans le vault claude-vault
- Vérifier si stale (> 7 jours depuis `updated:`)
- Si stale → signaler et proposer mise à jour

## Patterns d'erreurs actifs
- PATTERN-ARCH-001 : hooks inerts → implémenter dans SKILL.md, pas hooks/
- PATTERN-ENV-001 : chemins MSIX → utiliser %LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\
- PATTERN-OPS-001 : scheduled task OOM → limiter tokens, segmenter
- PATTERN-ARCH-002 : system prompt server-side → pas de hook pre_session Cowork

## Output attendu

Résumé structuré : version, commit, tests, Docker, prochaines priorités, patterns actifs.
Terminer par : "Prêt. Quelle est la prochaine tâche ?"

## Variantes
- `--summary-only` : TIER 1 uniquement
- `--check-workflows` : ajouter docker compose ps + tk workflow list
- `--update-summary` : mettre à jour BOOT_SUMMARY.md après les tâches
