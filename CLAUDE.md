# CLAUDE.md — TricorderKit v0.9

> Configuration Claude Code pour ce repo.
> Mis à jour : 2026-05-22 — Aligné AGENTS.md v0.8 + Extended Thinking policy + rotation session

---

## Identité du projet

- **Nom** : TricorderKit
- **Version** : 0.9
- **Type** : Agentic Knowledge OS — local-first
- **Propriétaire** : GeekFamilyCorp
- **Stack** : Claude Code + Obsidian + MCP + Neo4j + Qdrant + Docker + Temporal
- **Architecture** : TricorderKit exécute · MangaTracker spécialise · Japan-Alliance stocke

---

## Séquence de boot (lazy-load — économie tokens)

```text
TIER 1 — Toujours charger (~500 tokens)
  1. BOOT_SUMMARY.md            → version, tâches, patterns, statut Docker

TIER 2 — Charger uniquement si TIER 1 ne suffit pas (~2 500 tokens)
  2. tasks/lessons.md            → règles préventives actives (R12)
  3. .planning/STATE.md          → état détaillé si phase ou infra à vérifier
  4. .planning/TASKS.md          → items pending/in_progress uniquement (exclure ✅)
  5. .planning/DECISIONS.md      → 5 dernières entrées seulement

TIER 3 — À la demande uniquement (~10 000 tokens)
  - .planning/RISKS.md
  - docs/00→06
```

> Ne charger README_FIRST.md qu'en cas de doute sur les limites du projet.
> Ne jamais charger AGENTS.md au boot — il est lu par Claude Code automatiquement.

---

## Extended Thinking Policy

**Désactivé par défaut** pour toutes les tâches suivantes :
- Remplissage de fiches (manga, anime, LN, seiyū, studio, goodie, personnage)
- Recherche web simple et récupération de données factuelles
- Génération de fichiers depuis un template existant
- Exécution de commandes CLI

**Activé uniquement si** le message contient explicitement `[THINK]` ou si la tâche implique :
- Raisonnement architectural multi-fichiers
- Débogage de régression complexe
- Décision irréversible (DEC-NNN)

---

## Session Rotation Policy

- Ouvrir un nouveau fil toutes les **15–20 messages**
- Avant de fermer : générer `session_capsule.json` compact via `/tk:pack-context`
- Coller la capsule en premier message du nouveau fil
- Mettre à jour `BOOT_SUMMARY.md` en fin de session

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

```text
plugins/<nom>/
├── README.md
├── SKILL.md
├── manifest.yml
├── scripts/
└── tests/
```

## Structure des skills

```text
skills/<nom>/
├── SKILL.md
├── examples/
└── tests/
```

---

## Règles de commit

```text
feat: <description>
fix: <description>
docs: <description>
refactor: <description>
test: <description>
chore: <description>
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
ANTHROPIC_API_KEY
NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD
QDRANT_URL / QDRANT_API_KEY
TEMPORAL_ADDRESS
LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY
OBSIDIAN_VAULT_PATH
```

---

*Version 0.9 — 2026-05-22 — Aligné AGENTS.md v0.8 · Extended Thinking policy · Session rotation*
