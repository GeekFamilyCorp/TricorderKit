# docs/05_hooks_policy.md — Hook Policy TricorderKit v1.0

> Politique formelle des hooks. Opposable à tout agent ou script opérant dans ce repo.
> Version : 1.0 — 16/05/2026

---

## Règle 0 — Principe fondamental

**Un hook ne doit jamais appeler un autre hook directement.**

Un hook est un intercepteur léger (≤ 15 lignes de logique réelle). Il délègue à un Skill ou démarre un Workflow Temporal. Toute logique métier dans un hook est un anti-pattern.

---

## Catalogue des événements autorisés

| Événement Claude Code | Hook associé | Script | Rôle |
|---|---|---|---|
| `PreToolUse` | pre_intent | `core/hooks/pre_intent_hook.py` | Qualification de l'intention |
| `PreToolUse` | pre_execution | `core/hooks/pre_execution_hook.py` | Estimation coût + risk guard |
| `PostToolUse` | post_execution | `core/hooks/post_execution_hook.py` | Validation résultat + quality_score |
| `Stop` | post_session | `core/hooks/post_session_hook.py` | Déclenche usageObserverWorkflow |

Tout nouvel événement doit être approuvé ici avant implémentation.

---

## Règles de codage

### R1 — Format de log obligatoire

Tout hook qui écrit dans `.cache/hooks/*.log` doit produire des JSON-lines avec au minimum :

```json
{
  "hook_name": "post_execution",
  "skill_name": "<nom_du_skill_ou_goat>",
  "timestamp": "2026-05-16T11:17:24.179Z",
  "status": "ok|error|skipped",
  "duration_ms": 42,
  "tokens_used": 150
}
```

Champs obligatoires : `hook_name`, `timestamp`, `status`. Les autres sont recommandés.

### R2 — Longueur maximale

Un hook script ne doit pas dépasser **50 lignes** (hors docstring et imports).
Si la logique dépasse ce seuil, extraire dans une fonction importée depuis un module `core/hooks/lib/`.

### R3 — Pas de récursion

Interdiction absolue de déclencher un hook depuis un hook, même indirectement via un outil ou un subagent.

### R4 — Fail silently

Un hook ne doit jamais faire planter la session principale. Tout appel externe (Temporal, fichier) doit être dans un `try/except` avec sortie propre (`sys.exit(0)`).

### R5 — Dry-run avant déploiement

Tout nouveau hook doit être testé avec `--dry-run` ou dans un environnement isolé avant d'être enregistré dans `.claude/settings.json`.

---

## Matrice couche → responsabilité

| Besoin | Couche | Anti-pattern |
|---|---|---|
| Logique métier réutilisable | Skill | L'écrire dans un hook |
| Règle globale de comportement | `CLAUDE.md` | La mettre dans un hook |
| Action automatique sur événement | Hook (≤ 15 lignes) | Mettre de la logique dans le hook |
| Tâche longue / observabilité | Workflow Temporal | Bloquer le hook en attendant le résultat |
| Nouvel outil externe | Plugin | Scripter dans un hook |

---

## Seuils de performance

| Métrique | Seuil warning | Seuil critique | Action |
|---|---|---|---|
| `duration_ms` | > 500 ms | > 2 000 ms | Extraire dans un Workflow asynchrone |
| `tokens_used` | > 300 | > 800 | Revoir l'estimation dans pre_execution |
| `quality_score` | < 0.50 | < 0.25 | Alerte dans `usage_observer` report |

Ces seuils sont lus par `usage_observer.activities.ts` pour le rapport hebdomadaire.

---

## Révision

Cette politique est révisée lors de chaque Phase majeure (Phase 4 → 5 → 6).
Toute modification doit être loguée dans `.planning/DECISIONS.md`.
