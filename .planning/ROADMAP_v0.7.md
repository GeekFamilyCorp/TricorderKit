# ROADMAP v0.7 — TricorderKit

> Feuille de route détaillée. Mise à jour à chaque phase complétée.

---

## Vision cible

```text
TricorderKit v0.7 = CLI-first Agentic OS
Temporal workflows + Skill registry + Deep research + Obsidian knowledge layer
```

---

## Phase 1 — Fondations ✅ Complétée (10/05/2026)

**Objectif :** poser le cadre. Zéro dispersion autorisée après cette phase.

| Livrable | Statut |
|---|---|
| README_FIRST.md | ✅ |
| AGENTS.md | ✅ |
| CLAUDE.md | ✅ |
| .planning/STATE.md | ✅ |
| .planning/TASKS.md | ✅ |
| .planning/DECISIONS.md | ✅ |
| .planning/RISKS.md | ✅ |
| CHANGELOG.md | ✅ |
| MainBrain v1.4 | ✅ |
| core/contracts/skill_output.schema.json | ✅ |

**Règle :** tout nouveau GitHub entrant doit être classé, scoré, audité et rattaché à un module avant tout travail.

---

## Phase 2 — CLI-first 🔶 En cours

**Objectif :** réduire le bruit agentique. Un agent ne doit jamais interroger une API brute si une CLI existe.

**Durée estimée :** 3–5 jours

| Livrable | Priorité | Statut |
|---|---|---|
| plugins/cli-forge/cli_manifest.schema.json | S | ✅ |
| plugins/cli-forge/registry.yml | S | ✅ |
| plugins/cli-forge/scripts/validate_cli_manifest.py | S | ✅ |
| CLI github-goat | S | ✅ dry-run validé |
| CLI source-watch-goat | A | 🔶 en cours |
| CLI obsidian-goat | A | 🔲 planned |
| CLI vault-audit-goat | A | 🔲 planned |
| CLI security-goat | B | 🔲 planned |
| skills/tk-cli-forge/SKILL.md | S | 🔲 pending |
| tests/cli_contracts/ | S | ✅ |
| Dry-run mode pour chaque CLI | S | ✅ |

**Critère de sortie :** `/tk:cli-forge github` génère une CLI fonctionnelle avec output JSON et dry-run validé.

---

## Phase 3 — Workflows persistants 🔲 À démarrer

**Objectif :** rendre les tâches longues fiables. Aucune tâche > 30s hors Temporal.

**Durée estimée :** 1–2 semaines

| Livrable | Priorité |
|---|---|
| plugins/workflow-engine/ complet | S |
| Temporal worker minimal | S |
| Workflow source_watch (veille manga/anime) | S |
| Workflow vault_audit | S |
| Workflow skill_eval (non-régression) | A |
| Workflow github_ingestion | A |
| Workflow research_report | A |
| docker-compose.yml (Neo4j + Qdrant + Temporal + Langfuse) | S |
| Rate limiting token_budget par workflow | S |

**Critère de sortie :** workflow `source_watch` tourne en boucle sur MangaDex et écrit dans Obsidian sans intervention manuelle.

---

## Phase 4 — Deep Research 🔲 À démarrer

**Objectif :** industrialiser les recherches MangaTracker / AnimeTracker / GitHub.

**Durée estimée :** 2 semaines

| Livrable | Priorité |
|---|---|
| plugins/deep-research-core/ complet | S |
| trusted_sources.yml | S |
| japanese_sources.yml | S |
| Pipeline manga_sources_research | S |
| Pipeline github_research | S |
| Pipeline anime_staff_research | A |
| Connecteurs AniList GraphQL | S |
| Connecteurs MangaDex REST | S |
| Connecteurs Jikan REST | A |
| Score de fiabilité (0.0–1.0) | A |
| Cache SQLite offline | A |

**Critère de sortie :** `/tk:deep-research "One Piece volume 110"` produit un rapport Markdown sourcé indexé dans Obsidian en < 60s.

---

## Phase 5 — Fermeture boucle qualité 🔲 À démarrer

**Objectif :** chaque action importante produit un artefact traçable. Zéro action non auditée.

**Durée estimée :** ongoing

| Livrable | Priorité |
|---|---|
| plugins/obsidian-agent-layer/ | A |
| plugins/security-audit-cli/ | A |
| plugins/eval-lab/ | A |
| scripts/health_check.py | A |
| Dashboard HTML santé système | B |
| Skill dependency graph (visualisation) | B |
| Notion/Airtable bridge | C |

**Critère de sortie :** tout skill modifié déclenche automatiquement un eval non-régression et bloque le merge si régression.

---

## Jalons globaux

| Jalons | Date cible |
|---|---|
| Phase 1 complète | 10/05/2026 ✅ |
| Première CLI github-goat opérationnelle | 17/05/2026 |
| Docker Compose services up | 24/05/2026 |
| Workflow source_watch actif | 07/06/2026 |
| Deep research manga opérationnel | 21/06/2026 |
| Eval-lab non-régression automatique | 05/07/2026 |

---

*Dernière mise à jour : 10/05/2026*
