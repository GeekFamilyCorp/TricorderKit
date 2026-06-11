# CHANGELOG — TricorderKit

> Format : [version] — date — description

---

## [Unreleased] — DEC-046 v1.0 « Self-Improving » — Lots D (MCP, N3) + E (reliability N6 + workflows N7)

### Ajouté
- **mcp/registry_allowlist.yaml** — allowlist MCP **machine-lisible, deny-by-default** : serveurs + tools + permissions + rate limits, patterns de tools bannis, politique de secrets (références `${VAR}` uniquement, DEC-039). Rend exécutable la politique écrite (`mcp/README_MCP_POLICY.md`).
- **mcp/scripts/mcp_gateway.py** — moteur de gouvernance : `list` (déclarés + configurés), `audit` (`.mcp.json` confronté à l'allowlist : serveurs non déclarés, secrets en clair, tools bannis), `allowlist-check` (décision autorisé/refusé). Sortie conforme `core/contracts/skill_output.schema.json`, journal par appel `mcp/logs/mcp_calls.jsonl` (gitignoré).
- **CLI** — `tk mcp list | audit | allowlist-check` câblés dans `cli/tk.py`.
- **tests/test_mcp_gateway.py** — 13 tests (deny-by-default, audit secrets/serveurs, contrat skill_output, codes retour CLI).

### Ajouté (Lot E — N6 + N7)
- **plugins/scraper-runtime/scripts/source_reliability_engine.py** (N6) — moteur de **fiabilité des sources** : score composite (officialité, fiabilité, fraîcheur, extractabilité, dédup) calculé depuis l'historique des runs, **dry-run strict** (lecture seule, jamais d'écriture vault ; promotion déléguée au writer du projet aval, routage DEC-016, archivage R31). Sortie `skill_output` (status=dry_run). + **8 tests**.
- **plugins/workflow-engine/workflows/** (N7) — 4 workflows Temporal d'auto-amélioration : `learning_review` (hebdo : compare → leçons → drafts, jamais de promotion), `skill_regression_test` (gate des tests + approbation humaine avant promotion), `source_freshness` (score N6 → re-scrape déporté), `tool_scout` (veille outillage déportée). Exécution collecte/veille **déportée** Antigravity/Hermes via `canal_agents` (DEC-029).
- **plugins/workflow-engine/activities/self_improving.activities.ts** — activities dédiées (dispatch canal_agents + consolidation CLI), type `SelfImprovingActivities` **isolé du worker en production** ; barrel séparé `workflows/self_improving.index.ts` ; doc d'activation `plugins/workflow-engine/SELF_IMPROVING.md`.

### Référence
- DEC-046 — cap v1.0 Self-Improving : N3 (gouvernance MCP), N6 (source reliability engine), N7 (workflows d'auto-amélioration). Plan : `.planning/PLAN_v1.0_SELF_IMPROVING_2026-06-11.md`.

## [0.9.5] — 01/06/2026 — graphify : RAG vault local-first (DEC-023) + dédup G1 ingestion veille

### Ajouté
- **plugins/graphify/scripts/hybrid_rag.py** — RAG vault **local-first** : indexeur incrémental, recherche dense, pont d'ingestion de veille, heartbeat de santé. Implémente DEC-023 (RAG hybride local-first).
- **Dédup G1 dans l'ingestion de veille** — chaque fiche est confrontée au **Master Index** → marquée `nouveau`/`existant`, avec gate `n_a_creer` qui empêche la création de doublons.

### Sécurité / Gouvernance
- **LICENSE** — licence MIT ajoutée (© 2026 GeekFamilyCorp).
- **Gate frontière publique** — `scripts/check_public_boundary.py` (scan des fichiers suivis : termes privés hors whitelist + chemins personnels absolus toujours bloquants), **appliqué** en CI (`.github/workflows/public-boundary.yml`) et en pre-push (`.githooks/pre-push`, `make install-hooks`). Nettoyage frontière (Lot 2) : retrait des dossiers legacy, capsules privées et chemins personnels ; `cowork-boot` relocalisé vers MangaTracker. (DEC-026)

### Référence
- DEC-023 (.planning/DECISIONS.md) — RAG hybride local-first. Commits `cbd9f53` (RAG), `124baba` (dédup G1).
- DEC-026 (.planning/DECISIONS.md) — gate frontière publique appliqué.

> Note : 6 tests graphify (`test_hybrid_rag.py`, `test_hybrid_rag_integration.py`) validés en local, à intégrer à la suite committée (non comptés dans le total 503).

## [0.9.4] — 29/05/2026 — obsidian-goat v0.2.1 : `next-id` (allocation d'ID, R34) + rétrospective

### Ajouté
- **tools/obsidian-goat/obsidian_goat.py** (v0.2.0 → v0.2.1) — commande `next-id <prefix> [--check <id>]` : scanne noms de fichiers + contenu (sans exclure backups/réservés) → prochain ID libre, trous, et vérification de collision d'un ID précis. Implémente R34 (allocation d'ID sûre, complète R29).
- **tests/cli_contracts/test_obsidian_goat.py** — classe `TestNextIdR34` (5 tests). Suite complète **28/28 PASS**.
- **tasks/lessons.md** — LESSON-008→012 (règles **R32-R36** : pas d'édition octet + validation parse/smoke ; git FS réel + vérif sandbox ; allocation ID ; vérif nature avant fiche ; cache CLI writable).

### Référence
- DEC-019 — rétrospective 28/29 mai + auto-améliorations. Vault : `RETRO_2026-05-28_29`, `PATTERN-EDIT-DUALFS-001`, `SUCCESSES_INDEX`.

## [0.9.3] — 29/05/2026 — obsidian-goat v0.2.0 : garde-fou R29 (anti-collision d'ID)

### Ajouté
- **tools/obsidian-goat/obsidian_goat.py** (v0.1.0 → v0.2.0) — nouvelle commande `replace-id <old_id> <new_id>` : remplacement d'identifiant **borné au token complet** (lookbehind/lookahead `\w`). Empêche le piège ED040 (un préfixe nu ne corrompt plus un token plus long) ; tokens partageant le préfixe détectés et listés `protected_prefix_tokens`. **Dry-run par défaut**, `--apply` pour écrire, `--root` pour cibler un vault hors ENV, `--exclude` répétable (exclut par défaut `99_Migration_Backups`/`03_Manifestes_Migration`). Implémente la règle R29 (DEC-017/DEC-018).
- **tests/cli_contracts/test_obsidian_goat.py** — classe `TestReplaceIdR29` (4 tests : dry-run token complet, préfixe nu protégé, apply sans corruption, refus old==new). Suite complète **23/23 PASS**.

### Référence
- DEC-018 (.planning/DECISIONS.md) — améliorations post-assainissement + rollout studios.

## [0.9.2] — 23/05/2026 — M5 : security hardening + Windows deployment

### Ajouté
- **plugins/workflow-engine/activities/sanitize_input.activity.ts** — Pre-Execution Hook anti-prompt-injection : Llama Guard 3 (Ollama) + regex fallback 12 patterns. `ApplicationFailure.nonRetryable` si payload unsafe → quarantaine Temporal. Ferme RISK-005.
- **plugins/deep-research-core/index_qdrant.py** — génération d'IDs Qdrant : `hashlib.sha1` → `uuid.uuid5(NAMESPACE, name)`. Déterministe + sans collision. Test idempotence inclus. Ferme ERR-T-001.
- **.semgrep/no-shell-true.yaml** — 3 règles custom : `no-shell-true` (CWE-78), `no-os-system` (CWE-78), `no-sha1-for-ids` (CWE-327).

### Modifié
- **plugins/security-audit-cli/security_runner.py** — architecture `_run_*` pure (découplée de Typer) · `encoding="utf-8", errors="replace"` sur tous les accès fichier · exclusions UUID par chemin relatif · suppression emoji → ASCII `PASS/FAIL` (compatibilité Windows tâche planifiée).
- **plugins/security-audit-cli/tests/test_security_runner.py** — 18/18 tests PASS (était 17/18 : `test_scan_skip_if_semgrep_missing` corrigé).

### Corrections Windows
- `subprocess.run()` : `encoding="utf-8"` forcé partout (R18) — élimine les crashs cp1252
- `Path.read_text()` : même correction dans `_run_docker` et `_run_uuid`
- `pytest --basetemp` : défini hors `AppData\Temp` dans `pyproject.toml` (R-WIN-003)
- Rich Console : `isatty()` conditionnel pour tâches planifiées (R19)

### Full Audit résultat
`scan PASS · secrets PASS · deps PASS · docker PASS · uuid PASS`

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
