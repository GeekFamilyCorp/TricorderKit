# TricorderKit — Workflow & Agent Operating Standard
> Version 1.0 — 2026-05-18
> Complément au `docs/04_LLM_OPERATING_GUIDE.md` — à lire **après** la séquence de démarrage obligatoire.
> Source : généré par `script.py` (GeekFamilyCorp) — intégré au repo le 2026-05-18.

---

## 🧭 Workflow Orchestration

### 1. Plan Mode Default

Entrer en mode plan pour **toute tâche non triviale** (3 étapes ou plus, décision architecturale, modification d'un contrat ou d'un plugin).

**Procédure :**
1. Écrire le plan dans `tasks/todo.md` avec des items cochables avant toute implémentation
2. Valider le plan mentalement ou avec l'utilisateur si la tâche touche l'architecture, les contrats, les manifests ou l'infrastructure Docker
3. Exécuter étape par étape en cochant au fil de l'eau
4. Si quelque chose déraille → **STOP. Re-plan immédiat.** Ne pas continuer à pousser.
5. Utiliser le mode plan aussi pour les étapes de **vérification**, pas seulement pour la construction

```markdown
# tasks/todo.md — Plan <NOM_TÂCHE> — <DATE>
## Objectif
<description concise>

## Étapes
- [ ] Étape 1 — <action précise>
- [ ] Étape 2 — <action précise>
- [ ] Étape 3 — <action précise>

## Preuve de fin attendue
<test / log / output CLI / health check>

## Résultat (à remplir après)
- Statut : ✅ / ❌ / ⚠️ partiel
- Écarts : <aucun / liste>
- Décision loguée : DEC-XXX (si applicable)
```

---

### 2. Subagent Strategy

Déléguer systématiquement hors du contexte principal pour préserver la fenêtre de contexte.

**Déléguer à un sous-agent quand :**
- Exploration large d'une base de code ou d'un vault
- Recherche documentaire (sources, APIs, versions)
- Analyse parallèle de plusieurs fichiers non liés
- Tâche de longue durée sans dépendance au contexte courant

**Règles :**
- **1 sous-agent = 1 tâche** (focalisé, sortie déterministe)
- Le sous-agent produit un output JSON ou Markdown structuré, **jamais une réponse conversationnelle**
- Résultat du sous-agent → indexé dans vault Obsidian ou logué dans `tasks/todo.md`
- **NOUVEAU (2026-05-18) :** Toute sortie de sous-agent injectée dans le contexte principal doit être en **caveman lite** — JSON structuré ou Markdown tabulaire. Jamais prose narrative.

```
Exemple de délégation :
  Tâche principale : mettre à jour source-watch-goat
  Sous-agent A     : rechercher l'API REST MangaDex (endpoints, rate limits, pagination)
  Sous-agent B     : auditer l'existant source-watch-goat (commandes déclarées vs implémentées)
  Fusion           : main context intègre les 2 outputs et implémente
```

**Template spawn sous-agent :**
```
Objectif : [UNE action, UNE sortie]
Scope : [fichiers/URLs concernés — PAS de lecture large]
Output attendu : JSON|Markdown tabulaire — JAMAIS prose narrative
Format retour : { "status": "ok|error", "data": {...}, "tokens_used": N }
Contrainte tokens : budget max [N] tokens de sortie
```

---

### 3. Self-Improvement Loop

Après **toute correction de l'utilisateur**, mettre à jour `tasks/lessons.md`.

**Format d'entrée dans `tasks/lessons.md` :**

```markdown
## LESSON-<NNN> — <DATE>
**Contexte :** <situation où l'erreur s'est produite>
**Erreur :** <ce qui s'est mal passé>
**Règle préventive :** <règle concrète pour éviter la répétition>
**Fichiers concernés :** <liste si applicable>
```

