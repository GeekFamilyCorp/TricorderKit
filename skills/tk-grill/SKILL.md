---
name: tk-grill
description: Interroge l'utilisateur sans relâche sur un plan, un design ou une décision architecturale TricorderKit, en descendant chaque branche de l'arbre de décision une question à la fois, jusqu'à compréhension partagée — puis matérialise le résultat en entrée DEC-NNN routée et journalisée. À utiliser quand l'utilisateur veut stress-tester une décision, « se faire griller » sur un design, instruire un DEC avant de le loguer, ou dès qu'une tâche relève du Risk Guard MEDIUM/HIGH/CRITICAL. Ne PAS utiliser pour le remplissage de fiches de domaine (déléguer aux skills de lookup de domaine) ni pour une simple récupération factuelle.
---

# tk-grill — Interrogation socratique alignée TricorderKit

> Version : 0.1.0 — 2026-06-03
> Ancrage : TricorderKit v0.9 · AGENTS.md v0.8 · DEC-016 (routage) · Risk Guard
> Origine : adaptation maison de `grill-me` (mattpocock/skills) — interrogation socratique
> réinstrumentée pour produire une décision **déterministe, traçable et routée**, pas une simple conversation.

---

## 🎯 Rôle & déclencheurs

tk-grill prend un plan/design encore flou et le **résout branche par branche** par interrogation,
chaque question accompagnée d'une **réponse recommandée**. Contrairement à `grill-me` générique,
il ne s'arrête pas à « compréhension partagée » : il **atterrit** sur une entrée `DEC-NNN` prête à
coller dans `.planning/DECISIONS.md`, route le livrable (DEC-016) et propose la mise à jour d'état.

### Déclencheurs
- Naturels : `grille-moi`, `grill me`, `stress-test`, `instruis ce DEC`, `poke des trous`, `challenge ce design`
- Commande : `/tk:grill <sujet>`
- **Automatique** : toute tâche évaluée Risk Guard **MEDIUM / HIGH / CRITICAL** déclenche tk-grill avant exécution.

### Ce qu'il N'EST PAS
- ❌ Un outil de recherche factuelle (déléguer aux skills de lookup de domaine).
- ❌ Un générateur de fiches.
- ❌ Un exécutant : il **instruit** la décision, il ne l'applique pas. L'application reste un acte séparé et explicite.

---

## ⚙️ Pré-vol obligatoire (avant la 1re question)

1. **Lire le contexte décisionnel** : `.planning/DECISIONS.md` (5 dernières + toute entrée liée au sujet).
   → Si le sujet recoupe un DEC **Appliquée** ou **Révoquée**, le signaler immédiatement : on n'instruit pas une décision déjà tranchée (règle « interdiction de recréation »).
2. **Lire l'état** : `.planning/STATE.md` (phase active) et `.planning/TASKS.md` (items `pending`/`in_progress` liés).
3. **Interdiction de recréation** : vérifier `plugins/cli-forge/generated/`, `skills/`, `plugins/workflow-engine/` — si la chose existe déjà, le grill porte sur l'évolution, pas la création.
4. **CLI avant LLM** : si une CLI `goat`/`tk` répond déjà à la question, l'exécuter au lieu de demander.
5. **Classer le Risk Guard** du sujet (LOW/MEDIUM/HIGH/CRITICAL) — il fixe la profondeur du grill et le gate de sortie.

> Si un point est répondable par exploration du repo ou des `.planning`, **explorer au lieu de demander**.

---

## 🔄 Protocole d'interrogation

Règles dures :
- **Une seule question à la fois.** Jamais de salve.
- **Chaque question porte une réponse recommandée** (« Reco : … parce que … »), pour combler le gap, pas seulement le pointer.
- **Descendre l'arbre de décision** : résoudre les dépendances entre choix une par une, ne pas sauter en aval tant qu'un nœud amont est ouvert.
- **Explorer plutôt que demander** dès que le repo/.planning contient la réponse.
- **S'arrêter** quand tous les nœuds de l'arbre sont résolus OU quand l'utilisateur dit « stop / ça suffit / loggue ».

