# vault/ — TricorderKit v0.7

Mémoire locale du projet — complément au vault Obsidian.

## Structure

```text
vault/
├── memory/        # Mémoire projet persistante
├── reports/       # Rapports générés (health, audit, research)
├── decisions/     # Copies locales des décisions importantes
└── sources/       # Sources de recherche collectées
```

## Relation avec Obsidian

Le vault Obsidian principal est configuré via la variable d'environnement
`OBSIDIAN_VAULT_PATH` dans `.env` (voir `.env.example`).

Ce dossier `vault/` sert de cache local pour les rapports générés par TricorderKit
(health_check, deep-research, vault-audit) et les sources collectées par source-watch-goat.

## Fichiers générés ici

- `reports/health_YYYYMMDD_HHMM.html` — dashboard santé HTML
- `reports/manga_watch_YYYY-MM-DD.md` — rapport veille manga
- `sources/` — sources collectées par deep-research-core
