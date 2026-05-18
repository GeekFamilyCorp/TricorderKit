# SKILL : claude-code-router
**Version** : 0.1.0
**Trigger** : "lance tk-orchestrator", "exécute une commande TricorderKit", "router vers tk", "tk:dispatch", "délègue à Claude Code", "claude-code-router"

---

## Rôle

Pont entre **Cowork** (interface utilisateur) et **tk-orchestrator** (moteur d'exécution CLI/Temporal). Quand une tâche dépasse les capacités de Cowork (subprocess, accès fichiers système, Docker, npm), ce skill prépare et route vers tk-orchestrator via le protocole MCP workspace.

Ce skill évite à l'utilisateur de basculer manuellement vers Claude Code pour chaque opération système.

---

## Séquence de routage

### 1. Analyser la demande

Classifier la demande selon les critères de routage :

| Type de demande | Route vers |
|----------------|-----------|
| Lecture/écriture fichier workspace | Cowork direct (Read/Write/Edit tools) |
| Subprocess Python/Node local | `mcp__workspace__bash` |
| Workflow Temporal (source-watch, etc.) | `connector_hub.py dispatch --temporal` |
| CLI goat (obsidian-goat, source-watch-goat…) | `mcp__workspace__bash` + chemin goat |
| Tâche > 10 steps ou multi-fichiers | tk-orchestrator via bash |
| Accès Obsidian vault | MCP `obsidian-claude-vault` ou `obsidian-japan-alliance` |

### 2. Construire la commande

Construire la commande selon le type :

**CLI goat direct** :
```bash
python3 {REPO_ROOT}/tools/obsidian-goat/obsidian_goat.py {command} --vault {vault} [--dry-run]
```

**Connector hub** :
```bash
python3 {REPO_ROOT}/plugins/connector-hub/connector_hub.py dispatch --source {source} [--temporal] [--dry-run]
```

**tk-orchestrator** :
```bash
python3 {REPO_ROOT}/plugins/cli-forge/generated/tk-orchestrator/tk_orchestrator.py route --task "{task}" [--dry-run]
```

### 3. Dry-run obligatoire (R3)

**Toujours** simuler avec `--dry-run` avant exécution réelle, sauf si :
- L'utilisateur a explicitement dit "exécute sans simulation"
- La commande est en lecture seule (list, status, check)

Présenter le résultat dry-run et demander confirmation pour les actions destructives.

### 4. Exécuter

Via `mcp__workspace__bash` :
```python
result = subprocess.run(
    cmd, capture_output=True, text=True, timeout=30,
    cwd=REPO_ROOT, env={**os.environ, "PYTHONUTF8": "1"}
)
```

### 5. Retourner le résultat

Format de sortie R15 :
```json
{
  "status": "success|error|dry_run",
  "route": "goat|connector_hub|temporal|orchestrator",
  "command": ["python3", "..."],
  "output": {...},
  "next_action": "..."
}
```

---

## Table de routage détaillée

### Requêtes Obsidian
- "lis la note X" → `obsidian-goat read-note`
- "écris/crée une note" → `obsidian-goat write-note` (+ dry-run)
- "mets à jour le hot cache" → `obsidian-goat update-hot-cache`
- "ajoute au log" → `obsidian-goat append-log`

### Requêtes ingestion manga/animé
- "lance la veille MangaDex" → `connector_hub dispatch --source mangadex [--temporal]`
- "surveille toutes les sources" → `connector_hub dispatch --all --temporal`
- "statut des sources" → `connector_hub status`

### Requêtes deep-research
- "recherche approfondie sur X" → skill `rtk` + `deep-research-core`
- "génère une fiche Obsidian" → skill `docmancer`

### Requêtes Temporal
- "démarre le workflow source-watch" → `dispatch_temporal.py dispatch --workflow source-watch`
- "vérifie le statut du workflow" → `dispatch_temporal.py status {workflow_id}`

### Requêtes orchestration complexe
- Tâches multi-étapes, enchaînement de CLIs → déléguer à `tk-orchestrator`

---

## Gardes-fous

- **Jamais** d'appel réseau direct depuis ce skill — passer par les CLIs goat ou les MCP
- **Jamais** de modification Obsidian sans `check-note` préalable (règle R7 anti-doublon)
- **Jamais** de déclenchement Temporal sans dry-run validé en cas de `--interval` > 0
- Budget tokens : si > 70%, activer token-savior lite avant de construire la commande

---

## Dépendances

- `mcp__workspace__bash` — exécution subprocess
- `tools/obsidian-goat/obsidian_goat.py` — opérations Obsidian
- `plugins/connector-hub/connector_hub.py` — ingestion sources
- `plugins/connector-hub/scripts/dispatch_temporal.py` — Temporal
- Skills : `rtk`, `docmancer`, `token-savior`
- `AGENTS.md` — règles R1 (CLI avant LLM), R3 (dry-run), R7 (anti-doublon), R15 (caveman)

---

## Exemple complet

**Requête** : "lance la veille MangaDex en mode Temporal"

```
[claude-code-router] Route: connector_hub → temporal
Dry-run d'abord :

$ python3 plugins/connector-hub/connector_hub.py dispatch --source mangadex --temporal --dry-run --format json

{
  "mode": "temporal",
  "sources": ["mangadex"],
  "temporal_result": {
    "status": "dry_run",
    "workflow_id": "tricorderkit-source-watch-20260518",
    "message": "Dry-run: aucun workflow déclenché"
  }
}

Confirmer l'exécution réelle ? (oui/non)
```
