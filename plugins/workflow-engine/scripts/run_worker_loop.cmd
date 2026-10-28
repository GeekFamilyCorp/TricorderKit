@echo off
REM ============================================================
REM  run_worker_loop.cmd - Worker Temporal TricorderKit AU PREMIER PLAN, avec relance.
REM  A utiliser comme action de TACHE PLANIFIEE : le Planificateur arrete les processus
REM  enfants quand l'action se termine. Ce script ne rend donc jamais la main (boucle),
REM  contrairement a start_worker.cmd qui lance le worker detache puis sort.
REM  Adresse : variable TEMPORAL_ADDRESS si definie (serveur distant), sinon locale.
REM  Attente entre relances : ping (timeout echoue sans console).
REM ============================================================
setlocal
if not defined TEMPORAL_ADDRESS set "TEMPORAL_ADDRESS=localhost:7233"
if not defined TEMPORAL_NAMESPACE set "TEMPORAL_NAMESPACE=default"
if not defined TEMPORAL_TASK_QUEUE set "TEMPORAL_TASK_QUEUE=tricorderkit-hooks"
if not defined OBSIDIAN_VAULT_PATH set "OBSIDIAN_VAULT_PATH=%USERPROFILE%\Documents\obsidian\linked-project"
cd /d "%~dp0.."
:loop
if /i "%TEMPORAL_ADDRESS:~0,9%"=="localhost" python "%~dp0..\..\..\tools\caps\caps.py" ensure workflows
echo [%date% %time%] demarrage worker sur %TEMPORAL_ADDRESS%
call "%~dp0..\node_modules\.bin\ts-node.cmd" scripts/start_worker.ts
echo [%date% %time%] worker arrete (code %errorlevel%) - relance dans 30 s
ping -n 31 127.0.0.1 >nul
goto loop
