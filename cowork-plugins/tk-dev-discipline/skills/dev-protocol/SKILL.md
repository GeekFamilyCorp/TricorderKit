---
name: dev-protocol
description: >-
  Applique un protocole de développement discipliné à une tâche non triviale : brainstorm socratique
  → spec courte → plan écrit avec checkpoints → implémentation incrémentale par sous-agents avec
  revue à deux étages (conformité puis qualité) → tests → vérification avant de déclarer terminé →
  ship. À utiliser quand l'utilisateur veut "faire les choses dans l'ordre", "spec d'abord", "un
  plan avant de coder", "approche rigoureuse", "TDD", "revue avant merge", ou dès qu'une tâche
  touche plus d'un fichier OU écrit en prod, sur le VPS ou dans le vault. Phase 1 délègue le cadrage
  à tk-dev-discipline:interview-me ; la porte finale délègue à doubt-driven-development. Ne pas
  utiliser pour un correctif trivial en une étape et un seul fichier (faire direct), ni pour
  corriger/durcir une app existante sans nouvelle fonctionnalité → code-corrector.
license: Proprietary
metadata:
  version: "2.0"
  author: GeekFamilyCorp
  langues: fr
  inspiration: "obra/superpowers (design seulement, aucun import de code)"
---

# dev-protocol — brainstorm → spec → plan → implémentation → tests → revue → ship

Transforme « code-moi ça » en une séquence traçable avec une porte à chaque étape. Chaque phase
ci-dessous est **autonome** : les instructions suffisent sans autre skill, sauf deux délégations
explicites (phase 1 → `tk-dev-discipline:interview-me`, porte finale → `doubt-driven-development`).

Règles citées (R53 : confirmation avant action irréversible ou externe ; R16 : grep des tests avant
commit ; R50 : revue pré-push ; R57/R58 : déléguer si parallélisable, quota par dispatch) — définitions
dans `${CLAUDE_PLUGIN_ROOT}/references/regles.md`.

## Seuil d'application (vérifiable)

Appliquer le protocole si **au moins une** condition est vraie :
- la tâche modifiera **plus d'un fichier** ;
- la tâche écrit en **production**, sur le **VPS** ou dans le **vault** (quelle que soit la taille).

Sinon : faire directement, sans cérémonie. Sur-cadrer est un défaut.

## Phase 1 — Brainstorm socratique (porte : intention validée)

