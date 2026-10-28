---
name: model-router
description: >
  Choisit le modele Claude optimal (Haiku 4.5, Sonnet 4.6 ou Opus 4.6) pour une tache donnee en combinant longueur du prompt, type de tache detecte et budget mensuel restant. Applique automatiquement le mode caveman (compression sortie -75%) sur T1/T2 pour maximiser l'economie de tokens. Se declenche AVANT toute execution significative sur les requetes utilisateur. Mots-cles : "quel modele", "route la tache", "choisis le modele", "dispatche", "optimise mon token", "economise des tokens", "classifie cette demande", "tache simple", "tache complexe", toute nouvelle demande entrante non triviale.
---

# Model Router

Skill central du plugin token-optimizer. Orchestre la classification, l'optimisation des sorties (caveman), puis la delegation vers un sous-agent specialise par modele.

## Quand declencher

Activer ce skill DES QU'UNE nouvelle requete utilisateur arrive ET que la requete depasse le simple aller-retour conversationnel (question factuelle tres courte). Ne pas activer pour les reponses directes de moins de 2 tours.

## Methodologie en 5 etapes

### 1. Extraire les signaux du prompt

Mesurer en une passe :

- **Longueur input** : compter approximativement les tokens (ratio 1 token = 0,75 mot en francais/anglais). Utiliser `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/classify.py "<prompt>"` si disponible.
- **Type de tache** : detecter via mots-cles et structure. Lire `references/task-types.md` pour la grille complete.
- **Presence de code/fichiers/donnees** : verifier les attachements, les blocs markdown `code`, les mentions de fichiers, CSV, SQL, JSON volumineux.
- **Profondeur de raisonnement demandee** : reperer "explique pourquoi", "analyse", "compare", "planifie", "audit", "architecture", "trade-off".

### 2. Calculer le tier de complexite

Appliquer la grille suivante :

| Tier | Modele cible | Signaux declencheurs |
|------|-------------|---------------------|
| **T1 - Simple** | Haiku 4.5 (`claude-haiku-4-5-20251001`) | Prompt < 1500 tokens, tache = FAQ / resume court / reformulation / traduction simple / classification / extraction basique |
| **T2 - Standard** | Sonnet 4.6 (`claude-sonnet-4-6`) | 1500-15000 tokens, redaction article / analyse documentaire / code non critique / refactor limite / recherche multi-sources / orchestration legere |
| **T3 - Complexe** | Opus 4.6 (`claude-opus-4-6`) | > 15000 tokens OU code critique/securite OU raisonnement multi-etapes long OU architecture systeme OU debug complexe OU planification strategique multi-variables |

**Regles de forcage** :

- Si le prompt mentionne "legal", "medical", "securite", "production", "incident" -> monter d'un tier.
- Si le prompt est une conversation creative courte -> forcer T1.
- Si le budget mensuel est sature (cf. `budget-tracker`) -> desescalader d'un tier sauf mention "critique" explicite.

### 3. Appliquer la compression sortie (caveman)

**AVANT de deleguer**, activer le skill `caveman` selon le tier :

| Tier | Mode caveman | Economie tokens sortie estimee |
|------|-------------|-------------------------------|
| T1 | **full** | ~75% |
| T2 | **lite** | ~45% |
| T3 | desactive (sauf si precision non compromise) | 0% |

**Exceptions — ne pas activer caveman si** :
- La tache demande un document formel / rapport long / code complet
- L'utilisateur a explicitement demande une reponse detaillee
- La tache T3 implique des instructions multi-etapes irreversibles

Pour activer : inclure dans le prompt passe au sous-agent la directive `[MODE CAVEMAN FULL]` ou `[MODE CAVEMAN LITE]` selon le tier.

### 4. Verifier le budget mensuel

Consulter le skill `budget-tracker` pour l'etat du quota mensuel (`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py status --json`). Si alerte detectee :

- **80% atteint** -> avertir l'utilisateur, recommander T(n-1) sauf mention "critique"
- **95% atteint** -> forcer Haiku + caveman ultra pour le reste du mois sauf override explicite

### 5. Deleguer au sous-agent approprie

Trois agents sont disponibles dans `agents/` :

- `haiku-executor` (Haiku 4.5) pour T1
- `sonnet-executor` (Sonnet 4.6) pour T2
- `opus-executor` (Opus 4.6) pour T3

Passer le prompt complet au sous-agent choisi via le `Task` tool en precisant `subagent_type`.

## Optimisations pre-delegation

AVANT de deleguer, appliquer ces optimisations dans l'ordre :

1. **Compression sortie caveman** (etape 3 ci-dessus) : economie -40 a -90% tokens output selon niveau.
2. **Compression de contexte** : si le contexte precedent > 10000 tokens, declencher le skill `context-compress`.
3. **Docs fraiches** : si le prompt evoque une bibliotheque/framework (React, Next.js, FastAPI, Supabase, etc.), suggerer l'ajout de `use context7` pour declencher l'injection de docs via le MCP Context7.
4. **CLI compression** : si des commandes bash sont prevues, verifier que rtk est actif (cf. skill `cli-compress`).

## Format de sortie attendu

Annoncer explicitement la decision avant de deleguer :

```
Classification : <tier> (<raison principale>)
Modele choisi : <nom modele> (<alias>)
Mode caveman : <full|lite|desactive> (~<X>% tokens sortie economises)
Budget mensuel : <alerte si > 50%, sinon omis>
Optimisations : [caveman | compression | context7 | rtk]
```

Puis appeler le sous-agent via Task tool.

## Auto-optimisation budget (Lots 2-3)

AVANT de classer, consulter l'etat d'auto-optimisation (ecrit par `optimizer.py`) :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/optimizer.py status
```

Appliquer les drapeaux `auto_state` :

- `score_bias` (N) : passer `--bias N` a `classify.py` -> les taches limites descendent d'un tier.
- `haiku_reroute` (true) : router les T2 NON critiques vers `haiku-executor`.
- `force_haiku` (true) : forcer Haiku sauf mention "critique" / "urgent".
- `caveman_default` (lite|full|ultra) : activer ce niveau de caveman par defaut.

### Comptage des economies (reroute Lot 3)

Quand une tache est descendue d'un tier pour raison budget (ex. T2 -> T1), enregistrer l'economie estimee :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py log-offload --target haiku --saved <equiv_economise>
```

Estimation : `equiv_economise = equiv(tier_origine) - equiv(haiku)` a partir des tokens estimes par `classify.py` (poids : Haiku 1/1, Sonnet 3/5, Opus 15/25). Ces economies apparaissent dans `budget.py status` et `budget_analyzer.py`.

## References

- `references/task-types.md` : grille detaillee des types de taches
- `references/routing-matrix.md` : matrice longueur x type -> modele
- `references/examples.md` : 12 exemples concrets de routage
