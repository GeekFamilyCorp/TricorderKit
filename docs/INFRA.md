# INFRA.md — Architecture infrastructure Docker

> Référence d'architecture stable (sans métriques volatiles ni secrets).
> Pour l'état temps réel : `goat infra audit` ou `docker ps`. Pour les opérations : voir `RUNBOOK_INFRA.md`.
> Périmètre : stack local-first FileAI Master + TricorderKit + services support.

---

## Vue d'ensemble

L'infrastructure regroupe deux ensembles applicatifs et leurs services support, orchestrés par `docker compose` depuis le dossier projet.

| Ensemble | Rôle |
|---|---|
| **FileAI Master** | Gestion et analyse de documents |
| **TricorderKit** | Cœur agentique : workflows, graphe, embeddings, observabilité |
| **Services support** | Bases de données, UI, agents MCP, interface LLM |

Réseau bridge dédié : `tricorder-network` (services TricorderKit interconnectés).

---

## Services critiques

### FileAI Master
- **Conteneur** : `filemaster-ai`
- **Image** : `docs_manager-filemaster-ai`
- **Port** : `9000` → `8000` (exposé `0.0.0.0`)
- **Type** : API Python
- **Volumes** : `docs_manager_filemaster-data`, `docs_manager_filemaster-analysis`, `docs_manager_filemaster-logs`
- **Fonction** : gestion documents, analyse fichiers, API.

### Agent Gateway
- **Conteneur** : `agent-gateway`
- **Image** : `agent_gateway-agent-gateway`
- **Port** : `8080` → `8080` (exposé `0.0.0.0`)
- **Type** : API Python
- **Volumes** : `agent_gateway_gateway-cache`, `-logs`, `-state`, `-webhooks`
- **Fonction** : orchestration des agents, webhooks persistants, cache requêtes, logging centralisé.

### Langfuse (observabilité LLM)
- **Conteneur** : `tricorder-langfuse`
- **Image** : `langfuse/langfuse:2.92.0`
- **Port** : `3001` → `3000` (local `127.0.0.1`)
- **Base** : PostgreSQL 15 (`tricorder-langfuse-db`, interne)
- **Fonction** : monitoring des tokens, tracing des appels LLM, analytics, gestion des prompts.

### Neo4j (graphe de connaissances)
- **Conteneur** : `tricorder-neo4j`
- **Image** : `neo4j:5.18`
- **Ports** : `7474` (HTTP/Browser), `7687` (Bolt) — local `127.0.0.1`
- **Plugins** : APOC, Graph Data Science
- **Mémoire** : 1 GB max
- **Volumes** : `tricorder_neo4j_data`, `tricorder_neo4j_logs`
- **Collections** : concepts, tasks, skills, sources, entities, vault, agents, sessions, decisions
- **Authentification** : variables `NEO4J_USER` / `NEO4J_PASSWORD` (voir `.env` — jamais en clair dans la doc).

### Temporal (workflows)
- **Conteneur** : `tricorder-temporal`
- **Image** : `temporalio/auto-setup:1.23`
- **Port** : `7233` (gRPC) — local `127.0.0.1`
- **Base** : PostgreSQL 15 (`tricorder-temporal-db`, interne)
- **UI** : `tricorder-temporal-ui` (`temporalio/ui:latest`) sur `8081` → `8080`
- **Health check** : `tctl --address localhost:7233 cluster health` (peut prendre 2-3 min après redémarrage).
- **Fonction** : workflows durables, task queues, retry logic.

### Qdrant (base vectorielle)
- **Conteneur** : `tricorder-qdrant`
- **Image** : `qdrant/qdrant:v1.8.4`
- **Ports** : `6333` (REST), `6334` (gRPC) — local `127.0.0.1`
- **Volume** : `tricorder_qdrant_data`
- **Collections** : concepts, tasks, skills, sources, entities, vault, agents, sessions, decisions
- **Note health check** : l'endpoint `/healthz` n'existe pas sur cette image → health check retiré du `docker-compose`. Sonde réelle de vivacité : `GET /collections` (200 OK).

