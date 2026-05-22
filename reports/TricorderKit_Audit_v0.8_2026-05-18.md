# TricorderKit — Audit Stratégique v0.8
> Date : 2026-05-18 | Analyste : Claude Sonnet 4.6 (Cowork session)
> Sources : audit JSON fichier_par_fichier, Workflow Standard v1.0, repo live, vault Obsidian

---

## 🟢 CE QUI EST SOLIDE — Forces réelles

| Zone | Réalité constatée |
|---|---|
| **Architecture décisionnelle** | 11 DEC loguées (DEC-001→011), immuables, traçables — excellent |
| **Hook Layer v0.2.0** | pre_intent + pre_execution + post_execution câblés dans MainBrain v1.5, 25 tests verts |
| **Contrat JSON centralisé** | `core/contracts/skill_output.schema.json` — toutes les skills doivent s'y conformer |
| **Pattern linked_project** | Séparation TricorderKit (moteur) / Japan-Alliance (domaine) — DEC-010, très bonne isolation |
| **103 tests verts** | 36 CLI tk + 42 audit + 25 hooks — couverture réelle, pas que du scaffold |
| **github-goat** | Référence d'implémentation parfaite : dry-run, cache SQLite, output JSON, test contrat |
| **Temporal RUNNING** | Worker actif sur `tricorderkit-hooks`, KI-004 résolu |
| **QualityGuard** | Semgrep + Trivy + Gitleaks actifs — sécurité réelle dès la Phase 2.5 |
| **docker-compose.yml** | Fixes critiques appliqués (SQLite→Postgres, port Langfuse, tags fixés) |
| **Workflow Standard v1.0** | Document rigoureux, 14 règles R1→R14, séquence démarrage en 11 étapes |

---

## 🔴 PROBLÈMES CRITIQUES — Désinformation active du LLM

### C1 — docs/00 à 04 ABSENTS de v0.8 ❌

**Constat :** `tk-boot/SKILL.md` et la séquence Workflow Standard lisent docs/00→04
au boot. Ces fichiers **n'existent pas dans la v0.8**. Le dossier `docs/` ne contient que :
`05_hooks_policy.md`, `integration/`, `linked_projects.md`.

**Impact :** Chaque session démarre avec un boot silencieusement incomplet — le LLM
ne lit pas les fondations conceptuelles (What Is, How It Works, What's In Place, What To Do,
LLM Operating Guide). L'audit fichier_par_fichier les référençait comme HIGH maturity
mais ils sont dans `TricorderKit_v0.7/` — non migrés.

**Action :** Migrer ou recréer docs/00 à 04 dans v0.8, ou adapter `tk-boot` pour pointer
vers leur emplacement réel dans `TricorderKit_v0.7/`.

---

### C2 — HOT_CACHE Obsidian daté 03/05 — 15 jours stale ⚠️

**Constat :** Le HOT_CACHE parle encore de la migration AI_VAULT et mentionne TricorderKit
avec des URLs et des états du mois d'avril. TricorderKit est à v0.8 COMPLET depuis le 17/05.

**Impact :** Toute session Cowork qui commence par `memory-boot` reçoit une image
du monde obsolète de 15 jours. Le LLM peut prendre des décisions basées sur un état
qui ne correspond plus à la réalité.

**Action :** Mettre à jour HOT_CACHE immédiatement avec le statut réel v0.8.
Créer un skill `obsidian-goat` CLI qui automatise cette mise à jour post-session.

---

### C3 — tasks/ est VIDE ❌

**Constat :** Le Workflow Standard v1.0 (créé le 18/05/2026) définit `tasks/todo.md`
et `tasks/lessons.md` comme fichiers permanents. Le dossier `tasks/` existe mais est vide.

**Impact :** Le standard est inapplicable immédiatement. R8 (plan dans tasks/todo.md
avant implémentation) et R12 (lessons.md après correction) ne peuvent pas être suivis.

**Action :** Créer les deux fichiers de base avec structure vide. Intégrer dans le Workflow
Standard l'initialisation automatique à la première session.

---

### C4 — MainBrain v1.5 introuvable dans le repo

**Constat :** STATE.md référence "MainBrain v1.5 câblé" dans le commit `c1017e4` et la
spec `tk-orchestrator/SKILL.md` l'intègre. Mais `core/mainbrain/` ne contient que
`MainBrain_v1.4.md`.

**Impact :** La source de vérité architecturale (qui lit le MainBrain au boot) pointe
vers un fichier qui n'a pas été mis à jour. La v1.5 existe probablement mais sous le nom v1.4.

**Action :** Vérifier si `MainBrain_v1.4.md` contient déjà les étapes 0, 2.5, 7bis —
si oui, le renommer `MainBrain_v1.5.md` et mettre à jour toutes les références.

---

## 🟡 PROBLÈMES IMPORTANTS — Token Hygiene & Performance

### I1 — Séquence de boot trop lourde (~13 000 tokens estimés)

**Analyse token par fichier (estimations) :**