### Vagues de grill (ordre canonique TricorderKit)
Adapter au sujet, mais couvrir au minimum ces axes — ce sont les gardes-fous non négociables du projet :

| Vague | Question-noyau | Garde-fou projet |
|---|---|---|
| 1. Cadrage | Quel problème exact, et pourquoi maintenant ? Mesure de succès ? | Évite la solution sans problème |
| 2. Existant | Qu'est-ce qui existe déjà (CLI/skill/workflow/DEC) ? | Interdiction de recréation |
| 3. CLI vs LLM | Une CLI déterministe peut-elle le faire ? | CLI avant LLM |
| 4. Contrat | Format de sortie ? Respecte-t-il `core/contracts/skill_output.schema.json` ? | Output contractuel |
| 5. Routage | Quel dépôt cible (framework générique / repo de domaine) ? | DEC-016 |
| 6. Sûreté | Dry-run prévu ? Réversibilité ? Rollback explicite ? | Dry-run obligatoire |
| 7. Coût | Budget tokens estimé ? Segmentation si > 80 % ? | Token Hygiene |
| 8. Fiabilité | Sources/validation si données externes (2 sources ou primaire) ? | Règles métier du domaine |
| 9. Risque | Niveau Risk Guard final → gate de sortie adapté | Risk Guard |

---

## 🚦 Gate de sortie (selon Risk Guard)

- **LOW** → proposer directement l'entrée DEC + MAJ STATE.
- **MEDIUM** → confirmation courte de l'utilisateur avant de loguer.
- **HIGH** → exiger un **plan explicite** + validation nominative avant toute application ; loguer le DEC en `Statut : Acceptée — application différée`.
- **CRITICAL** → **refus d'atterrir seul** : escalade, on ne loggue qu'après arbitrage explicite de Sébastien.

---

## 📝 Format de sortie (obligatoire)

Markdown propre. Le grill se termine **toujours** par ces deux blocs :

### `## 📋 À copier`
Une entrée `DEC-NNN` prête à coller dans `.planning/DECISIONS.md`, au gabarit maison :
```
## DEC-NNN — <titre> — <AAAA-MM-JJ>
- **Contexte** : …
- **Décision** : …
- **Alternatives écartées** : …
- **Risk Guard** : LOW|MEDIUM|HIGH|CRITICAL
- **Routage (DEC-016)** : <dépôt cible>
- **Dry-run / rollback** : …
- **Reste à faire** : …
- **Statut** : Proposée | Acceptée | Acceptée — application différée
```
Suivi du diff `STATE.md` proposé (1 ligne) et, le cas échéant, de l'item `TASKS.md`.

> `goat next-id` (ou lecture du dernier DEC) **avant** d'attribuer le numéro — jamais d'ID inventé.

### `## 📊 Notes de fiabilité`
- Nœuds de l'arbre **résolus** vs **laissés ouverts** (et pourquoi).
- Hypothèses non vérifiées restantes.
- Sources citées si données externes (URL + date pub + date accès).
- Écart détecté avec un DEC existant, s'il y a lieu.

---

## 🧪 Auto-contrôle avant de rendre

- [ ] Pré-vol fait (DECISIONS + STATE + TASKS lus) ?
- [ ] Aucune question déjà répondable par le repo n'a été posée ?
- [ ] Chaque question avait une réponse recommandée ?
- [ ] Les 9 axes-gardes-fous couverts (ou explicitement écartés comme non pertinents) ?
- [ ] Bloc `## 📋 À copier` + `## 📊 Notes de fiabilité` présents ?
- [ ] Gate de sortie cohérent avec le Risk Guard ?
- [ ] Numéro DEC obtenu via `goat next-id` / dernier DEC, pas inventé ?

---

*tk-grill v0.1.0 — adaptation maison de grill-me, instrumentée pour la gouvernance DEC-NNN de TricorderKit.*
