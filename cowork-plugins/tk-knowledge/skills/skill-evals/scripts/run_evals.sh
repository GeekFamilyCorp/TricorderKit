#!/bin/sh
# run_evals.sh — lance les evals d'UN skill via les scripts de skill-creator (POSIX sh).
#
# Usage :
#   sh run_evals.sh <dossier-du-skill> [--evals <dossier-evals>] [--model <alias|id>]
#                   [--workspace <dir>] [--known-skills a,b] [--ignore-refs a,b] [--static-only]
#
#   <dossier-du-skill>  dossier contenant SKILL.md (ex. …/tricorderkit-skills/skills/code-corrector)
#   --evals             dossier contenant evals.json / triggers.json
#                       (défaut : <ce skill>/evals/<name> puis <dossier-du-skill>/evals)
#   --model             modèle passé à run_eval.py (défaut : celui de la session, cf. claude -p)
#   --workspace         dossier de résultats (défaut : <dossier-du-skill>-workspace/evals-<date>)
#   --static-only       ne lance que les contrôles déterministes (aucun appel LLM)
#
# Variables : SKILL_CREATOR_ROOT (chemin de skill-creator si non trouvé automatiquement)
#             PLUGINS_ROOT (racine des plugins pour vérifier les renvois → skill ; défaut : 4-5 niveaux au-dessus)
#             CLAUDE_PLUGIN_ROOT (racine du plugin tk-knowledge, posée par Cowork/Claude Code)
#
# Étapes : 1) check_static.py  2) quick_validate.py  3) run_eval.py sur triggers.json
#          4) rappel des commandes pour les cas qualité (sous-agents + grader + aggregate + viewer)
# Code retour : 0 si toutes les étapes lancées passent, 1 sinon, 2 si prérequis absent.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
SKILL_DIR=""
EVALS_DIR=""
MODEL=""
WORKSPACE=""
KNOWN=""
IGNORE=""
STATIC_ONLY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --evals) EVALS_DIR="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --known-skills) KNOWN="$2"; shift 2 ;;
    --ignore-refs) IGNORE="$2"; shift 2 ;;
    --static-only) STATIC_ONLY=1; shift ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) if [ -z "$SKILL_DIR" ]; then SKILL_DIR="$1"; else echo "argument inconnu : $1" >&2; exit 2; fi; shift ;;
  esac
done

[ -n "$SKILL_DIR" ] || { echo "usage : sh run_evals.sh <dossier-du-skill> [options]" >&2; exit 2; }
[ -f "$SKILL_DIR/SKILL.md" ] || { echo "SKILL.md introuvable dans $SKILL_DIR" >&2; exit 2; }
SKILL_DIR=$(cd "$SKILL_DIR" && pwd)
NAME=$(sed -n 's/^name:[[:space:]]*//p' "$SKILL_DIR/SKILL.md" | head -n 1 | tr -d '"'"'")
[ -n "$NAME" ] || NAME=$(basename "$SKILL_DIR")

# ---- localiser les evals
if [ -z "$EVALS_DIR" ]; then
  for c in "$HERE/../evals/$NAME" "$SKILL_DIR/evals"; do
    [ -f "$c/evals.json" ] && { EVALS_DIR=$(cd "$c" && pwd); break; }
  done
fi
[ -n "$EVALS_DIR" ] || { echo "aucun evals.json pour $NAME (cherché : $HERE/../evals/$NAME, $SKILL_DIR/evals)" >&2; exit 2; }

# ---- localiser skill-creator
find_skill_creator() {
  [ -n "${SKILL_CREATOR_ROOT:-}" ] && [ -f "$SKILL_CREATOR_ROOT/scripts/run_eval.py" ] && { echo "$SKILL_CREATOR_ROOT"; return; }
  for c in \
    "${CLAUDE_PLUGIN_ROOT:-/nonexistent}/../standalone/skill-creator" \
    "${CLAUDE_PLUGIN_ROOT:-/nonexistent}/../../standalone/skill-creator" \
    "$HERE/../../../../standalone/skill-creator" \
    "$HOME"/.claude/skills/synced/*/skill-creator \
    "$HOME"/.claude/plugins/synced/*/skill-creator \
    "$HOME"/.claude/plugins/synced/*/skills/skill-creator \
    /mnt/skills/*/skill-creator /mnt/skills/*/*/skill-creator ; do
    [ -f "$c/scripts/run_eval.py" ] && { cd "$c" && pwd; return; }
  done
}
SC=$(find_skill_creator || true)

# ---- workspace
if [ -z "$WORKSPACE" ]; then
  WORKSPACE="$(dirname "$SKILL_DIR")/$(basename "$SKILL_DIR")-workspace/evals-$(date +%Y-%m-%d)"
fi
mkdir -p "$WORKSPACE"
STATUS=0
echo "== skill-evals : $NAME"
echo "   skill     : $SKILL_DIR"
echo "   evals     : $EVALS_DIR"
echo "   workspace : $WORKSPACE"
echo "   skill-creator : ${SC:-NON TROUVÉ}"

