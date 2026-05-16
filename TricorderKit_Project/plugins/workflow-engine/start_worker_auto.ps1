# start_worker_auto.ps1 — Lancement automatique du Temporal Worker TricorderKit
# Exécuté par la tâche planifiée Windows "TricorderKit-Worker" au démarrage de session.

$env:OBSIDIAN_VAULT_PATH = "%USERPROFILE%\iCloudDrive\iCloudmdobsidian\Japan-Alliance"

Set-Location "%USERPROFILE%\Documents\Claude\Projects\TricorderKit Autonome\TricorderKit_Project\plugins\workflow-engine"

npx ts-node scripts/start_worker.ts
