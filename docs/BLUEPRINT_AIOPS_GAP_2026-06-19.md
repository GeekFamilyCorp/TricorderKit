# Blueprint AI-Ops — Gap analysis (2026-06-19)

> Cartographie du blueprint d'infrastructure AI-Ops (16 blocs 00→16) sur l'état réel de TricorderKit.
> Légende : ✅ couvert · 🔶 partiel · 🔲 manquant (roadmap). Composants domaine/exécution → **projet lié privé** ; données → **vault lié** (jamais en repo public).

| # | Bloc blueprint | Statut | Où / quoi dans TricorderKit |
|---|---|---|---|
| 00 | core-runtime | ✅ | `docker-compose.yml`, `Makefile`, `BOOTSTRAP.md`, `INSTALL.md`, `.env.example`, `scripts/health_check.py` |
| 01 | config — system-prompts | ✅ | gouvernance → vault mémoire (`09_System_Prompts`) + `AGENTS.md`/`CLAUDE.md` |
| 01 | config — project-rules | ✅ | `AGENTS.md`, `CLAUDE.md`, `docs/06_workflow_standard.md` |
| 01 | config — model-routing | 🔶 | plugin `token-optimizer` (router/budgets) — exposer `models.yaml`/`token-budgets.yaml` en `.example` |
| 01 | config — channels / environments | 🔶 | `.env.example` ✅ ; channels → projet lié privé |
| 02 | skills | ✅ | `skills/` (11) + `plugins/` (13) ; skills domaine → projet lié privé |
| 03 | memory | ✅ | plugin `memory-boot` + vault mémoire (long/court terme, compaction, embeddings via RAG) |
| 04 | data (raw/processed/curated/exports) | ✅(ext) | hors repo : VPS + vault lié (règle "repos = squelette, pas données") |
| 05 | models (ollama/vllm/quantized/hf-sync) | 🔲 | **roadmap** — Ollama tourne sur VPS ; pas de couche `models/` générique |
| 06 | rag (ingestion/retrieval/vector-db/eval) | ✅ | plugin `graphify` + `mcp/servers/vault-search` + plugin `eval-lab` |
| 07 | workflows | 🔶 | plugin `workflow-engine` (Temporal) ✅ ; orchestrateurs crewai/langgraph/autogen = **roadmap** |
| 08 | integrations | 🔶 | plugin `connector-hub` ✅ ; discord/email/storage → projet lié privé |
| 09 | cloudbot-dashboard | 🔲 | **roadmap** (UI dédiée ; un dashboard tiers existe déjà côté VPS) |
| 10 | observability | 🔶 | Langfuse (`docker-compose`) + `core/hooks/langfuse_observer.py` ✅ ; prometheus/grafana/phoenix = **roadmap** |
| 11 | security | ✅ | plugin `security-audit-cli` + `mcp/registry_allowlist.yaml` + R37 gate ; nginx/tls/ufw → VPS (live) |
| 12 | audio-multimodal | 🔲 | **roadmap** (stt/tts/vision) |
| 13 | backups | ✅ | scripts → projet lié privé `infra/` + kit de reprise ; borg sur VPS |
| 14 | deployment | 🔶 | `docker-compose.yml`, `.github/workflows`, `scripts/` ✅ ; Dockerfiles par service = partiel |
| 15 | docs | 🔶 | `docs/00→06` + anonymization/INFRA/linked_projects ✅ ; +`architecture.md` (ajouté) ; runbooks à compléter |
| 16 | lab | ✅ | `scratch/`, `examples/` |

## Verdict
Socle couvert à ~75 %. **Aucun composant net-new codé ici** (décision : structure + gap-analysis). Les 🔲/🔶 net-new sont des items **roadmap** à séquencer feature par feature sur GO (cf. `ROADMAP.md`).

## Prochaines features candidates (roadmap, non engagées)
1. `models/` générique (registry + profils, vLLM optionnel). 2. Observabilité prometheus/grafana/phoenix (au-delà de Langfuse). 3. Dashboard UI dédié. 4. Audio/multimodal. 5. Orchestrateurs alternatifs (langgraph/crewai) en complément de Temporal.
