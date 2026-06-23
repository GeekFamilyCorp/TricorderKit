# hooks — token-optimizer

**Désactivés le 2026-06-23 (R52).** `hooks.json = {"hooks": {}}`.

## Pourquoi
Les hooks précédents utilisaient la syntaxe POSIX `${CLAUDE_PLUGIN_ROOT}` :
- `PreToolUse/Bash` → `bash ${CLAUDE_PLUGIN_ROOT}/scripts/rtk-rewrite.sh`
- `PostToolUse/Task` → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py log-from-task`

Sous **Cowork (hôte Windows)**, le runner de hooks passe par `cmd.exe`, qui **n'expanse pas** `${VAR}`
(cmd utilise `%VAR%`). Le token `${CLAUDE_PLUGIN_ROOT}` reste donc **littéral** → chemin invalide →
le hook `PostToolUse/Task` échouait et **bloquait l'outil Agent** à chaque délégation.

On ne peut pas corriger en mettant un chemin absolu : ce plugin est dans le **repo public** (gate R37,
aucun chemin personnel autorisé), et `${CLAUDE_PLUGIN_ROOT}` reste le token correct côté Claude Code.

## Impact
Aucune perte de fonction réelle : le suivi de budget reste accessible via les **skills**
`budget-tracker` / `budget-analyzer` (invoqués normalement). Seul le *log automatique* via hook est suspendu.

## Réactiver (version Cowork-native — TODO)
Concevoir un hook portable cmd+sh : soit un lanceur sans dépendance au `${VAR}` (résolution interne du
chemin par le script lui-même), soit deux commandes selon l'OS, et garantir un **exit 0** (jamais bloquant).
