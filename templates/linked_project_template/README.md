# [PROJECT_NAME] — linked_project TricorderKit

> Projet privé spécialisé branché sur TricorderKit.
> Domaine : [DOMAIN]

---

## Usage

Ce dépôt est un **linked_project** : il contient les données métier, sources et workflows
spécialisés pour le domaine `[DOMAIN]`. Le moteur d'exécution reste TricorderKit.

## Structure

```text
[PROJECT_NAME]/
├── project_config/
│   ├── project.yaml      ← configuration métier principale
│   └── sources.yaml      ← sources spécialisées
├── vault/                ← mémoire Obsidian du projet
├── sources/              ← sources brutes et datasets
├── prompts/              ← prompts propres au domaine
├── workflows/            ← workflows spécialisés
├── skills/               ← skills métier
├── reports/              ← rapports générés par TricorderKit
├── exports/              ← données exportées
├── project_logs/         ← logs d'exécution
└── project_decisions/    ← décisions métier et architecture
```

## Connexion à TricorderKit

Déclarer ce projet dans :

```text
TricorderKit/configs/local/linked_projects.yaml
```

Puis vérifier :

```bash
tk project status [PROJECT_ID]
tk project audit [PROJECT_ID]
```

## Règle fondamentale

```
TricorderKit exécute. Ce projet spécialise.
```

Ce dépôt ne modifie jamais le cœur TricorderKit.
La communication passe par config, CLI, fichiers Markdown/JSON/YAML et workflows déclarés.

---

*Template TricorderKit v0.8*
