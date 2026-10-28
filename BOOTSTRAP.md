# TricorderKit — Bootstrap « from zero »

> Installation complète depuis une machine vierge jusqu'à l'infrastructure opérationnelle :
> services, plugins, et pont temps-réel Claude ⇄ Antigravity.
> Pour le détail des options d'install et le dépannage, voir [`INSTALL.md`](INSTALL.md) et [`docs/troubleshooting.md`](docs/troubleshooting.md).

---

## 0. Architecture en trois couches

| Couche | Rôle | Distribué via |
|---|---|---|
| **Infra** | Neo4j · Qdrant · Temporal · Langfuse | `docker-compose.yml` |
| **Plugins** | Briques réutilisables (recherche, graph, mémoire, vault, tokens, orchestration) | **Plugin marketplace** (`.claude-plugin/marketplace.json`) |
| **Pont temps-réel** | Canal append-only Claude ⇄ Antigravity + offload des tâches longues | `_sync_antigravity/` (Python déterministe, zéro token LLM) |

> Devise du projet : **le framework exécute · les projets liés spécialisent · le vault stocke.**

---

## 1. Prérequis

| Outil | Version | Vérifier |
|---|---|---|
| Python | ≥ 3.11 | `python --version` |
| Node.js | ≥ 20 | `node --version` |
| Docker Desktop | récent | `docker --version` |
| Git | any | `git --version` |
| Claude Code CLI | latest | `claude --version` |

---

## 2. Cloner le dépôt

```bash
git clone https://github.com/GeekFamilyCorp/TricorderKit.git
cd TricorderKit
```

Au clonage, la configuration **project-scope** est déjà active quand vous ouvrez le dossier dans Claude Code :
`.claude/commands/`, `.claude/agents/`, `.claude/hooks/` et les skills opérationnels de `skills/` sont disponibles localement sans installation supplémentaire.

---

## 3. Variables d'environnement

```bash
cp .env.example .env
```

Renseigner au minimum dans `.env` :

| Variable | Usage |
|---|---|
| `ANTHROPIC_API_KEY` | Modèles Claude |
| `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` | Knowledge graph (plugin graphify) |
| `QDRANT_URL` / `QDRANT_API_KEY` | Vecteurs (graphify, deep-research) |
| `TEMPORAL_ADDRESS` | Workflows (workflow-engine) |
| `LANGFUSE_NEXTAUTH_SECRET` / `LANGFUSE_SALT` | Observabilité |
| `OBSIDIAN_VAULT_PATH` | Couche vault (obsidian-agent-layer, memory-boot) |
| `GITHUB_TOKEN` | CLIs cli-forge (lecture API) |

> Ne jamais committer `.env`. Le hook `validate_no_secret_commit.py` bloque les fuites ; `tk doctor` scanne aussi le repo.

---

## 4. Infrastructure Docker

```bash
docker compose up -d      # Neo4j · Qdrant · Temporal (+UI) · Langfuse
```

Attendre ~30 s au premier démarrage, puis vérifier les ports :

| Service | Port | URL |
|---|---|---|
| Neo4j Browser | 7474 | http://localhost:7474 |
| Neo4j Bolt | 7687 | bolt://localhost:7687 |
| Qdrant | 6333 | http://localhost:6333 |
| Langfuse | 3001 | http://localhost:3001 ⚠️ pas 3000 |
| Temporal UI | 8080 | http://localhost:8080 |

---

## 5. Dépendances runtime

```bash
# Python (scripts utilitaires, plugins Python)
pip install requests httpx rich pyyaml qdrant-client temporalio feedparser neo4j

# Node (MCP graph-server + workflow-engine Temporal)
( cd mcp/servers/graph-server && npm install && npm run build )
( cd plugins/workflow-engine && npm install )
```

Le serveur MCP `graph-server` est déclaré dans `.mcp.json` (racine) et démarre automatiquement avec Claude Code une fois `dist/index.js` construit.

---

## 6. Installer les plugins via le marketplace

C'est le maillon natif qui rend toute la brique « plugins » installable d'un clic, depuis n'importe quelle machine.

### Ajouter le marketplace

```text
# Depuis le dépôt GitHub (recommandé — les chemins relatifs ne résolvent qu'en mode git)
/plugin marketplace add GeekFamilyCorp/TricorderKit

# OU depuis un clone local
/plugin marketplace add ./.claude-plugin/marketplace.json
```

### Installer les plugins

