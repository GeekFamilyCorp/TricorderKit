#!/usr/bin/env bash
# rtk-install.sh — installe et configure rtk pour Claude Code / Cowork.

set -euo pipefail

echo "=== Installation de rtk (Rust Token Killer) ==="

if command -v rtk >/dev/null 2>&1; then
  echo "rtk deja installe : $(rtk --version)"
else
  os="$(uname -s)"
  case "$os" in
    Darwin|Linux)
      echo "Installation via script officiel..."
      curl -fsSL https://www.rtk-ai.app/install.sh | sh
      ;;
    MINGW*|CYGWIN*|MSYS*)
      echo "Windows detecte : utiliser WSL ou installer via cargo :"
      echo "  cargo install rtk"
      exit 1
      ;;
    *)
      echo "OS non supporte : $os"
      exit 1
      ;;
  esac
fi

echo ""
echo "=== Configuration pour Claude Code ==="
rtk init -g

echo ""
echo "OK. rtk est installe et configure."
echo "Desactivation ponctuelle : RTK_OFF=1 <commande>"
echo "Desactivation globale    : rtk disable"
