# obsidian-agent-layer

> TricorderKit plugin v0.1.0 — Couche d'intégration Obsidian
> Construction de notes structurées, routing vault, CRUD via MCP.

---

## Commandes

```bash
# Via tk CLI (recommandé)
tk obsidian vault-list              # Lister les vaults configurés
tk obsidian build "SQLite" --type project --author "SQLite Consortium"
tk obsidian dry-run                 # Démo SQLite sans écriture

# Direct (depuis la racine du repo)
python plugins/obsidian-agent-layer/scripts/obsidian_runner.py vault-list
python plugins/obsidian-agent-layer/scripts/obsidian_runner.py build "SQLite" --type project
python plugins/obsidian-agent-layer/scripts/obsidian_runner.py dry-run
python plugins/obsidian-agent-layer/scripts/obsidian_runner.py build "Test" --json
```

> **Note** : Les opérations d'écriture réelles (`write_note`, `patch_note`) nécessitent
> un contexte agent Claude avec les outils MCP Obsidian connectés. Le CLI s'exécute
> toujours en `dry_run=True`.

---

## Modules

| Module | Rôle |
|---|---|
| `vault_router.py` | Routing automatique vault (claude-vault / notes-vault) par type de note ou chemin |
| `note_builder.py` | Construction notes structurées (project, paper, person, organization, concept, source, note générique) |
| `obsidian_client.py` | Client unifié — CRUD notes, HOT_CACHE, daily log, rate-limit |
| `scripts/obsidian_runner.py` | CLI Typer — point d'entrée principal |

---

## Routing vault

| Type de note | Vault |
|---|---|
| project, paper, person, organization, concept, source | `notes-vault` (obsidian-my-domain-project) |
| daily_log, memory, decision, note | `claude-vault` (obsidian-claude-vault) |

---

## Types de notes supportés

| Type | Chemin généré | Champs requis |
|---|---|---|
| `project` | `Knowledge/Projects/<slug>.md` | title, url, license, status |
| `paper` | `Knowledge/Papers/<slug>.md` | title, authors, year |
| `person` | `Knowledge/People/<slug>.md` | name, affiliation |
| `organization` | `Knowledge/Organizations/<slug>.md` | name, founded |
| `concept` | `Knowledge/Concepts/<slug>.md` | title, definition |
| `source` | `Knowledge/Sources/<slug>.md` | title, url |
| `note` | `10_INBOX/<slug>.md` | title |

---

## Tests

```bash
pytest tests/test_obsidian_agent_layer.py -v   # 35 tests
```

---

## Limites

- `max_ops_per_session = 50` — rate-limit opérations MCP par session
- Écriture réelle : contexte agent Claude requis (MCP `obsidian-claude-vault` / `obsidian-my-domain-project`)
- Routing custom : passer `explicit_vault="claude-vault"` à `create_client()`

---

*obsidian-agent-layer v0.1.0 — TricorderKit v0.9*
