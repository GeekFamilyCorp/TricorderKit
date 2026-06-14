# AUDIT — Intégration des 5 fichiers d'amélioration (juin 2026)

> Type : audit + plan priorisé · Cible : `.planning/` (interne)
> Date : 2026-06-01 · Auteur : assistant TricorderKit · Statut : proposition (non appliqué)
> Source : analyse des fichiers `02_PRIORITY`, `03_Obsidian Memory`, `04_Pipeline-RAG`, `05_Zero-Token Cost`, `06_plan d'amelioration`
> Axes demandés : économie de tokens · multi-sessions · mémoire & auto-apprentissage

---

## 1. Verdict synthétique

Sur les ~30 idées techniques contenues dans les 5 fichiers, **environ 70 % décrivent des mécanismes déjà construits dans TricorderKit v0.9.** Les fichiers ont une grande valeur comme *cadre conceptuel* et *checklist de maturité*, mais peu de leur contenu est « à ajouter ».

Le gisement réel se concentre sur **quatre chantiers** :

| # | Chantier | Fichier source | Statut repo | Effort | Impact | Priorité |
|---|---|---|---|---|---|---|
| G1 | Registre Central canonique (dédup à la source + slicing par ID) | 02 | ✅ **Déjà construit** (à durcir) | Faible | Moyen | **P3** |
| G2 | Routeur SLM local (Ollama/Qwen, zero-token) | 05 + 06§4 | 🔴 Absent | Moyen | **Élevé** | **P1** |
| G3 | RAG hybride dense+sparse + RRF + re-ranking | 04 | 🔴 Absent (graphify doc-only) | Moyen-élevé | Moyen | **P2** |
| G4 | Janitor : archivage à froid + cap descriptions MCP 2 Ko + supergateway | 06 | 🟠 À vérifier / non automatisé | Faible-moyen | Moyen | **P2/P3** |

> **Mise à jour 2026-06-01 (vérification vault).** G1 reclassé : le Registre Central **existe déjà** dans le vault projet lie et il est plus mûr que le fichier 02. Voir section 3-G1. Conséquence : les seuls vrais *builds neufs* sont **G2** (prioritaire) puis **G3** ; G1 devient un *durcissement* (P3), G4 reste optionnel.

Tout le reste est **déjà couvert** (section 2) et ne justifie pas de travail neuf, au plus un *renforcement de règle* dans `CLAUDE.md`/`AGENTS.md`.

---

## 2. Ce qui est DÉJÀ couvert (à ne pas reconstruire)

| Idée des fichiers | Couverture actuelle dans le repo |
|---|---|
| Session Digest / Crash Buffer / Hot Caching (03 §3, 06) | `BOOT_SUMMARY.md` (~500 tok vs ~13 500), `memory-boot`/HOT_CACHE, `tk rapport`, Session Rotation Policy (CLAUDE.md) |
| Mémoire procédurale `CLAUDE.md`/`AGENTS.md` (03 §2) | Présents et actifs, avec boot tiers lazy-load |
| Pont sémantique MCP Obsidian (03 §1) | MCP `obsidian-claude-vault` + `obsidian-vault-lie` actifs |
| Séparation Inbox/Wiki, raw→synthèse (03 §2, 06 §2) | `obsidian-agent-layer` + `deep-research-core` (ingestion async) |
| Bascule Supabase / Obsidian (03 §5) | Schéma Supabase linked_project (29 tests), notes de synthèse seules dans le vault |
| GraphRAG / Wikilinks (03 §7) | `graphify` (Neo4j + Qdrant, DEC-009) — *conception faite, pipeline à coder (voir G3)* |
| Token Hygiene Guard / slicing / filtrage Bash (03 §6, 06 §1) | `core/mainbrain` token guard, `rtk` (CLI-compress), `token-savior`, budget guard T1/T2/T3 |
| Profils d'exécution MCP (03 §11) | skill `claude-code-router` (routage Cowork→tk-orchestrator) |
| Pattern Gateway / Manager-Worker (03 §12-13) | Partiellement : `tk-orchestrator` + sous-agents ; le *Gateway MCP* unique reste une option (voir G4) |
| Workflow fiable / reprise sur crash (03 §6) | `workflow-engine` (Temporal), worker RUNNING |
| Éval & trace (Braintrust/Langfuse) (06 PART2) | `eval-lab` + Langfuse actif :3001 |
| Compression sortie / caveman / context-compress | plugin `token-optimizer` v0.8 complet |
| Consolidation mémoire | skill `consolidate-memory` |