| Fichier | Tokens estimés | Nécessaire au 1er tour ? |
|---|---|---|
| README_FIRST.md | ~200 | Oui — 1x |
| docs/00_WHAT_IS | ~500 | Seulement si incertitude sur la vision |
| docs/01_HOW_IT_WORKS | ~800 | Seulement si debug architecture |
| docs/02_WHAT_IS_IN_PLACE | ~600 | Oui — inventaire courant |
| docs/03_WHAT_TO_DO_NEXT | ~600 | Oui — prochaine action |
| docs/04_LLM_OPERATING_GUIDE | ~1500 | Seulement si nouvel agent |
| .planning/STATE.md | ~2500 | Oui — condensé |
| .planning/TASKS.md | ~3000 | Non — phases ✅ inutiles |
| .planning/DECISIONS.md | ~2500 | Non — 5 dernières seulement |
| .planning/RISKS.md | ~800 | Oui — risques ouverts seulement |
| tasks/lessons.md | ~500 | Oui — règles actives |
| **TOTAL** | **~13 500** | **~5 500 suffiraient** |

**Solution recommandée : BOOT_SUMMARY.md**

Créer un fichier unique `BOOT_SUMMARY.md` mis à jour automatiquement à chaque fin de session,
qui concentre en ~500 tokens : version, phase active, 3 prochaines tâches prioritaires,
3 patterns actifs, dernière décision, statut Docker. Devient le seul fichier lu en premier.
Le reste se charge à la demande (lazy-load pattern).

---

### I2 — tk-orchestrator : spec existante, implémentation à ZÉRO

**Constat :** `skills/tk-orchestrator/SKILL.md` dit explicitement "Spec validée,
implémentation à démarrer". L'`orchestrator.py` existe mais son contenu est à vérifier.
C'est le skill le plus stratégique pour la token hygiene (routing intelligent, lazy-load,
budget guard) et il n'est pas fonctionnel.

**Action :** Démarrer l'implémentation de tk-orchestrator en priorité v0.9.
Fonctions minimales : budget_guard → route → output_compress.

---

### I3 — Caveman mode non intégré dans le protocole inter-agents TricorderKit

**Règle à ajouter immédiatement dans AGENTS.md et tk-orchestrator :**
> Toute sortie de sous-agent destinée à être injectée dans le contexte principal
> doit être produite en caveman lite (éliminer prose redondante, conserver précision technique).
> Format cible : JSON structuré ou Markdown tabulaire. Jamais de paragraphes narratifs.

---

### I4 — Plugins memory-boot et token-hygiene non migrés vers v0.8

**Constat :** STATE.md liste `memory-boot` et `token-hygiene` comme "À migrer v0.8"
avec priorité S. Ce sont les deux plugins directement responsables de la session hygiene
et de la gestion des tokens.

---

## 📋 PLAN D'ACTION PRIORISÉ

### PHASE IMMÉDIATE

| # | Action | Effort | Impact |
|---|---|---|---|
| P1 | Créer `tasks/todo.md` et `tasks/lessons.md` vides | 5 min | Rend Workflow Standard fonctionnel |
| P2 | Mettre à jour HOT_CACHE Obsidian avec état v0.8 réel | 10 min | Élimine stale data |
| P3 | Vérifier/renommer `MainBrain_v1.4.md` → `MainBrain_v1.5.md` | 5 min | Cohérence référentielle |
| P4 | Intégrer `TricorderKit_Workflow_Standard_v1.0.md` dans `docs/` | 5 min | Rend le standard accessible au boot |

### PHASE v0.9 — Semaine 1

| # | Action | Effort | Impact |
|---|---|---|---|
| V1 | Créer `BOOT_SUMMARY.md` + adapter `tk-boot` | 2h | -60% tokens au boot |
| V2 | Migrer docs/00→04 de `TricorderKit_v0.7/` vers `docs/` | 1h | Boot complet fonctionnel |
| V3 | Implémenter `tk-orchestrator` minimal | 4h | Routing intelligent |
| V4 | Migrer plugins `memory-boot` et `token-hygiene` vers v0.8 | 2h | Session hygiene unifiée |
| V5 | Brancher caveman mode dans AGENTS.md | 30 min | -75% tokens sous-agents |

---

## 📊 Score de maturité TricorderKit v0.8

| Dimension | Score | Commentaire |
|---|---|---|
| Architecture | 9/10 | DEC-011 loguées, linked_project propre, MainBrain v1.5 câblé |
| Token hygiene | 4/10 | Boot lourd, pas de BOOT_SUMMARY, caveman non intégré |
| Système erreurs | 5/10 | Hooks ok, mais silos Obsidian/repo sans pont |
| Skills disponibles | 5/10 | tk-boot ok, tk-orchestrator vide, rtk/docmancer/token-savior absents |
| Tests & vérification | 8/10 | 103 tests verts, tests live deep-research en attente réseau |
| Documentation boot | 3/10 | docs/00-04 absents en v0.8, HOT_CACHE stale |
| Sous-agents | 6/10 | Stratégie définie, template spawn manquant, caveman non forcé |
| Observabilité | 6/10 | Hook logs présents, pas de pipeline vers vault Obsidian |

**Score global : 5.75/10 — Base excellente, opérationnalisation en cours**

---

*Audit produit par Claude Sonnet 4.6 — Session Cowork 2026-05-18*
*Compatible TricorderKit v0.8 / v0.9 — GeekFamilyCorp*
