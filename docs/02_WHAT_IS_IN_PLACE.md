# TricorderKit — Inventaire opérationnel

> Version 0.8 — Mise à jour : 2026-05-18
> Source de vérité : `.planning/STATE.md` (commit HEAD `dd6902f`)

---

## Infrastructure Docker

| Service | Port | Statut | Notes |
|---|---|---|---|
| Neo4j | 7474 / 7687 | ✅ RUNNING | Graph store |
| Qdrant | 6333 | ✅ RUNNING | Vector store |
| Langfuse | **3001** | ✅ RUNNING | Port 3000 réservé Docker Desktop |
| Temporal | 7233 | ✅ RUNNING | Worker actif `tricorderkit-hooks` |
| Temporal UI | 8080 | ✅ RUNNING | |
| Temporal PostgreSQL | 5432 | ✅ RUNNING | Fix KI-004 : SQLite→Postgres |

---

## Plugins

| Plugin | Statut | Détail |
|---|---|---|
| cli-forge | ✅ Opérationnel | github-goat + source-watch-goat (dry_run_validated) |
| workflow-engine | ✅ Opérationnel | Worker RUNNING, usageObserver v0.2.0 + skillEval v0.2.0 |
| deep-research-core | ✅ Complet (tests live prêts) | collect + dedup + score + export + index_qdrant |
| hook-layer | ✅ v0.2.0 COMPLET | pre_intent + pre_execution + post_execution, 25 tests |
| eval-lab | ✅ Complet | eval_runner Typer + baseline_store + regression_checker |
| obsidian-agent-layer | ✅ Complet | vault_router + note_builder + obsidian_client |
| security-audit-cli | ✅ Complet | Semgrep 1.162.0 + Trivy 0.70.0 + Gitleaks 8.30.1 |
| connector-hub | ✅ v0.1.0 | list/status/dispatch — 19 sources, routing CLI |
| graphify | ✅ Opérationnel | graph-server MCP : ping/store/relate/retrieve |
| memory-boot | 🔲 À migrer v0.8 | Skill disponible en Cowork, plugin non conforme v0.8 |
| token-hygiene | 🔲 À migrer v0.8 | Plugin non conforme v0.8 |
| agents-standard | 🔲 À créer | v0.9 |
| skill-registry | 🔲 À créer | v0.9 |

---

## Skills

| Skill | Statut | Fichier |
|---|---|---|
| tk-boot | ✅ v0.2.0 | `skills/tk-boot/SKILL.md` |
| tk-orchestrator | ⚠️ Spec validée, implémentation démarrée | `skills/tk-orchestrator/SKILL.md` |
| consolidate-memory | ✅ Disponible | `skills/consolidate-memory/` |
| skill-creator | ✅ Disponible | `skills/skill-creator/` |
| skill-manager | ✅ Disponible | `skills/skill-manager/` |

---

## CLIs (cli-forge pattern)

| CLI | Statut | Commandes |
|---|---|---|
| github-goat | ✅ dry_run_validated | list-repos, get-repo, search-repos, list-issues |
| source-watch-goat | ✅ dry_run_validated | sources déclarées, MangaDex connecté |
| tk (façade) | ✅ v0.2.0 | status, doctor, project list/status, vault scan, workflow list, research run, audit, health |

---

## Tests

| Suite | Statut | Coverage |
|---|---|---|
| tests/test_cli_local.py | ✅ 36/36 PASS | CLI tk toutes commandes, encoding, JSON contract |
| tests/test_linked_project.py | ✅ 42/42 PASS | linked_project_audit + local_vs_github_audit |
| core/hooks/tests/test_hooks.py | ✅ 25/25 PASS | pre_intent, pre_execution, post_execution |
| tests/cli_contracts/test_github_goat.py | ✅ (voir TASKS) | dry-run + JSON contract |
| tests/live/ (deep-research) | ⚠️ Prêts — réseau requis | MangaDex + AniList (Jikan 504 non bloquant) |
| **TOTAL** | **103 PASS** | |

---

## QualityGuard

| Outil | Version | Statut |
|---|---|---|
| Semgrep | 1.162.0 | ✅ Actif |
| Trivy | 0.70.0 | ✅ Actif |
| Gitleaks | 8.30.1 | ✅ Actif |
| error_memory SQLite | — | ✅ SHA-256 + block-check actif |

---

## Fichiers fondateurs

| Fichier | Statut | Notes |
|---|---|---|
| README.md | ✅ v0.8 | Badges + What's New |
| README_FIRST.md | ✅ | Point d'entrée forcé |
| AGENTS.md | ✅ v0.8 | Caveman Protocol + Workflow Standard |
| CLAUDE.md | ✅ | Hook Stop enregistré |
| CHANGELOG.md | ✅ | Entrée [0.8.0] complète |
| BOOT_SUMMARY.md | ✅ NEW | Tier 1 boot (~500 tokens) |
| core/mainbrain/MainBrain_v1.5.md | ✅ | Étapes 0, 2.5, 7bis câblées |
| core/contracts/skill_output.schema.json | ✅ v1.0.0 | Contrat JSON obligatoire |
| docs/06_workflow_standard.md | ✅ NEW | R8→R15, séquence 11 étapes |
| tasks/todo.md | ✅ NEW | Plan session courant |
| tasks/lessons.md | ✅ NEW | LESSON-001 à 005 |
| .planning/DECISIONS.md | ✅ | DEC-001 à DEC-011 |

---

*TricorderKit v0.8 — GeekFamilyCorp — 2026-05-18*
