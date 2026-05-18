# Skill: docmancer — Document & Note Generator

> Version 0.1.0 — 2026-05-18
> Génération automatique de notes Obsidian et documents Markdown structurés.
> S'appuie sur obsidian-agent-layer pour le CRUD vault et les templates.

---

## Triggers

```text
/tk:docmancer
/tk:doc
docmancer
génère une note
crée une fiche
indexe dans obsidian
note obsidian pour
fiche manga
fiche animé
fiche auteur
sauvegarde dans le vault
persiste dans obsidian
```

---

## Prérequis

1. `plugins/obsidian-agent-layer/` présent et opérationnel
2. MCP `obsidian-claude-vault` connecté (vault TricorderKit)
3. MCP `obsidian-japan-alliance` connecté si domaine manga/animé

---

## Instructions agent

### Séquence d'exécution

```text
ÉTAPE 1 — Intent extraction
  → Extraire : type (manga|anime|author|studio|generic), content, vault_target, dry_run
  → vault_target par défaut : "claude-vault"
  → Pour mangas/animés/auteurs : vault_target = "japan-alliance"

ÉTAPE 2 — Sélection template (via note_builder.py)
  | Type       | Template               | Vault cible        |
  |------------|------------------------|-------------------|
  | manga      | templates/manga.md     | japan-alliance     |
  | anime      | templates/anime.md     | japan-alliance     |
  | author     | templates/author.md    | japan-alliance     |
  | studio     | templates/studio.md    | japan-alliance     |
  | session    | templates/session.md   | claude-vault       |
  | generic    | templates/generic.md   | claude-vault       |
  | decision   | templates/decision.md  | claude-vault       |

ÉTAPE 3 — Vérification existence (anti-doublon R7)
  python plugins/obsidian-agent-layer/vault_router.py \
    --action check --path "<note_path>" --vault <vault>
  → Si note existe : proposer mise à jour, non réécriture

ÉTAPE 4 — Construction frontmatter + body
  python plugins/obsidian-agent-layer/note_builder.py \
    --type <type> --data '<json_content>' [--dry-run]

ÉTAPE 5 — Écriture vault (MCP ou obsidian_client.py)
  python plugins/obsidian-agent-layer/obsidian_client.py \
    --action write --path "<note_path>" --content '<content>' --vault <vault>

ÉTAPE 6 — Output contractuel JSON
```

### Templates disponibles

#### Template manga (frontmatter)

```yaml
---
type: manga
title: "<titre>"
title_jp: "<titre japonais>"
author: "<auteur>"
publisher_jp: "<éditeur japonais>"
publisher_fr: "<éditeur français>"
status: ongoing|completed|hiatus
volumes: <nombre>
chapters: <nombre>
genres: []
tags: ["#manga", "#japan-alliance"]
reliability: confirmed|probable|to_verify|incomplete
sources: []
created: "<YYYY-MM-DD>"
updated: "<YYYY-MM-DD>"
---
```

#### Template session (frontmatter)

```yaml
---
type: session-log
date: "<YYYY-MM-DD>"
project: tricorderkit
version: "<version>"
tags: ["#session", "#tricorderkit"]
status: completed
---
```

### Règles importantes

- **Anti-doublon (R7)** : toujours vérifier existence avant création
- **Frontmatter obligatoire** : toute note doit avoir un frontmatter YAML valide
- **Atomicité** : 1 note = 1 entité (pas de notes multi-sujets)
- **Taille cible** : 100–500 tokens par note (principe CLAUDE.md)
- **Fiabilité** : toujours indiquer le niveau (`confirmed|probable|to_verify|incomplete`)
- **Dry-run (R3)** : activer `--dry-run` pour prévisualiser avant écriture réelle
- **Décisions** : loguer dans `.planning/DECISIONS.md` si la note implique un choix archi

---

## Commandes de référence

```bash
# Construction note manga (dry-run)
python plugins/obsidian-agent-layer/note_builder.py \
  --type manga \
  --data '{"title":"Dungeon Meshi","author":"Ryoko Kui","publisher_jp":"Enterbrain"}' \
  --dry-run

# Vérification existence
python plugins/obsidian-agent-layer/vault_router.py \
  --action check --path "Mangas/Dungeon_Meshi.md" --vault japan-alliance

# Écriture réelle
python plugins/obsidian-agent-layer/obsidian_client.py \
  --action write --path "Mangas/Dungeon_Meshi.md" --vault japan-alliance \
  --content '<frontmatter+body>'

# Mise à jour note existante
python plugins/obsidian-agent-layer/obsidian_client.py \
  --action patch --path "Mangas/Dungeon_Meshi.md" \
  --field "volumes" --value "14"
```

---

## Format de sortie contractuel

```json
{
  "status": "success",
  "skill_name": "docmancer",
  "skill_version": "0.1.0",
  "timestamp": "2026-05-18T10:00:00Z",
  "output": {
    "action": "created",
    "note_path": "Mangas/Dungeon_Meshi.md",
    "vault": "japan-alliance",
    "type": "manga",
    "template_used": "templates/manga.md",
    "frontmatter_keys": ["title", "author", "publisher_jp", "status", "reliability"],
    "reliability": "confirmed",
    "dry_run": false,
    "next_steps": ["Lier à la fiche auteur Ryoko Kui", "Ajouter volumes manquants"]
  },
  "metadata": {
    "tokens_estimated": 350,
    "vault_path": "C:/Users/sebas/Documents/obsidian/Japan-Alliance/Mangas/Dungeon_Meshi.md"
  }
}
```

---

## Gestion d'erreurs

| Erreur | Cause | Action |
|---|---|---|
| `Note already exists` | Doublon détecté | Proposer patch, non réécriture |
| `obsidian-agent-layer introuvable` | Plugin non installé | Vérifier `plugins/obsidian-agent-layer/` |
| `MCP obsidian-japan-alliance timeout` | Vault non connecté | Fallback claude-vault + warning |
| `Frontmatter invalide` | Données manquantes | Demander les champs requis à l'utilisateur |
| `Template inconnu` | Type non supporté | Utiliser template `generic` |

---

## Pipeline rtk → docmancer

Ce skill est conçu pour être appelé directement après `rtk` :

```text
/rtk "Dungeon Meshi"
  → résultats scorés
  → /tk:docmancer --type manga --data <rtk_output>
    → note créée dans japan-alliance vault
```

Output caveman pour pipeline (R15) :

```json
{
  "status": "ok",
  "task": "docmancer_write",
  "data": {"note": "Mangas/Dungeon_Meshi.md", "vault": "japan-alliance", "action": "created"},
  "tokens_used": 350,
  "next_action": "review_queue_add"
}
```

---

*TricorderKit v0.8 — GeekFamilyCorp — 2026-05-18*
