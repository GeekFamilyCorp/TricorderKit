# obsidian-agent-layer

> TricorderKit plugin v0.1.0 — Couche d'intégration Obsidian
> Construction de notes structurées, routing vault, CRUD via MCP.

---

## Commandes

```bash
# Via tk CLI (recommandé)
tk obsidian vault-list              # Lister les vaults configurés
tk obsidian build "One Piece" --type manga --author "Oda Eiichiro"
tk obsidian dry-run                 # Démo Dragon Ball sans écriture

# Direct (depuis la racine du repo)
python plugins/obsidian-agent-layer/scripts/obsidian_runner.py vault-list
python plugins/obsidian-agent-layer/scripts/obsidian_runner.py build "One Piece" --type manga
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
| `note_builder.py` | Construction notes structurées (manga, anime, seiyuu, studio, note générique) |
| `obsidian_client.py` | Client unifié — CRUD notes, HOT_CACHE, daily log, rate-limit |
| `scripts/obsidian_runner.py` | CLI Typer — point d'entrée principal |

---

## Routing vault

| Type de note | Vault |
|---|---|
| manga, anime, seiyuu, studio, mangaka | `notes-vault` (obsidian-japan-alliance) |
| daily_log, memory, decision, note | `claude-vault` (obsidian-claude-vault) |

---

## Types de notes supportés

| Type | Chemin généré | Champs requis |
|---|---|---|
| `manga` | `Mangas/<titre>/<slug>.md` | title, author, publisher, status |
| `anime` | `Animes/<titre>/<slug>.md` | title, studio, status |
| `seiyuu` | `Personnes/Seiyuu/<slug>.md` | name, agency |
| `studio` | `Studios/<slug>.md` | name, founded |
| `note` | `10_INBOX/<slug>.md` | title |

---

## Tests

```bash
pytest tests/test_obsidian_agent_layer.py -v   # 34 tests
```

---

## Limites

- `max_ops_per_session = 50` — rate-limit opérations MCP par session
- Écriture réelle : contexte agent Claude requis (MCP `obsidian-claude-vault` / `obsidian-japan-alliance`)
- Routing custom : passer `explicit_vault="claude-vault"` à `create_client()`

---

*obsidian-agent-layer v0.1.0 — TricorderKit v0.9*
