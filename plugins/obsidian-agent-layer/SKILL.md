# obsidian-agent-layer — Skill Intégration Vault Obsidian
> Version : 0.1.0 — 16/05/2026
> Ancrage : TricorderKit v0.8 — Phase 5 active
> Statut : Scaffoldé — en développement

---

## 🎯 Rôle & déclencheurs

`obsidian-agent-layer` est la **couche d'intégration Obsidian** de TricorderKit. Il fournit une API unifiée pour lire, créer, mettre à jour et indexer des notes dans les vaults Obsidian connectés sans passer par le MCP brut.

### Responsabilités
1. **CRUD notes** — créer, lire, patcher, déplacer, supprimer des notes avec frontmatter structuré
2. **Recherche sémantique** — full-text + tags + frontmatter dans les vaults
3. **Fiches structurées** — produire des notes conformes aux templates TricorderKit (manga, animé, studio, seiyū)
4. **Sync bidirectionnelle** — détecter les changements et propager vers les BDD (Qdrant, SQLite)
5. **HOT_CACHE** — mettre à jour l'état du projet en fin de session

### Déclencheurs
- Commande : `/tk:obsidian write <note_path> <content>`
- Commande : `/tk:obsidian search <query> --vault <vault_name>`
- Après exécution d'un pipeline deep-research-core (auto-persist)
- Fin de session : mise à jour HOT_CACHE + daily log

### Ce qu'il N'EST PAS
- ❌ Un remplaçant du MCP Obsidian (il s'appuie dessus)
- ❌ Un moteur de recherche vectorielle (délègue à Qdrant)
- ❌ Un éditeur de vault (pas de suppression en masse)

---

## ⚙️ Architecture

```
plugins/obsidian-agent-layer/
├── SKILL.md                   ← Ce fichier
├── manifest.yml               ← Compatible cli-forge
├── obsidian_client.py         ← Wrapper MCP → API Python unifiée
├── note_builder.py            ← Construction frontmatter + body Obsidian
├── vault_router.py            ← Routing vault (claude-vault / japan-alliance / custom)
├── template_registry.py       ← Templates Obsidian par type (manga, anime, seiyū...)
├── sync_engine.py             ← Détection changements + propagation Qdrant/SQLite
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_note_builder.py
    ├── test_vault_router.py
    └── test_obsidian_client.py
```

---

## 🗂️ Vaults supportés

| Vault ID          | Path Obsidian                        | Usage principal                    |
|---|---|---|
| `claude-vault`    | Claude Vault (MCP connecté)          | Mémoire système, daily logs, HOT_CACHE |
| `japan-alliance`  | Japan-Alliance Vault (MCP connecté)  | Fiches manga, animé, seiyū, studios |
| `custom`          | Configurable via manifest.yml        | Usage projet spécifique            |

---

## 📤 Output Contract

```json
{
  "status": "success|partial|error|dry_run",
  "skill_name": "obsidian-agent-layer",
  "skill_version": "0.1.0",
  "timestamp": "...",
  "output": {
    "summary": "3 notes créées, 1 mise à jour, 0 erreur",
    "data": {
      "notes_created": 3,
      "notes_updated": 1,
      "notes_failed": 0,
      "vault": "japan-alliance",
      "paths": [
        "Mangas/Dragon Ball/dragon-ball.md",
        "Mangakas/Toriyama-Akira.md"
      ]
    },
    "files_created": [],
    "next_steps": ["Indexer les nouvelles notes dans Qdrant"]
  }
}
```

---

## 🚀 Commandes CLI

```bash
# Écrire une note depuis stdin JSON
echo '{"path": "Mangas/Test/test.md", "content": "# Test"}' \
  | python plugins/obsidian-agent-layer/obsidian_client.py write

# Recherche full-text
python plugins/obsidian-agent-layer/obsidian_client.py search "Dragon Ball" --vault japan-alliance

# Construire une fiche manga structurée
python plugins/obsidian-agent-layer/note_builder.py manga --title "Dragon Ball" --author "Toriyama Akira"

# Mettre à jour le HOT_CACHE
python plugins/obsidian-agent-layer/obsidian_client.py update-hot-cache

# Dry-run : simuler une écriture
python plugins/obsidian-agent-layer/obsidian_client.py write --dry-run
```

---

## 📝 Templates supportés

| Type    | Frontmatter clés                                      | Dossier cible                |
|---|---|---|
| `manga` | title, author, publisher, magazine, status, volumes   | `Mangas/<title>/`            |
| `anime` | title, studio, director, seasons, episodes, status    | `Animes/<title>/`            |
| `seiyuu`| name, birth_date, agency, notable_roles               | `Personnes/Seiyuu/<name>/`   |
| `studio`| name, founded, notable_works, type                    | `Studios/<name>/`            |
| `note`  | (générique — title, tags, date)                       | Libre                        |

---

## 🛡️ Gardes-fous

- **Dry-run obligatoire** avant toute écriture en masse (> 10 notes)
- **Vérification existence** : jamais d'écrasement silencieux — patch si note existante
- **Rollback** : conserver la version précédente en `_archive/` sur modification destructive
- **Rate-limit MCP** : max 50 opérations par session, pause entre lots

---

## 📊 Notes de fiabilité

| Élément             | Niveau           | Commentaire                                              |
|---|---|---|
| CRUD notes          | 🟡 Probable      | Dépend stabilité MCP Obsidian — testé en session active |
| Routing vault       | ✅ Confirmé      | Deux vaults MCP connectés et stables                    |
| Templates           | 🟡 Probable      | Templates v0.1 — évolution attendue Phase 6             |
| Sync Qdrant         | 🟠 À vérifier    | Qdrant non encore connecté en Phase 5                   |

---

*obsidian-agent-layer v0.1.0 — 16/05/2026 — TricorderKit v0.8*
