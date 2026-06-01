# STATUS.md — TricorderKit v0.9
> Mis à jour : 2026-06-01
> Source : BOOT_SUMMARY.md + scan `plugins/` + audit session

---

## Modules core

| Module | Stabilité | Description |
|---|---|---|
| `core/mainbrain` | ✅ Stable | Algorithme de décision MainBrain v1.5 |
| `core/contracts` | ✅ Stable | Schémas JSON contractuels (skill output) |
| `core/hooks` | ✅ Stable | Hook layer v0.2 (Pre-Intent / Pre-Execution / Post-Execution) |
| `cli/tk.py` | ✅ Stable | CLI unifiée — tk status / health / doctor / skill / workflow / vault / research / project / security / obsidian / rapport |
| `plugins/workflow-engine` | 🔄 Evolving | Temporal workflows + activities + worker (wiring connector-hub en cours) |
| `plugins/deep-research-core` | ✅ Stable | Pipeline recherche autonome (RSS, web, APIs) |
| `plugins/cli-forge` | 🔄 Evolving | Générateur CLI déterministe — tests partiels |
| `plugins/eval-lab` | 🔄 Evolving | Quality loop — eval_runner + regression_checker |
| `plugins/connector-hub` | 🔄 Evolving | Hub de connexion services (Temporal wiring en cours) |
| `plugins/hook-layer` | ✅ Stable | Hooks câblés dans MainBrain + 25 tests |
| `plugins/obsidian-agent-layer` | 🔄 Evolving | Vault router + note builder — 34 tests |
| `plugins/security-audit-cli` | ✅ Stable | Secrets scan + anonymization check + dep audit |
| `plugins/memory-boot` | 🔄 Evolving | Boot de session — migration v0.8 complète |
| `plugins/token-optimizer` | ✅ Stable | Budget guard + router + caveman mode |
| `plugins/graphify` | 🔄 Evolving | RAG vault local-first — index_vault · hybrid_rag · search_vault · ingest_veille (DEC-023) |
| `supabase/` | 🔄 Evolving | Schéma PostgreSQL domain data (7 tables, RLS) |

---

## Tableau de bord plugins

| Plugin | Status | CLI | Tests | Docs | Production-ready |
|---|---|---|---|---|---|
| cli-forge | ✅ Actif | ✅ | ❌ | ❌ | ⚠️ Partiel |
| workflow-engine | ✅ Actif | ✅ | ❌ | ❌ | ⚠️ Partiel |
| deep-research-core | ✅ Actif | ✅ | ✅ | ✅ | ✅ |
| connector-hub | ✅ Actif v0.1.0 | ✅ | ❌ | ✅ | ⚠️ Partiel |
| security-audit-cli | ✅ Actif | ✅ | ✅ | ✅ | ✅ |
| eval-lab | ✅ Actif | ❌ | ✅ | ❌ | ⚠️ Partiel |
| memory-boot | ✅ Actif v0.8 | ❌ | ✅ | ✅ | ⚠️ Partiel |
| obsidian-agent-layer | ✅ Actif | ✅ | ✅ | ✅ | ⚠️ Partiel |
| graphify | ✅ Actif | ✅ | ⚠️ | ✅ | ⚠️ Partiel |
| token-optimizer | ✅ Actif v0.8 | ✅ | ✅ | ✅ | ✅ |

---

## Légende

| Symbole | Signification |
|---|---|
| ✅ | Présent / Opérationnel |
| ❌ | Absent |
| ⚠️ | Partiel — manque tests ou docs |
| 🔧 | WIP — pas encore dans Plugins actifs |

### Stabilité modules

| Symbole | Signification |
|---|---|
| ✅ Stable | Interface figée, tests complets, docs à jour |
| 🔄 Evolving | Fonctionnel mais en évolution active (tests ou docs partiels) |
| 🧪 Experimental | Prototype — interface susceptible de changer |

**Production-ready** = Statut actif + au moins CLI ou Tests + Docs.

---

## Résumé

- **Prêts production** : 3 / 10 (`deep-research-core`, `token-optimizer`, `security-audit-cli`)
- **Partiels** : 7 / 10 (`cli-forge`, `workflow-engine`, `connector-hub`, `eval-lab`, `memory-boot`, `obsidian-agent-layer`, `graphify`)
- **Non prêts** : 0 / 10
- **WIP** : 0 / 10

---

*TricorderKit v0.9.5 — 2026-06-01 — 503 tests PASS, 0 FAIL*