```text
/plugin install token-optimizer@tricorderkit
/plugin install deep-research-core@tricorderkit
/plugin install graphify@tricorderkit
/plugin install memory-boot@tricorderkit
/plugin install obsidian-agent-layer@tricorderkit
/plugin install connector-hub@tricorderkit
/plugin install eval-lab@tricorderkit
/plugin install security-audit-cli@tricorderkit
/plugin install cli-forge@tricorderkit
/plugin install workflow-engine@tricorderkit
```

Ou tout gérer via l'UI : `/plugin`.

### Catalogue

| Plugin | Rôle | Dépendances infra |
|---|---|---|
| `token-optimizer` | Routing Haiku/Sonnet/Opus, classification, caveman, budget. **6 skills + 3 agents + hooks** | — |
| `deep-research-core` | Recherche autonome multi-sources, synthèse Markdown | Qdrant |
| `graphify` | Knowledge graph Neo4j + Qdrant. Fournit le **MCP graph-server** | Neo4j, Qdrant |
| `memory-boot` | Boot mémoire depuis le vault Obsidian (skills `memory-boot`, `rapport`) | Obsidian |
| `obsidian-agent-layer` | CRUD notes, templates, routing vault | Obsidian |
| `connector-hub` | Ingestion passive multi-sources | — |
| `eval-lab` | Non-régression contre `skill_output.schema.json` | — |
| `security-audit-cli` | Secret scan, CVE, anonymisation | — |
| `cli-forge` | Forge + registre de CLIs validées | `GITHUB_TOKEN` |
| `workflow-engine` | Workflows Temporal (TypeScript) | Temporal |

> Activation persistante par projet via `.claude/settings.json` → `"enabledPlugins": { "token-optimizer": true, ... }`.

---

## 7. Bus multi-agents — canal_agents

Transport **append-only**, lecture par curseur (anti-staleness), **zéro token LLM** : un scheduler ou un run Haiku léger appelle le script, aucun modèle cher ne poll.

```bash
# Vérifier la santé du bus
python3 canal_agents/scripts/sync_bus.py health

# Émettre un heartbeat de présence (tout agent du roster : claude/codex/antigravity/qwen)
python3 canal_agents/scripts/sync_bus.py heartbeat claude --state idle

# Lire les événements non consommés (avance le curseur de l'agent)
python3 canal_agents/scripts/sync_bus.py read --agent claude
```

Agents pris en charge : `claude`, `codex`, `antigravity`, `qwen`, … (roster `AGENTS` dans `sync_bus.py`).
Protocole complet (schémas d'événements, commandes, contrat d'offload, verrou) :
[`canal_agents/PROTOCOL.md`](canal_agents/PROTOCOL.md).

| Élément | Fichier |
|---|---|
| Moteur du bus (publié) | `canal_agents/scripts/sync_bus.py` |
| Protocole (publié) | `canal_agents/PROTOCOL.md` |
| Bus d'événements (local) | `canal_agents/bus/events.jsonl` (append-only) |
| Curseurs par agent (local) | `canal_agents/bus/cursor.<agent>` |
| État machine-lisible (local) | `canal_agents/STATUS.json` |
| Inbox par agent (local) | `canal_agents/commands/<agent>_inbox/` |

---

## 8. Vérification finale

```bash
tk doctor                 # ou: python cli/tk.py doctor
```

Attendu : `[OK]` Python, Docker, Neo4j :7474, Qdrant :6333, Langfuse :3001, Temporal :7233, `.env`, dossiers `plugins/`/`skills/`, aucun secret.

```text
# Plugins chargés
/plugin

# Bus multi-agents vivant
python3 canal_agents/scripts/sync_bus.py health
```

---

## 9. Checklist condensée

```text
[ ] git clone + cd TricorderKit
[ ] cp .env.example .env  →  renseigner les clés
[ ] docker compose up -d  →  ports 7474/6333/3001/8080 OK
[ ] pip install + npm install (graph-server build, workflow-engine)
[ ] /plugin marketplace add GeekFamilyCorp/TricorderKit
[ ] /plugin install <plugin>@tricorderkit  (×10 ou via /plugin)
[ ] canal_agents/scripts/sync_bus.py health  →  bus vivant
[ ] tk doctor  →  tout vert
```

---

*Généré le 2026-06-04 — aligné CLAUDE.md v0.9 · AGENTS.md v0.8 · tk-realtime/1 · DEC-016 routage dépôts.*
