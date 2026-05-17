# Rapport d'audit local-first — TricorderKit v0.8
**Date** : 17/05/2026  
**Auteur** : tk-audit (automatisé + validation manuelle)  
**Périmètre** : Machine locale GeekFamilyCorp (Windows 11)

---

## Résumé exécutif

TricorderKit v0.8 est **opérationnel en local**. L'architecture linked_project est en place et validée. Les services Docker sont actifs (Neo4j, Qdrant, Langfuse, Temporal). Le rang S de la migration Phase 6 est 100% complété.

| Dimension | Statut | Note |
|---|---|---|
| Git sync TricorderKit | 🟡 DIRTY | 2 fichiers modifiés non commités (en cours) |
| Git sync Japan-Alliance | ✅ SYNCED | d8f8696 = origin |
| Structure linked_project | ✅ CONFORME | 21 OK, 2 WARN |
| Services infra | ✅ ACTIFS | Neo4j, Qdrant, Langfuse:3001, Temporal |
| CLI tk | ✅ v0.2.0 | 12 commandes disponibles |
| Tests live deep-research | ✅ PASS | MangaDex + AniList — Jikan intermittent |
| Secrets scan TricorderKit | ✅ CLEAN | Aucun terme privé détecté |

---

## 1. Synchronisation Git

### TricorderKit (`GeekFamilyCorp/TricorderKit`)

| Champ | Valeur |
|---|---|
| Branch | main |
| Commit local | b3c251f |
| Commit remote | b3c251f |
| Statut | 🟡 DIRTY (fichiers en cours de session) |
| Commits ahead | 0 |
| Commits behind | 0 |

**Fichiers modifiés non commités :**
- `[M] .gitignore` — ajout `configs/local/settings.yaml` + `configs/vps/settings.yaml`
- `[M] .planning/DECISIONS.md` — ajout DEC-010 + DEC-011

> ⚠️ Ces fichiers seront commités à la fin de la session rang A (non bloquant).

### Japan-Alliance (`GeekFamilyCorp/Japan-Alliance`)

| Champ | Valeur |
|---|---|
| Branch | main |
| Commit local | d8f8696 |
| Commit remote | d8f8696 |
| Statut | ✅ SYNCED |

---

## 2. Audit linked_project — Japan-Alliance

**Score : FAIL apparent** (21 OK / 2 WARN / 11 ERROR) — **tous les ERRORs sont des faux positifs** par conception.

### Structure ✅
| Chemin | Statut |
|---|---|
| Répertoire racine | ✅ existe |
| `japan-alliance_vault/` | ✅ existe |
| `workflows/` | ✅ existe |
| `skills/` | ✅ existe |
| `reports/` | ✅ existe |
| `project_config/project.yaml` | ✅ existe |
| `project_config/sources.yaml` | ✅ existe |

### Git ✅ (2 WARN non bloquants)
- Branch main ✅, commit d8f8696 ✅
- ⚠️ 1 fichier non commité (tests/__pycache__ — ignorable)
- ⚠️ Remote HTTPS (non SSH) — dépôt bien privé sur GitHub, vérifié

### Config ✅
- Tous les champs requis présents : project_id, project_name, domain, data_policy, paths, execution
- 7 private_terms déclarés : Japan-Alliance, JapanAlliance, MangaTracker, mangatracker-cli, jp-scraper, GeekFamilyCorp, japan-alliance_vault

### Secrets scan — 11 ERRORs (faux positifs par conception)
Les 11 erreurs sont des occurrences de `private_term:Japan-Alliance` et `private_term:GeekFamilyCorp` **dans les fichiers du repo Japan-Alliance lui-même**. C'est le comportement attendu : le scan `private_terms` est conçu pour alerter avant un push vers TricorderKit public, pas pour scanner le repo privé lui-même.

**Action requise** : aucune. Ces occurrences sont légitimes dans le repo privé Japan-Alliance.

