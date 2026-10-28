---
name: connector-hub
description: "Hub d'ingestion passif multi-sources. Lit les declarations sources.yaml de chaque linked_project actif, construit un registre unifie et route chaque ingestion vers le CLI adapte. Declencheurs : ingestion sources, veille multi-sources, registre de connecteurs, router une source, connector hub."
---

# SKILL.md — connector_hub

> Plugin TricorderKit v0.8 — Hub d'ingestion passif multi-sources

---

## Rôle

Le Connector Hub est le point d'entrée unique pour la veille multi-sources.
Il lit les déclarations `sources.yaml` de chaque linked_project actif,
construit un registre unifié et route chaque ingestion vers le CLI adapté.

---

## Quand utiliser ce plugin

- Pour connaître toutes les sources déclarées : `connector_hub list`
- Pour vérifier qu'une source est joignable : `connector_hub status`
- Pour déclencher une ingestion manuelle : `connector_hub dispatch --source <id>`
- Pour lancer toutes les ingestions : `connector_hub dispatch --all --dry-run` (toujours dry-run en premier)

---

## Commandes

```bash
# Lister toutes les sources actives
python plugins/connector-hub/connector_hub.py list

# Lister aussi les sources désactivées
python plugins/connector-hub/connector_hub.py list --all

# JSON contract-compliant
python plugins/connector-hub/connector_hub.py list --format json

# Vérifier joignabilité (HTTP HEAD)
python plugins/connector-hub/connector_hub.py status

# Simuler le dispatch de toutes les sources
python plugins/connector-hub/connector_hub.py dispatch --all --dry-run

# Dispatcher uniquement arXiv, sur une requête donnée
python plugins/connector-hub/connector_hub.py dispatch --source "arXiv API" --query "vector databases"

# Dispatcher une source spécifique d'un linked_project
python plugins/connector-hub/connector_hub.py dispatch --source my-domain-project_source_1
```

---

## Architecture des sources

Les sources proviennent de deux niveaux :

| Niveau | Fichier | Contenu |
|--------|---------|---------|
| Core (générique) | `plugins/deep-research-core/sources/trusted_sources.yml` | APIs publiques génériques (GitHub, arXiv, Hacker News, Wikipedia) |
| Linked project | `<linked_project_root>/project_config/sources.yaml` | Sources propres au domaine du projet lié |

---

## Routage des sources

Aucune source n'est câblée en dur dans le hub.

| Origine | CLI appelé |
|---------|------------|
| Core (`trusted_sources.yml`, catégorie `<d>`) | `collect_sources.py --domain <d> --sources "<nom>" --query <requête>` |
| Linked project | bloc `dispatch: {cli, args}` de la source dans `sources.yaml` |

`--source` accepte un id, un nom, un type ou un domaine (ex. `research`).
Une source de linked_project sans bloc `dispatch:` est listée mais non dispatchable.

---

## Lien avec Temporal

Le Connector Hub complète `source_watch.workflow.ts` :
- Le workflow Temporal gère la **répétition** (sleep + signal pause/resume/stop)
- Le Connector Hub gère le **routage** (quel CLI pour quelle source)

Pour déclencher un workflow Temporal :

```bash
# (via tk CLI — une fois l'intégration Temporal câblée)
tk workflow start source_watch --project my-domain-project
```

---

## Règles opérationnelles TricorderKit

1. **Dry-run obligatoire** avant tout `dispatch --all` en production.
2. **CLI avant LLM** : utiliser ce hub avant de générer des données manuellement.
3. **Sources validées uniquement** — voir `docs/linked_projects.md` pour les critères de fiabilité.
4. Ne jamais ajouter une source `requires_auth: true` sans vérifier que le secret est dans `.env` (jamais en dur).

---

## Output JSON (contract)

`--format json` produit un objet conforme à la structure suivante :

```json
{
  "connector_hub_version": "0.2.0",
  "timestamp": "2026-05-17T...",
  "total": 5,
  "dispatchable": 4,
  "sources": [
    {
      "id": "core_arxiv_api",
      "name": "arXiv API",
      "url": "http://export.arxiv.org/api/query",
      "type": "api_atom",
      "reliability": "0.95",
      "enabled": true,
      "origin": "core",
      "domain": "research",
      "dispatchable": true,
      "handler_desc": "collect_sources.py --domain research"
    }
  ]
}
```
