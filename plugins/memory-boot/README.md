# memory-boot

Plugin Claude Cowork — initialise la mémoire de session depuis Obsidian.

## Skills inclus

| Skill | Déclencheur | Rôle |
|-------|-------------|------|
| `memory-boot` | `boot`, `reprends le contexte`, `charge ta mémoire` | Lit HOT_CACHE + PATTERNS + ERRORS, produit un résumé de démarrage, log dans le Daily Log |
| `rapport` | `rapport`, `status`, `bilan`, `avancées` | Génère un bilan des accomplissements, projets actifs, tâches ouvertes, 3 suggestions d'amélioration |

## Prérequis

Le MCP `obsidian-claude-vault` doit être connecté dans Claude Cowork.

## Structure Obsidian attendue

```
vault/
├── 00_SYSTEM/
│   ├── 05_Hot_Cache/HOT_CACHE.md     ← contexte vivant
│   └── 06_Successes/
│       ├── SUCCESSES_INDEX.md         ← index des réussites
│       ├── skills/                    ← fiche par skill créé
│       ├── plugins/                   ← fiche par plugin livré
│       └── projects/                  ← fiche par projet lancé
├── 10_INBOX/Daily_Logs/              ← logs quotidiens
│   └── YYYY-MM-DD.md
└── 40_ERRORS/
    ├── Error_Log/ERRORS.md            ← journal des erreurs
    └── Patterns/PATTERNS_INDEX.md     ← patterns récurrents
```

## Utilisation

```
# Démarrage de session
boot

# Bilan des avancées
rapport

# Rapport sur un projet spécifique
rapport sur [nom du projet]
```

## Auteur
GeekFamilyCorp — v1.1.0
