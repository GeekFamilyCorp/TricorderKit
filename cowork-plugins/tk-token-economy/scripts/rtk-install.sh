#!/usr/bin/env bash
# rtk-install.sh — installe rtk (Rust Token Killer) de façon ÉPINGLÉE.
#
# Deux voies, jamais de `curl | sh` :
#   1. cargo install rtk --version <RTK_VERSION>           (si Rust est présent)
#   2. binaire de release épinglé + vérification SHA-256   (sinon)
#
# Ce script N'EXÉCUTE PAS `rtk init -g` : le plugin fournit déjà son propre hook
# PreToolUse (hooks/hooks.json -> scripts/rtk-rewrite.sh). Deux mécanismes de hook
# sur les mêmes commandes se marcheraient dessus.
#
# À épingler avant usage (R53 : rien n'est installé sans GO explicite) :
RTK_VERSION="${RTK_VERSION:-<VERSION_A_EPINGLER>}"
# SHA-256 attendus du binaire de release, par plateforme (à remplir depuis la page
# de release https://github.com/rtk-ai/rtk/releases/tag/v${RTK_VERSION}) :
RTK_SHA256_LINUX_X86_64="${RTK_SHA256_LINUX_X86_64:-<SHA256_A_EPINGLER>}"
RTK_SHA256_DARWIN_ARM64="${RTK_SHA256_DARWIN_ARM64:-<SHA256_A_EPINGLER>}"

set -euo pipefail

if command -v rtk >/dev/null 2>&1; then
  echo "rtk déjà installé : $(rtk --version 2>/dev/null || echo '?')"
  exit 0
fi

if [[ "$RTK_VERSION" == "<VERSION_A_EPINGLER>" ]]; then
  echo "Version rtk non épinglée : renseigner RTK_VERSION (et les SHA-256) avant d'installer." >&2
  exit 2
fi

# Voie 1 : cargo, version épinglée (source auditable, pas de binaire tiers)
if command -v cargo >/dev/null 2>&1; then
  echo "Installation via cargo (rtk ${RTK_VERSION})..."
  cargo install rtk --version "${RTK_VERSION}" --locked
  echo "OK. Ne PAS lancer 'rtk init -g' : le hook du plugin s'en charge."
  exit 0
fi

# Voie 2 : binaire de release épinglé + checksum
os="$(uname -s)"; arch="$(uname -m)"
case "${os}-${arch}" in
  Linux-x86_64)  asset="rtk-x86_64-unknown-linux-gnu.tar.gz"; sha="$RTK_SHA256_LINUX_X86_64" ;;
  Darwin-arm64)  asset="rtk-aarch64-apple-darwin.tar.gz";     sha="$RTK_SHA256_DARWIN_ARM64" ;;
  MINGW*|CYGWIN*|MSYS*) echo "Windows : utiliser WSL ou 'cargo install rtk --version ${RTK_VERSION}'." >&2; exit 1 ;;
  *) echo "Plateforme non couverte : ${os}-${arch}. Passer par cargo." >&2; exit 1 ;;
esac

if [[ "$sha" == "<SHA256_A_EPINGLER>" ]]; then
  echo "SHA-256 non renseigné pour ${asset} : refus d'installer un binaire non vérifié." >&2
  exit 2
fi

url="https://github.com/rtk-ai/rtk/releases/download/v${RTK_VERSION}/${asset}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
echo "Téléchargement ${url}"
curl -fsSL -o "${tmp}/${asset}" "$url"
echo "${sha}  ${tmp}/${asset}" | sha256sum -c - || { echo "Checksum INVALIDE : abandon." >&2; exit 3; }
tar -xzf "${tmp}/${asset}" -C "$tmp"
install -m 0755 "${tmp}/rtk" "${HOME}/.local/bin/rtk"
echo "OK : rtk ${RTK_VERSION} installé dans ~/.local/bin (vérifier que ce dossier est dans PATH)."
echo "Ne PAS lancer 'rtk init -g' : le hook du plugin (hooks/hooks.json) s'en charge."
echo "Bypass ponctuel : RTK_OFF=1 <commande>"
