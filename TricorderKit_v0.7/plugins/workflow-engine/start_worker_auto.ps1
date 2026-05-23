# start_worker_auto.ps1 — Relais vers TricorderKit_Project
# Ce fichier existe pour combler le chemin incorrect de la tâche planifiée "TricorderKit-Worker".
# La tâche pointe sur TricorderKit_v0.7 (chemin obsolète) ; ce script redirige vers le bon dossier.
# Pour corriger définitivement : mettre à jour la tâche via Task Scheduler (nécessite admin).

$correctScript = "C:\Users\sebas\Documents\Claude\Projects\TricorderKit Autonome\TricorderKit_Project\plugins\workflow-engine\start_worker_auto.ps1"

if (Test-Path $correctScript) {
    & $correctScript
} else {
    Write-Error "TricorderKit-Worker: script cible introuvable à $correctScript"
    exit 1
}
