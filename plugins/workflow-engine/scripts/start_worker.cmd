@echo off
REM ============================================================
REM  start_worker.cmd — Lance le Worker Temporal TricorderKit
REM  en ARRIERE-PLAN DETACHE + CACHE (aucune fenetre a fermer).
REM  Le worker SURVIT a la fermeture de toute fenetre console.
REM  Queue : tricorderkit-hooks @ localhost:7233.
REM ============================================================
set "TEMPORAL_ADDRESS=localhost:7233"
set "TEMPORAL_NAMESPACE=default"
set "TEMPORAL_TASK_QUEUE=tricorderkit-hooks"
set "OBSIDIAN_VAULT_PATH=%USERPROFILE%\Documents\obsidian\linked-project"
powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath '%~dp0..\node_modules\.bin\ts-node.cmd' -ArgumentList 'scripts/start_worker.ts' -WorkingDirectory '%~dp0..' -WindowStyle Hidden"
exit /b 0
