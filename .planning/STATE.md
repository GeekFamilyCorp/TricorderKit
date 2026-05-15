# STATE.md — TricorderKit v0.8

> État courant du projet. Mettre à jour à chaque session.

---

## Version courante

- **Version** : 0.8
- **Date** : 15/05/2026
- **Phase active** : Phase 4 — Deep Research *(débloquée)*

---

## Statut des phases

| Phase | Nom | Statut | Vérifié |
|---|---|---|---|
| 0 | Bootstrap | ✅ Verified | 2026-05-13 |
| 1 | Fondations (fichiers fondateurs) | ✅ Verified | 2026-05-10 |
| 2 | CLI-Forge | ✅ Verified | 2026-05-13 |
| 2.5 | QualityGuard | ✅ Verified | 2026-05-15 |
| 3 | Workflows persistants (Temporal) | ✅ Verified | 2026-05-15 |
| 4 | Deep Research | 🔶 En cours | — |
| 5 | Quality Loop | 🔲 Pending | Débloqué après 2.5 + 4 |

---

## Statut des plugins

| Plugin | Statut | Priorité |
|---|---|---|
| cli-forge | ✅ Scaffold + github-goat + source-watch-goat (dry_run_validated) | S |
| workflow-engine | ✅ Scaffold + source_watch.workflow.ts | S |
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
| Temporal | 🔲 Non déployé (Phase 3 scaffold OK, worker non lancé) |
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

---

## Prochaine action recommandée

```text
Phase 4 — Deep Research (suite) :
  1. Implémenter deduplicate_findings.py
  2. Implémenter export_report.py (generateur Markdown)
  3. Test live MangaDex + Jikan (appels reseau reels)
  4. Indexation Qdrant (collection manga_knowledge)
```

---

*Dernière mise à jour : 15/05/2026*
