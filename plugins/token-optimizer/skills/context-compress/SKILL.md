---
name: context-compress
description: >
  Compresse le contexte d'une conversation longue en preservant les decisions, fichiers touches, et prochaines etapes. Base sur les techniques du repo Agent-Skills-for-Context-Engineering (muratcankoylan). Mots-cles : "compresse le contexte", "trop long", "resume cette conversation pour continuer", "fais un handoff", "optimise ma memoire", "context trop charge".
---

# Context Compress

Applique une compression structuree du contexte pour maintenir les performances et reduire les tokens sans perte d'information critique.

## Quand declencher

- Le contexte actif depasse **60% de la fenetre du modele**
- L'utilisateur demande explicitement ("compresse", "resume pour continuer")
- Avant de passer un long contexte a un sous-agent (handoff)
- En prevention, toutes les 20-30 interactions dans une session longue

## Principe : compression structuree plutot qu'agressive

> Regle d'or (Agent-Skills-for-Context-Engineering) : la metrique a optimiser est **tokens-par-tache**, pas **tokens-par-requete**. Une compression qui fait perdre un detail crucial oblige a redemander -> +tokens.

## Template de compression

Structurer la sortie en 5 sections strictes :

```markdown
## Contexte compresse

### 1. Objectif utilisateur
<1-2 phrases sur ce que l'utilisateur cherche a accomplir>

### 2. Decisions actees
- <decision 1 : ce qui a ete tranche et pourquoi>
- <decision 2>

### 3. Fichiers / ressources touches
- <chemin/fichier> : <etat actuel>
- <url/doc> : <statut>

### 4. Etat courant
<ce qui vient juste d'etre fait, quel est le dernier output>

### 5. Prochaines etapes identifiees
1. <etape immediate suivante>
2. <etape apres>
3. <blocages eventuels>
```

## Regles de compression

- **Ne jamais** compresser les messages des **2 derniers tours** (ils contiennent le contexte immediat actif).
- **Ne jamais** perdre les **chemins de fichiers**, **noms de variables critiques**, **URLs**, **identifiants**.
- **Toujours preserver** les specs/contraintes negociees (ex : "le budget est 5000 euros", "doit etre compatible SAFARI 14").
- **Compresser aggressivement** les echanges informatifs / reformulations / diagnostics intermediaires.

## Ratio cible

Viser **10-20% du contexte initial**. Au-dela de 30%, la compression est insuffisante. En dessous de 5%, risque de perte d'info.

## Apres compression

1. Presenter la compression a l'utilisateur et demander validation avant d'en faire l'unique source de verite.
2. Archiver le contexte complet original dans `~/.token-optimizer/context-archive/<timestamp>.md` pour rollback.
3. Mentionner dans le prompt aux agents suivants : "Contexte compresse disponible - fichier original archive".

## Integration avec superpowers

Si le plugin `superpowers` est actif, cette compression alimente le pattern "handoff" utilise par les sous-agents de TDD/review/merge. Le format ci-dessus est compatible.
