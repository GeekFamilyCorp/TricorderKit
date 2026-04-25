---
name: model-router
description: >
  Choisit le modele Claude optimal (Haiku 4.5, Sonnet 4.6 ou Opus 4.6) pour une tache donnee
  en combinant longueur du prompt, type de tache detecte et budget mensuel restant.
  Se declenche AVANT toute execution significative sur les requetes utilisateur.
  Mots-cles : "quel modele", "route la tache", "choisis le modele", "dispatche",
  "optimise mon token", "economise des tokens", "classifie cette demande",
  "tache simple", "tache complexe", toute nouvelle demande entrante non triviale.
---

# Model Router

Skill central du plugin token-optimizer. Orchestre la classification puis la delegation vers un sous-agent specialise par modele.

## Quand declencher

Activer ce skill DES QU'UNE nouvelle requete utilisateur arrive ET que la requete depasse le simple aller-retour conversationnel (question factuelle tres courte). Ne pas activer pour les reponses directes de moins de 2 tours.

## Methodologie en 4 etapes

### 1. Extraire les signaux du prompt

Mesurer en une passe :

- **Longueur input** : compter approximativement les tokens (ratio 1 token = 0,75 mot en francais/anglais). Utiliser `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/classify.py "<prompt>"` si disponible.
- **Type de tache** : detecter via mots-cles et structure. Lire `references/task-types.md` pour la grille complete.
- **Presence de code/fichiers/donnees** : verifier les attachements, les blocs markdown `code`, les mentions de fichiers, CSV, SQL, JSON volumineux.
- **Profondeur de raisonnement demandee** : reperer "explique pourquoi", "analyse", "compare", "planifie", "audit", "architecture", "trade-off".

### 2. Calculer le tier de complexite

| Tier | Modele cible | Signaux declencheurs |
|------|-------------|---------------------|
| **T1 - Simple** | Haiku 4.5 (`claude-haiku-4-5-20251001`) | Prompt < 1500 tokens, tache = FAQ / resume court / reformulation / traduction simple |
| **T2 - Standard** | Sonnet 4.6 (`claude-sonnet-4-6`) | 1500-15000 tokens, redaction / analyse documentaire / code non critique |
| **T3 - Complexe** | Opus 4.6 (`claude-opus-4-6`) | > 15000 tokens OU code critique/securite OU architecture systeme |

**Regles de forcage** :

- Si le prompt mentionne "legal", "medical", "securite", "production", "incident" → monter d'un tier.
- Si le prompt est une conversation creative courte → forcer T1.
- Si le budget mensuel est sature (cf. `budget-tracker`) → desescalader d'un tier sauf mention "critique" explicite.

### 3. Verifier le budget mensuel

Consulter `budget-tracker` (appel a `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budget.py status`). Si la fenetre d'alerte est atteinte :

- 80% atteint → avertir l'utilisateur, recommander T(n-1) sauf mention "critique"
- 95% atteint → forcer Haiku pour le reste du mois sauf override explicite

### 4. Deleguer au sous-agent approprie

Trois agents sont disponibles dans `agents/` :

- `haiku-executor` (Haiku 4.5) pour T1
- `sonnet-executor` (Sonnet 4.6) pour T2
- `opus-executor` (Opus 4.6) pour T3

Passer le prompt complet au sous-agent choisi via le `Task` tool en precisant `subagent_type`.

## Optimisations pre-delegation

AVANT de deleguer, appliquer ces 3 optimisations dans l'ordre :

1. **Compression de contexte** : si le contexte precedent > 10000 tokens, declencher le skill `context-compress`.
2. **Docs fraiches** : si le prompt evoque une bibliotheque/framework, suggerer l'ajout de `use context7` pour declencher l'injection de docs via le MCP Context7.
3. **CLI compression** : si des commandes bash sont prevues, verifier que rtk est actif (cf. skill `cli-compress`).

## Format de sortie attendu

Annoncer explicitement la decision avant de deleguer :

```
Classification : <tier> (<raison principale>)
Modele choisi : <nom modele> (<alias>)
Budget restant ce mois : <%>
Optimisations appliquees : [compression | context7 | rtk]
```

Puis appeler le sous-agent via Task tool.
