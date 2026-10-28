# Protocole de test — Lots 1 à 3 (auto-budget)

> Objectif : éprouver l'analyse budget, l'auto-optimisation sûre et le reroute Haiku
> en conditions réelles, AVANT d'ajouter l'offload (L4/L5).

Chemin source du plugin : `C:\dev\TricorderKit\plugins\token-optimizer`
Données : `~/.token-optimizer/budget.json` (créé au 1er appel).

---

## Étape 0 — Recharger le plugin (pour skills + hook)

Le niveau « scripts » (étapes 1-4) marche sans rien recharger. Pour que les **skills**
(`model-router`, `budget-analyzer`, `auto-optimize`) se déclenchent et que le **hook**
PostToolUse logge les events, il faut que Cowork recharge le plugin depuis la source :

1. Paramètres Cowork → Plugins → token-optimizer.
2. Recharger / réinstaller depuis le dossier source `C:\dev\TricorderKit\plugins\token-optimizer`
   (ou désactiver puis réactiver).
3. Vérifier que les 9 skills apparaissent, dont les nouveaux : `budget-analyzer`, `auto-optimize`.

> Si tu n'es pas sûr de la manip exacte dans l'UI, demande-moi : je peux la regarder à l'écran avec toi.

---

## Étape 1 — Vérifier l'état budget (niveau script)

```bash
python3 "C:\dev\TricorderKit\plugins\token-optimizer\scripts\budget.py" status
```

Attendu : un tableau par modèle, un mode d'alerte `informative`, une `Policy`. Si c'est ta
première fois, tout est à 0 (normal).

## Étape 2 — Lancer l'analyse

```bash
python3 "C:\dev\TricorderKit\plugins\token-optimizer\scripts\budget_analyzer.py"
```

Attendu : répartition par modèle, rythme/jour, projection fin de mois, ETA des seuils,
gaspillages détectés (vides si peu de données), recommandations (auto / à proposer).
Avec peu d'`events`, un rappel « l'analyse s'affinera avec l'usage » s'affiche — c'est normal.

## Étape 3 — Tester l'auto-optimisation (dry-run puis apply)

```bash
python3 "C:\dev\TricorderKit\plugins\token-optimizer\scripts\optimizer.py" analyze
python3 "C:\dev\TricorderKit\plugins\token-optimizer\scripts\optimizer.py" apply
python3 "C:\dev\TricorderKit\plugins\token-optimizer\scripts\optimizer.py" status
python3 "C:\dev\TricorderKit\plugins\token-optimizer\scripts\optimizer.py" rollback --last
```

Attendu : `analyze` montre les changements potentiels ; `apply` écrit les drapeaux
`auto_state` (réversibles) ; `status` les affiche + le nombre de points de rollback ;
`rollback --last` restaure l'état précédent. Tout est journalisé dans
`~/.token-optimizer/optimizer-log.jsonl`.

## Étape 4 — Tester le biais de classement (reroute)

```bash
python3 "C:\dev\TricorderKit\plugins\token-optimizer\scripts\classify.py" --prompt "Redige une analyse de 800 mots avec synthese de sources" --json
python3 "C:\dev\TricorderKit\plugins\token-optimizer\scripts\classify.py" --prompt "Redige une analyse de 800 mots avec synthese de sources" --bias 40 --json
```

Attendu : sans bias → `T2` ; avec `--bias 40` → `T1` (le score effectif chute).

---

## Étape 5 — Test en conditions réelles (après reload, niveau skills/hook)

1. **Analyse via skill** : demande en chat « analyse mon budget tokens » → le skill
   `budget-analyzer` doit se déclencher et restituer le rapport.
2. **Auto-optimisation via skill** : « auto-optimise mon budget » → `optimizer.py apply`
   doit s'exécuter et te résumer ce qui a été appliqué.
3. **Hook de logging** : lance une tâche qui délègue à un sous-agent (Task). Vérifie qu'il
   n'y a **plus d'erreur PostToolUse** et que `budget.py status` montre une conso/events
   incrémentés (si le payload Task expose des tokens).
4. **Reroute en pression** : mets temporairement un petit budget pour simuler la pression :
   ```bash
   python3 "...\scripts\budget.py" set-budget --total 100000
   python3 "...\scripts\optimizer.py" apply
   ```
   puis observe que le `model-router` route plus agressivement vers Haiku + active caveman.
   Reviens ensuite à ton budget normal (`set-budget --total <ta_valeur>` ou garde 20M).

---

## Calibration (recommandé après ~2 semaines)

Compare le total estimé (`budget.py status`) avec ton usage réel (console Anthropic) puis :

```bash
python3 "...\scripts\budget.py" set-budget --calibration 1.15   # exemple : +15%
```

## Points de vigilance

- Chiffres = **estimations** (hook + estimation `classify.py`), pas la facturation exacte.
- L'auto-apply ne touche que des drapeaux de données réversibles (`auto_state`), jamais le code.
- Rien de sensible n'est concerné tant que l'offload externe (L4/L5) n'est pas en place.

## Retour attendu

Note ce qui marche / coince (surtout : le hook ne loggue-t-il bien plus d'erreur ? les events
s'incrémentent-ils ?). On ajuste, puis on attaque L4 (Hermes/Ollama) et L5 (Antigravity).
