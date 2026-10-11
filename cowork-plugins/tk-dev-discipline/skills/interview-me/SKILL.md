---
name: interview-me
description: "Extrait ce que l'utilisateur veut réellement par un entretien une-question-à-la-fois (outil AskUserQuestion), jusqu'à ~95 % de confiance sur l'intention, le périmètre, les contraintes, le critère de réussite et le format de livrable, AVANT tout plan, spec ou code. Usage manuel : 'interroge-moi', 'cadre ma demande', 'es-tu sûr d'avoir compris', 'stress-test mon idée', 'pose-moi les bonnes questions', ou quand la demande est sous-spécifiée et qu'on se surprend à combler des trous. Ne pas utiliser quand la demande est déjà claire et détaillée, ni quand la décision est déjà prise et qu'il faut la challenger (→ tk-dev-discipline:doubt-driven-development)."
license: MIT
metadata:
  version: "1.1"
  author: GeekFamilyCorp
  domain: cadrage
  activation: manuel
  updated: "2026-09-07"
---

# interview-me — Cadrer avant d'exécuter

> Évite de partir sur la mauvaise piste. Chaque question passe par l'outil **`AskUserQuestion`** (choix multiples concrets quand c'est possible, question ouverte sinon).

## Principe
- **Une question à la fois**, sur la plus grande incertitude restante. Attendre la réponse.
- S'arrêter à ~95 % de confiance sur : le quoi, le pour-qui/pourquoi, les contraintes (coût, réversibilité, délai), le critère de réussite, le format de livrable.
- Reformuler l'intention en une phrase et la faire valider avant de lancer.

## Ordre (priorité à l'ambiguïté qui change l'action)
1. Intention réelle — le problème sous-jacent, pas la solution demandée.
2. Périmètre et priorité — dans / hors scope ; quoi en premier.
3. Contraintes GFC — zéro coût ? réversible / NO-DROP (R31) ? poste saturé → VPS ? prod ou dry-run ? public ou privé (R37) ?
4. Critère de réussite — « réussi si… ».
5. Format de livrable — fichier ? script ? note vault ? où ?

## Heuristiques
- Une réponse qui ouvre une incertitude majeure → la traiter avant de continuer.
- Décision déjà prise, il faut la tester → ce n'est plus un entretien : `doubt-driven-development`.
- Ton : vouvoiement, efficace, challengeant, exécutant dès que l'instruction est claire.

## Anti-patterns
4 questions d'un coup · interroger alors que c'est déjà clair · combler les trous en silence · reformuler la solution demandée sans chercher le problème.

## Exemples (entrée → première question)
1. **« Automatise mes veilles. »** → `AskUserQuestion` : « Quel est le résultat que vous voulez voir chaque semaine ? (a) un rapport Markdown dans le Projet, (b) une note dans le vault, (c) un message dans un canal, (d) autre » — l'intention (à quoi sert la veille) prime sur le mécanisme.
2. **« Nettoie le vault. »** → `AskUserQuestion` : « Que signifie "propre" ici ? (a) doublons d'œuvres fusionnés, (b) liens cassés réparés, (c) frontmatter normalisé, (d) dossiers réorganisés » — le périmètre change l'outil (dedup → `vault-dedup-merge`, structure → `obsidian-vault`) et le risque (NO-DROP).

## Modèles
`default` ; alias dans `${CLAUDE_PLUGIN_ROOT}/models.json`.

## Changelog
### v1.1 — 2026-09-07
- `metadata.version` et `disable-model-invocation: true` (usage manuel). `AskUserQuestion` explicitement l'outil de chaque question. Exclusion « décision déjà prise → doubt-driven-development ». 2 exemples entrée → première question. Contraintes GFC complétées (R31, R37).
### v1.0 — 2026-06-27
- Création : entretien une-question-à-la-fois, ordre de priorité, heuristiques, anti-patterns.
