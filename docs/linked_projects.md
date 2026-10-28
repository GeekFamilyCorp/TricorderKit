# Convention linked_project — TricorderKit v0.9

> Règle fondamentale : **TricorderKit exécute. Le projet lié spécialise.**

---

## 1. Principe directeur

TricorderKit est un moteur local-first générique, anonymisé et réutilisable.

Il ne contient pas de données privées, de stratégies commerciales, de sources confidentielles ni d'automatisations métier non anonymisées.

Chaque utilisateur peut relier un second dépôt GitHub privé, appelé **linked_project**, qui contient tout ce qui est propre à son domaine.

```
TricorderKit (public)  ←→  linked_project (privé)
     moteur                  spécialisation
```

---

## 2. Séparation des responsabilités

### TricorderKit contient

```text
cli/          → entrypoints CLI génériques (tk)
core/         → hooks, mainbrain, contracts
plugins/      → modules génériques (deep-research, workflow-engine, etc.)
skills/       → skills génériques
tools/        → utilitaires et audits génériques
workflows/    → templates de workflows
mcp/          → serveurs MCP génériques
configs/      → configs locales (non versionnées) et exemples
docs/         → documentation technique
templates/    → templates linked_project
tests/        → tests unitaires et contrats
```

### linked_project contient

```text
project_config/    → project.yaml, sources.yaml
vault/             → mémoire métier Obsidian
sources/           → sources spécialisées privées
prompts/           → prompts propres au domaine
workflows/         → workflows spécialisés
skills/            → skills métier
reports/           → rapports générés
exports/           → données exportées
project_logs/      → logs projet
project_decisions/ → décisions métier
```

---

## 3. Règles d'isolation

### TricorderKit peut lire dans linked_project

```text
project_config/
workflows/
prompts/
sources/
vault/
```

### TricorderKit peut écrire dans linked_project

```text
reports/
exports/
project_logs/
```

### TricorderKit ne doit jamais écrire dans

```text
sources_originales/
archives/
private/
secrets/
```

Sauf autorisation explicite dans `project_config/project.yaml` → `execution.allow_tricorderkit_write: true`.

---

## 4. Configuration

### 4.1 Fichier de config local (non versionné)

```text
configs/local/linked_projects.yaml
```

Ce fichier contient les chemins réels de la machine. Il est dans `.gitignore`.

```yaml
tricorderkit_root: C:/Users/<user>/Documents/Projects/TricorderKit

linked_projects:
  - id: my-domain-project
    name: My Domain Project
    type: private_project
    visibility: private
    domain: your_domain_here
    github_repo: your-org/your-private-repo
    root: C:/Users/<user>/Documents/Projects/MyDomainProject
    enabled: true
    paths:
      vault: my-project_vault/
      tools: tools/
      pipelines: pipelines/
      sources: pipelines/sources/
      tests: tests/
      data: data/
      docs: docs/
      skills: skills/
      plugins: plugins/
    data_policy:
      allow_public_export: false
      allow_anonymized_reports: true
      allow_private_sources: true
    execution:
      allow_tricorderkit_write: true
      require_human_validation: true
      default_output_format: [markdown, json]
```

### 4.2 Exemple versionné

```text
configs/local/linked_projects.example.yaml
```

Fichier committé avec des chemins fictifs. Sert de référence pour créer le fichier local.

### 4.3 Fichier project.yaml dans le projet lié

```text
linked_project/project_config/project.yaml
```

Contient la configuration métier du projet : domaine, sources, policy de données, termes privés, chemins internes.

---

## 5. Communication entre les deux dépôts

La communication passe exclusivement par :

- **config** : `linked_projects.yaml`, `project.yaml`
- **CLI** : commandes `tk project *`
- **fichiers** : Markdown, JSON, YAML
- **workflows déclarés** : fichiers `.yml` dans `linked_project/workflows/`
- **connecteurs explicites** : déclarés dans `project_config/`

Le linked_project ne modifie jamais le cœur TricorderKit directement.

---

## 6. Commandes CLI

```bash
# Lister les projets liés actifs
tk project list

# État d'un projet lié
tk project status my-domain-project

# Audit complet d'un projet lié
tk project audit my-domain-project

# Scan du vault d'un projet lié
tk project vault scan my-domain-project

# Lister les workflows d'un projet lié
tk project workflow list my-domain-project

# Rapport complet
tk project report my-domain-project
```

Toutes les commandes supportent `--format json` ou `--format md`.

---

## 7. Créer un nouveau linked_project

Utiliser le template inclus dans TricorderKit :

```bash
cp -r examples/linked-project-template/ ../mon-nouveau-projet
```

Puis :
1. Remplir `project_config/project.yaml`
2. Remplir `project_config/sources.yaml`
3. Initialiser le dépôt Git et le rendre privé
4. Ajouter l'entrée dans `configs/local/linked_projects.yaml`
5. Vérifier avec `tk project status mon-nouveau-projet`

---

## 8. Audit et validation

```bash
# Audit local complet du projet lié
tk project audit my-domain-project

# Audit diff local vs GitHub
python tools/audit/local_vs_github_audit.py --project my-domain-project

# Audit structure et cohérence
python tools/audit/linked_project_audit.py --project my-domain-project
```

---

## 9. Règle de contrôle (à appliquer avant chaque action)

```
Si c'est générique, stable et réutilisable → TricorderKit
Si c'est métier, privé ou spécifique      → linked_project
Si c'est long, distant ou persistant      → VPS (optionnel)
```

---

---

## 10. Template anonyme (public-safe)

Pour créer un linked_project publiable ou partager sa structure sans données privées :

```bash
cp -r templates/linked_project_anon /path/to/new-project
```

Le template `linked_project_anon/` :
- Contient uniquement des placeholders `[PROJECT_NAME]`, `[DOMAIN]`, etc.
- Passe le scan `security-audit-cli` (aucun terme privé)
- Inclut `CLAUDE.md`, `BOOT_SUMMARY.md`, `project_config/` et toute la structure
- Est conçu pour être commité dans un repo public

Valider après substitution des placeholders :

```bash
python plugins/security-audit-cli/security_runner.py --target /path/to/new-project
```

---

*TricorderKit v0.9 — 2026-05-22*