**Conséquence :** refuser toute proposition de « réimplémenter » l'un de ces points (Règle 6 — interdiction de recréation). Seuls G1–G4 ouvrent un travail neuf.

---

## 3. Les quatre chantiers réels

### G1 — Registre Central canonique (P3 — DÉJÀ CONSTRUIT, à durcir)

**Constat (vérifié dans le vault, 2026-06-01).** Le pattern du fichier 02 est **déjà opérationnel**, et plus abouti que ce que 02 propose :
- `00_System/03_Manifestes_Migration/99_MASTER_INDEX.md` — Master Index canonique **complet, 1 232 entrées, généré chaque nuit, 0 anomalie** (tâche 02h).
- Index typés par rubrique (ex. `01_Mangas & Light Novels/index.md`) avec frontmatter `prefixe_id`/`work_id` et **protocole anti-doublon déjà écrit** : « Ne jamais créer de doublon. Vérifier ici avant toute création. ID = work_id ». Colonnes ID/Romaji/JP/Auteur(MG)/Éditeur(ED)/Magazine/Status + règle d'ajout en 5 étapes.
- **Registre de Liaison** cross-média (manga↔anime) + registre de sources normalisé (`10_Registry_Routing/05_Registry_Normalise/35_Normalized_Registry.md`).

Donc : **rien à créer.** Le slicing par ID et la dédup à la source existent.

**Résidu réel (durcissement, P3).** Deux risques de cohérence subsistent :
1. **Double couche d'index.** La règle « vérifier avant création » pointe vers l'`index.md` partiel (curé main, ~17 lignes affichées côté manga), alors que l'exhaustif est dans `99_MASTER_INDEX.md`. Un agent qui ne contrôle que l'index partiel peut rater une œuvre existante → faux négatif → doublon. → **Faire du `99_MASTER_INDEX` (ou un index `work_id` interrogeable) la source de vérité opposable pour la dédup.**
2. **Attribution d'ID.** Règle écrite « dernier MA + 1 » (manuelle) vs `goat next-id` (R34). IDs épars (MA001…MA996) ⇒ « last+1 » lit mal le vrai max. → **Aligner sur `goat next-id` lisant le max réel depuis le Master Index** (Règle 2 — CLI avant LLM).
3. *(Bonus)* dédup exacte uniquement ⇒ rate les variantes de translittération (lié à R29-R31). Une passe fuzzy romaji/JP dans le job de nuit fermerait l'écart.

**Risk Guard : LOW.** Modif de règle (`AGENTS.md` + en-tête des `index.md`) + ajustement du job de nuit, pas de nouveau moteur.

### G2 — Routeur SLM local zero-token (P1 — prioritaire validé)

**Constat.** `model-router` et `claude-code-router` font du routage **côté Claude** (donc facturé en tokens). Le fichier 05 propose de déporter la *décision de routage* (quel vault / quel profil MCP) sur un petit modèle local gratuit (Qwen 2.5 3B ou Llama 3.2 3B via Ollama, < 2,5 Go RAM, `keep_alive: 0`). Confirmé absent du repo.

**Recommandation.** Monter un PoC `local-router` (livré avec cet audit, section 5) :
- script gateway Python interceptant le prompt → appel Ollama en *Structured Outputs* (JSON garanti, `temperature: 0`) → choix du profil → lancement de l'agent avec la bonne config MCP.
- profils MCP séparés (Knowledge/RAG, Scraping/Ingestion, Dev/Audit) — réduit le « Tool Schema Bloat » (03 §10).

