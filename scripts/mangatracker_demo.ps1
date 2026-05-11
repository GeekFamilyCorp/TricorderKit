# example_cli_demo.ps1 — TricorderKit v0.7
# Generic demo for your domain CLI (Windows PowerShell)
# Adapt this script to your own CLI tool installed under tools/

$ScriptDir = Split-Path -Parent $PSScriptRoot
$CLI = Join-Path $ScriptDir "tools\your-cli"

Write-Host "=== Your CLI Demo ===" -ForegroundColor Cyan
Write-Host "Directory: $CLI"
Write-Host ""

# Replace the following with your actual CLI commands
# See tools/your-cli/README.md for available commands

Write-Host "--- 1. Audit sources ---" -ForegroundColor Yellow
# python -m your_cli.cli audit sources
Write-Host "[stub] Replace with: python -m your_cli.cli audit sources"

Write-Host ""
Write-Host "--- 2. Scan new content ---" -ForegroundColor Yellow
# python -m your_cli.cli content scan-new --source your_source
Write-Host "[stub] Replace with: python -m your_cli.cli content scan-new --source your_source"

Write-Host ""
Write-Host "--- 3. Sync to Obsidian dry-run ---" -ForegroundColor Yellow
# python -m your_cli.cli sync obsidian --dry-run
Write-Host "[stub] Replace with: python -m your_cli.cli sync obsidian --dry-run"

Write-Host ""
Write-Host "=== Demo complete ===" -ForegroundColor Green
Write-Host "See tools/your-cli/README.md and docs/integration/ for full documentation."
