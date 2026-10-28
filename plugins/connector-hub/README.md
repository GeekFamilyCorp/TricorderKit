# connector-hub — TricorderKit v0.8

> Hub d'ingestion passif multi-sources. Point d'entrée unique pour la veille multi-sources.

---

## Rôle dans l'architecture

```
trusted_sources.yml (core)       ─┐                     ┌► collect_sources.py (sources core)
sources.yaml (My-Domain-Project) ─┼─► connector_hub.py ─┤
linked_projects.yaml (config)    ─┘                     └► CLI déclaré par le linked_project
```

Le Connector Hub est le point d'entrée qui :
1. Lit toutes les déclarations sources (linked_projects + core)
2. Construit un registre unifié
3. Route chaque ingestion vers le bon CLI déterministe

Aucune source n'est câblée en dur dans le hub : le routage vient de
`trusted_sources.yml` (sources génériques) ou du `sources.yaml` du linked_project.

---

## Quickstart

```bash
# Voir toutes les sources déclarées
python plugins/connector-hub/connector_hub.py list

# Vérifier la joignabilité
python plugins/connector-hub/connector_hub.py status

# Simuler le dispatch de toutes les sources (dry-run obligatoire en premier)
python plugins/connector-hub/connector_hub.py dispatch --all --dry-run

# Interroger arXiv sur un sujet
python plugins/connector-hub/connector_hub.py dispatch --source "arXiv API" --query "vector databases"

# Tout le domaine « research » (arXiv, Hacker News, Wikipedia)
python plugins/connector-hub/connector_hub.py dispatch --source research --dry-run
```

---

## Commandes

| Commande | Description |
|----------|-------------|
| `list` | Registre unifié de toutes les sources actives |
| `list --all` | Inclut les sources désactivées |
| `status` | HTTP HEAD sur chaque source + latence |
| `dispatch --source <clé>` | Ingestion par id, nom, type ou domaine |
| `dispatch --query <requête>` | Requête de veille (sources core) |
| `dispatch --all` | Toutes les sources actives |
| `dispatch --dry-run` | Simulation sans subprocess |
| `dispatch --temporal` | Délègue à `source_watch.workflow.ts` via Temporal |

Toutes les commandes acceptent `--format json` pour un output contractuel.

---

## Routage

| Origine | CLI appelé |
|---------|------------|
| Core (`trusted_sources.yml`, catégorie `<d>`) | `collect_sources.py --domain <d> --sources "<nom>" --query <requête>` |
| Linked project | le bloc `dispatch:` de la source dans `project_config/sources.yaml` |

La requête d'une source core vient de `--query`, sinon du champ `watch_query`
de la source, sinon de `TK_WATCH_QUERY` (défaut : `local-first software`).

---

## Ajouter une source

**Source générique** : ajouter une entrée dans une catégorie de
`plugins/deep-research-core/sources/trusted_sources.yml` (avec un fetcher dans
`collect_sources.py` si le type est nouveau).

**Source d'un domaine privé** : l'ajouter au `sources.yaml` du linked_project
avec un bloc `dispatch:` :

```yaml
sources:
  - id: source_primary
    name: "Ma source"
    url: "https://api.example.com"
    type: rest_api
    dispatch:
      cli: scripts/collect_primary.py   # relatif à la racine du projet lié
      args: ["--since", "24h"]
```

Puis vérifier : `connector_hub.py list` (la source apparaît, `→` = dispatchable)
et `connector_hub.py dispatch --source source_primary --dry-run`.

---

## Lien Temporal

Pour la veille continue, le Connector Hub alimente le workflow Temporal :

```
connector_hub dispatch --all --temporal   →   source_watch.workflow.ts (cycle automatique)
                                              └─ scanSource → connector_hub dispatch --source <nom>
```

Le hub peut être appelé manuellement pour un dispatch ponctuel ;
le workflow Temporal gère la répétition périodique (cf. `interval_minutes`).

---

*TricorderKit v0.8 — connector-hub v0.2.0*
