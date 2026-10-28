---
description: Boot TricorderKit session — charge le contexte, HOT_CACHE, patterns d'erreurs, état du projet. Séquence tier 1/2/3.
allowed-tools: Read, Bash, mcp__obsidian-claude-vault__read_note, mcp__obsidian-claude-vault__patch_note
---

Exécute la séquence de démarrage TricorderKit v0.9.

## Séquence obligatoire

### TIER 1 — Toujours (~500 tokens)
1. Lire `BOOT_SUMMARY.md` — résumé exécutif : version, commit, tests, Docker, prochaines tâches
2. Lire `tasks/lessons.md` — règles préventives actives (LESSON-001 à NNN)

Si TIER 1 + lessons.md suffisent pour la demande → aller directement à l'action.

### TIER 2 — Si TIER 1 insuffisant (~2 500 tokens)
3. Lire `.planning/STATE.md` — état détaillé du projet
4. Lire `.planning/TASKS.md` — pending/in_progress uniquement (exclure ✅)
5. Lire `.planning/DECISIONS.md` — 5 dernières entrées uniquement

### TIER 3 — À la demande (~10 000 tokens)
6. `docs/00_WHAT_IS_TRICORDERKIT.md`
7. `docs/01_HOW_IT_WORKS.md`
8. `docs/02_WHAT_IS_IN_PLACE.md`
9. `docs/03_WHAT_TO_DO_NEXT.md`
10. `docs/04_LLM_OPERATING_GUIDE.md`
11. `docs/06_workflow_standard.md`

## HOT_CACHE Obsidian (si MCP disponible)
- Lire `00_SYSTEM/05_Hot_Cache/HOT_CACHE.md` dans le vault `claude-vault`
  → via `mcp__obsidian-claude-vault__read_note`
- Vérifier si stale (> 7 jours depuis `updated:`)
- Si stale → signaler et proposer mise à jour via `/tk:orchestrator`

## Patterns d'erreurs actifs

| Code | Règle |
|------|-------|
| ARCH-001 | Hooks Cowork inertes → comportement auto dans SKILL.md orchestrateur |
| ENV-001 | MSIX paths → utiliser LOCALAPPDATA pour fichiers Claude Desktop |
| OPS-001 | Scheduled tasks → prompt ≤ 300 tokens (OOM sinon) |
| ARCH-002 | System prompt Cowork côté serveur → estimation uniquement |

## État infrastructure (vérifier si `--check-infra`)

```bash
docker compose ps        # Neo4j 7474 · Qdrant 6333 · Langfuse 3001 · Temporal 7233
```

- Temporal worker `tricorderkit-hooks` : task queue `tricorderkit-hooks`
- Redémarrer si nouvelles activities déployées :
  `npx ts-node plugins/workflow-engine/scripts/start_worker.ts`

## Plugins actifs (v0.9)

`cli-forge` · `workflow-engine` · `deep-research-core` · `hook-layer v0.2.0`
`eval-lab` · `obsidian-agent-layer` · `security-audit-cli` · `connector-hub v0.1.0`
`memory-boot v0.8` · `token-optimizer v0.8`

## CLIs enregistrées

`github-goat` dry_run_validated · `obsidian-goat` dry_run_validated (manifest ✅ + 19 tests)

## Output attendu

Résumé structuré :
- Version et commit HEAD
- Tests : N PASS, N skipped, 0 FAIL
- Services Docker : statut
- Prochaines priorités (backlog `[ ]`)
- Patterns actifs

Terminer par : **"Prêt. Quelle est la prochaine tâche ?"**

## Variantes

| Flag | Action |
|------|--------|
| `--summary-only` | TIER 1 uniquement (BOOT_SUMMARY + lessons) |
| `--check-infra` | + `docker compose ps` + liste des workers Temporal |
| `--update-summary` | Mettre à jour `BOOT_SUMMARY.md` après session |
| `--full` | TIER 1 + TIER 2 complet |
