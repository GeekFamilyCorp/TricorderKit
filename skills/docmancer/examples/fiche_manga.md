# Exemple : Création fiche manga avec docmancer

## Input utilisateur

```
/tk:docmancer --type manga "Dungeon Meshi de Ryoko Kui, éditeur Enterbrain"
```

## Exécution

### Étape 1 — Vérification existence
```bash
python plugins/obsidian-agent-layer/vault_router.py \
  --action check --path "Mangas/Dungeon_Meshi.md" --vault japan-alliance
# → {"exists": false}
```

### Étape 2 — Build note (dry-run)
```bash
python plugins/obsidian-agent-layer/note_builder.py \
  --type manga \
  --data '{"title":"Dungeon Meshi","title_jp":"ダンジョン飯","author":"Ryoko Kui","publisher_jp":"Enterbrain","status":"completed","volumes":14}' \
  --dry-run
```

### Étape 3 — Écriture réelle
```bash
python plugins/obsidian-agent-layer/obsidian_client.py \
  --action write --path "Mangas/Dungeon_Meshi.md" --vault japan-alliance \
  --content '<output_note_builder>'
```

## Note générée

```markdown
---
type: manga
title: "Dungeon Meshi"
title_jp: "ダンジョン飯"
author: "Ryoko Kui"
publisher_jp: "Enterbrain"
publisher_fr: "Kurokawa"
status: completed
volumes: 14
reliability: confirmed
sources: ["mangadex", "anilist"]
tags: ["#manga", "#japan-alliance", "#fantasy"]
created: "2026-05-18"
updated: "2026-05-18"
---

# Dungeon Meshi

Manga de fantasy culinaire de Ryoko Kui, sérialisé dans Harta (Enterbrain).
14 volumes — terminé.

## Liens
- [[Ryoko_Kui]] (auteure)
- [[Enterbrain]] (éditeur JP)
- [[Kurokawa]] (éditeur FR)
```

## Output contractuel

```json
{
  "status": "success",
  "skill_name": "docmancer",
  "output": {
    "action": "created",
    "note_path": "Mangas/Dungeon_Meshi.md",
    "vault": "japan-alliance",
    "reliability": "confirmed"
  }
}
```