**Gain :** la décision de routage et de pré-chargement de contexte ne consomme plus de tokens Claude ; Claude ne fait que le raisonnement final à haute valeur. **Risk Guard : MEDIUM** (dépendance locale Ollama, machine i5/16 Go — d'où `keep_alive: 0`). PoC isolé, aucun couplage au code existant.

### G3 — RAG hybride dense + sparse + RRF + re-ranking (P2)

**Constat.** `graphify` est aujourd'hui **doc-only** (README/SKILL/manifest, aucun pipeline). Le fichier 04 fournit une implémentation de référence : Qdrant (dense) + BM25 (sparse) → fusion RRF → re-ranking cross-encoder, n'injectant que 2-3 chunks à Claude.

**Recommandation.** Implémenter le pipeline dans `graphify` en réutilisant Qdrant déjà actif (:6333) :
- index dense (modèle d'embedding local, ex. `nomic-embed-text` via Ollama → mutualise G2) + index sparse (BM25 ou natif Qdrant BM42/Splade) ;
- fonction `search_vault(query)` exposée en *tool* MCP renvoyant uniquement le Top-N re-rangé.

**Gain :** réduit « lost in the middle » et hallucinations, coupe encore les tokens d'entrée. **Risk Guard : MEDIUM** (nouveau code + tests). Dépend partiellement de G2 (Ollama pour embeddings).

### G4 — Janitor + hygiène MCP (P2/P3)

**Constat (vérifié dans le `claude-vault`, 2026-06-01).** La *structure* et le *protocole* d'archivage existent (`60_ARCHIVE/` Processed+Deprecated, `40_ERRORS`, `50_METRICS`, `ARCHIVE_INDEX.md` : règle « status: archived » + « Daily Logs > 90 j » + « jamais supprimer »), **mais aucune automatisation** : l'archive est vide (« Aucune note archivée — vault initialisé le 2026-04-04 »), aucune routine de compression en embeddings, aucune tâche planifiée janitor sur le claude-vault. Donc : règle écrite, exécution manuelle, pas de garbage collection programmé. Descriptions MCP non plafonnées ; transport STDIO par défaut.

**Recommandation.**
- **P2 — Cap descriptions MCP à 2 Ko** : audit des serveurs MCP les plus chargés, compression des champs `description` (03 §14, 06). ROI immédiat sur tokens d'entrée à chaque tour.
- **P2 — Janitor** : routine hebdo (Temporal) compressant les anciens logs/erreurs en embeddings et ne gardant que le dernier Session Digest chaud.
- **P3 — supergateway / Streamable HTTP** : convertir les MCP STDIO en Streamable HTTP pour le parallélisme des sous-agents (06 PART2). À évaluer seulement si goulots d'étranglement constatés.

**Risk Guard : LOW à MEDIUM.**

---

## 4. Plan priorisé par axe demandé

### Axe « économie de tokens »
1. **G4-cap** Plafond descriptions MCP 2 Ko — *quick-win* (ROI à chaque tour).
2. **G2** Routeur local (décision de routage hors facturation).
3. **G3** RAG hybride (n'injecter que 2-3 chunks).
4. **G1-durcissement** dédup contre le Master Index complet (évite la relecture inutile).

### Axe « multi-sessions »
- Déjà solide (BOOT_SUMMARY, rotation, memory-boot). **Renforcement** : ajouter au protocole de fin de session l'écriture systématique d'un *Session Digest* compact + la mise à jour du Master Index (déjà nocturne) comme dernière action (cohérence inter-fils).

### Axe « mémoire & auto-apprentissage »
- **G1-durcissement** : faire du `99_MASTER_INDEX` la source de vérité opposable pour la dédup (anti-dérive R29-R31).
- **G3** (GraphRAG opérationnel) donne la mémoire relationnelle (note → concept parent → projet).
- **Renforcement auto-apprentissage** : router les leçons (`tasks/lessons.md`, patterns d'erreurs ARCH/ENV/OPS) vers un index interrogeable par le RAG, pour que les règles préventives soient *récupérées* au lieu d'être rechargées en bloc.

### Séquencement recommandé
```
Sprint 1 (prioritaire)        : G2 PoC routeur local (PoC livré → industrialisation)
                                + G4-cap descriptions MCP (quick-win token)
Sprint 2 (mémoire)            : G3 RAG hybride dans graphify (réutilise Ollama de G2)
Sprint 3 (durcissement)       : G1 dédup vs Master Index complet + alignement goat next-id
Sprint 4 (optionnel)          : G4 janitor + supergateway si goulots constatés
```

---

## 5. Entrées DECISIONS proposées (à logger après validation)

> Dernière décision existante : DEC-020. Numérotation proposée à partir de DEC-021.

- **DEC-021** — *(reformulé après vérif vault)* Durcir le Registre Central **existant** : faire de `99_MASTER_INDEX.md` la source de vérité opposable pour la dédup (au lieu de l'`index.md` partiel), aligner l'attribution d'ID sur `goat next-id` (R34), ajouter une passe fuzzy romaji/JP au job de nuit. Justification : fermer le risque de faux négatif / doublon (R29-R31). Statut proposé : *à valider*.
- **DEC-022** — Introduire un routeur SLM local (Ollama/Qwen 2.5 3B) pour la décision de routage zero-token, en complément (non remplacement) de `model-router`. Statut proposé : *PoC validé → décision d'industrialisation*.
- **DEC-023** — Implémenter le pipeline RAG hybride (dense+sparse+RRF+cross-encoder) dans `graphify`, sur Qdrant existant. Statut proposé : *à valider*.
- **DEC-024** — Politique d'hygiène MCP : plafond 2 Ko sur les descriptions + routine janitor hebdo Temporal. Statut proposé : *à valider*.

---

## 6. Garde-fous appliqués

- **Règle 6 (interdiction recréation)** : G3 vérifié — `graphify` doc-only, pas de pipeline existant. G2 vérifié — aucune réf. Ollama/Qwen dans `token-optimizer`/skills.
- **Règle 2 (CLI avant LLM)** : G1 s'appuie sur `goat next-id` pour l'attribution d'ID.
- **Règle 4 (dry-run)** : toute écriture vault issue de ces chantiers passera par `--dry-run`.
- **Routage dépôts (DEC-016)** : pipeline/CLI/skills → depot-exec-lie ; framework/orchestration générique → TricorderKit ; aucune donnée de fiche dans ce dépôt.
- **Anonymisation** : ce document évite les chemins personnels ; le PoC (section 5 livrée séparément) est paramétrable (profils génériques, pas de noms de vault en dur).

---

## 📊 Notes de fiabilité

| Élément | Niveau | Base |
|---|---|---|
| `graphify` doc-only (pas de sparse/RRF/rerank) | ✅ Confirmé | `ls`/`grep` sur `plugins/graphify` (3 fichiers .md/.yml, 0 match rerank/bm25/rrf) |
| Routeur local absent (model-router côté Claude) | ✅ Confirmé | `model-router` présent, 0 réf. ollama/qwen/llama dans `token-optimizer` |
| `claude-code-router` = routage côté Claude | ✅ Confirmé | lecture SKILL.md |
| Registre central canonique **déjà construit** | ✅ Confirmé | vault projet lie via MCP : `99_MASTER_INDEX.md` (1 232 entrées, nocturne, 0 anomalie), `index.md` typés par rubrique avec protocole anti-doublon, Registre de Liaison cross-média, `35_Normalized_Registry.md` |
| Double couche d'index (risque faux négatif dédup) | ✅ Confirmé | `index.md` partiel (~17 lignes manga) ≠ `99_MASTER_INDEX` exhaustif ; la règle de dédup pointe vers le partiel |
| Janitor non automatisé | ✅ Confirmé | `claude-vault` via MCP : structure + protocole d'archivage présents (`60_ARCHIVE`, `ARCHIVE_INDEX.md`, `40_ERRORS`, `50_METRICS`) mais archive vide, aucune routine de compression embeddings, aucune tâche planifiée janitor |

**Écarts résiduels levés** : G1 (registre central) existe → reclassé durcissement P3 ; G4 (janitor) = protocole écrit mais automatisation absente → gap confirmé. Plus aucun point « à vérifier » ouvert.

*Fin de l'audit — proposition non appliquée. Aucune modification du code existant.*
