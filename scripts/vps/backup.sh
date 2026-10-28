#!/usr/bin/env bash
# backup.sh — Sauvegarde VPS via Borg (TricorderKit v1.0, DEC-046 Phase 1 / N4)
#
# Sauvegarde idempotente des données critiques (volumes Docker exportés, configs,
# staging veille) dans un dépôt Borg chiffré. Exécution SUR le VPS.
#
# Aucun secret en dur (frontière publique + DEC-039) : tout vient de l'environnement.
#   BORG_REPO         : chemin/URL du dépôt Borg (REQUIS)            ex. /srv/borg/tricorderkit
#   BORG_PASSPHRASE   : passphrase du dépôt (REQUIS, jamais loguée)  -> Credential Manager / env
#   BACKUP_SOURCES    : chemins à sauvegarder, séparés par espace (REQUIS)
#   BACKUP_PREFIX     : préfixe d'archive (défaut: tkit)
#   BORG_KEEP_DAILY   : rétention quotidienne (défaut 7)
#   BORG_KEEP_WEEKLY  : rétention hebdo (défaut 4)
#   BACKUP_DRY_RUN=1  : simulation (défaut) ; mettre 0 pour exécuter réellement
#
# Exit 0 si OK, 1 si échec, 2 si environnement/paramètres invalides.
set -uo pipefail

DRY="${BACKUP_DRY_RUN:-1}"   # dry-run PAR DÉFAUT (Règle 4)
PREFIX="${BACKUP_PREFIX:-tkit}"
KEEP_DAILY="${BORG_KEEP_DAILY:-7}"
KEEP_WEEKLY="${BORG_KEEP_WEEKLY:-4}"

die() { printf '  [ERR] %s\n' "$1" >&2; exit "${2:-2}"; }

command -v borg >/dev/null 2>&1 || die "borg absent (apt install borgbackup)" 2
[ -n "${BORG_REPO:-}" ]        || die "BORG_REPO non défini" 2
[ -n "${BORG_PASSPHRASE:-}" ]  || die "BORG_PASSPHRASE non défini (ne JAMAIS coder en dur)" 2
[ -n "${BACKUP_SOURCES:-}" ]   || die "BACKUP_SOURCES non défini" 2

export BORG_REPO BORG_PASSPHRASE
export BORG_RELOCATED_REPO_ACCESS_IS_OK=no

# Vérifie les sources
for src in $BACKUP_SOURCES; do
  [ -e "$src" ] || die "source introuvable : $src" 2
done

# Initialise le dépôt si absent (idempotent)
if ! borg info >/dev/null 2>&1; then
  echo "  [..] dépôt Borg absent -> init (repokey-blake2)"
  if [ "$DRY" = "1" ]; then
    echo "  [DRY] borg init --encryption=repokey-blake2 \$BORG_REPO"
  else
    borg init --encryption=repokey-blake2 || die "échec borg init" 1
  fi
fi

ARCHIVE="${PREFIX}-$(date -u +%Y%m%dT%H%M%SZ)"
echo "=== backup -> ${BORG_REPO}::${ARCHIVE} (dry_run=${DRY}) ==="

CREATE_OPTS=(--stats --compression zstd,6 --exclude-caches)
[ "$DRY" = "1" ] && CREATE_OPTS+=(--dry-run --list)

# shellcheck disable=SC2086
if borg create "${CREATE_OPTS[@]}" "::${ARCHIVE}" $BACKUP_SOURCES; then
  echo "  [OK] create terminé"
else
  die "échec borg create" 1
fi

# Rétention (prune) — seulement en exécution réelle
if [ "$DRY" = "1" ]; then
  echo "  [DRY] borg prune -d ${KEEP_DAILY} -w ${KEEP_WEEKLY} --prefix ${PREFIX}-"
else
  borg prune --glob-archives "${PREFIX}-*" \
    --keep-daily "$KEEP_DAILY" --keep-weekly "$KEEP_WEEKLY" --stats \
    || die "échec borg prune" 1
  borg compact || true
fi

echo "  [OK] backup terminé (archive=${ARCHIVE})"
