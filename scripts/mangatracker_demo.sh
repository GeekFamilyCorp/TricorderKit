#!/usr/bin/env bash
# example_cli_demo.sh — TricorderKit v0.7
# Generic demo for your domain CLI
# Adapt this script to your own CLI tool installed under tools/

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLI="$SCRIPT_DIR/tools/your-cli"

echo "=== Your CLI Demo ==="
echo "Directory: $CLI"
echo ""

# Replace the following with your actual CLI commands
# See tools/your-cli/README.md for available commands

echo "--- 1. Audit sources ---"
# python -m your_cli.cli audit sources
echo "[stub] Replace with: python -m your_cli.cli audit sources"

echo ""
echo "--- 2. Scan new content ---"
# python -m your_cli.cli content scan-new --source your_source
echo "[stub] Replace with: python -m your_cli.cli content scan-new --source your_source"

echo ""
echo "--- 3. Sync to Obsidian dry-run ---"
# python -m your_cli.cli sync obsidian --dry-run
echo "[stub] Replace with: python -m your_cli.cli sync obsidian --dry-run"

echo ""
echo "=== Demo complete ==="
echo "See tools/your-cli/README.md and docs/integration/ for full documentation."
