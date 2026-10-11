---
name: skill-evals
description: "Écrit, exécute et consigne les jeux d'evals des skills critiques de l'utilisateur (déclenchement, non-déclenchement, qualité, régression, token-hygiene) au format natif de skill-creator (evals.json + triggers.json), avec contrôles déterministes hors LLM (check_static.py : frontmatter, description ≤ 1024, chemins en dur, IP, nom de modèle versionné, renvois → skill fantômes, changelog) AVANT tout juge LLM. À utiliser quand l'utilisateur dit « écris/lance les evals de X », « teste ce skill avant de le repackager », « est-ce que X se déclenche encore », « régression sur un skill », « vérifie qu'il n'y a pas de chemin en dur », ou avant toute réécriture ou repackaging d'un skill (R59). Ne pas utiliser pour : créer ou réécrire un skill → skill-creator (création) ; inventaire, health check ou conflits de skills → tk-knowledge:skill-manager (inventaire)."
license: Proprietary — GeekFamilyCorp, usage privé
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
metadata:
  version: "1.0"
  author: GeekFamilyCorp
  domain: eval-lab
  activation: auto
  plan: "TricorderKit v0.3 — Phase 8 eval-lab"
  created: "2026-09-07"
compatibility: "Nécessite python3 (stdlib) pour check_static.py ; le skill Anthropic skill-creator (scripts/run_eval.py, quick_validate.py, aggregate_benchmark.py, eval-viewer) pour le reste ; la CLI claude pour run_eval.py (sinon triggers jugés à la main)."
---

# skill-evals — le banc d'essai des skills critiques

Un skill sans test se dégrade en silence : un renvoi vers un skill archivé, un nom de modèle qui
dérive, une description qui ne déclenche plus. Ce skill impose la règle de la Phase 8 :
**chaque skill critique a ≥ 5 tests, les régressions se voient, et le déterministe passe avant le
juge LLM.** Règles citées : R51 (recouper, ne pas affirmer de mémoire), R53 (proposer, ne pas
exécuter), R59 (repackager après chaque MAJ — donc tester avant), R31 NO-DROP.

## Quand lancer
| Moment | Quoi |
|---|---|
| Avant toute réécriture d'un skill | jeu complet → c'est la **ligne de base** ; sans elle, pas de régression détectable |
| Après la réécriture, avant repackaging (R59) | jeu complet ; comparer à la ligne de base ; un cas qui passait et échoue = STOP |
| Après un renommage/archivage de skill voisin | `check_static.py` seul (renvois → skill) sur tous les skills qui le citent |
| Périodiquement (tâche planifiée `default`, jamais `deep`) | `check_static.py` sur tous les SKILL.md ; les cas LLM restent manuels |

## Le jeu d'evals d'un skill — `evals/<skill>/`
Deux fichiers, **format natif de skill-creator, sans champ inventé** ; gabarit complet et exemple
dans `${CLAUDE_PLUGIN_ROOT}/skills/skill-evals/references/gabarit-eval.md`.

- `evals.json` — `{skill_name, evals:[{id, prompt, expected_output, files, expectations[]}]}`
  (schéma : `references/schemas.md` de skill-creator). Le **type** du cas se lit en tête de
  `expected_output` : `[TRIGGER]`, `[NO-TRIGGER → skill]`, `[QUALITÉ]`, `[RÉGRESSION]`,
  `[TOKEN-HYGIENE]`.
- `triggers.json` — `[{query, should_trigger}]`, le format exact de `scripts/run_eval.py` ;
  `kind` et `expected_skill` sont documentaires. C'est ici que vit le **no-trigger**, mesuré par
  script ; il est doublé dans `evals.json` pour le grader quand `claude -p` manque.

Minimum par skill : 2 `[TRIGGER]` (dont un quasi-faux-positif : phrase voisine d'un autre skill qui
doit rester ici), 1 `[NO-TRIGGER]` nommant le skill compétent, 2 `[QUALITÉ]`. Ajouter un
`[RÉGRESSION]` par défaut corrigé dans le changelog du skill.

### Assertions : déterministe d'abord
Chaque `expectation` est préfixée. Les `[DET …]` se vérifient par `grep`/script, **avant** de payer
un juge :
`[DET must_contain]` · `[DET must_not_contain]` · `[DET must_match]` (regex) ·
`[DET must_not_match]` · `[DET tool_used]` · `[DET tool_not_used]` · `[DET file_exists]`.
`[LLM]` ne sert qu'à ce qu'un grep ne tranche pas, et l'énoncé oblige le juge à **citer une preuve**.
Ce qu'on vérifie systématiquement en `[QUALITÉ]` : sections attendues, tableau au bon en-tête,
« sur GO » / rien d'exécuté sans accord, aucun chemin en dur, vouvoiement de l'utilisateur, **alias de
modèle (`fast`/`default`/`deep`) et jamais un nom de version**.

Une assertion qui passerait aussi sur une sortie fausse est à réécrire (cf. `agents/grader.md`,
« Critique the Evals »).

## Exécution — commandes exactes
Racines : `SE=${CLAUDE_PLUGIN_ROOT}/skills/skill-evals` ; `SC` = dossier de skill-creator
(`~/.claude/skills/synced/*/skill-creator` ou `/mnt/skills/*/skill-creator` ; `run_evals.sh` le
cherche seul, sinon `SKILL_CREATOR_ROOT=…`).

