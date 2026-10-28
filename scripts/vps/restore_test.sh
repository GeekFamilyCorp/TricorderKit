#!/usr/bin/env bash
# restore_test.sh — Test de restauration Borg (TricorderKit v1.0, DEC-046 Phase 1 / N4)
#
# Vérifie qu'une sauvegarde est RÉELLEMENT restaurable : extrait la dernière
# archive dans un répertoire temporaire jetable, contrôle la présence de
# fichiers-témoins, puis nettoie. NE TOUCHE JAMAIS aux données live.
# Critère « reboot sans perte » du plan v1.0 (Phase 1).
#
# Aucun secret en dur (frontière publique) : tout vient de l'environnement.
#   BORG_REPO        : dépôt Borg (REQUIS)
#   BORG_PASSPHRASE  : passphrase (REQUIS, jamais loguée)
#   RESTORE_EXPECT   : motifs-témoins attendus dans l'archive, séparés par espace
#                      (optionnel ; si absent, on vérifie seulement la non-vacuité)
#   RESTORE_KEEP=1   : conserver le répertoire extrait (debug) au lieu de nettoyer
#
# Exit 0 si la restauration est validée, 1 si échec, 2 si environnement invalide.
set -uo pipefail

die() { printf '  [ERR] %s\n' "$1" >&2; exit "${2:-2}"; }

command -v borg >/dev/null 2>&1 || die "borg absent" 2
[ -n "${BORG_REPO:-}" ]       || die "BORG_REPO non défini" 2
[ -n "${BORG_PASSPHRASE:-}" ] || die "BORG_PASSPHRASE non défini" 2
export BORG_REPO BORG_PASSPHRASE

LATEST=$(borg list --last 1 --short 2>/dev/null) || die "borg list a échoué" 1
[ -n "$LATEST" ] || die "aucune archive dans le dépôt" 1
echo "=== restore_test — archive=${LATEST} ==="

WORK=$(mktemp -d "${TMPDIR:-/tmp}/tkit_restore.XXXXXX") || die "mktemp a échoué" 1
cleanup() { [ "${RESTORE_KEEP:-0}" = "1" ] || rm -rf "$WORK"; }
trap cleanup EXIT

echo "  [..] extraction vers ${WORK}"
( cd "$WORK" && borg extract --strip-components 0 "::${LATEST}" ) \
  || die "échec borg extract" 1

filecount=$(find "$WORK" -type f | wc -l | tr -d ' ')
[ "$filecount" -gt 0 ] || die "archive extraite vide" 1
echo "  [OK] ${filecount} fichier(s) restauré(s)"

MISSING=0
if [ -n "${RESTORE_EXPECT:-}" ]; then
  for pat in $RESTORE_EXPECT; do
    if find "$WORK" -path "*${pat}*" -print -quit | grep -q .; then
      echo "  [OK] témoin présent : ${pat}"
    else
      echo "  [FAIL] témoin absent : ${pat}"
      MISSING=$((MISSING+1))
    fi
  done
fi

# Intégrité du dépôt (rapide)
if borg check --archives-only --last 1 >/dev/null 2>&1; then
  echo "  [OK] borg check (dernière archive) — intègre"
else
  echo "  [WARN] borg check a signalé un problème (à investiguer)"
fi

if [ "$MISSING" -eq 0 ]; then
  echo "  [OK] restauration VALIDÉE"
  exit 0
else
  die "${MISSING} témoin(s) manquant(s) — restauration NON validée" 1
fi
