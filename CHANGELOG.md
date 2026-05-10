# CHANGELOG — TricorderKit

> Format : [version] — date — description

---

## [0.7.0] — 10/05/2026 — En cours

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