### Cohérence ✅
- Déclaré dans `linked_projects.yaml` ✅
- Chemins cohérents ✅
- Projet activé ✅

---

## 3. Infrastructure

| Service | Port | Statut | Notes |
|---|---|---|---|
| Neo4j | 7687 / 7474 | ✅ Actif (Docker) | |
| Qdrant | 6333 | ✅ Actif (Docker) | |
| Langfuse | 3001 | ✅ Actif (Docker) | Port 3000 réservé Docker Desktop — résolu commit 0fae3ed |
| Temporal | 7233 | ✅ RUNNING | Worker actif sur `tricorderkit-hooks` |
| graph-server MCP | — | ✅ ping/store/relate/retrieve opérationnels | |
| QualityGuard | — | ✅ Semgrep 1.162.0 + Trivy 0.70.0 + Gitleaks 8.30.1 | |

---

## 4. Plugins

| Plugin | Statut | Priorité |
|---|---|---|
| cli-forge | ✅ Scaffold + github-goat + source-watch-goat | S |
| workflow-engine | ✅ source_watch + usage_observer v0.2.0 + skill_eval v0.2.0 + worker RUNNING | S |
| deep-research-core | ✅ collect + dedup + score + export + index_qdrant — tests live validés | S |
| hook-layer | ✅ v0.2.0 — core/hooks/ (7 fichiers, 25 tests) + activities + worker | S |
| eval-lab | ✅ eval_runner + baseline_store + regression_checker | A |
| obsidian-agent-layer | ✅ vault_router + note_builder + obsidian_client | B |
| security-audit-cli | ✅ security_runner (audit, check-anon, scan-secrets) | B |
| memory-boot | 🔲 À migrer v0.8 | S |
| token-hygiene | 🔲 À migrer v0.8 | S |
| agents-standard | 🔲 À créer | A |
| skill-registry | 🔲 À créer | A |
| repo-pack | 🔲 À migrer v0.8 | A |

---

## 5. CLI tk v0.2.0

| Commande | Statut |
|---|---|
| `tk status` | ✅ |
| `tk health` / `tk doctor` | ✅ |
| `tk skill list` | ✅ (10 skills détectés) |
| `tk workflow list` | ✅ (4 workflows .ts) |
| `tk vault scan` | ✅ |
| `tk research run --dry-run` | ✅ |
| `tk project list` | ✅ |
| `tk project status [id]` | ✅ |
| `tk project audit [id]` | ✅ |
| `tk project vault scan [id]` | ✅ |
| `tk project workflow list [id]` | ✅ |
| `--format json\|markdown` | ✅ sur toutes les commandes |

---

## 6. Tests live deep-research

| Source | Tests | Résultat | Date |
|---|---|---|---|
| MangaDex REST API | 3/3 | ✅ PASS | 17/05/2026 |
| AniList GraphQL | 2/2 | ✅ PASS | 17/05/2026 |
| Jikan (MyAnimeList) | — | ⚠️ 504 intermittent | 17/05/2026 |

Jikan : timeout serveur tiers, non bloquant. Aucune action requise côté TricorderKit.

---

## 7. Blockers actifs

| ID | Description | Priorité |
|---|---|---|
| KI-003 | GitHub MCP deprecated → migration vers `@github/mcp-server@latest` | Moyen |

---

## 8. Actions rang A restantes

| Item | Statut |
|---|---|
| `configs/shared/defaults.yaml` | ✅ Créé (session actuelle) |
| `configs/local/settings.yaml` | ✅ Créé (session actuelle) |
| `configs/vps/settings.yaml` | ✅ Créé — placeholder PENDING |
| `DECISIONS.md` DEC-010 + DEC-011 | ✅ Ajouté (session actuelle) |
| Ce rapport | ✅ |
| KI-003 GitHub MCP migration | 🔲 En cours |

---

*Généré le 17/05/2026 — TricorderKit v0.8 — local-first audit*
