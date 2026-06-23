# hooks — token-optimizer

**Reconçus portables le 2026-06-23 (R52).** Auparavant désactivés (cf. historique en bas).

## Design portable cmd + sh, non bloquant
Les hooks n'utilisent PLUS la syntaxe POSIX `${CLAUDE_PLUGIN_ROOT}` (que `cmd.exe` sous Cowork
n'expanse pas). À la place, chaque hook est un **bootstrap Python** qui :
1. lit `CLAUDE_PLUGIN_ROOT` depuis **l'environnement** (`os.environ`) — portable cmd/sh, pas d'expansion shell ;
2. exécute le script sous-jacent **seulement s'il existe** ;
3. **sort toujours en `exit 0`** (try/except + timeout) → **jamais bloquant**.

Le bootstrap est encodé en **base64** (zéro espace) → robuste à tout tokeniseur de commande :
`python3 -c "exec(__import__('base64').b64decode('<B64>').decode())"`.

- `PreToolUse/Bash` → lance `scripts/rtk-rewrite.sh` via bash **si bash + le script existent**, sinon
  no-op (passthrough, aucune modification de la commande). Sous Windows/Cowork sans bash : no-op silencieux.
- `PostToolUse/Task` → lance `scripts/budget.py log-from-task` (stdin hérité = l'événement JSON) si présent,
  sinon no-op. `budget.py` est déjà défensif (avale les erreurs, exit 0 en mode hook).

## Comportement par environnement
- **Claude Code** (POSIX, `CLAUDE_PLUGIN_ROOT` dans l'env) → les hooks s'exécutent normalement.
- **Cowork / Windows** → si l'env fournit `CLAUDE_PLUGIN_ROOT`, le budget est loggé ; sinon no-op sûr.
  Dans tous les cas : **exit 0**, aucun blocage de l'outil Agent.

## Vérifier
`python outputs/test_hooks.py` (hors repo) charge `hooks.json`, exécute chaque commande sous cmd avec
stdin `{}` et vérifie `returncode==0`. Source des bootstraps : `outputs/gen_hook_b64.py`.

<details><summary>Historique — incident 2026-06-23</summary>
Les hooks d'origine (`bash ${CLAUDE_PLUGIN_ROOT}/...`, `python3 ${CLAUDE_PLUGIN_ROOT}/...`) échouaient
sous Cowork : `cmd.exe` ne substitue pas `${VAR}` (il utilise `%VAR%`), le chemin restait littéral, et
le hook `PostToolUse/Task` **bloquait l'outil Agent**. Désactivés (`{"hooks":{}}`), puis reconçus
portables (ci-dessus). Un chemin absolu était exclu (repo public, gate R37).
</details>
