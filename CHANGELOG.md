# CHANGELOG — TricorderKit

> Format : [version] — date — description

---

## [0.9.1] — 23/05/2026 — Public-ready : docs, install, anonymisation

### Ajouté
- **ROADMAP.md** — fichier public à la racine, phases 1–12 (1–8 Complete, 9–12 Planned)
- **scripts/install-menu.py** — wizard d'installation guidée (4 étapes : prérequis, .env, Docker, tk doctor)
- **Makefile** — 11 targets : `install`, `doctor`, `health`, `test`, `test-all`, `lint`, `docker-up/down`, `validate`, `security`, `clean`
- **docs/anonymization.md** — guide complet anonymisation avant push public + checklist + règle R17

### Modifié
- **README.md** — version 0.9, badge phase, section "v0.9 What's New", roadmap 12 phases
- **STATUS.md** — ajout table modules (16 modules : stable / evolving / experimental)
- **INSTALL.md** — `scripts/install-menu.py` désormais opérationnel (retrait "à venir")
- **docs/linked_projects.md** — v0.9, exemples anonymisés (japan-alliance → my-domain-project)
- **.gitignore** — `vault/*.json` et `reports/` gitignorés, version v0.9

### Sécurité / Anonymisation
- Suppression de tous les chemins `C:\Users\<username>` hardcodés dans les fichiers versionnés
- Suppression des références au nom du linked_project dans le périmètre public (`cli/tk.py`, `connector_hub.py`, `pipeline_rtk_docmancer.py`, `obsidian_goat.py`, `dispatch_temporal.py`, `docmancer/SKILL.md`, `trusted_sources.yml`)
- `mcp/MCP_AUTH_DIAGNOSTIC.md` — username anonymisé (`<username>`)
- `templates/linked_project_template/` — exemples de config anonymisés

---

## [0.9.0] — 18/05/2026 — Orchestration M1+M2 + linked_project Phase 1

### Ajouté
- **tk-orchestrator v0.3.0** — budget_guard phase 2 (DEC-006)
  - Tiers T1/T2/T3 : `haiku-4-5` (query) / `sonnet-4-6` (action/audit) / `opus-4-6` (workflow/research)
  - `tier_for_intent()`, `tier_from_complexity()` (escalade has_code/multifile/destructive)
  - `guard_action()` → proceed|pause|abort selon budget session
  - CLI `budget-guard` + CLI `session-budget` — 25 tests pytest ✅
- **Pipeline observabilité B2** — `tools/observability/hook_log_to_obsidian.py`
  - Parse `.cache/hooks/*.log` JSON-lines → note Obsidian `ERRORS.md`
  - Catégories : HIGH/CRITICAL, qualité <60%, erreurs d'exécution
- **Pipeline rtk→docmancer M3** — `tools/pipelines/pipeline_rtk_docmancer.py`
  - 5 étapes : collect→dedup→score→build_note→write_obsidian
  - Dry-run validé : Chainsaw Man → `Mangas/Chainsaw Man/Chainsaw-Man.md`
- **Supabase Japan-Alliance** — 7 tables, 5 ENUMs, RLS complet — 29 tests ✅ (DEC-012)
- **Temporal connector dispatch** — bypass registre + idempotence (DEC-013)
- **Skills pont Cowork** — token-savior + claude-code-router — 19 tests ✅ (DEC-014)
- **Plugins v0.8** — memory-boot (21 tests) + token-optimizer (31 tests)
- **Skills** — rtk + docmancer + `/tk:boot` command

### Décisions
- DEC-012 : Supabase pour Japan-Alliance
- DEC-013 : Bypass registre connector_hub en mode Temporal
- DEC-014 : Skills token-savior + claude-code-router comme ponts Cowork

### Tests
- **247 PASS** (+25 budget_guard | 10 échecs pré-existants non régressés)

---

## [0.8.0] — 17/05/2026 — Linked project architecture + Quality loop

### Ajouté
- **Architecture linked_project** — séparation moteur générique / domaine privé (DEC-010)
  - `configs/local/linked_projects.yaml` (non versionné) + `linked_projects.example.yaml` (versionné)
  - `docs/linked_projects.md` — convention officielle
  - `templates/linked_project_template/` — template reproductible (9 sous-dossiers + configs)
  - Japan-Alliance déclaré comme premier linked_project actif
