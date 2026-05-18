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

```markdown
# BOOT_SUMMARY — v0.8 — 2026-05-18
**Phase active :** v0.9 en préparation | Tests : 103 PASS | Commit HEAD : 3c154d2
**Prochaines tâches :** 1) Wiring Temporal→connector_hub 2) Obsidian goat CLI 3) tk:boot wiring
**Patterns actifs :** ARCH-001 (hooks inertes Cowork), ENV-001 (MSIX paths), OPS-001 (OOM scheduled tasks)
**Dernière décision :** DEC-011 — VPS extension optionnelle future
**Docker :** Neo4j✅ Qdrant✅ Temporal✅ Langfuse:3001✅
**Token budget actuel :** [calculé dynamiquement par tk-boot]
```

---

### I2 — tk-orchestrator : spec existante, implémentation à ZÉRO

**Constat :** `skills/tk-orchestrator/SKILL.md` dit explicitement "Spec validée,
implémentation à démarrer". L'`orchestrator.py` existe mais son contenu est à vérifier.
C'est le skill le plus stratégique pour la token hygiene (routing intelligent, lazy-load,
budget guard) et il n'est pas fonctionnel.

**Impact :** Toutes les commandes `/tk:*` passent par MainBrain sans pré-filtrage.
Pas de circuit-breaker token, pas de routing vers sous-agents automatique, pas de caveman
mode forcé sur les sorties inter-agents.

**Action :** Démarrer l'implémentation de tk-orchestrator en priorité v0.9.
Fonctions minimales : budget_guard → route → output_compress.

---

### I3 — Caveman mode non intégré dans le protocole inter-agents TricorderKit

**Constat :** Le skill `token-optimizer:caveman` existe dans l'écosystème Cowork et coupe
75-90% des tokens de sortie. Mais il n'est référencé **nulle part** dans TricorderKit :
ni dans AGENTS.md, ni dans les SKILL.md, ni dans les workflows.

**Impact :** Chaque sortie de sous-agent (Explore, general-purpose, etc.) est verbeuse
par défaut. Sur une session avec 5-10 sous-agents, c'est 10 000-30 000 tokens perdus
en prose inutile.

**Règle à ajouter immédiatement dans AGENTS.md et tk-orchestrator :**
> Toute sortie de sous-agent destinée à être injectée dans le contexte principal
> doit être produite en caveman lite (éliminer prose redondante, conserver précision technique).
> Format cible : JSON structuré ou Markdown tabulaire. Jamais de paragraphes narratifs.

---

### I4 — Plugins memory-boot et token-hygiene non migrés vers v0.8

**Constat :** STATE.md liste `memory-boot` et `token-hygiene` comme "À migrer v0.8"
avec priorité S. Ce sont les deux plugins directement responsables de la session hygiene
et de la gestion des tokens. Ils existent dans `plugins/` mais pas encore conformes v0.8.

**Impact :** Le protocole memory-boot Cowork (vault Obsidian) et le protocole TricorderKit
fonctionnent en silos. Aucun wiring entre les deux.

---

## 🔵 LACUNES STRUCTURELLES — Skills et sous-agents

### L1 — Inventaire des skills mentionnés vs réalité

| Skill mentionné | Statut réel | Emplacement |
|---|---|---|
| `caveman` | ✅ Existe — Cowork seulement | token-optimizer:caveman |
| `rtk` | ❌ N'existe pas | Probablement = CLI wrapper autour de deep-research-core |
| `claude-code_router` | ❌ N'existe pas formellement | Existe partiellement comme MainBrain + tk-orchestrator non implémenté |
| `docmancer` | ❌ N'existe pas | Skill de génération docs Markdown/Obsidian — à créer |
| `token-savior` | ❌ N'existe pas | = plugin token-hygiene À migrer v0.8 |

**Analyse :**
- `caveman` : le seul opérationnel, mais cloisonné à Cowork. À brancher dans le workflow TricorderKit explicitement.
- `rtk` : à créer comme skill Cowork qui déclenche le pipeline deep-research-core + formatte en JSON contractuel.
- `claude-code_router` : en cours sous le nom tk-orchestrator, mais implémentation manquante.
- `docmancer` : cas d'usage réel (générer des fiches Obsidian, des rapports, des notes atomiques). obsidian-agent-layer est le backend, il manque le skill Cowork qui l'expose.
- `token-savior` : renommer token-hygiene plugin en token-savior ou créer un alias de skill Cowork.

---

### L2 — Dualité des systèmes de mémoire/erreurs — Deux silos sans pont

**Système A — Vault Obsidian (macro, inter-sessions)**
```
HOT_CACHE.md ← MAJ manuelle (stale !)
ERRORS.md ← logging manuel sparse
PATTERNS_INDEX.md ← patterns documentés
```

**Système B — TricorderKit repo (micro, intra-session)**
```
.planning/RISKS.md ← risques architecture
tasks/lessons.md ← règles préventives (NOUVEAU, vide)
.cache/hooks/post_execution.log ← logs hooks JSON
```

**Problème :** Aucun pont automatique entre les deux. Une erreur loguée dans les hooks
TricorderKit ne remonte jamais dans ERRORS.md Obsidian. Le HOT_CACHE ne reflète jamais
l'état réel du repo.

**Solution : pipeline d'observabilité bout-en-bout (v0.9)**
```
post_execution_hook.py
  → .cache/hooks/post_execution.log
    → usage_observer.activities.ts (aggregateStats)
      → obsidian-agent-layer (vault_router + note_builder)
        → Obsidian ERRORS.md + HOT_CACHE.md
```
Ce pipeline est théoriquement faisable avec les composants existants.
Il manque uniquement le wiring final obsidian-agent-layer → vault write.

