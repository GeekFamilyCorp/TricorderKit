# CLAUDE.md — TricorderKit v0.7

> Configuration Claude Code pour ce repo.

---

## Identité du projet

- **Nom** : TricorderKit
- **Version** : 0.7
- **Type** : Agentic Knowledge OS — local-first
- **Propriétaire** : GeekFamilyCorp
- **Stack** : Claude Code + Obsidian + MCP + Neo4j + Qdrant + Docker + Temporal

---

## Fichiers à lire au boot

```text
README_FIRST.md
AGENTS.md
.planning/STATE.md
.planning/TASKS.md
```

---

## Conventions de code

### TypeScript (CLI, workflows Temporal)
- Strict mode activé
- Output JSON par défaut pour toutes les commandes CLI
- Types explicites, pas d'`any`

### Python (scripts utilitaires)
- Python 3.11+
- Output JSON ou Markdown
- Pas de dépendances inutiles

### Markdown (vault, docs)
- Frontmatter YAML obligatoire
- 1 idée = 1 fichier (principe atomique)
- Taille cible : 100–500 tokens par note

---

## Structure des plugins

Chaque plugin dans `plugins/` doit contenir :

```text
plugins/<nom>/
├── README.md           → description + usage
├── SKILL.md            → instructions pour agents
├── manifest.yml        → métadonnées + config
├── scripts/            → scripts exécutables
└── tests/              → tests du plugin
```

---

## Structure des skills

Chaque skill dans `skills/` doit contenir :

```text
skills/<nom>/
├── SKILL.md            → instructions détaillées
├── examples/           → exemples d'utilisation
└── tests/              → eval tests
```

---

## Règles de commit

```text
feat: <description>     → nouvelle fonctionnalité
fix: <description>      → correction
docs: <description>     → documentation
refactor: <description> → refactoring
test: <description>     → tests
chore: <description>    → maintenance
```

Chaque commit important → entrée dans `CHANGELOG.md`.

---

## Commande principale

```bash
/tk:boot
```

---

## Variables d'environnement requises

```text
ANTHROPIC_API_KEY       → Claude Code
NEO4J_URI               → graph database
NEO4J_USER              → graph database
NEO4J_PASSWORD          → graph database
QDRANT_URL              → vector database
QDRANT_API_KEY          → vector database (optionnel local)
TEMPORAL_ADDRESS        → workflow engine
LANGFUSE_PUBLIC_KEY     → observabilité
LANGFUSE_SECRET_KEY     → observabilité
OBSIDIAN_VAULT_PATH     → vault local
```

---

## Docker Compose services cibles

```yaml
services:
  neo4j:
    image: neo4j:5
    ports: ["7474:7474", "7687:7687"]
  
  qdrant:
    image: qdrant/qdrant
    ports: ["6333:6333"]
  
  langfuse:
    image: langfuse/langfuse
    ports: ["3000:3000"]
  
  temporal:
    image: temporalio/auto-setup
    ports: ["7233:7233"]
```

---

*Version 0.7 — 10/05/2026*