- **CLI `tk` v0.2.0** — entrypoint unifié : `tk status/health/doctor/skill list/workflow list/vault scan/research run --dry-run/project *` + `--format json|markdown` sur toutes les commandes
- **Hook layer v0.2** — Pre-Intent, Pre-Execution, Post-Execution hooks câblés dans MainBrain v1.5 ; 25 tests pytest ; activities Temporal + worker RUNNING
- **Plugins quality loop** — eval-lab (eval_runner, baseline_store, regression_checker), security-audit-cli, obsidian-agent-layer (vault_router, note_builder)
- **Audit tools** — `tools/audit/linked_project_audit.py` (structure, git, config, secrets, consistency) + `tools/audit/local_vs_github_audit.py` (diff local vs GitHub)
- **Config layers** — `configs/shared/defaults.yaml` (versionné) + `configs/local/settings.yaml` + `configs/vps/settings.yaml` (gitignorés)
- **Reports** — `reports/local_first_audit_2026-05-17.md` — premier audit système complet
- **Tests live deep-research** — MangaDex ✅ + AniList ✅ (Jikan intermittent côté serveur tiers)

### Modifié
- MainBrain v1.4 → v1.5 (hooks Pre-Intent, Pre-Execution, Post-Execution câblés)
- `docker-compose.yml` — Langfuse port 3000 → 3001 (conflit Docker Desktop résolu)
- GitHub MCP — migration `@modelcontextprotocol/server-github` → `ghcr.io/github/github-mcp-server` (Docker officiel, KI-003)
- `.gitignore` — ajout configs locaux non versionnés

### Décisions
- DEC-008 : LangGraph pour boucles agentiques courtes
- DEC-009 : architecture hybride graph+vector (Neo4j + Qdrant)
- DEC-010 : pattern linked_project — TricorderKit exécute, le projet lié spécialise
- DEC-011 : VPS extension optionnelle future (non déployé)

### Résolus
- KI-004 : Temporal worker — tsconfig CommonJS + DB postgres12 + barrel export + docker cleanup
- ERR-T-002 : `${CLAUDE_PLUGIN_ROOT}` → chemin absolu + `datetime.utcnow()` → timezone-aware
- KI-003 : GitHub MCP déprécié → migration Docker officielle

---

## [0.7.0] — 10/05/2026 — Complet

### Ajouté
- README_FIRST.md — fichier de boot obligatoire
- AGENTS.md — instructions pour tous les agents Claude
- CLAUDE.md — configuration Claude Code
- .planning/ — dossier de pilotage (STATE, TASKS, DECISIONS, RISKS, ROADMAP)
- MainBrain v1.4 — upgrade avec Risk Guard + CLI Selector + Token Hygiene Guard
- Plugin cli-forge — génération CLIs déterministes pour agents
- Plugin workflow-engine — orchestration Temporal (squelette)
- Plugin deep-research-core — recherche autonome locale (squelette)
- Skill /tk:boot — boot de session
- Skill /tk:cli-forge — génération CLI
- Skill /tk:deep-research — recherche autonome
- Commande /tk:dry-run — simulation sans effet de bord
- Commande /tk:health — dashboard santé système
- Commande /tk:changelog — génération auto entrée changelog
- Contract testing : core/contracts/skill_output.schema.json
- Rate limiting agentique : token_budget par workflow
- docker-compose.yml — Neo4j + Qdrant + Temporal + Langfuse
- CLI github-goat — GitHub API, lecture seule, SQLite cache
- CLI source-watch-goat — MangaDex + AniList + Jikan, SQLite cache
- Script validate_repo.py — validation arborescence
- Script health_check.py — dashboard santé HTML/JSON
- Tests cli_contracts/ — contract tests dry-run

### Modifié
- Repositionnement stratégique : CLI-first Agentic OS (vs memory-first v0.6)
- MainBrain v1.3 → v1.4 (ajout Risk Guard, CLI Selector, Token Hygiene Guard)
- Arborescence repo complète reconstruite

### Décisions
- DEC-001 : Temporal comme moteur de workflows
- DEC-002 : cli-forge en priorité Phase 2
- DEC-003 : Neo4j pour le graph
- DEC-004 : Qdrant pour le vector
- DEC-005 : Output schema JSON obligatoire
- DEC-006 : Rate limiting token par workflow
- DEC-007 : Règle atomique 1 idée = 1 node

---

## [0.6.0] — 05/05/2026

### Acquis
- Vision Agentic Knowledge OS
- Stack Claude Code + Obsidian + MCP + Neo4j + Qdrant + Docker
- 7 axes d'amélioration documentés
- MainBrain v1.3 avec pipeline cognitif
- Claude Vault v0.2 arborescence décimale
- Nodes typés (manga, anime, mangaka, publisher, trend...)
- Edges typés (supports, contradicts, adapted_into, created_by...)
- Règle atomique : 1 idée = 1 node (100–500 tokens)

---

## [0.1.0 → 0.5.x] — Historique antérieur

- Mise en place memory-boot, token-hygiene, repo-pack
- RAG initial + hygiene tokens
- Sécurité des skills + registre
- Observabilité initiale + eval-lab prototype

---

*Généré automatiquement — ne pas modifier manuellement*  
*Commande : /tk:changelog*
