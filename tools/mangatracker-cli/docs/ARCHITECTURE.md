# Architecture MangaTracker CLI

```text
mangatracker-cli
├── manga
├── ln
├── anime
├── seiyu
├── studio
├── game
├── goods
├── events
├── sync
└── audit
```

## Règles

1. Source officielle japonaise en premier.
2. Source commerciale fiable pour prix, stock, ISBN, disponibilité.
3. Média professionnel pour annonce ou contexte.
4. Source communautaire uniquement pour détection/croisement.
5. Ne jamais inventer dates, staff, cast, ventes, ISBN, CERO, prix.

## Sorties

- Markdown compatible Obsidian.
- JSON compatible BDD.
- Logs exploitables par MCP.