Objectif : comprendre ce que l'utilisateur veut *vraiment* avant de proposer quoi que ce soit.
1. Reformuler la demande en une phrase et la faire confirmer.
2. Si la demande est sous-spécifiée → déléguer à `tk-dev-discipline:interview-me` (une question à la fois,
   jusqu'à ~95 % de confiance). Sinon poser soi-même, une par une, les questions qui restent :
   pourquoi maintenant ? qu'est-ce qui existe déjà ? qu'est-ce qui ne doit surtout pas changer ?
   comment saura-t-on que c'est réussi ?
3. Proposer **2 ou 3 approches** avec leurs compromis (simplicité, risque, réversibilité), recommander
   une, laisser choisir.
Porte : l'utilisateur confirme l'intention et l'approche. Pas de spec avant.

## Phase 2 — Spec courte (porte : spec approuvée)

Rédiger, dans un fichier ou un bloc unique, 5 rubriques et rien de plus :
**Objectif** (1 phrase) · **Périmètre** (fichiers/services touchés) · **Non-objectifs** (ce qu'on ne fait
pas, explicitement) · **Critères d'acceptation** (vérifiables : commande + résultat attendu) ·
**Risques et rollback** (que se passe-t-il si ça casse, comment on revient en arrière).
Porte : approbation humaine si écriture prod/VPS/vault ; sinon auto-validation après relecture.

## Phase 3 — Plan écrit avec checkpoints (porte : plan revu)

Découper en **tâches de 15 à 60 minutes**, chacune avec : fichiers touchés, test qui la prouve,
dépendances, parallélisable ou non. Ajouter un **checkpoint** après chaque tâche à risque (« ici on
s'arrête et on vérifie X avant de continuer »). Le plan est un fichier daté que l'on met à jour au
fil de l'exécution — c'est ce qui permet la reprise inter-sessions (R62).
Porte : relecture du plan avec un regard adverse — quelle tâche cache un piège ? où manque un test ?

## Phase 4 — Implémentation incrémentale par sous-agents (porte : chaque incrément passe)

Pour chaque tâche du plan :
1. **Dispatcher un sous-agent** avec un brief autonome : contexte minimal, fichiers précis, critère
   d'acceptation, interdictions (pas de prod, pas de secret, pas de refacto hors périmètre), quota
   (R58). Les tâches indépendantes partent en parallèle, jamais deux tâches lourdes ensemble.
2. **Revue à deux étages**, par un agent frais ou soi-même après pause :
   - **Étage 1 — conformité** : le résultat fait-il exactement ce que la tâche demandait, ni plus ni
     moins ? Un ajout non demandé est un défaut, même utile. Retour au sous-agent si non.
   - **Étage 2 — qualité** : lisibilité, simplicité, cas limites, absence de duplication, tests
     présents et pertinents. Seulement après l'étage 1.
3. **Commit atomique** par tâche, message décrivant le *pourquoi*. Cocher la tâche dans le plan.
Porte : l'incrément compile, ses tests passent, le plan est à jour.

## Phase 5 — Tests (porte : tests verts, preuve exécutable)

- Un test par comportement, écrit **avant** le code quand c'est possible (rouge → vert → refacto).
- Les critères d'acceptation de la spec deviennent des tests ou des commandes de vérification.
- Avant commit : grep des tests touchés (R16), exécution complète de la suite concernée.
Porte : sortie de la suite de tests collée dans le plan, pas « ça passe » de mémoire.

## Phase 6 — Revue globale (porte : revue OK)

Relire l'ensemble du diff (`git diff main...HEAD`) selon trois axes, dans cet ordre :
sécurité (entrées non validées, secrets, contrôles affaiblis) → simplicité (ce qui peut être retiré) →
cohérence (nommage, conventions du dépôt, docs à jour). Pour un dépôt public, vérifier la frontière
R37 (aucun chemin personnel, aucun secret) avant de continuer.

## Phase 7 — Vérification avant de déclarer terminé, puis ship

**Verification-before-completion** : ne jamais dire « c'est fait » sans avoir, dans cette session,
(a) relancé la commande qui prouve le critère d'acceptation, (b) relu la sortie, (c) comparé au résultat
attendu de la spec. Une affirmation sans sortie collée ne vaut rien (R51).
Porte finale : si la tâche écrit en prod/VPS/vault → passer par `doubt-driven-development` (trois
modes d'échec, dry-run, rollback prêt) avant le GO ; le push ou le déploiement n'a lieu qu'après GO
explicite (R53).

## Exemple de tâche cadrée

Demande : « ajoute un export CSV des fiches validées ».
- **Seuil** : 3 fichiers (route, service, test) → protocole appliqué.
- **Phase 1** : reformulation « exporter en CSV les fiches au statut `verifie`, depuis l'API » ;
  questions : encodage attendu (UTF-8 BOM pour Excel ?), volume (pagination ou flux ?), qui y accède ?
  Trois approches : endpoint synchrone / génération par flux / tâche différée. Recommandation : flux.
- **Phase 2** : objectif, périmètre (`api/export.py`, `services/fiches.py`, `tests/test_export.py`),
  non-objectifs (pas d'export XLSX, pas de filtre par date), critères (`curl /export.csv | head -3`
  rend l'en-tête + 2 lignes ; 10 000 fiches en < 5 s), rollback (retirer la route).
- **Phase 3** : T1 service de sélection (test unitaire) · T2 sérialisation CSV en flux (test sur 3 fiches
  avec virgule et guillemet) · checkpoint : mesurer sur 10 000 · T3 route + auth.
- **Phase 4** : T1 et T2 en parallèle par deux sous-agents ; revue conformité (T2 avait ajouté un
  paramètre `delimiter` non demandé → retiré) puis qualité.
- **Phase 5-7** : suite verte (sortie collée), diff relu, commande de critère relancée, pas d'écriture
  prod → pas de passage par doubt-driven-development. Livraison.

## Changelog
- **2026-09-07 — 2.0** : phases réécrites en instructions autonomes (brainstorm socratique, spec en 5
  rubriques, plan avec checkpoints, sous-agents + revue à deux étages, verification-before-completion) ;
  seuil vérifiable ; délégations réduites à `interview-me` et `doubt-driven-development` ; exemple
  complet ; frontmatter normalisé.
- **2026-06 — 1.0** : version initiale (orchestrateur vers des skills non installés).
