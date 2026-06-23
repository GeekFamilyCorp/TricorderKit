# ROADMAP — TricorderKit

> Version : 1.1.0 — Mise à jour : 2026-06-23
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
| 8.6 | Sécurité & gouvernance frontière — gate public-boundary **appliqué** (CI + pre-push, DEC-026), nettoyage frontière privé/public (legacy + capsules + chemins personnels), licence MIT, règle de sync R38 (DEC-027) | ✅ Complete | 01/06/2026 |

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

### v1.0 — Self-Improving (DEC-046) ✅

| Phase | Nom | Statut | Date |
|---|---|---|---|
| v1.0 | **Self-Improving** — learning-engine (experience cards → leçons → propositions de skill gardées par tests + revue humaine), gouvernance MCP machine-lisible (deny-by-default, `mcp/registry_allowlist.yaml` + `tk mcp audit`), scraper-runtime standardisé, moteur de fiabilité des sources, 5 évaluateurs eval-lab, 4 workflows Temporal d'auto-amélioration (exécution déportée). Chantiers N1–N7 code-complets. | ✅ Complete | 11/06/2026 |

**v1.0 livrables :**
- `plugins/learning-engine/` — experience cards → leçons → propositions de skill contrôlées (drafts uniquement ; promotion = 8 tests verts **et** revue humaine)
- `plugins/scraper-runtime/` — profils de scraping + run contract + registre de sources + moteur de fiabilité (dry-run, lecture seule)
- `mcp/registry_allowlist.yaml` + `mcp/scripts/mcp_gateway.py` — gouvernance MCP machine-lisible, `tk mcp list | audit | allowlist-check`
- `plugins/eval-lab/evaluators.py` — 5 évaluateurs (scraping, fiabilité sources, dédup, RAG retrieval, coût/latence)
- `plugins/workflow-engine/workflows/` — 4 workflows d'auto-amélioration (learning_review, skill_regression_test, source_freshness, tool_scout), worker isolé `tricorderkit-self-improving`

---

### Phases 9–12 — Futures : Extension + Communauté 🔲

| Phase | Nom | Statut | Priorité |
|---|---|---|---|
| 9 | VPS deployment — durcissement live (doctor + sauvegardes Borg + fail2ban) — DEC-011 : local-first maintenu | 🟡 In progress | LOW |
| 10 | Multi-linked-project — support de plusieurs projets liés simultanés | 🟡 In progress | MEDIUM |
| 11 | Plugin marketplace — registry public, contribution guidelines | 🔲 Planned | LOW |
| 12 | Community release — GitHub public, documentation communautaire | 🔲 Planned | LOW |

> **Phase 10 — état réel** : socle livré (moteur linked_project générique, phase 6). **Deux projets liés actifs** sont déjà déclarés et routés — un assistant IA de domaine + un vault Obsidian read-only — via `configs/local/linked_projects.example.yaml`, `tk project <id>` et la doctrine de routage interne. Reste pour « complet » : support simultané testé de bout en bout (concurrence, conflits) + documentation.

---

## Prochaines étapes (court terme — prochains jours)

| # | Action | Statut |
|---|---|---|
| A | Publier la **GitHub Release v1.1.0** (tag `v1.1.0`) | ✅ Fait (2026-06-23) |
| B | Arbitrer la **PR #2** (ouverte le 13/05) — rebase / merge / fermeture justifiée | 🔜 À faire |
| C | Intégrer les **tests graphify** à la suite committée | ✅ Fait (4 unit PASS + 1 integration Qdrant-gated) |
| D | **Indexer le vault dans Qdrant** (collection dim 768) + exposer `search_vault` en tool MCP (DEC-023) | 🟡 En cours |
| E | **Phase 10** — support multi-linked-project simultané, testé de bout en bout | 🟡 En cours |
| F | Gate **docs-sync** — cohérence mécanique README ↔ STATUS ↔ ROADMAP ↔ structure/version/tests | ✅ Fait (DEC-028, étendu au ROADMAP par DEC-047) |
| G | Évaluer la **sortie du schéma de domaine** (Supabase) hors moteur public | 🔲 À étudier |

---

## Principes d'évolution

TricorderKit respecte trois contraintes non négociables à chaque phase :

1. **Local-first** — aucune dépendance à un service cloud externe n'est obligatoire. Tous les services (Neo4j, Qdrant, Temporal, Langfuse) tournent en local via Docker.
2. **CLI avant LLM** — les opérations déterministes sont exécutées par des CLIs, pas par inférence LLM.
3. **Dry-run avant write** — toute écriture externe est simulée et validée avant exécution réelle.

---

## État actuel (v1.1.0 — 2026-06-23)

```
Tests       : 634 tests collected — 633 PASS + 1 skip (live Qdrant) — suite validée en CI
Plugins     : 13 actifs (3 production-ready, 10 en évolution, 0 experimental)
Skills      : tk-boot · tk-orchestrator · rtk · docmancer · token-savior · tk-grill · god-mode · code-corrector · agent-config-audit · skill-creator · skill-manager · consolidate-memory
Experiments : ragas_eval · temporal_memory · dedup_embeddings · graphrag · openevolve_poc (isolés, promotion sur DEC)
CLIs        : github-goat ✅ · obsidian-goat ✅ (replace-id R29 / next-id R34, dry-run)
Sécurité    : gate frontière publique + gate docs-sync appliqués (CI + pre-push, DEC-026 / DEC-028 / DEC-047) · licence MIT
Infrastructure : Neo4j ✅ · Qdrant ✅ · Temporal ✅ · Langfuse ✅ · models/ registry + observability · tools/caps (capability-on-demand)
```

---

*TricorderKit v1.1.0 — GeekFamilyCorp — 2026*
