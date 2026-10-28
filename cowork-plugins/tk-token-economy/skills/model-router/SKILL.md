---
name: model-router
description: >
  Classifie une demande en tier de complexité (T1 simple, T2 standard, T3 complexe) avec un score 0-100,
  choisit l'alias de modèle correspondant (fast / default / deep, identifiants dans models.json) et délègue
  à l'agent exécuteur adapté en tenant compte du budget mensuel estimé. À utiliser sur demande explicite
  de l'utilisateur : « quel modèle pour ça », « route cette tâche », « classifie cette demande », « évalue la
  complexité », « dispatche en économisant des tokens », ou avant de lancer un lot de sous-agents dont le
  coût compte. Ne pas utiliser pour une réponse conversationnelle directe (répondre normalement), pour
  suivre ou analyser la consommation (→ budget), ni pour compresser la sortie (→ caveman).
license: MIT
metadata:
  version: "2.0"
  updated: "2026-09-07"
  author: GeekFamilyCorp
---

# Model Router

Skill central du plugin : classification → choix d'alias → optimisations → délégation. Activation manuelle uniquement (usage ponctuel ou avant un lot de sous-agents).

Modèles : ce skill ne connaît que des **alias** — `fast` (T1), `default` (T2), `deep` (T3). Les identifiants réels vivent dans `${CLAUDE_PLUGIN_ROOT}/models.json` ; ne jamais en écrire un en dur. Doctrine de routage : R54 / DEC-031 (voir `${CLAUDE_PLUGIN_ROOT}/references/regles.md`).

## Procédure

### 1. Classifier (un seul appel, déterministe)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/classify.py --prompt "<texte de la demande>" --json
```

Options : `--stdin` (prompt long), `--budget-saturated` (budget ≥ 80 %), `--bias N` (pression budget, voir `references/auto-budget.md`).

Retour : `score`, `tier`, `alias`, `family`, `model` (lu dans models.json, sinon l'alias), `dimensions`, `explanation`. La grille des cinq dimensions et des types de tâches est dans `references/task-types.md` ; la matrice longueur × type dans `references/routing-matrix.md`.

Si le script est indisponible, appliquer la grille à la main :

| Tier | Alias | Signaux |
|------|-------|---------|
| T1 | `fast` | prompt court, FAQ / résumé / reformulation / traduction simple / classification / extraction |
| T2 | `default` | rédaction, analyse documentaire, code non critique, refactor limité, recherche multi-sources |
| T3 | `deep` | code critique / sécurité, architecture, debug complexe, raisonnement multi-étapes long |

Forçages : « legal », « medical », « sécurité », « production », « incident » → +1 tier ; brouillon / « juste pour voir » → −1 tier ; « utilise Opus » / « mode économique » → respecter l'utilisateur.

### 2. Vérifier le budget (estimation)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py status --json
```

`escalation_policy` : `normal` → rien ; `downgrade_one_tier` → −1 tier sauf « critique » ; `force_haiku` → T1 sauf « critique » / « urgent ». Rappel : ce sont des estimations, pas la facturation (voir skill `budget`).

Drapeaux d'auto-optimisation (`optimizer.py status`) : lecture et application décrites dans `references/auto-budget.md`.

### 3. Optimisations avant délégation

1. **caveman** : proposer `lite` pour T1/T2 si l'utilisateur l'a activé (skill manuel, jamais imposé) ; jamais sur T3, documents formels ou code complet.
2. **context-compress** : si le contexte précédent dépasse ~10 000 tokens.
3. **docs-fresh** : si une bibliothèque / framework est cité, interroger le connecteur Context7 (skill `docs-fresh`).
4. **cli-compress** : si des commandes shell sont prévues, le hook rtk agit seul s'il est installé.

### 4. Annoncer puis déléguer

```
Classification : <tier> (<raison principale>, score <n>/100)
Alias modèle   : <fast|default|deep> (voir models.json)
Budget estimé  : <alerte si ≥ 50 %, sinon omis>
Optimisations  : [caveman | context-compress | docs-fresh | rtk]
```

Puis appeler via le `Task` tool l'agent correspondant : `haiku-executor` (fast), `sonnet-executor` (default), `opus-executor` (deep). Les agents sont dans `${CLAUDE_PLUGIN_ROOT}/agents/`.

Si un tier a été abaissé pour raison budget, enregistrer l'économie estimée :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py log-offload --target haiku --saved <equiv>
```

## Références

- `references/task-types.md` — grille des types de tâches et des cinq dimensions de score
- `references/routing-matrix.md` — matrice longueur × type, coûts relatifs
- `references/examples.md` — exemples de routage
- `references/auto-budget.md` — drapeaux d'auto-optimisation et comptage des économies
- `${CLAUDE_PLUGIN_ROOT}/models.json` — alias → identifiants

## Changelog

- 2026-09-07 — v2.0 : fusion de `task-classifier` (grille + appel CLI unique) ; activation manuelle ; identifiants de modèle sortis vers `models.json` ; §Auto-optimisation déplacé en `references/auto-budget.md` ; caveman n'est plus imposé.
- 2026-04 — v1.x : routeur initial à trois tiers, caveman automatique, lots budget 2-3.
