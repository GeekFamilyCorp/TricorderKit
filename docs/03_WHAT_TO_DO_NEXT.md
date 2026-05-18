# TricorderKit — Quoi faire ensuite ?

> Version 0.8 → v0.9 — 2026-05-18
> Source : `.planning/STATE.md` + `.planning/TASKS.md` + Audit 2026-05-18

---

## Statut global

v0.8 est **COMPLET** (103 tests verts, commit `dd6902f`).
La prochaine version est **v0.9**.

---

## Priorités v0.9 — Rang S (critiques)

### S1 — Wiring Temporal → connector_hub.dispatch

**Objectif :** déclencher automatiquement `source_watch.workflow.ts` via le connector_hub.
**Pourquoi :** fermer la boucle entre l'intention (tk CLI) et l'exécution durable (Temporal).
**Fichiers :** `plugins/connector-hub/`, `plugins/workflow-engine/workflows/source_watch.workflow.ts`
**Preuve de fin :** `tk workflow list` affiche un run actif après `tk dispatch source-watch`

### S2 — tk-orchestrator implémentation minimale

**Objectif :** implémenter `skills/tk-orchestrator/orchestrator.py` (budget_guard + router + output_compress).
**Pourquoi :** routing intelligent des commandes /tk:*, caveman mode forcé sur sorties inter-agents.
**Fichiers :** `skills/tk-orchestrator/orchestrator.py`, `skills/tk-orchestrator/budget/`, `skills/tk-orchestrator/router/`
**Preuve de fin :** `/tk:orchestrate "test"` → JSON contractuel, budget affiché, caveman mode actif

### S3 — Migrer memory-boot + token-hygiene plugins → v0.8

**Objectif :** conformité contrat JSON, manifest v0.8, tests.
**Pourquoi :** les deux plugins les plus critiques pour la session hygiene sont non-conformes.
**Fichiers :** `plugins/memory-boot/`, `plugins/token-optimizer/`
**Preuve de fin :** `pytest plugins/memory-boot/tests/ plugins/token-optimizer/tests/` → PASS

### S4 — /tk:boot wiring `.claude/commands/`

**Objectif :** créer `.claude/commands/boot.md` pour que `/tk:boot` soit disponible nativement.
**Pourquoi :** le skill est défini mais pas câblé en tant que commande Claude Code.
**Fichiers :** `.claude/commands/boot.md`
**Preuve de fin :** `/tk:boot` exécutable depuis une session Claude Code fraîche

---

## Priorités v0.9 — Rang A (importants)

### A1 — Obsidian goat CLI

**Objectif :** créer `tools/obsidian-goat/obsidian_goat.py` (read-note, write-note, update-hot-cache, append-log).
**Pourquoi :** automatiser la mise à jour du HOT_CACHE Obsidian en fin de session (actuellement manuelle).
**Pattern :** suivre exactement github-goat (dry-run, cache SQLite, JSON output, test contrat).
**Preuve de fin :** `python obsidian_goat.py update-hot-cache --dry-run` → JSON propre

### A2 — Japan-Alliance Phase 1 — schéma Supabase

**Objectif :** créer les tables `series`, `authors`, `publishers`, `volumes`, `ai_extractions`, `review_queue`.
**Pourquoi :** phase 1 du linked_project Japan-Alliance, bloque toutes les phases suivantes.
**Repo :** `GeekFamilyCorp/Japan-Alliance`
**Preuve de fin :** migration Supabase appliquée, tables visibles dans le dashboard

### A3 — ROADMAP_v0.9.md

**Objectif :** créer `.planning/ROADMAP_v0.9.md` avec jalons datés.
**Pourquoi :** continuité du planning (ROADMAP_v0.7.md existe, rien pour v0.9).

---

## Priorités v0.9 — Rang B (utiles)

### B1 — Skills manquants à créer

| Skill | Description |
|---|---|
| `rtk` | Wrapper Cowork → pipeline deep-research-core CLI |
| `docmancer` | Génération notes Obsidian / docs Markdown via obsidian-agent-layer |
| `token-savior` | Alias/skill Cowork → token-hygiene plugin |
| `claude-code_router` | Formalisation du routing (tk-orchestrator exposé en Cowork) |

### B2 — Pipeline observabilité bout-en-bout

**Objectif :** câbler hook logs → Temporal → obsidian-agent-layer → Obsidian ERRORS.md + HOT_CACHE.
**Prérequis :** S3 (memory-boot migré) + A1 (obsidian-goat CLI).

### B3 — Tests live deep-research

**Objectif :** exécuter `pytest tests/ --live` (MangaDex + AniList).
**Prérequis :** connexion réseau activée.

---

## Risques actifs

| ID | Niveau | Description | Action |
|---|---|---|---|
| R-001 | MEDIUM | Tests live deep-research jamais exécutés | Priorité B3 |
| R-002 | LOW | docs/00→04 absents de v0.8 → créés le 18/05 | ✅ Résolu |
| R-003 | LOW | HOT_CACHE 15j stale → mis à jour le 18/05 | ✅ Résolu |

---

*TricorderKit v0.8 → v0.9 — GeekFamilyCorp — 2026-05-18*
