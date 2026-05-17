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

# Dispatcher uniquement MangaDex
python plugins/connector-hub/connector_hub.py dispatch --source mangadex

# Dispatcher une source spécifique d'un linked_project
python plugins/connector-hub/connector_hub.py dispatch --source japan-alliance_source_1
```

---

## Architecture des sources

Les sources proviennent de deux niveaux :

| Niveau | Fichier | Contenu |
|--------|---------|---------|
| Core (générique) | `plugins/deep-research-core/sources/trusted_sources.yml` | APIs publiques génériques (GitHub, etc.) |
| Linked project | `<linked_project_root>/project_config/sources.yaml` | Sources domaine-spécifiques (MangaDex, AniList, Jikan...) |

---

## Mapping types → CLIs

| Type déclaré | CLI appelé | Commande |
|--------------|------------|----------|
| `mangadex`   | source-watch-goat | `latest-manga` |
| `anilist`    | source-watch-goat | `trending-anime` |
| `jikan`      | source-watch-goat | `trending-manga` |
| `github`     | github-goat | `list-repos GeekFamilyCorp` |
| `rss`        | collect_sources.py | `--type rss` |
| `rest_api`   | collect_sources.py | `--type rest_api` |
| `graphql`    | collect_sources.py | `--type graphql` |
| `web`        | collect_sources.py | `--type web` |

---

## Lien avec Temporal

Le Connector Hub complète `source_watch.workflow.ts` :
- Le workflow Temporal gère la **répétition** (sleep + signal pause/resume/stop)
- Le Connector Hub gère le **routage** (quel CLI pour quelle source)

Pour déclencher un workflow Temporal :

```bash
# (via tk CLI — une fois l'intégration Temporal câblée)
tk workflow start source_watch --project japan-alliance
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
  "connector_hub_version": "0.1.0",
  "timestamp": "2026-05-17T...",
  "total": 5,
  "dispatchable": 4,
  "sources": [
    {
      "id": "japan-alliance_source_1",
      "name": "MangaDex",
      "url": "https://api.mangadex.org",
      "type": "mangadex",
      "reliability": "high",
      "enabled": true,
      "origin": "japan-alliance",
      "dispatchable": true,
      "handler_desc": "MangaDex REST — dernières MAJ"
    }
  ]
}
```