---

## Services support

| Service | Conteneur | Image | Port | Accès |
|---|---|---|---|---|
| Temporal UI | `tricorder-temporal-ui` | `temporalio/ui:latest` | 8081 | local |
| PostgreSQL Langfuse | `tricorder-langfuse-db` | `postgres:15` | 5432 | interne |
| PostgreSQL Temporal | `tricorder-temporal-db` | `postgres:15` | 5432 | interne |
| Hermes Agent (MCP) | `hermes-agent` | `hermes-agent:latest` | 5000, 8000-8001, 9119 | — |
| Open WebUI | `open-webui` | — | 3000 | local |
| GitHub MCP (x2) | — | — | 8082 | — |

---

## Cartographie des ports

| Service | Mapping | Exposition |
|---|---|---|
| FileAI Master | `0.0.0.0:9000 → 8000` | publique |
| Agent Gateway | `0.0.0.0:8080 → 8080` | publique |
| Temporal UI | `127.0.0.1:8081 → 8080` | locale |
| Langfuse | `127.0.0.1:3001 → 3000` | locale |
| Neo4j Browser | `127.0.0.1:7474 → 7474` | locale |
| Neo4j Bolt | `127.0.0.1:7687 → 7687` | locale |
| Qdrant REST | `127.0.0.1:6333 → 6333` | locale |
| Qdrant gRPC | `127.0.0.1:6334 → 6334` | locale |
| Temporal gRPC | `127.0.0.1:7233 → 7233` | locale |

> Seuls FileAI Master et Agent Gateway sont exposés sur `0.0.0.0`. Vérifier que c'est intentionnel avant tout déploiement non isolé.

---

## Volumes persistants

| Volume | Ensemble | Type |
|---|---|---|
| `tricorder_qdrant_data` | TricorderKit | local |
| `tricorder_temporal_db` | TricorderKit | PostgreSQL |
| `tricorder_langfuse_db` | TricorderKit | PostgreSQL |
| `tricorder_neo4j_data` | TricorderKit | local |
| `tricorder_neo4j_logs` | TricorderKit | local |
| `docs_manager_filemaster-data` | FileAI | local |
| `docs_manager_filemaster-analysis` | FileAI | local |
| `docs_manager_filemaster-logs` | FileAI | local |
| `agent_gateway_gateway-cache` | Agent Gateway | local |
| `agent_gateway_gateway-logs` | Agent Gateway | local |
| `agent_gateway_gateway-state` | Agent Gateway | local |
| `agent_gateway_gateway-webhooks` | Agent Gateway | local |

> Les tailles ne sont pas documentées ici : variables dans le temps, à lire via `docker system df -v`.

---

## Dépendances et secrets

Secrets requis (à externaliser dans `.env`, jamais en clair dans la doc ni le repo public) :

```text
NEO4J_USER / NEO4J_PASSWORD
POSTGRES_USER / POSTGRES_PASSWORD   (Langfuse + Temporal)
```

> Frontière publique TricorderKit (DEC-026 / R37) : passer `make gate` avant tout push. Aucun secret ni chemin perso ne doit franchir le gate.

---

## Dette connue / à traiter

- **Sécurité** : externaliser tous les secrets hardcodés (Neo4j, PostgreSQL) — court terme.
- **Backups** : stratégie de sauvegarde des volumes DB à formaliser — court terme.
- **Observabilité** : Prometheus pour métriques additionnelles — moyen terme.
- **Production** : TLS/SSL, reverse proxy (nginx), alerting sur seuils, scaling multi-instance Neo4j/Qdrant — long terme.

---

*Référence d'architecture — sans état temps réel. Pour l'instantané daté, régénérer via la CLI d'audit.*
