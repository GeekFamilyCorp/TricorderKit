@echo off
REM ============================================================
REM  start_worker.cmd — Lance le Worker Temporal TricorderKit
REM  en ARRIERE-PLAN DETACHE + CACHE (aucune fenetre a fermer).
REM  Le worker SURVIT a la fermeture de toute fenetre console.
REM  Queue : tricorderkit-hooks @ localhost:7233.
REM ============================================================
REM Adresse Temporal : variable d'environnement si definie (ex. serveur distant), sinon locale.
if not defined TEMPORAL_ADDRESS set "TEMPORAL_ADDRESS=localhost:7233"
set "TEMPORAL_NAMESPACE=default"
set "TEMPORAL_TASK_QUEUE=tricorderkit-hooks"
set "OBSIDIAN_VAULT_PATH=%USERPROFILE%\Documents\obsidian\linked-project"
REM Contrat preflight : monter la capacite workflows (Temporal) AVANT le worker.
REM Sans cela, a l'ouverture de session, le worker meurt si Temporal n'est pas pret.
if /i not "%TEMPORAL_ADDRESS:~0,9%"=="localhost" goto :launch
python "%~dp0..\..\..\tools\caps\caps.py" ensure workflows
if errorlevel 1 (
  echo [start_worker] Temporal indisponible ^(Docker Desktop demarre ?^) - worker non lance
  exit /b 1
)
:launch
powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath '%~dp0..\node_modules\.bin\ts-node.cmd' -ArgumentList 'scripts/start_worker.ts' -WorkingDirectory '%~dp0..' -WindowStyle Hidden"
exit /b 0