# ---- 1. contrôles déterministes
echo; echo "-- 1/4 check_static.py"
# racine des plugins (pour découvrir les skills existants et vérifier les renvois → skill)
PLUGINS_ROOT="${PLUGINS_ROOT:-$(cd "$HERE/../../../.." 2>/dev/null && pwd)}"
set -- "$SKILL_DIR" --known-skills "skill-creator,${KNOWN}"
[ -d "$PLUGINS_ROOT" ] && set -- "$@" --scan-root "$PLUGINS_ROOT" --scan-root "$PLUGINS_ROOT/.."
[ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && set -- "$@" --scan-root "$CLAUDE_PLUGIN_ROOT/.."
[ -n "$IGNORE" ] && set -- "$@" --ignore-refs "$IGNORE"
python3 "$HERE/check_static.py" "$@" --json > "$WORKSPACE/check_static.json" 2>&1
python3 "$HERE/check_static.py" "$@" || STATUS=1

# ---- 2. quick_validate.py
echo; echo "-- 2/4 quick_validate.py"
if [ -n "$SC" ]; then
  python3 "$SC/scripts/quick_validate.py" "$SKILL_DIR" || STATUS=1
else
  echo "   IGNORÉ : skill-creator introuvable. Installer le skill Anthropic « skill-creator » ou exporter"
  echo "   SKILL_CREATOR_ROOT=/chemin/vers/skill-creator, puis relancer."
fi

[ "$STATIC_ONLY" -eq 1 ] && { echo; echo "== mode --static-only : arrêt après les contrôles hors LLM (statut $STATUS)"; exit $STATUS; }

# ---- 3. déclenchement (run_eval.py)
echo; echo "-- 3/4 run_eval.py sur triggers.json"
if [ ! -f "$EVALS_DIR/triggers.json" ]; then
  echo "   IGNORÉ : pas de triggers.json dans $EVALS_DIR"
elif [ -z "$SC" ]; then
  echo "   IGNORÉ : skill-creator introuvable (voir 2/4)"
elif ! command -v claude >/dev/null 2>&1; then
  echo "   IGNORÉ : la CLI « claude » est absente ; run_eval.py exécute « claude -p ». Sur Claude.ai (sans CLI),"
  echo "   les triggers se jugent à la main avec le grader (agents/grader.md) sur les cas [TRIGGER]/[NO-TRIGGER] d'evals.json."
else
  set -- --eval-set "$EVALS_DIR/triggers.json" --skill-path "$SKILL_DIR" --verbose
  [ -n "$MODEL" ] && set -- "$@" --model "$MODEL"
  ( cd "$SC" && python3 -m scripts.run_eval "$@" ) > "$WORKSPACE/triggers-results.json" || STATUS=1
  python3 - "$WORKSPACE/triggers-results.json" <<'PY' || STATUS=1
import json, sys
d = json.load(open(sys.argv[1]))
s = d["summary"]; print(f"   déclenchement : {s['passed']}/{s['total']} requêtes conformes")
for r in d["results"]:
    print(f"   [{'PASS' if r['pass'] else 'FAIL'}] attendu={r['should_trigger']} taux={r['trigger_rate']:.2f} : {r['query'][:80]}")
if d["results"] and all(r["trigger_rate"] == 0 for r in d["results"]):
    print("   SUSPECT : aucune requête n'a déclenché, même les cas [TRIGGER] — « claude -p » a probablement échoué")
    print("   (timeout 30 s, auth, sandbox). Résultat NON MESURÉ : ne pas le consigner comme une régression.")
    sys.exit(1)
sys.exit(0 if s["failed"] == 0 else 1)
PY
fi

# ---- 4. cas qualité : rappel de la procédure skill-creator (pas automatisable en sh : sous-agents)
echo; echo "-- 4/4 cas qualité / régression (evals.json) — procédure skill-creator"
cat <<EOF
   Les cas [QUALITÉ]/[RÉGRESSION]/[TOKEN-HYGIENE] demandent une exécution par sous-agent puis un grader :
   a) pour chaque eval d'evals.json : sous-agent « Skill path: $SKILL_DIR / Task: <prompt> /
      Save outputs to: $WORKSPACE/iteration-1/eval-<id>/with_skill/outputs/ » ; écrire eval_metadata.json
      et timing.json (schéma : ${SC:-<skill-creator>}/references/schemas.md) ;
   b) grader (agents/grader.md) → grading.json par run, champs exacts text / passed / evidence ;
      les expectations préfixées [DET …] se vérifient par script avant le juge LLM ;
   c) agrégation :  cd ${SC:-<skill-creator>} && python -m scripts.aggregate_benchmark $WORKSPACE/iteration-1 --skill-name $NAME
   d) revue :       python ${SC:-<skill-creator>}/eval-viewer/generate_review.py $WORKSPACE/iteration-1 --skill-name $NAME \\
                      --benchmark $WORKSPACE/iteration-1/benchmark.json --static $WORKSPACE/review.html
EOF

echo; echo "== statut : $STATUS (0 = tout ce qui a été lancé passe)"
exit $STATUS
