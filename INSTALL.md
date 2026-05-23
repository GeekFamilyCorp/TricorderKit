# TricorderKit — Installation Guide

> Version : v0.9 | Stack : Claude Code · Temporal · Neo4j · Qdrant · Langfuse
> Commande centrale : `tk doctor` — toujours la première chose à lancer après une modification.

---

## Prérequis

| Outil | Version | Vérifier |
|---|---|---|
| Python | ≥ 3.11 | `python --version` |
| Docker Desktop | récent | `docker --version` |
| Git | any | `git --version` |
| Claude Code CLI | latest | `claude --version` |

---

## Option 1 — Guided install

Script interactif : configure l'environnement, copie `.env`, démarre Docker et valide l'installation.

```bash
python scripts/install-menu.py
# ou via make :
make install
```

---

## Option 2 — Docker

Installation minimale : infrastructure seule. Recommandée pour tester rapidement.

```bash
# 1. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env — renseigner au minimum :
#   ANTHROPIC_API_KEY, NEO4J_PASSWORD, LANGFUSE_NEXTAUTH_SECRET,
#   LANGFUSE_SALT, OBSIDIAN_VAULT_PATH

# 2. Démarrer les services
docker compose up -d

# 3. Vérifier (attendre ~30s au premier démarrage)
tk doctor
```

Services démarrés : Neo4j · Qdrant · Langfuse · Temporal.

---

## Option 3 — Local developer

Installation complète avec dépendances Python et validation.

```bash
# 1. Cloner le repo
git clone https://github.com/GeekFamilyCorp/TricorderKit.git
cd TricorderKit

# 2. Installer
make install

# 3. Valider
make doctor
```

> `Makefile` — à venir. Équivalent manuel :
> ```bash
> cp .env.example .env          # puis éditer .env
> pip install requests httpx rich pyyaml qdrant-client temporalio feedparser
> docker compose up -d
> python cli/tk.py doctor
> ```

### Ports exposés

| Service | Port | URL |
|---|---|---|
| Neo4j Browser | 7474 | http://localhost:7474 |
| Neo4j Bolt | 7687 | bolt://localhost:7687 |
| Qdrant | 6333 | http://localhost:6333 |
| Langfuse | 3001 | http://localhost:3001 ⚠️ pas 3000 |
| Temporal UI | 8080 | http://localhost:8080 |

---

## Configure a private linked project

Connecter un projet privé à TricorderKit en 3 étapes.

```bash
# 1. Copier le template public anonymisé
cp -r examples/linked-project-template/ /path/to/my-project/.tricorderkit/

# 2. Renseigner les valeurs réelles (fichiers sans .example)
cd /path/to/my-project/.tricorderkit/
cp project.config.example.yaml project.config.yaml
cp .env.example .env
# Éditer project.config.yaml et .env

# 3. Déclarer dans TricorderKit
cp configs/local/linked_projects.example.yaml configs/local/linked_projects.yaml
# Ajouter votre projet dans linked_projects.yaml

make setup-linked-project
```

> `make setup-linked-project` — à venir. Équivalent manuel :
> ```bash
> python cli/tk.py project status your-project-id
> python cli/tk.py project audit your-project-id
> ```

Voir `examples/linked-project-template/README.md` pour la structure complète
et `examples/linked-project-template/README_PRIVACY.md` pour les règles d'anonymisation.

---

## Verify

```bash
tk doctor
```

Sortie attendue après une installation complète :

```
[OK]    Python 3.x.x
[OK]    Docker running
[OK]    Neo4j :7474
[OK]    Qdrant :6333
[OK]    Langfuse :3001
[OK]    Temporal :7233
[OK]    .env présent
[OK]    Dossier plugins/
[OK]    Dossier skills/
[OK]    Dossier reports/
[WARN]  Dossier memory/  — memory/ absent    ← normal si non créé
[OK]    Modules détectés : 10
[OK]    Linked projects : 1
[OK]    Aucun secret dans le repo
```

Format JSON (intégration CI) :

```bash
tk doctor --format json
```

---

## Run security checks

```bash
# Scan de sécurité complet du projet lié
tk security scan

# Vérification secrets uniquement
tk doctor --secrets
```

> `tk security scan` et `tk doctor --secrets` — à venir.
> Actuellement, `tk doctor` inclut la vérification des secrets dans sa sortie standard.

---

## Troubleshooting

Voir [docs/troubleshooting.md](docs/troubleshooting.md) pour le guide complet.

### Raccourcis courants

**Docker services ne démarrent pas**
```bash
docker compose logs neo4j
docker compose logs qdrant
docker compose restart
```
Sur Windows : Langfuse utilise le port **3001** (3000 occupé par Docker Desktop).

**`tk doctor` affiche `[FAIL] Docker running`**
```bash
# Vérifier que Docker Desktop est lancé
docker ps
```

**`tk doctor` affiche `[WARN] Dossier memory/`**
```bash
mkdir memory
```

**`tk doctor` signale un secret dans le repo**
```bash
# Identifier le fichier
git grep -n "ANTHROPIC_API_KEY=" -- ":!.env" ":!.env.example" ":!*.md" ":!cli/tk.py"
# Si vrai secret : révoquer la clé immédiatement, puis :
git log -p --all -S "sk-ant-" --follow -- .
```

**Python < 3.11**
```bash
# Windows : installer depuis python.org
# macOS
brew install python@3.12
```

**Dépendance manquante**
```bash
pip install qdrant-client temporalio httpx rich pyyaml
```

---

*TricorderKit v0.9 — 2026-05-22*
