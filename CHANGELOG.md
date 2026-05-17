# CHANGELOG — TricorderKit

> Format : [version] — date — description

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
