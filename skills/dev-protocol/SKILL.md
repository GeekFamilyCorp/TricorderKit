---
name: dev-protocol
description: Protocole de développement discipliné pour une tâche non triviale : brainstorm → spec → plan → implémentation incrémentale (pilotée par sous-agents) → TDD → revue → ship. À utiliser quand l'utilisateur veut "faire les choses dans l'ordre", "spec d'abord", "un plan avant de coder", "approche disciplinée/rigoureuse", "TDD", "revue avant merge", ou quand une tâche est assez grosse/risquée pour mériter un cadrage. Orchestrateur : il SÉQUENCE et DÉLÈGUE aux skills existants, il ne les refait pas. Inspiré d'obra/superpowers (design, pas d'import de code). NE PAS utiliser pour un correctif trivial en une étape (overkill).
version: "1.0"
author: claude
---

# dev-protocol — Cadrage discipliné brainstorm → spec → plan → TDD → review → ship

> Transforme « code-moi ça » en une séquence **traçable et vérifiable**, avec une porte à chaque étape.
> C'est un **orchestrateur** : chaque phase délègue au bon skill existant (spec-driven, planning,
> incremental, TDD, code-review, shipping, head-agent, canal_agents). On ne duplique pas ces skills,
> on les met en ordre — et on s'arrête aux portes pour validation humaine quand l'enjeu le justifie.

## Quand l'appliquer
- Tâche **> 1 fichier** ou **à risque** (prod, sécurité, irréversible, code inconnu). Sinon : faire direct.

## Les phases (avec porte de sortie)
1. **Brainstorm / clarifier** — cerner l'intention réelle, les contraintes, le « pourquoi maintenant ».
   Si flou : 1 question à la fois (cf. `interview-me`). *Porte : intention validée.*
2. **Spec** — rédiger une spécification courte (objectif, périmètre, non-objectifs, critères d'acceptation).
   Déléguer à `spec-driven-development`. *Porte : spec approuvée (humain si enjeu).* 
3. **Plan / découpage** — tâches ordonnées, dépendances, ce qui est parallélisable. `planning-and-task-breakdown`.
   *Porte : plan revu.*
4. **Implémentation incrémentale** — petits incréments livrables ; déléguer les sous-tâches indépendantes à
   des **sous-agents** (`head-agent` / Task) et, pour le multi-agents, au bus `canal_agents`.
   `incremental-implementation`. *Porte : chaque incrément compile/passe.*
5. **TDD** — un test par comportement (rouge → vert), preuve exécutable. `test-driven-development`.
   *Porte : tests verts.*
6. **Revue** — revue multi-axes (qualité, sécurité, simplicité) avant merge. `code-review-and-quality`,
   `security-and-hardening`, et les **gates R37/R38** du repo. *Porte : revue OK + gates vertes.*
7. **Ship** — checklist de lancement, rollback, observabilité. `shipping-and-launch`. *Porte : déployable.*

## Garde-fous
- **Adaptatif** : sauter les phases inutiles pour une petite tâche ; ne pas sur-cadrer (l'overkill est un défaut).
- **Portes humaines** sur ce qui est structural/risqué/irréversible (cohérent avec code-corrector / agent-config-audit).
- **Anti-duplication** : ce skill **n'implémente pas** spec/plan/TDD/review — il les **séquence** et délègue.
- **Traçabilité** : journaliser décisions et étapes là où la boucle de réflexion existe (reflection/learning-engine).
- **R37** : générique, aucun terme/chemin privé dans le repo public.