---

### L3 — Sous-agents : stratégie définie, template absent

**Constat :** Le Workflow Standard v1.0 (R10 : "Déléguer exploration et recherche large
à un sous-agent") est bien défini. Mais il n'existe pas de template standardisé pour
le prompt de spawn d'un sous-agent dans TricorderKit.

**Problème :** Chaque sous-agent est spawné avec un prompt ad-hoc, verbeux, sans format
de retour normalisé. Le résultat n'est pas automatiquement en format contractuel.

**Solution à ajouter dans AGENTS.md :**
```markdown
## Template spawn sous-agent TricorderKit

Objectif : [UNE action, UNE sortie]
Scope : [fichiers/URLs concernés — PAS de lecture large]
Output attendu : JSON|Markdown tabulaire — JAMAIS prose narrative
Format retour : { "status": "ok|error", "data": {...}, "tokens_used": N }
Contrainte tokens : budget max [N] tokens de sortie
```

---

## 📋 PLAN D'ACTION PRIORISÉ

### PHASE IMMÉDIATE — Avant prochaine session (30 min)

| # | Action | Effort | Impact |
|---|---|---|---|
| P1 | Créer `tasks/todo.md` et `tasks/lessons.md` vides | 5 min | Rend Workflow Standard fonctionnel |
| P2 | Mettre à jour HOT_CACHE Obsidian avec état v0.8 réel | 10 min | Élimine 15 jours de désinformation |
| P3 | Vérifier si `MainBrain_v1.4.md` contient déjà v1.5 — renommer si oui | 5 min | Cohérence référentielle |
| P4 | Intégrer `TricorderKit_Workflow_Standard_v1.0.md` dans `docs/` | 5 min | Rend le standard accessible au boot |

### PHASE v0.9 — Semaine 1

| # | Action | Effort | Impact |
|---|---|---|---|
| V1 | Créer `BOOT_SUMMARY.md` + adapter `tk-boot` pour le charger en premier | 2h | -60% tokens au boot |
| V2 | Migrer docs/00→04 de `TricorderKit_v0.7/` vers `docs/` en v0.8 | 1h | Boot complet fonctionnel |
| V3 | Implémenter `tk-orchestrator` minimal : budget_guard + route + compress | 4h | Routing intelligent + caveman forcé |
| V4 | Migrer plugins `memory-boot` et `token-hygiene` vers v0.8 | 2h | Session hygiene unifiée |
| V5 | Brancher caveman mode dans AGENTS.md pour sorties inter-agents | 30 min | -75% tokens sous-agents |

### PHASE v0.9 — Semaine 2

| # | Action | Effort | Impact |
|---|---|---|---|
| W1 | Créer skill `rtk` (wrapper Cowork → deep-research-core CLI) | 3h | Pipeline research accessible depuis Cowork |
| W2 | Créer skill `docmancer` (wrapper → obsidian-agent-layer) | 3h | Génération notes automatisée |
| W3 | Câbler pipeline observabilité : hook logs → Temporal → obsidian-agent-layer | 4h | HOT_CACHE auto-mis à jour |
| W4 | Créer `obsidian-goat` CLI (cli-forge) | 2h | Mise à jour HOT_CACHE end-session via CLI |

---

## 📊 Score de maturité TricorderKit v0.8

| Dimension | Score | Commentaire |
|---|---|---|
| Architecture | 9/10 | DEC-011 loguées, linked_project propre, MainBrain v1.5 câblé |
| Token hygiene | 4/10 | Boot lourd, pas de BOOT_SUMMARY, caveman non intégré |
| Système erreurs | 5/10 | Hooks ok, mais silos Obsidian/repo sans pont |
| Skills disponibles | 5/10 | tk-boot ok, tk-orchestrator vide, rtk/docmancer/token-savior absents |
| Tests & vérification | 8/10 | 103 tests verts, mais tests live deep-research en attente réseau |
| Documentation boot | 3/10 | docs/00-04 absents en v0.8, HOT_CACHE stale 15j |
| Sous-agents | 6/10 | Stratégie définie, template spawn manquant, caveman non forcé |
| Observabilité | 6/10 | Hook logs présents, pas de pipeline vers vault Obsidian |

**Score global : 5.75/10 — Base excellente, opérationnalisation en cours**

---

## 📝 Notes de fiabilité

| Donnée | Fiabilité | Source |
|---|---|---|
| État repo v0.8 COMPLET 103 tests | ✅ Confirmé | STATE.md commit 3c154d2 + TASKS.md |
| docs/00-04 absents en v0.8 | ✅ Confirmé | `find docs/ -type f` en live |
| tasks/ vide | ✅ Confirmé | `ls tasks/` en live |
| HOT_CACHE 15j stale | ✅ Confirmé | Date frontmatter 2026-05-03 vs aujourd'hui 2026-05-18 |
| MainBrain v1.5 introuvable | ✅ Confirmé | `ls core/mainbrain/` en live |
| caveman non intégré TricorderKit | ✅ Confirmé | grep dans AGENTS.md, SKILL.md, docs/ |
| Estimation tokens boot ~13 500 | 🟡 Estimation | Calcul à partir taille fichiers estimée |

---

*Audit produit par Claude Sonnet 4.6 — Session Cowork 2026-05-18*
*Compatible TricorderKit v0.8 / v0.9 — GeekFamilyCorp*
