# Roadmap — composants net-new du blueprint AI-Ops

> Suite de la gap-analysis (`BLUEPRINT_AIOPS_GAP_2026-06-19.md`). Les 5 blocs ci-dessous n'existent pas encore. Chacun est un chantier à part, sur GO, feature par feature. ⚠️ Plusieurs **recoupent l'existant** — à arbitrer avant tout code (YAGNI / R37).

| # | Composant | Effort | Priorité | Recoupe l'existant ? | Prérequis / décision |
|---|---|---|---|---|---|
| A | `models/` générique (registry + profils, vLLM optionnel) | M | Moyenne | Ollama (4 modèles) + LiteLLM gateway déjà sur VPS | Décider : couche d'abstraction utile, ou LiteLLM suffit ? vLLM = **GPU requis** (absent VPS+poste) → écarté tant que pas de GPU |
| B | Observabilité prometheus/grafana/phoenix | M-L | Basse | **Langfuse** (traces+coûts) + `cpu_guard` + sysstat déjà en place | Décision : Langfuse couvre le besoin LLM ; Prometheus/Grafana = métriques système (le watchdog suffit aujourd'hui). À faire seulement si besoin de dashboards système riches |
| C | Dashboard UI dédié (backend/frontend) | L | Basse-Moyenne | **Paperclip** + **open-webui** déjà sur VPS | Décision forte : construire un UI maison vs exploiter Paperclip/open-webui. Recommandé : réutiliser l'existant |
| D | Audio/multimodal (stt faster-whisper, tts piper, vision llava/moondream) | L | Basse | rien | **Bloqueur matériel : GPU** (ni VPS ni poste). Exploratoire. À reporter |
| E | Orchestrateurs alternatifs (langgraph/crewai/autogen) | M | Basse | **Temporal** (workflow-engine) + `canal_agents` couvrent déjà l'orchestration | Risque doublon. N'introduire que pour un besoin précis non couvert par Temporal |

## Recommandation (regard critique)
La majorité de ces net-new **dupliquent des briques déjà opérationnelles** (LiteLLM, Langfuse, Paperclip/open-webui, Temporal). Conformément à R37/YAGNI, **ne rien construire par anticipation**. Ordre suggéré si un besoin réel émerge :
1. **A (models/ registry)** — la plus utile (abstraction propre Ollama/LiteLLM), sans GPU.
2. **B (Grafana)** — seulement si supervision système riche nécessaire.
3. **C/E** — uniquement si Paperclip/Temporal montrent une limite concrète.
4. **D (audio/vision)** — gelé tant qu'il n'y a pas de GPU.

## Process par feature (quand GO)
ADR (`engineering:architecture`) → scaffolding plugin (`plugins/<nom>`) → tests → gate R37 + sync README/STATUS (R38) → push sur GO. Consigner dans le kit (R49).


## Statut (2026-06-19)
- **A — models/ registry** : ✅ **DÉMARRÉ** — `models/` (model_registry.yaml + registry.py CLI + README), smoke `list`/`resolve` OK. Sans GPU. (commit `3e83ee1`)
- **B — Prometheus/Grafana** : ✅ **DÉMARRÉ** (scaffold) — `observability/` (compose.monitoring.yml + prometheus.yml + datasource Grafana + README), loopback + secrets via env. À lancer à la demande. (commit `3e83ee1`)
- **C dashboard · D audio · E orchestrateurs alt** : restent en roadmap (recoupent l'existant / GPU absent).
