---
name: doubt-driven-development
description: >-
  Soumet une décision non triviale à une revue adverse à contexte frais AVANT de la valider — trois
  modes d'échec concrets, recoupement sur la source réelle, réversibilité vérifiée, dry-run. À
  utiliser quand la justesse prime sur la vitesse : opération irréversible (écriture en masse,
  purge, push prod, modification d'un service ou d'un timer), logique sensible, terrain inconnu, ou
  toute affirmation d'état faite de mémoire. Usage manuel (déclenchement explicite) pour ne pas
  ralentir les tâches simples. Déclencheurs : "doute", "vérifie cette décision", "es-tu sûr", "revue
  adverse", "stress-test", "avant de pousser/purger/écrire en masse". Ne pas utiliser pour cadrer
  une demande floue AVANT qu'une décision existe → tk-dev-discipline:interview-me, ni pour dérouler
  tout un développement → dev-protocol (qui appelle ce skill en porte finale).
license: MIT
metadata:
  version: "1.1"
  author: GeekFamilyCorp
  langues: fr
---

# Doute méthodique — vérifier avant de valider

Douter maintenant coûte moins que déboguer après. Règles citées (R51 : recouper l'état réel ;
R53 : confirmer avant irréversible ; R22 : deux échecs identiques → changer de méthode ; R31 :
NO-DROP) — définitions dans `${CLAUDE_PLUGIN_ROOT}/references/regles.md`.

## Quand l'appliquer
Toute décision qui remplit **une** de ces conditions :
- **irréversible ou coûteuse à défaire** : écriture en masse, purge, suppression, push en production,
  modification d'un service qui tourne, d'un timer, d'une tâche planifiée ;
- **sensible** : touche à l'authentification, aux secrets, aux données d'autrui, à un contrat d'API ;
- **terrain inconnu** : code, machine ou outil qu'on n'a pas encore manipulé dans cette session ;
- **affirmation d'état de mémoire** : « ça tourne », « c'est déjà fait », « le fichier existe » sans
  l'avoir vérifié aujourd'hui.

## Frontières
- **Avant** ce skill : si l'intention elle-même est floue, ce n'est pas une décision à stresser mais une
  demande à cadrer → `tk-dev-discipline:interview-me`. Le doute s'applique à une décision **formulée**.
- **Séquence** : dans `dev-protocol`, ce skill est la **porte finale** (phase 7) avant tout GO d'écriture
  prod/VPS/vault. Il ne remplace pas les phases spec/plan/tests ; il les stresse.
- **Après** : si la revue révèle un bug, passer à `debugging-and-error-recovery`.

## Protocole (contexte frais)
1. **Énoncer** la décision en une phrase + l'hypothèse qui la fonde.
2. **Posture adverse** — « comment ça échoue, corrompt, ou se révèle faux ? » → écrire **3 modes
   d'échec concrets**, chacun avec le symptôme qu'on observerait.
3. **Recouper sur la source réelle (R51)** : machine, fichiers, compteurs, dry-run — jamais le cache
   ni la mémoire de session.
4. **Réversibilité (R53, R31)** : backup ? rollback documenté ? archive plutôt que suppression ?
   Si non → la créer **avant** de continuer.
5. **Dry-run ou petit lot** avant le réel ; comparer attendu vs obtenu, chiffres à l'appui.
6. **Décider** : GO seulement si les 3 modes d'échec sont couverts ; sinon corriger, ou demander
   confirmation explicite (R53) en exposant le mode non couvert.

## Exemple — les trois modes d'échec
Décision : « renommer en masse 400 fichiers du vault pour normaliser les ID ».
| Mode d'échec | Symptôme observable | Couverture |
|---|---|---|
| Collision : deux fichiers normalisent vers le même nom | le second écrase le premier, count final < 400 | lister les cibles avant, refuser si doublon |
| Backlinks cassés : les `[[liens]]` pointent vers l'ancien nom | notes orphelines dans Obsidian | réécrire les liens dans la même passe, compter avant/après |
| Mauvais dossier : le script tourne sur une copie ou un archivage | aucun changement dans le vault réel, ou changement dans `_ARCHIVE` | afficher le chemin absolu + hostname, exiger confirmation |
Dry-run sur 10 fichiers → 10 renommés, 37 liens réécrits, 0 collision → GO sur le lot complet, archive
datée des originaux créée d'abord.

## Heuristiques
- « Ça marchait avant » n'est pas une preuve d'aujourd'hui.
- Un succès silencieux sur données réelles est suspect : vérifier l'effet, pas le code de sortie.
- Deux échecs avec la même approche → STOP et changer de méthode (R22).

## Anti-patterns
Confiance par défaut sur l'irréversible. Sauter le dry-run « parce que c'est évident ». Valider sans
backup ni rollback. Stresser une décision qui n'est pas encore formulée (c'est du cadrage).

## Changelog
- **2026-09-07 — 1.1** : §Quand généralisé (quatre conditions) ; cas concrets du projet d'origine retirés de
  la version publique ; exemple des trois modes d'échec ; frontières écrites avec
  `interview-me` et `dev-protocol` ; `disable-model-invocation` (usage manuel) ; frontmatter normalisé.
- **2026-07 — 1.0** : version initiale.
