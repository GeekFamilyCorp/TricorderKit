# mangatracker_demo.ps1 — TricorderKit v0.7
# Démo rapide des commandes mangatracker-cli (Windows PowerShell)

$ScriptDir = Split-Path -Parent $PSScriptRoot
$CLI = Join-Path $ScriptDir "tools\mangatracker-cli"

Write-Host "=== MangaTracker CLI Demo ===" -ForegroundColor Cyan
Write-Host "Répertoire : $CLI"
Write-Host ""

Push-Location $CLI

Write-Host "--- 1. Audit sources ---" -ForegroundColor Yellow
python -m mangatracker_cli.cli audit sources

Write-Host ""
Write-Host "--- 2. Manga scan-new (Shonen Jump+) ---" -ForegroundColor Yellow
python -m mangatracker_cli.cli manga scan-new --source shonenjumpplus --type chapter1

Write-Host ""
Write-Host "--- 3. LN scan-ranking (Syosetu) ---" -ForegroundColor Yellow
python -m mangatracker_cli.cli ln scan-ranking --source syosetu --format json

Write-Host ""
Write-Host "--- 4. Anime scan-news (Comic Natalie) ---" -ForegroundColor Yellow
python -m mangatracker_cli.cli anime scan-news --source comic-natalie

Write-Host ""
Write-Host "--- 5. Sync Obsidian dry-run ---" -ForegroundColor Yellow
python -m mangatracker_cli.cli sync obsidian --dry-run

Pop-Location
Write-Host ""
Write-Host "=== Demo terminée ===" -ForegroundColor Green
