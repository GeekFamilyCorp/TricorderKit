# connector-hub — TricorderKit v0.8

> Hub d'ingestion passif multi-sources. Point d'entrée unique pour la veille multi-sources.

---

## Rôle dans l'architecture

```
sources.yaml (Japan-Alliance)  ─┐
trusted_sources.yml (core)     ─┼─► connector_hub.py ─► source-watch-goat
linked_projects.yaml (config)  ─┘                     ─► github-goat
                                                       ─► collect_sources.py
```

Le Connector Hub est le point d'entrée qui :
1. Lit toutes les déclarations sources (linked_projects + core)
2. Construit un registre unifié
3. Route chaque ingestion vers le bon CLI déterministe

---

## Quickstart

```bash
# Voir toutes les sources déclarées
python plugins/connector-hub/connector_hub.py list

# Vérifier la joignabilité
python plugins/connector-hub/connector_hub.py status

# Simuler le dispatch de toutes les sources (dry-run obligatoire en premier)
python plugins/connector-hub/connector_hub.py dispatch --all --dry-run

# Déclencher MangaDex
python plugins/connector-hub/connector_hub.py dispatch --source mangadex
```

---

## Commandes

| Commande | Description |
|----------|-------------|
| `list` | Registre unifié de toutes les sources actives |
| `list --all` | Inclut les sources désactivées |
| `status` | HTTP HEAD sur chaque source + latence |
| `dispatch --source <id>` | Ingestion d'une source par ID ou type |
| `dispatch --all` | Toutes les sources actives |
| `dispatch --dry-run` | Simulation sans subprocess |

Toutes les commandes acceptent `--format json` pour un output contractuel.

---

## Sources supportées

| Type | Handler CLI |
|------|-------------|
| `mangadex` | source-watch-goat latest-manga |
| `anilist` | source-watch-goat trending-anime |
| `jikan` | source-watch-goat trending-manga |
| `github` | github-goat list-repos |
| `rss` / `rest_api` / `graphql` / `web` | collect_sources.py |

---

## Ajouter une source

1. Éditer `<linked_project>/project_config/sources.yaml`
2. Ajouter une entrée avec le bon `type` (voir tableau ci-dessus)
3. Vérifier : `connector_hub.py list` → la source apparaît dans le registre
4. Tester : `connector_hub.py dispatch --source <id> --dry-run`

---

## Lien Temporal

Pour la veille continue, le Connector Hub alimente le workflow Temporal :

```
connector_hub dispatch --all   ←→   source_watch.workflow.ts (cycle automatique)
```

Le hub peut être appelé manuellement pour un dispatch ponctuel ;
le workflow Temporal gère la répétition périodique (cf. `interval_minutes`).

---

*TricorderKit v0.8 — connector-hub v0.1.0*
