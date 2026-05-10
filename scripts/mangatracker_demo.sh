#!/usr/bin/env bash
# mangatracker_demo.sh — TricorderKit v0.7
# Démo rapide des commandes mangatracker-cli

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLI="$SCRIPT_DIR/tools/mangatracker-cli"

echo "=== MangaTracker CLI Demo ==="
echo "Répertoire : $CLI"
echo ""

cd "$CLI"

echo "--- 1. Audit sources ---"
python -m mangatracker_cli.cli audit sources

echo ""
echo "--- 2. Manga scan-new (Shonen Jump+) ---"
python -m mangatracker_cli.cli manga scan-new --source shonenjumpplus --type chapter1

echo ""
echo "--- 3. LN scan-ranking (Syosetu) ---"
python -m mangatracker_cli.cli ln scan-ranking --source syosetu --format json

echo ""
echo "--- 4. Anime scan-news (Comic Natalie) ---"
python -m mangatracker_cli.cli anime scan-news --source comic-natalie

echo ""
echo "--- 5. Sync Obsidian dry-run ---"
python -m mangatracker_cli.cli sync obsidian --dry-run

echo ""
echo "=== Demo terminée ==="
