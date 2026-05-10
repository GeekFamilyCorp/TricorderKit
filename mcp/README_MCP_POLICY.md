# Politique MCP — TricorderKit v0.7

> Règle fondamentale : **CLI = travail lourd. MCP = accès structuré. Claude = raisonnement et synthèse.**

---

## Ce que le MCP DOIT faire

- Accéder à kintone (records structurés, statuts, validation humaine)
- Lire un rapport court généré par le CLI
- Modifier un statut ou déclencher une commande whitelistée
- Synchroniser une fiche validée
- Interroger un index local court

## Ce que le MCP NE DOIT PAS faire

- Scraper directement des sites web
- Injecter des pages HTML entières dans le contexte
- Remplacer un parseur CLI
- Lancer des commandes shell arbitraires
- Accéder à des secrets sans contrôle
- Modifier le vault sans dry-run

---

## Hiérarchie CLI → MCP → Claude

| Cas | Outil |
|---|---|
| Scraper une page / liste de titres | CLI |
| Scanner sources japonaises en batch | CLI |
| Normaliser / dédupliquer des résultats | CLI |
| Lire une synthèse courte | Claude |
| Accéder à kintone | MCP kintone ou cli-kintone |
| Exporter vers Obsidian | CLI |
| Décision éditoriale | Claude |

---

## Whitelist CLI autorisée

```bash
python -m mangatracker_cli.cli audit sources
python -m mangatracker_cli.cli manga scan-new [--source] [--type]
python -m mangatracker_cli.cli ln scan-ranking [--source]
python -m mangatracker_cli.cli anime scan-news [--source]
python -m mangatracker_cli.cli sync obsidian --dry-run
python -m mangatracker_cli.cli sync kintone --dry-run
python tools/jp-scraper/src/jp_scraper/cli.py sources audit
python tools/jp-scraper/src/jp_scraper/cli.py scrape source [--source]
python scripts/vault_optimizer/vault_analyzer.py --vault .
python scripts/vault_optimizer/vault_manifest.py
python scripts/validate_repo.py
python scripts/health_check.py
```

## Commandes interdites

```text
rm -rf
curl | sh / wget | sh
eval
bash -c depuis entrée utilisateur
écriture hors TricorderKit/
```

---

## Configuration MCP projet

Voir `.mcp.json` à la racine.  
Les secrets sont dans `.env` (jamais committés).  
Variables requises : `KINTONE_BASE_URL`, `KINTONE_API_TOKEN`.

*Version 0.1.0 — 10/05/2026*
