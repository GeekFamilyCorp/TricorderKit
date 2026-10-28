#!/usr/bin/env bash
# rtk-rewrite.sh — hook PreToolUse qui prefixe les commandes dev par `rtk`
# si le binaire est installe et si RTK_OFF n'est pas defini.
#
# Appele avec le JSON du tool-call sur stdin, renvoie un JSON potentiellement modifie.

set -euo pipefail

# Si rtk absent ou desactive, pas de reecriture : passer le payload tel quel
if ! command -v rtk >/dev/null 2>&1; then
  cat
  exit 0
fi

if [[ "${RTK_OFF:-0}" == "1" ]]; then
  cat
  exit 0
fi

# Lire le payload JSON
payload="$(cat)"

# Extraire la commande (jq optionnel)
if ! command -v jq >/dev/null 2>&1; then
  echo "$payload"
  exit 0
fi

cmd=$(echo "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null || echo "")

if [[ -z "$cmd" ]]; then
  echo "$payload"
  exit 0
fi

# Liste des binaires supportes par rtk (extrait, cf `rtk list-commands`)
supported_bins=( git gh npm yarn pnpm docker kubectl pytest jest cargo go make eslint ruff clippy )

first_word=$(echo "$cmd" | awk '{print $1}')
prefix=""
for b in "${supported_bins[@]}"; do
  if [[ "$first_word" == "$b" ]]; then
    prefix="rtk "
    break
  fi
done

if [[ -z "$prefix" ]]; then
  echo "$payload"
  exit 0
fi

# Remplacer la commande dans le JSON
new_cmd="${prefix}${cmd}"
echo "$payload" | jq --arg c "$new_cmd" '.tool_input.command = $c'
