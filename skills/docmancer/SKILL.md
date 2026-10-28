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
fiche projet
fiche article
fiche personne
sauvegarde dans le vault
persiste dans obsidian
```

---

## Prérequis

1. `plugins/obsidian-agent-layer/` présent et opérationnel
2. MCP `obsidian-claude-vault` connecté (vault TricorderKit)
3. MCP `obsidian-my-domain-project` connecté si une note cible le vault d'un linked_project

---

## Instructions agent

### Séquence d'exécution

```text
ÉTAPE 1 — Intent extraction
  → Extraire : type (project|paper|person|organization|concept|source|generic), content, vault_target, dry_run
  → vault_target par défaut : "claude-vault"
  → Pour les entités d'un domaine métier : vault_target = "my-domain-project" (linked_project)

ÉTAPE 2 — Sélection template (via note_builder.py)
  | Type       | Template               | Vault cible        |
  |------------|------------------------|-------------------|
  | project      | templates/project.md      | claude-vault ou linked_project |
  | paper        | templates/paper.md        | claude-vault ou linked_project |
  | person       | templates/person.md       | claude-vault ou linked_project |
  | organization | templates/organization.md | claude-vault ou linked_project |
  | concept      | templates/concept.md      | claude-vault       |
  | source       | templates/source.md       | claude-vault       |
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

#### Template project (frontmatter)

```yaml
---
type: project
title: "<nom du projet>"
url: "<dépôt ou site officiel>"
maintainer: "<organisation ou personne>"
license: "<licence>"
language: "<langage principal>"
status: active|maintenance|archived
latest_release: "<version>"
topics: []
tags: ["#project"]
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
# Construction note projet (dry-run)
python plugins/obsidian-agent-layer/note_builder.py \
  --type project \
  --data '{"title":"Qdrant","url":"https://github.com/qdrant/qdrant","license":"Apache-2.0"}' \
  --dry-run

# Vérification existence
python plugins/obsidian-agent-layer/vault_router.py \
  --action check --path "Projects/Qdrant.md" --vault claude-vault

# Écriture réelle
python plugins/obsidian-agent-layer/obsidian_client.py \
  --action write --path "Projects/Qdrant.md" --vault claude-vault \
  --content '<frontmatter+body>'

# Mise à jour note existante
python plugins/obsidian-agent-layer/obsidian_client.py \
  --action patch --path "Projects/Qdrant.md" \
  --field "latest_release" --value "1.12.0"
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
    "note_path": "Projects/Qdrant.md",
    "vault": "claude-vault",
    "type": "project",
    "template_used": "templates/project.md",
    "frontmatter_keys": ["title", "url", "license", "status", "reliability"],
    "reliability": "confirmed",
    "dry_run": false,
    "next_steps": ["Lier à la fiche organisation", "Ajouter la dernière version publiée"]
  },
  "metadata": {
    "tokens_estimated": 350,
    "vault_path": "${OBSIDIAN_VAULT_PATH}/Projects/Qdrant.md"
  }
}
```

---

## Gestion d'erreurs

| Erreur | Cause | Action |
|---|---|---|
| `Note already exists` | Doublon détecté | Proposer patch, non réécriture |
| `obsidian-agent-layer introuvable` | Plugin non installé | Vérifier `plugins/obsidian-agent-layer/` |
| `MCP obsidian-my-domain-project timeout` | Vault non connecté | Fallback claude-vault + warning |
| `Frontmatter invalide` | Données manquantes | Demander les champs requis à l'utilisateur |
| `Template inconnu` | Type non supporté | Utiliser template `generic` |

---

## Pipeline rtk → docmancer

Ce skill est conçu pour être appelé directement après `rtk` :

```text
/rtk "Qdrant"
  → résultats scorés
  → /tk:docmancer --type project --data <rtk_output>
    → note créée dans le vault cible
```

Output caveman pour pipeline (R15) :

```json
{
  "status": "ok",
  "task": "docmancer_write",
  "data": {"note": "Projects/Qdrant.md", "vault": "claude-vault", "action": "created"},
  "tokens_used": 350,
  "next_action": "review_queue_add"
}
```

---

*TricorderKit v0.8 — GeekFamilyCorp — 2026-05-18*
