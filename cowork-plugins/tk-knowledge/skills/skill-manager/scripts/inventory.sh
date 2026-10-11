#!/bin/sh
# inventory.sh — inventaire multi-racines des SKILL.md (skill-manager, gfc-ops)
# POSIX sh. Lecture seule. Aucun chemin en dur : les racines derivent de $HOME
# (ou de la variable SKILL_ROOTS), les anciennes surfaces sont tentees en repli.
#
# Usage :
#   sh inventory.sh                      # racines par defaut sous $HOME/.claude + replis
#   sh inventory.sh /chemin/.claude      # base explicite (remplace $HOME/.claude)
#   SKILL_ROOTS="/a /b" sh inventory.sh  # liste de racines explicites (globs autorises)
#   sh inventory.sh --tsv                # sortie tabulee (sans mise en forme)
#
# Colonnes : nom | racine | lignes | mots | frontmatter (OK/KO:cles) | chemins en dur (n)
#
# Frontmatter : cles autorisees = name description license allowed-tools metadata compatibility
#   (meme liste que quick_validate.py du skill Anthropic skill-creator). Toute autre cle
#   de premier niveau (version, author, created, updated, domain, activation...) => KO.
# Chemins en dur : /sessions/<id>/, C:\Users\<nom>\, /home/<nom>/, /Users/<nom>/ dans le corps.

FORMAT=pretty
BASE=""
for a in "$@"; do
  case "$a" in
    --tsv) FORMAT=tsv ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) BASE="$a" ;;
  esac
done
[ -z "$BASE" ] && BASE="${HOME:-/root}/.claude"

# --- Racines candidates ------------------------------------------------------
# Format : "<label>|<glob de SKILL.md>"
if [ -n "$SKILL_ROOTS" ]; then
  ROOTS=""
  for r in $SKILL_ROOTS; do ROOTS="$ROOTS custom|$r/*/SKILL.md custom|$r/*/skills/*/SKILL.md"; done
else
  ROOTS="\
skills-synced|$BASE/skills/synced/*/*/SKILL.md \
skills-local|$BASE/skills/*/SKILL.md \
plugins-synced|$BASE/plugins/synced/*/*/skills/*/SKILL.md \
plugins-local|$BASE/plugins/*/skills/*/SKILL.md \
mnt-skills|/mnt/skills/*/*/SKILL.md \
session-mnt|/sessions/*/mnt/.claude/skills/*/SKILL.md \
session-plugins|/sessions/*/mnt/.remote-plugins/*/skills/*/SKILL.md"
fi

# disable-model-invocation : cle Claude Code valide (skills manuels), toleree ici bien que
# quick_validate.py (Skills API / claude.ai) la rejette — voir A_TRANCHER dans le SKILL.md.
ALLOWED=" name description license allowed-tools metadata compatibility disable-model-invocation "

# --- Analyse d'un SKILL.md ---------------------------------------------------
# Sortie : name<TAB>root<TAB>lines<TAB>words<TAB>fm<TAB>hardpaths
analyze() {
  f="$1"; label="$2"
  lines=$(wc -l < "$f" | tr -d ' ')
  words=$(wc -w < "$f" | tr -d ' ')
  # Frontmatter : bloc entre la 1re ligne '---' et la suivante
  # (tolerant aux fins de ligne CRLF : le \r est retire avant analyse)
  fm=$(awk '{sub(/\r$/,"")} NR==1 && $0!="---"{exit} NR==1{next} /^---[ \t]*$/{exit} {print}' "$f")
  if [ -z "$fm" ]; then
    name=$(basename "$(dirname "$f")"); fmstatus="KO:absent"
  else
    name=$(printf '%s\n' "$fm" | awk -F': *' '/^name:/{print $2; exit}' | tr -d '"'"'")
    [ -z "$name" ] && name=$(basename "$(dirname "$f")")
    # cles de premier niveau = lignes commencant en colonne 0 par un identifiant suivi de ':'
    keys=$(printf '%s\n' "$fm" | awk '/^[A-Za-z][A-Za-z0-9_-]*:/{sub(":.*",""); print}')
    bad=""
    for k in $keys; do
      case "$ALLOWED" in *" $k "*) ;; *) bad="$bad$k,";; esac
    done
    if [ -z "$bad" ]; then fmstatus="OK"; else fmstatus="KO:${bad%,}"; fi
    printf '%s\n' "$fm" | grep -q '^description:' || fmstatus="$fmstatus,no-description"
  fi
  # Chemins en dur (corps + frontmatter)
  hard=$(grep -c -E '(/sessions/[A-Za-z0-9_-]+/|[A-Za-z]:\\Users\\[A-Za-z0-9_.-]+\\|/home/[A-Za-z0-9_.-]+/|/Users/[A-Za-z0-9_.-]+/)' "$f" 2>/dev/null || true)
  [ -z "$hard" ] && hard=0
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$name" "$label" "$lines" "$words" "$fmstatus" "$hard"
}

# --- Parcours ----------------------------------------------------------------
TMP="${TMPDIR:-/tmp}/inventory.$$"
: > "$TMP"
trap 'rm -f "$TMP"' EXIT INT TERM
seen_roots=""
for entry in $ROOTS; do
  label=${entry%%|*}; glob=${entry#*|}
  for f in $glob; do
    [ -f "$f" ] || continue
    case "$seen_roots" in *"[$label]"*) ;; *) seen_roots="$seen_roots[$label]";; esac
    analyze "$f" "$label" >> "$TMP"
  done
done

total=$(wc -l < "$TMP" | tr -d ' ')
ko=$(awk -F'\t' '$5 ~ /^KO/' "$TMP" | wc -l | tr -d ' ')
hp=$(awk -F'\t' '$6 > 0' "$TMP" | wc -l | tr -d ' ')
over=$(awk -F'\t' '$3 > 500' "$TMP" | wc -l | tr -d ' ')

if [ "$FORMAT" = tsv ]; then
  printf 'name\troot\tlines\twords\tfrontmatter\thardpaths\n'
  sort "$TMP"
else
  printf '# Inventaire skills — base=%s — racines trouvees : %s\n' "$BASE" "${seen_roots:-aucune}"
  printf '| nom | racine | lignes | mots | frontmatter | chemins en dur |\n|---|---|---|---|---|---|\n'
  sort "$TMP" | awk -F'\t' '{printf "| %s | %s | %s | %s | %s | %s |\n",$1,$2,$3,$4,$5,$6}'
  printf '\nTotal : %s skills · frontmatter KO : %s · chemins en dur : %s · > 500 lignes : %s\n' "$total" "$ko" "$hp" "$over"
fi
[ "$total" -gt 0 ] || { echo "Aucun SKILL.md trouve (base=$BASE). Passer une base ou SKILL_ROOTS." >&2; exit 1; }
exit 0
