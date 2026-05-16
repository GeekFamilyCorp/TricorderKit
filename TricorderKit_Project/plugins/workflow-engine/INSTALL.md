# Installation — TricorderKit Workflow Engine (Temporal Worker)

> Version : 0.2.0 — Hook Layer
> Testé sur : Windows 11, Node 20, Docker Desktop 4.x

Ce guide couvre l'installation complète du Temporal Worker TricorderKit, depuis les prérequis jusqu'au démarrage automatique au login Windows.

---

## Prérequis

| Outil | Version minimale | Vérification |
|---|---|---|
| Docker Desktop | 4.x | `docker --version` |
| Docker Compose | 2.x (inclus dans Docker Desktop) | `docker compose version` |
| Node.js | 18 LTS ou 20 LTS | `node --version` |
| npm | 9+ | `npm --version` |

> **Important** : `temporalio/auto-setup` ne supporte **pas** SQLite. Le driver utilisé est `postgres12`. Ne pas changer la variable `DB` dans le `docker-compose.yml`.

---

## Étape 1 — Cloner le dépôt

```powershell
git clone https://github.com/GeekFamilyCorp/TricorderKit.git
cd TricorderKit\TricorderKit_Project
```

---

## Étape 2 — Lancer l'infrastructure Docker

Depuis le dossier `TricorderKit_Project/` :

```powershell
docker compose up -d
```

Services démarrés :

| Service | URL / Port | Rôle |
|---|---|---|
| `tricorder-neo4j` | `http://localhost:7474` | Graph Knowledge |
| `tricorder-qdrant` | `http://localhost:6333` | Vector Search |
| `tricorder-temporal-db` | port 5432 (interne) | Base Postgres de Temporal |
| `tricorder-temporal` | `localhost:7233` | Temporal Frontend (gRPC) |
| `tricorder-temporal-ui` | `http://localhost:8080` | UI Temporal |
| `tricorder-langfuse` | `http://localhost:3000` | Observabilité tokens |

Attendre que tous les healthchecks soient verts (~30 secondes) :

```powershell
docker compose ps
```

La colonne `STATUS` doit afficher `healthy` pour `temporal-db` et `running` pour `temporal`.

---

## Étape 3 — Installer les dépendances Node

```powershell
cd plugins\workflow-engine
npm install
```

---

## Étape 4 — Configurer les variables d'environnement

Définir le chemin du vault Obsidian (adapter à votre installation) :

```powershell
$env:OBSIDIAN_VAULT_PATH = "C:\Users\<votre_user>\iCloudDrive\iCloudmdobsidian\Japan-Alliance"
```

> **Note** : cette variable est requise par les activités `writeUsageStats` et `writeEvalResults` pour écrire les rapports dans Obsidian.

---

## Étape 5 — Lancer le worker manuellement (test)

```powershell
cd plugins\workflow-engine
$env:OBSIDIAN_VAULT_PATH = "C:\Users\<votre_user>\..."
npx ts-node scripts\start_worker.ts
```

Sortie attendue :

```
[TricorderKit Worker] Démarrage...
  Temporal  : localhost:7233
  Namespace : default
  TaskQueue : tricorderkit-hooks
...
[TricorderKit Worker] En attente de tâches...
    - readHookLogs
    - aggregateStats
    - writeUsageStats
    - runCliContracts
    - runEvalLabScenarios
    - writeEvalResults
Worker state changed { state: 'RUNNING' }
```

---

## Étape 6 — Démarrage automatique au login Windows (recommandé)

Le script `start_worker_auto.ps1` configure le chemin du vault et lance le worker automatiquement.

**6a. Éditer le script pour adapter votre chemin Obsidian :**

Ouvrir `plugins\workflow-engine\start_worker_auto.ps1` et remplacer la valeur de `$env:OBSIDIAN_VAULT_PATH` par votre chemin réel.

**6b. Enregistrer la tâche planifiée Windows :**

Coller dans PowerShell (pas besoin de droits admin) :

```powershell
$workerScript = "<chemin_absolu_vers_TricorderKit_Project>\plugins\workflow-engine\start_worker_auto.ps1"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -File `"$workerScript`""

$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERNAME"

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 2) `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "TricorderKit-Worker" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Démarre le Temporal Worker TricorderKit au démarrage de session Windows." `
    -RunLevel Highest `
    -Force
```

**6c. Vérifier l'enregistrement :**

```powershell
Get-ScheduledTask -TaskName "TricorderKit-Worker" | Select-Object TaskName, State
```

Résultat attendu : `State: Ready`

**6d. Tester le déclenchement :**

```powershell
Start-ScheduledTask -TaskName "TricorderKit-Worker"
```

Le worker démarre en arrière-plan. Vérifier dans le Gestionnaire des tâches → onglet "Détails" → chercher `powershell.exe`.

---

## Vérification finale

Une fois tout configuré, ouvrir l'UI Temporal pour confirmer que le worker est enregistré :

```
http://localhost:8080
```

Aller dans **Workers** → Task Queue `tricorderkit-hooks` → le worker doit apparaître avec ses 6 activités et 2 workflows enregistrés.

---

## Désinstallation

```powershell
# Supprimer la tâche planifiée
Unregister-ScheduledTask -TaskName "TricorderKit-Worker" -Confirm:$false

# Arrêter l'infrastructure Docker
docker compose down
```

---

## Troubleshooting

| Erreur | Cause probable | Solution |
|---|---|---|
| `Cannot find module 'workflows'` | `workflows/index.ts` absent | Vérifier que le fichier barrel existe dans `plugins/workflow-engine/workflows/` |
| `Connection refused localhost:7233` | Temporal non démarré | `docker compose up -d` puis attendre 30s |
| `Unsupported driver: sqlite` | Variable `DB=sqlite` dans docker-compose | Utiliser `DB=postgres12` avec le service `temporal-db` |
| `config_template.yaml not found` | Volume Docker surcharge le dossier config complet | Monter uniquement `./config/temporal/dynamicconfig` et non `./config/temporal` |
| `$env:VAR=value command` échoue | Syntaxe bash non valide en PowerShell | Utiliser `$env:VAR = "value"` sur une ligne séparée avant la commande |
| Worker démarre mais s'arrête | Terminal PowerShell fermé | Utiliser la tâche planifiée (Étape 6) ou lancer dans un terminal permanent |
