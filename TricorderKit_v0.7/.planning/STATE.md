# STATE.md — TricorderKit v0.8

> État courant du projet. Mettre à jour à chaque session.

---

## Version courante

- **Version** : 0.8
- **Date** : 16/05/2026
- **Phase active** : Phase 4 — Deep Research *(débloquée)*

---

## Statut des phases

| Phase | Nom | Statut | Vérifié |
|---|---|---|---|
| 0 | Bootstrap | ✅ Verified | 2026-05-13 |
| 1 | Fondations (fichiers fondateurs) | ✅ Verified | 2026-05-10 |
| 2 | CLI-Forge | ✅ Verified | 2026-05-13 |
| 2.5 | QualityGuard | ✅ Verified | 2026-05-15 |
| 3 | Workflows persistants (Temporal) | ✅ **Worker RUNNING** | 2026-05-16 |
| 4 | Deep Research | 🔶 En cours | — |
| 5 | Quality Loop | 🔲 Pending | Débloqué après 2.5 + 4 |

---

## Statut des plugins

| Plugin | Statut | Priorité |
|---|---|---|
| tk-orchestrator | ✅ v0.2.0 implémenté — 82 tests verts — schema-compliant (DEC-008) | S |
| cli-forge | ✅ Scaffold + github-goat + source-watch-goat (dry_run_validated) | S |
| workflow-engine | ✅ Worker RUNNING — 6 activités + 2 workflows — auto-start Windows configuré | S |
| deep-research-core | ✅ Scripts collect+score validés + japanese_sources.yml + pipelines github+anime | S |
| memory-boot | 🔲 À migrer v0.8 | S |
| token-hygiene | 🔲 À migrer v0.8 | S |
| agents-standard | 🔲 À créer | A |
| skill-registry | 🔲 À créer | A |
| repo-pack | 🔲 À migrer v0.8 | A |
| usage-observer | 🔲 À créer | A |
| eval-lab | 🔲 À créer (Phase 5) | A |
| obsidian-agent-layer | 🔲 À créer (Phase 5) | B |
| security-audit-cli | 🔲 À créer (Phase 5) | B |

---

## Infrastructure

| Service | Statut |
|---|---|
| Neo4j | ✅ Actif via Docker Compose |
| Qdrant | ✅ Actif via Docker Compose |
| Langfuse | ✅ Actif via Docker Compose |
| Temporal | ✅ **ACTIF** — Worker RUNNING sur `tricorderkit-hooks` / `localhost:7233` (16/05/2026) |
| graph-server MCP | ✅ ping / store / relate / retrieve opérationnels |
| QualityGuard | ✅ Semgrep 1.162.0 + Trivy 0.70.0 + Gitleaks 8.30.1 |
| error_memory SQLite | ✅ SHA-256 + block-check actif |

---

## Blockers actifs

| ID | Description | Niveau |
|---|---|---|
| KI-003 | GitHub MCP deprecated → migration vers `@github/mcp-server@latest` manuelle requise | Moyen |

---

## Bugs résolus récents

| ID | Description | Commit | Date |
|---|---|---|---|
| ERR-T-001 | UUID Qdrant invalide (chars non-hex) → SHA-1 hex pur | — | 2026-05-13 |
| ERR-T-002 | `${CLAUDE_PLUGIN_ROOT}` → chemin absolu + `datetime.utcnow()` → `datetime.now(timezone.utc)` | `40d3166` | 2026-05-15 |
| KI-004 | Temporal : SQLite non supporté → postgres12 + temporal-db + workflows/index.ts manquant | — | 2026-05-16 |

---

## GitHub Sync

| Repo | Branche | Dernier commit | Contenu pushé |
|---|---|---|---|
| `GeekFamilyCorp/TricorderKit` (public) | `main` | `HEAD` | workflow-engine complet (tsconfig, package.json, workflows/index.ts, INSTALL.md, start_worker_auto.ps1, docker-compose.yml, dynamicconfig) |
| `GeekFamilyCorp/Japan-Alliance` (privé) | `main` | `1bd4d8beb1` | sources config (trusted+japanese), 3 pipelines domaine, test_live_sources.py complet, SKILL.md interne |

**Règle d'anonymisation appliquée** : fichiers poussés vers TricorderKit ne contiennent aucune référence à Japan-Alliance (projet), MangaTracker ou mangatracker-cli. Les termes génériques (manga, anime, MangaDex, Jikan, AniList) sont conservés comme références aux services publics.

---

## Prochaine action recommandée

```text
Phase 4 — Deep Research (suite) :
  0. [DONE] tk-orchestrator v0.2.0 — 82 tests verts, schema-compliant (DEC-008)
  1. [DONE] deduplicate_findings.py — merge cross-source + fuzzy Jaccard (threshold 0.80)
  2. [DONE] export_report.py — rapport Markdown/Obsidian avec frontmatter YAML
  3. [DONE] Tests live reseau — 24/24 passes (MangaDex, Jikan, AniList, pipeline Berserk)
  4. [DONE] index_qdrant.py — collection manga_knowledge, UUID5 idempotent, multi-backend embedder
  5. [DONE] GitHub sync — TricorderKit (public, anonymisé) + Japan-Alliance (privé, complet)
  6. [DONE] Hook Layer v0.2.0 — 3 hooks + Temporal Worker RUNNING (16/05/2026)

Phase 4 — Prochaine étape :
  → Implémenter index_neo4j.py — ingestion graph (nœuds manga/anime/auteur, relations)
  → Ou démarrer Phase 5 : Quality Loop (eval-lab, obsidian-agent-layer)
```

---

*Dernière mise à jour : 16/05/2026 — KI-004 résolu : Temporal worker RUNNING*
