# BOOT_SUMMARY — TricorderKit
> Fichier généré automatiquement. Ne pas éditer manuellement.
> Mise à jour : fin de chaque session (skill `rapport` ou `/tk:boot --update-summary`).
> Objectif : remplacer le chargement de ~13 500 tokens par ~500 tokens au boot.

---

## Version & statut

| Champ | Valeur |
|---|---|
| Version | **v0.9** (M1→M4 COMPLETS — session 2026-05-22) |
| Commit HEAD | `f1a5a54` (GitHub sync ✅) |
| Dernière session | 2026-05-22 |
| Tests | **435 PASS** (413+20 observabilité+8 rapport+14 doctor−skipped), 15 skipped (live) |
| Blockers actifs | Aucun |

---

## Infrastructure Docker

| Service | Port | Statut |
|---|---|---|
| Neo4j | 7474/7687 | ✅ |
| Qdrant | 6333 | ✅ |
| Langfuse | **3001** | ✅ |
| Temporal | 7233 | ✅ Worker RUNNING `tricorderkit-hooks` |

---

## Prochaines tâches (v0.9 M5)

1. `⬜` security-audit-cli — CLI + tests manquants (priorité haute)
2. `⬜` obsidian-agent-layer — couverture tests (priorité moyenne)
3. `⬜` VPS deployment — optionnel (DEC-011)

### Complété session v0.9 M4 ✅ (2026-05-22)
- **Token Hygiene** — CLAUDE.md v0.9, cowork-boot skill, QUEUE.md, instructions Space Cowork JA
- **BOOT_SUMMARY_JA.md** — créé dans claude-vault (boot Cowork ≤ 500 tokens)
- **session_capsule_v0.9_JA.json** — généré et copié dans claude-vault
- **B3** — Tests live deep-research 24/24 PASS (MangaDex + Jikan + AniList + Pipeline)
- **FIX-CONF** — 359/359 PASS, version strings 0.8→0.9 M2 syncées
- **M4-OBS** — Langfuse hooks bout-en-bout, 20/20 tests, traces live :3001
- **M5-Temporal** — 8 activities source_watch → connector_hub.dispatch
- **M6-Supabase** — 5 tables content + RLS + seed studios, 36/36 tests
- **M7-boot** — obsidian-goat manifest + /tk:boot v0.9 TIER 1/2/3
- **M3-LIVE** — Pipeline rtk→docmancer : Chainsaw Man → Obsidian ✅
- **STATUS.md** — table 10 modules créée
- **tk rapport** — CLI + --json, 8 tests
- **tk doctor** — 14 checks, whitelist secrets, 14 tests
- **DEC-013** — Japan-Alliance vault-only strict (.py interdit)
- **R16** — version bump → grep tests/ pour strings hard-codées
- **R17** — _check_secrets whitelist — tester .env.example + *.md + source grep
- **linked-project template** — examples/ anonymisé, 527 lignes, 0 secret
- **INSTALL.md** — réécrit structure publique, tk doctor central

### Complété sessions v0.9 M1→M3 ✅
- memory-boot + token-optimizer migrés v0.8 (52 tests)
- skills rtk + docmancer créés
- obsidian-goat CLI v0.1.0 (19 tests, registry v0.2.0)
- .claude/commands/boot.md → /tk:boot natif
- connector_hub --temporal opérationnel
- Supabase Japan-Alliance Phase 1+2 (65 tests)
- tk-orchestrator budget_guard phase 2 (25 tests)
- B2 observabilité hook logs → Obsidian

---

## Patterns d'erreurs actifs

| Code | Règle |
|---|---|
| ARCH-001 | Hooks Cowork inertes → comportement auto dans SKILL.md orchestrateur |
| ENV-001 | MSIX paths → utiliser LOCALAPPDATA pour fichiers Claude Desktop externes |
| OPS-001 | Scheduled tasks → prompt ≤ 300 tokens |
| ARCH-002 | System prompt Cowork côté serveur → estimation uniquement |

---

## Dernières décisions

| Code | Résumé |
|---|---|
| DEC-013 | Japan-Alliance vault-only strict : aucun fichier .py autorisé |
| DEC-011 | VPS extension optionnelle future — local-first maintenu |
| DEC-010 | linked_project : TricorderKit exécute, Japan-Alliance spécialise |
| DEC-009 | Graphify hybride Neo4j + Qdrant |
| DEC-008 | LangGraph < 30s / Temporal > 30s |

---

## Plugins actifs

`cli-forge` ✅ · `workflow-engine` ✅ · `deep-research-core` ✅ · `hook-layer v0.2.0` ✅
`eval-lab` ✅ · `obsidian-agent-layer` ✅ · `security-audit-cli` ✅ · `connector-hub v0.1.0` ✅
`memory-boot` ✅ v0.8 · `token-optimizer` ✅ v0.8

---

## Pour aller plus loin (lazy-load)

| Besoin | Fichier à charger |
|---|---|
| Vision produit | `docs/00_WHAT_IS_TRICORDERKIT.md` |
| Architecture interne | `docs/01_HOW_IT_WORKS.md` |
| Inventaire opérationnel | `docs/02_WHAT_IS_IN_PLACE.md` |
| Backlog détaillé | `docs/03_WHAT_TO_DO_NEXT.md` |
| Guide LLM complet | `docs/04_LLM_OPERATING_GUIDE.md` |
| Workflow Standard | `docs/06_workflow_standard.md` |
| Règles agents | `AGENTS.md` |
| Toutes les décisions | `.planning/DECISIONS.md` |
| Tous les risques | `.planning/RISKS.md` |

---

## Skills disponibles

`tk-boot` ✅ · `tk-orchestrator` ✅ v0.2.0 · `consolidate-memory` ✅
`rtk` ✅ · `docmancer` ✅ · `token-savior` ✅ · `claude-code-router` ✅
`skill-creator` ✅ · `skill-manager` ✅ · `cowork-boot` ✅ NEW

## CLIs enregistrées (cli-forge registry v0.2.0)

`github-goat` ✅ dry_run_validated · `obsidian-goat` ✅ dry_run_validated (19 tests)

## Commandes CLI disponibles

`tk boot` ✅ · `tk rapport` ✅ · `tk rapport --json` ✅ · `tk doctor` ✅
`tk budget-guard` ✅ · `tk session-budget` ✅

---

*Auto-généré — TricorderKit v0.9 M4 — 2026-05-22 — 435 tests, 0 FAIL*
