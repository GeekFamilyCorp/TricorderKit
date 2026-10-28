# tk-data-ops v1.0.0 — PUBLIC (MIT)

Données et graphe TricorderKit : accès normé à Neo4j (MCP officiel, lecture seule par défaut), recherche hybride Qdrant+Neo4j (graphrag-hybrid), scraping adaptatif (Scrapling), veille de changements (changedetection.io + RSSHub).

Regroupement du 2026-09-07 (audit `claude/AUDIT_SKILLS_PLUGINS_2026-09-07.md`, lot L4) : un plugin = un domaine d'usage.

## Skills

| Skill | Rôle |
|---|---|
| `graphrag-hybrid` | Répond à une question par recherche hybride locale : similarité vectorielle dans Qdrant, puis expansion du voisinage dans Neo4j, puis synthèse par un modèle Ollama — pipeline neo4j-graphrag-python (Apache-2.0), zéro API … |
| `neo4j-graph-ops` | Interroge et fait évoluer le graphe de connaissances Neo4j d'une stack locale (APOC/GDS) via le serveur MCP officiel neo4j/mcp : lit le schéma, formule des requêtes Cypher en LECTURE d'abord, propose l'écriture et ne l'e… |
| `scrape-adaptive` | Collecte des pages web de façon robuste et respectueuse avec Scrapling (BSD-3 : parseur adaptatif qui retrouve un élément après refonte du site, spiders pause/reprise, robots.txt, serveur MCP natif) et Playwright en repl… |
| `watch-changes` | Met en place et exploite une veille de changements de pages et de flux, en local : changedetection.io (Apache-2.0, sélecteurs CSS/XPath/jq, notifications Apprise) pour surveiller des pages, RSSHub (AGPL-3.0) pour transfo… |

## Fichiers partagés

- `references/regles.md` — définitions en une ligne des règles R.. citées par les skills (source : `RULES_REGISTRY.md` du claude-vault).
- `models.json` — alias de modèles `fast` / `default` / `deep` ; seul endroit où un identifiant de modèle est écrit.

## Serveur MCP (opt-in, désactivé par défaut)

`.mcp.json.example` décrit le serveur MCP du plugin. Il n'est PAS actif à l'installation (sécurité : aucun serveur lancé, aucun secret attendu). Pour l'activer : renommer en `.mcp.json`, définir les variables d'environnement listées (jamais de valeur en clair dans le fichier), réinstaller le plugin. Pour revenir en arrière : renommer en `.mcp.json.example`.

## Retour arrière

Chaque version livrée est archivée (`plugins-2026-09-07/` v1 des anciens plugins, `plugins-2026-09-07-L4/` cette version). Revenir en arrière = désactiver ce plugin dans Réglages > Fonctionnalités et réinstaller le `.plugin` précédent. Aucune donnée n'est touchée par l'installation : les skills lisent ; ce qui écrit passe par le SAS ou par un GO explicite. NO-DROP : on désactive, on ne supprime pas.

## Changelog

### 1.0.0 — 2026-09-07
- Création par regroupement (L4) à partir de tricorderkit-skills 0.4.0 / gfc-maison-ops 1.4.0 / token-optimizer 0.3.0 ; renvois inter-skills réécrits sur les nouveaux noms de plugins ; validateur Anthropic 100 %.
