#!/usr/bin/env bash
set -euo pipefail
python -m mangatracker_cli.cli manga scan-new --source shonenjumpplus --type chapter1 --output exports
python -m mangatracker_cli.cli ln scan-ranking --source syosetu --output exports
python -m mangatracker_cli.cli anime scan-news --source comic-natalie --output exports
python -m mangatracker_cli.cli audit sources