```sh
# 0. contrôles hors LLM, sur un ou plusieurs skills (aucun appel modèle)
python3 "$SE/scripts/check_static.py" <dossier-skill> [...] --scan-root <racine-plugins> \
        [--known-skills a,plugin:b] [--ignore-refs nom-de-tache] [--json] [--strict]

# 1. tout-en-un pour UN skill : check_static → quick_validate → run_eval.py (triggers) → rappel qualité
sh "$SE/scripts/run_evals.sh" <dossier-skill> [--static-only] [--model <alias>] [--workspace <dir>]

# 2. déclenchement seul (format run_eval.py), depuis le dossier de skill-creator
cd "$SC" && python -m scripts.run_eval --eval-set "$SE/evals/<skill>/triggers.json" \
        --skill-path <dossier-skill> --runs-per-query 3 --trigger-threshold 0.5 --verbose

# 3. cas qualité : un sous-agent par eval (skill-creator, « Running and evaluating test cases »)
#    → <workspace>/iteration-N/eval-<id>/with_skill/outputs/ + eval_metadata.json + timing.json
#    → grader (agents/grader.md) → grading.json  → puis :
cd "$SC" && python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <skill>
python "$SC/eval-viewer/generate_review.py" <workspace>/iteration-N --skill-name <skill> \
        --benchmark <workspace>/iteration-N/benchmark.json --static <workspace>/review.html

# 4. optimiser la description (Claude Code / Cowork seulement, après accord de l'utilisateur)
cd "$SC" && python -m scripts.run_loop --eval-set "$SE/evals/<skill>/triggers.json" \
        --skill-path <dossier-skill> --model <alias-de-la-session> --max-iterations 5 --verbose
```
Pas de sous-agents (Claude.ai) : exécuter chaque prompt d'`evals.json` soi-même après lecture du
SKILL.md cible, un par un, puis grader ; sauter le benchmark.

## Lire `grading.json` et décider
`grading.json` (un par run) : `expectations[]` avec `text` / `passed` / `evidence` — ces trois
noms exacts, le viewer en dépend — puis `summary.pass_rate`, `execution_metrics`, `claims[]`,
`eval_feedback` (le grader critique aussi les evals : lire ses suggestions).
`run_eval.py` rend `results[].trigger_rate` et `pass` par requête.

**Seuil de passage** :
- déclenchement : 100 % des requêtes de `triggers.json` conformes (`trigger_rate ≥ 0.5` si
  `should_trigger`, `< 0.5` sinon), sur 3 runs ;
- qualité : **100 % des `[DET]`** et `pass_rate ≥ 0.8` sur l'ensemble ;
- régression : aucun cas qui passait dans la ligne de base ne doit échouer — un seul suffit à
  bloquer le repackaging ;
- un résultat « tout à zéro » sur les triggers signale un harnais qui n'a pas tourné (timeout,
  auth) : **NON MESURÉ**, pas une régression (R51).

## Consigner
1. **Projet** : `claude/veilles/JOURNAL_skill-evals.md` — une ligne datée par run :
   `date | skill | version | check_static OK/KO | triggers n/N | qualité pass_rate | verdict | lien workspace`,
   et une ligne au `claude/veilles/REGISTRE.md` à la création du journal.
2. **Vault** : `claude-vault/00_SYSTEM/00_Skills/<skill>/EVALS.md` — dernière ligne de base et
   verdict ; le skill n'est « testé » que si c'est écrit et daté (R79).
3. Les workspaces (`<skill>-workspace/evals-<date>/`) restent hors du dépôt public (R37).

## Exemples
- « Lance les evals de code-corrector avant que je le repackage » → `run_evals.sh` complet ; verdict +
  ligne au JOURNAL ; repackaging seulement si aucune régression.
- « Est-ce que model-router se déclenche encore sur "quel modèle pour cette tâche" ? » → `run_eval.py` sur
  `evals/model-router/triggers.json` ; si `trigger_rate < 0.5`, proposer `run_loop.py` (sur GO).
- « Vérifie qu'aucun skill ne cite encore task-classifier » → `check_static.py` sur tous les
  SKILL.md avec `--scan-root` ; les `REF-SKILL` listent les renvois fantômes.
- « Écris un jeu d'evals pour polyglotte » → gabarit `references/gabarit-eval.md`, 6 cas
  (2 trigger, 1 no-trigger, 2 qualité, 1 régression), `[DET]` d'abord.

## Frontières
Créer, réécrire ou packager un skill → `skill-creator`. Inventaire, health check /8, conflits,
archivage → `tk-knowledge:skill-manager` (qui peut appeler `check_static.py` comme 9e critère).
Ce skill mesure et consigne ; il ne
modifie jamais un SKILL.md cible, et ne repackage rien sans GO (R53).

## Changelog
- **2026-09-07 — 1.0** : création (Phase 8 eval-lab). `check_static.py` (stdlib, 11 contrôles),
  `run_evals.sh` (POSIX, adossé aux scripts de skill-creator), gabarit d'eval, jeux pour les skills
  critiques ; la version publique en fournit cinq : code-corrector, dev-protocol,
  doubt-driven-development, skill-manager, model-router.
