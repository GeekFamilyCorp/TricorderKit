# ROADMAP — TricorderKit

> Version : 0.9.5 — Mise à jour : 2026-06-01
> Ce fichier décrit les phases publiques de TricorderKit.
> Les détails opérationnels internes sont dans `.planning/ROADMAP_v0.9.md`.

---

## Phases

### Phases 1–6 — v0.7 / v0.8 : Construction des fondations ✅

| Phase | Nom | Statut | Date |
|---|---|---|---|
| 1 | Foundations — mémoire, skills, token hygiene, observabilité | ✅ Complete | 10/05/2026 |
| 2 | CLI-first — cli-forge, CLIs déterministes, SQLite cache | ✅ Complete | 17/05/2026 |
| 3 | Persistent workflows — Temporal 1.23, budget guard | ✅ Complete | 15/05/2026 |
| 4 | Deep Research — pipeline autonome RSS / web / APIs | ✅ Complete | 16/05/2026 |
| 5 | Quality loop — eval-lab, security-audit-cli, hook layer v0.2 | ✅ Complete | 16/05/2026 |
| 6 | Linked project architecture — TricorderKit devient moteur générique | ✅ Complete | 17/05/2026 |

---

### Phases 7–8 — v0.9 : Orchestration + Public-ready ✅

| Phase | Nom | Statut | Date |
|---|---|---|---|
| 7 | Orchestration + observabilité — Supabase, Langfuse hooks bout-en-bout, obsidian-agent-layer, tk doctor | ✅ Complete | 22/05/2026 |
| 8 | Public-ready — INSTALL.md, exemples linked_project anonymisés, ROADMAP.md, docs anonymization, 503 tests PASS | ✅ Complete | 23/05/2026 |
| 8.5 | v0.9.5 — graphify RAG vault local-first (DEC-023), dédup G1 ingestion veille, obsidian-goat ID safety (R29/R34), security hardening | ✅ Complete | 01/06/2026 |

**Phase 7 livrables :**
- Schéma Supabase (7 tables, RLS, seed 10 publishers) — `supabase/`
- Langfuse observabilité REST-direct (no SDK) — `core/hooks/langfuse_observer.py`
- `tk obsidian` — vault router + note builder (34 tests)
- `tk security` — secrets scan + anonymization check (16 tests)
- `tk doctor` — 14 checks, `[OK]`/`[WARN]`/`[FAIL]`
- `tk rapport` — rapport Markdown/JSON depuis BOOT_SUMMARY + STATUS

**Phase 8 livrables :**
- `INSTALL.md` — guide installation public (3 options)
- `examples/linked-project-template/` — 7 fichiers anonymisés
- `docs/linked_projects.md` + `docs/anonymization.md`
- `ROADMAP.md` (ce fichier) + `STATUS.md` enrichi (table modules)
- `README.md` v0.9 complet

---

### Phases 9–12 — Futures : Extension + Communauté 🔲

| Phase | Nom | Statut | Priorité |
|---|---|---|---|
| 9 | VPS deployment — déploiement optionnel (DEC-011 : local-first maintenu) | 🔲 Planned | LOW |
| 10 | Multi-linked-project — support de plusieurs projets liés simultanés | 🟡 In progress | MEDIUM |
| 11 | Plugin marketplace — registry public, contribution guidelines | 🔲 Planned | LOW |
| 12 | Community release — GitHub public, documentation communautaire | 🔲 Planned | LOW |

> **Phase 10 — état réel** : socle livré (moteur linked_project générique, phase 6). **Deux projets liés actifs** sont déjà déclarés et routés — un assistant IA de domaine + un vault Obsidian read-only — via `configs/local/linked_projects.example.yaml`, `tk project <id>` et la doctrine de routage interne. Reste pour « complet » : support simultané testé de bout en bout (concurrence, conflits) + documentation.

---

## Principes d'évolution

TricorderKit respecte trois contraintes non négociables à chaque phase :

1. **Local-first** — aucune dépendance à un service cloud externe n'est obligatoire. Tous les services (Neo4j, Qdrant, Temporal, Langfuse) tournent en local via Docker.
2. **CLI avant LLM** — les opérations déterministes sont exécutées par des CLIs, pas par inférence LLM.
3. **Dry-run avant write** — toute écriture externe est simulée et validée avant exécution réelle.

---

## État actuel (v0.9.5 — 2026-06-01)

```
Tests       : 503 PASS — 0 FAIL — 15 skipped (live)  (+6 graphify locaux à intégrer)
Plugins     : 10 actifs (3 production-ready, 6 evolving, 1 experimental)
CLIs        : github-goat ✅ · obsidian-goat ✅ (dry_run_validated)
Skills      : tk-boot · tk-orchestrator · rtk · docmancer · token-savior · claude-code-router
Infrastructure : Neo4j ✅ · Qdrant ✅ · Temporal ✅ · Langfuse ✅
```

---

*TricorderKit v0.9.5 — GeekFamilyCorp — 2026*
