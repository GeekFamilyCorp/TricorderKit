# TASKS.md — TricorderKit v0.7

> Backlog vivant. Mettre à jour après chaque session.

---

## Phase 1 — Fondations ✅ Complétée

- [x] README_FIRST.md
- [x] AGENTS.md
- [x] CLAUDE.md
- [x] .planning/STATE.md
- [x] .planning/DECISIONS.md
- [x] .planning/RISKS.md
- [x] .planning/TASKS.md
- [x] scripts/validate_repo.py
- [x] scripts/health_check.py
- [x] tests/cli_contracts/test_github_goat.py
- [x] tests/cli_contracts/test_source_watch_goat.py
- [x] skills/tk-boot/SKILL.md
- [x] plugins/deep-research-core/ (README, SKILL, manifest, sources, pipeline)
- [x] vault/README.md

---

## Phase 2 — CLI-first 🔶 En cours

### Outils installés (10/05/2026)

- [x] tools/mangatracker-cli/ (manga, ln, anime, seiyu, studio, game, goods, events, sync, audit)
- [x] tools/jp-scraper/ (rss, http, trafilatura, selectolax, delta, summary)
- [x] scripts/vault_optimizer/ (analyzer, manifest, delta, router, summarizer)
- [x] .claude/agents/ (5 agents)
- [x] .claude/commands/ (8 slash commands)
- [x] .claude/hooks/ (4 hooks)
- [x] .claude/skills/vault-token-optimizer/
- [x] .claude/skills/open-source-jp-scraper/
- [x] .mcp.json + mcp/README_MCP_POLICY.md
- [x] .tricorderkit/vault_optimizer.config.json
- [x] data/mangatracker/ (répertoires de cache + exports)
- [x] docs/integration/ (README_Implantation + REPORT)

### À faire — Parseurs mangatracker-cli

- [ ] `mangatracker_cli/connectors/parsers_shonenjumpplus.py`
- [ ] `mangatracker_cli/connectors/parsers_comicdays.py`
- [ ] `mangatracker_cli/connectors/parsers_syosetu.py`
- [ ] `mangatracker_cli/connectors/parsers_kakuyomu.py`
- [ ] `mangatracker_cli/connectors/parsers_comic_natalie.py`
- [ ] Tests intégration mangatracker
- [ ] Connecteur kintone réel (quand .env disponible)

### À faire — jp-scraper

- [ ] Tester jp-scraper live RSS (comic-natalie, animate-times)
- [ ] Adaptateurs spécifiques par source
- [ ] SQLite optionnel pour snapshots

### À faire — cli-forge

- [ ] Tester github-goat live
- [ ] Tester source-watch-goat live
- [ ] Valider manifest cli-forge : `python plugins/cli-forge/scripts/validate_cli_manifest.py --all`

---

## Phase 3 — Workflows 🔲 Pending

- [ ] docker-compose.yml (Neo4j + Qdrant + Temporal + Langfuse)
- [ ] plugins/workflow-engine/ completion

---

## Phase 4 — Deep Research 🔲 Pending

- [ ] plugins/deep-research-core/scripts/collect_sources.py
- [ ] plugins/deep-research-core/scripts/score_reliability.py
- [ ] Connecteurs AniList, MangaDex, Jikan

---

## Phase 5 — Qualité 🔲 Pending

- [ ] plugins/eval-lab/
- [ ] plugins/security-audit-cli/
- [ ] Dashboard HTML santé système

---

## Backlog

- [ ] MCP serveur Neo4j
- [ ] MCP serveur Qdrant
- [ ] Skill /tk:vault-audit
- [ ] Skill /tk:deep-research
- [ ] Notion/Airtable bridge
- [ ] Vérifier MCPs Airtable + Filesystem + Hostinger
- [ ] Configurer MCPs MangaTracker sur VPS

---

*Dernière mise à jour : 10/05/2026*
