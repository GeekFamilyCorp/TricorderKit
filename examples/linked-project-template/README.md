# linked-project-template — TricorderKit

> Template public anonymisé pour connecter un projet privé à TricorderKit.
> Aucune donnée réelle — tous les noms, chemins et clés sont des placeholders.

---

## Qu'est-ce qu'un linked project ?

Un **linked project** est un projet privé externe que TricorderKit peut piloter :
enrichissement de vault Obsidian, pipelines de recherche, workflows Temporal,
audits de sécurité. TricorderKit exécute — le projet lié spécialise.

```
TricorderKit/           ← moteur générique (ce repo)
sample-linked-project/  ← projet privé spécialisé (votre repo)
```

---

## Fichiers de ce template

| Fichier | Rôle |
|---|---|
| `project.config.example.yaml` | Configuration principale du projet lié |
| `sources.example.yaml` | Sources de données (RSS, APIs, scraping) |
| `workflows.example.yaml` | Workflows Temporal déclenchables depuis TricorderKit |
| `skills.example.yaml` | Skills exposés au moteur TricorderKit |
| `.env.example` | Variables d'environnement propres au projet lié |
| `README_PRIVACY.md` | Règles d'anonymisation avant tout partage public |

---

## Démarrage rapide

```bash
# 1. Copier le template dans votre projet privé
cp -r examples/linked-project-template/ /path/to/your/project/.tricorderkit/

# 2. Renommer les fichiers (retirer .example)
cd /path/to/your/project/.tricorderkit/
cp project.config.example.yaml project.config.yaml
cp sources.example.yaml sources.yaml
cp workflows.example.yaml workflows.yaml
cp skills.example.yaml skills.yaml
cp .env.example .env

# 3. Renseigner les valeurs réelles dans chaque fichier (sans .example)
# 4. Ajouter les fichiers sans .example au .gitignore de votre projet

# 5. Déclarer le projet dans TricorderKit
# Éditer configs/local/linked_projects.yaml (voir linked_projects.example.yaml)

# 6. Vérifier la connexion
python cli/tk.py project status sample-linked-project
```

---

## Règles de nommage

| Placeholder | Remplacer par |
|---|---|
| `sample-linked-project` | Identifiant unique de votre projet (`mon-projet`) |
| `/path/to/private/vault` | Chemin absolu vers votre vault Obsidian |
| `/path/to/your/project` | Chemin absolu vers la racine de votre projet |
| `your_*_here` | Valeur réelle de la variable |

---

## Sécurité

- Les fichiers **sans** `.example` ne doivent jamais être versionnés.
- Ajouter au `.gitignore` du projet lié :
  ```
  .tricorderkit/project.config.yaml
  .tricorderkit/sources.yaml
  .tricorderkit/workflows.yaml
  .tricorderkit/skills.yaml
  .tricorderkit/.env
  ```
- Lire `README_PRIVACY.md` avant tout push ou partage.

---

*TricorderKit v0.9 — template public anonymisé*