**Ritual de session :**
- Lire `tasks/lessons.md` **au démarrage** (après `.planning/DECISIONS.md`, avant d'agir)
- Appliquer chaque règle active comme une contrainte non-négociable
- Ne jamais supprimer une leçon — la marquer `[RÉSOLU]` si la cause racine est éliminée dans le code

---

### 4. Verification Before Done

**Jamais marquer une tâche comme terminée sans prouver qu'elle fonctionne.**

| Type de tâche | Preuve attendue |
|---|---|
| CLI / goat ajouté ou modifié | `python <goat>.py --dry-run <cmd>` → JSON propre |
| Workflow Temporal | Worker RUNNING + activité enregistrée confirmée dans les logs |
| Skill créée ou modifiée | `/tk:eval-skill <nom>` → statut `success` |
| Infra Docker | `docker compose ps` → tous les services `healthy` |
| Script Python | `pytest tests/` → zéro échec ou échecs documentés dans `RISKS.md` |
| Documentation | Diff entre ancien et nouveau contenu, relecture du paragraphe modifié |
| Décision architecturale | Entrée DEC-XXX dans `.planning/DECISIONS.md` créée et relue |

**Question de contrôle avant de conclure :**
> *"Un staff engineer approuverait-il ce changement tel quel ?"*

---

### 5. Demand Elegance (Balanced)

Pour tout changement **non trivial** : marquer une pause et se demander :
> *"Y a-t-il une solution plus élégante ?"*

Si un fix semble hacky :
> *"En tenant compte de tout ce que je sais maintenant, implémenter la solution élégante."*

**Ne pas appliquer** pour les corrections simples et évidentes — éviter le sur-engineering.

**Critères d'élégance dans TricorderKit :**
- Minimal impact : ne toucher que les fichiers nécessaires
- Pas de duplication : vérifier `plugins/cli-forge/generated/` et `skills/` avant de créer
- Root cause : corriger la cause, pas le symptôme
- Contrat respecté : output compatible avec `core/contracts/skill_output.schema.json`
- Dry-run first : toute commande write doit avoir un dry-run disponible

---

### 6. Autonomous Bug Fixing

Face à un bug report : **fixer directement**. Ne pas demander de guidage supplémentaire.

**Procédure :**
1. Localiser la preuve (logs, test échoué, output CLI, traceback)
2. Identifier la cause racine — pas le symptôme
3. Planifier le fix minimal dans `tasks/todo.md`
4. Implémenter
5. Vérifier avec le même test ou log qui avait révélé le bug
6. Logger dans `.planning/RISKS.md` si le bug révèle un risque systémique

**Zéro context-switch utilisateur requis** pour les niveaux de risque LOW et MEDIUM.
Pour les niveaux HIGH et CRITICAL : présenter le plan et attendre validation avant d'agir.

---

## 📋 Task Management Protocol

### Séquence d'exécution standard

```
1. PLAN   → écrire tasks/todo.md (items cochables)
2. VERIFY → valider le plan si impact architectural
3. TRACK  → cocher les items au fil de l'eau
4. REPORT → résumé haut niveau à chaque étape majeure
5. REVIEW → écrire le bilan dans tasks/todo.md
6. LEARN  → mettre à jour tasks/lessons.md après correction
```

---

## 🔑 Core Principles (Reformulation TricorderKit)

| Principe | Formulation TricorderKit |
|---|---|
| **Simplicity First** | CLI déterministe > appel LLM brut. Contrat JSON > improvisation. 1 fichier = 1 responsabilité. |
| **No Laziness** | Toujours identifier la cause racine. Jamais de fix temporaire sans ticket dans `RISKS.md`. |
| **Minimal Impact** | Ne toucher que le strict nécessaire. Vérifier que l'existant couvre déjà le besoin avant de créer. |

---

## 🔄 Séquence de démarrage mise à jour (v1.0)

```
1. README_FIRST.md
2. docs/00_WHAT_IS_TRICORDERKIT.md        (si disponible)
3. docs/01_HOW_IT_WORKS.md                (si disponible)
4. docs/02_WHAT_IS_IN_PLACE.md            (si disponible)
5. docs/03_WHAT_TO_DO_NEXT.md             (si disponible)
6. .planning/STATE.md                     ← état courant
7. .planning/DECISIONS.md                 ← 5 dernières seulement (immuables)
8. tasks/lessons.md                       ← appliquer toutes les règles actives
9. Identifier la demande
10. Écrire tasks/todo.md                  ← plan avant action
11. Agir
```

> **Note :** docs/00→04 sont en cours de migration vers v0.8. En attendant, consulter
> `TricorderKit_v0.7/docs/` ou le `README.md` principal.

---

## ⚠️ Règles non-négociables (complément aux Règles 1-7 du guide LLM)

| # | Règle | Sanction si violée |
|---|---|---|
| R8 | Toute tâche ≥ 3 étapes → plan écrit dans `tasks/todo.md` avant toute implémentation | Arrêt et retour au plan |
| R9 | Si déraillement → STOP et re-plan immédiat, jamais de continuation aveugle | Re-plan obligatoire |
| R10 | Déléguer exploration et recherche large à un sous-agent | Risque de context overflow |
| R11 | Jamais `done` sans preuve observable | Réouverture de la tâche |
| R12 | Après correction utilisateur → `tasks/lessons.md` mis à jour dans la même session | Dette de connaissance |
| R13 | Bug report → fix autonome sans demander de guidage (LOW/MEDIUM risk) | Non-respect du contrat d'autonomie |
| R14 | Fix hacky détecté → reformuler vers la solution élégante avant de committer | Refactoring forcé |
| R15 | Sortie sous-agent injectée dans contexte principal → caveman lite obligatoire | Gaspillage tokens |

---

*TricorderKit Workflow Standard v1.0 — GeekFamilyCorp — 2026-05-18*
*Compatible avec TricorderKit v0.7 / v0.8 — Complément au `docs/04_LLM_OPERATING_GUIDE.md`*
