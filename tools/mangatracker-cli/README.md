# MangaTracker CLI Pack v0.1

Pack CLI initial pour Japan-Alliance / MangaTracker.

Objectif : fournir une base exécutable, modulaire et extensible pour automatiser la veille et la structuration des données : manga, light novels, anime, seiyū, studios, jeux vidéo japonais, goods, événements, puis synchronisation Obsidian / kintone.

## Installation rapide

```bash
cd tools/mangatracker-cli
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## Commandes principales

```bash
mangatracker manga scan-new --source shonenjumpplus --type chapter1
mangatracker ln scan-ranking --source syosetu
mangatracker anime scan-news --source comic-natalie
mangatracker seiyu scan-agency --agency aoni
mangatracker studio scan --studio mappa
mangatracker game scan-cero --title "作品名"
mangatracker goods scan-maker --maker goodsmile
mangatracker events scan --source animejapan
mangatracker sync obsidian --vault ./exports
mangatracker audit sources
```

## Philosophie technique

Le scraping principal doit rester côté CLI. Le MCP doit servir uniquement à piloter le CLI, lire les logs, interroger une base propre, synchroniser Obsidian ou kintone et générer des rapports.

Cette approche limite la consommation de tokens et évite de demander à un agent de naviguer inutilement dans des pages multiples.

## Statut

Version : `v0.1.0`

- Fonctionnel : commandes CLI, exports Markdown/JSON, registre de sources, schémas, audit basique.
- À compléter : parseurs HTML/API par source, gestion anti-rate-limit avancée, tests d'intégration, connecteur kintone réel.
