# start_worker_auto.ps1 — Lancement automatique du Temporal Worker TricorderKit
# Exécuté par la tâche planifiée Windows "TricorderKit-Worker" au démarrage de session.

$env:OBSIDIAN_VAULT_PATH = "C:\Users\sebas\iCloudDrive\iCloudmdobsidian\Japan-Alliance"

Set-Location "C:\Users\sebas\Documents\Claude\Projects\TricorderKit Autonome\TricorderKit_v0.7\plugins\workflow-engine"

npx ts-node scripts/start_worker.ts
