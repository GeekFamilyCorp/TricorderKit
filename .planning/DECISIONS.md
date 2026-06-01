# DECISIONS.md — TricorderKit v0.7

> Log des decisions architecturales. Ne jamais supprimer une entree.

### DEC-001 — Temporal comme moteur de workflows
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Temporal pour tous les workflows longs (>30s). Local-first, reprise sur erreur.
- Alternatives rejetees : n8n, Activepieces, scripts cron

### DEC-002 — cli-forge avant obsidian-agent-layer
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Phase 2 CLI-first avant Phase 5 obsidian-agent-layer

### DEC-003 — Neo4j pour le graph
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Neo4j comme base graph
- Alternatives rejetees : Memgraph, ArangoDB

### DEC-004 — Qdrant pour le vector
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Qdrant comme base vectorielle
- Alternatives rejetees : ChromaDB, LanceDB

### DEC-005 — Output schema JSON obligatoire
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Chaque skill expose un output.schema.json valide avant usage prod

### DEC-006 — Rate limiting token par workflow
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Chaque workflow definit un token_budget max

### DEC-007 — Regle atomique : 1 idee = 1 node
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Notes Obsidian atomiques 100-500 tokens

### DEC-008 — LangGraph pour les boucles agentiques
- Date : 11/05/2026 | Statut : Acceptee
- Decision : LangGraph pour workflows agentiques courts (<30s). Temporal pour workflows longs (>30s).
- Raison : Temporal = durabilite/reprise. LangGraph = etat agentique, cycles reflect/act/observe. Synergie native avec Neo4j/Graphify.
- Alternatives rejetees : LangGraph seul (pas de durabilite), CrewAI (moins flexible)
- Impact : plugins/workflow-engine/ + plugins/graphify/ state API

### DEC-009 — Graphify : architecture hybride graph+vector
- Date : 11/05/2026 | Statut : Acceptee
- Decision : Interface hybride Neo4j (traversal) + Qdrant (semantique) via point d'entree unique
- Raison : Neo4j = liens structurels. Qdrant = similarite semantique. Les deux sont non-substituables.
- Impact : core/contracts/graph.schema.json + sync automatique Neo4j vers Qdrant a chaque ecriture

### DEC-010 — Pattern linked_project : séparation moteur / domaine
- Date : 17/05/2026 | Statut : Acceptée
- Décision : TricorderKit est un moteur générique anonymisé. Tout ce qui est domaine-spécifique (sources, scrapers, vocabulaire métier, vault privé) vit dans un linked_project privé séparé.
- Règle d'or : **TricorderKit exécute. Le projet lié spécialise.**
- Raison : (1) TricorderKit doit pouvoir être partagé publiquement sans fuites de données privées. (2) Séparer les cycles de vie — le moteur évolue indépendamment du contenu. (3) Permettre plusieurs linked_projects (Japan-Alliance, futurs projets) sur le même moteur.
- Implémentation :
  - `configs/local/linked_projects.yaml` (non versionné) — chemins réels locaux
  - `configs/local/linked_projects.example.yaml` (versionné) — template documentation
  - `docs/linked_projects.md` — convention officielle
  - `templates/linked_project_template/` — template reproductible
  - `tools/audit/linked_project_audit.py` — audit structure + git + config + secrets
  - `tools/audit/local_vs_github_audit.py` — sync local vs GitHub
  - CLI `tk project *` — commandes dédiées linked_project
- Linked projects actifs : **Japan-Alliance** (GeekFamilyCorp/Japan-Alliance — privé) + **MangaTracker** (GeekFamilyCorp/MangaTracker — privé)
- Isolation garantie par :
  - `.gitignore` TricorderKit exclut tous les fichiers locaux non génériques
  - `private_terms` dans `project_config/project.yaml` du linked_project
  - Scan secrets avant push via `linked_project_audit.py`
- Alternatives rejetées : monorepo (couplage fort, risque de fuite), sous-modules Git (complexité, friction workflow)
- Impact : Phase 6 complète — commits `5acec97` (TK) + `d8f8696` (JA)

### DEC-011 — VPS : extension optionnelle future (pas encore déployé)
- Date : 17/05/2026 | Statut : Acceptée — En préparation
- Décision : TricorderKit reste local-first. Un VPS pourra être ajouté comme extension optionnelle pour la persistance longue durée, le scheduling headless et le partage de rapports.
- Principe : le VPS ne remplace pas le local, il complète. La machine locale reste le point de vérité.
- État : `configs/vps/settings.yaml` créé comme template (status: PENDING — non déployé).
- Prochaines étapes VPS : choisir provider → configurer Docker Compose → configurer reverse proxy (Caddy) → sync sélectif reports/ uniquement.
- Alternatives rejetées : Cloud-only (dépendance, coût, latence) — aucune migration forcée.

### DEC-012 — Japan-Alliance = vault pur, MangaTracker = assistant CLI
- Date : 17/05/2026 | Statut : Acceptée
- Décision : Refonte complète de l’architecture linked_projects. Japan-Alliance devient un **vault Obsidian pur** (données uniquement, aucun code exécutable). MangaTracker devient l’**assistant IA dédié** qui absorbe l’intégralité du code, des CLIs, des skills et des pipelines.
- Raison :
  (1) Séparation nette données / logique : Japan-Alliance ne dépend plus d’aucun runtime.
  (2) Japan-Alliance doit être accessible en lecture à plusieurs LLMs (Claude, ChatGPT, Perplexity, Qwen) via API GitHub — un vault pur est plus simple à partager et documenter.
  (3) MangaTracker concentre la complexité opérationnelle et évolue indépendamment du vault.
  (4) Japan-Alliance a vocation à devenir un site web — une structure vault-only est directement exploitable pour la génération statique.
- Migration effectuée (2026-05-17) :
  - Tout le code Python, skills, pipelines, plugins migré vers MangaTracker
  - Japan-Alliance nettoyé : conserve uniquement `vault/`, `templates/`, `README.md`, `CONTEXT.md`
  - `CONTEXT.md` créé dans Japan-Alliance : guide de navigation pour Claude, ChatGPT, Perplexity, Qwen
  - `linked_projects.example.yaml` mis à jour : MangaTracker (type: ai_assistant) + Japan-Alliance (type: obsidian_vault, read_only: true)
- Règle d'or mise à jour : **TricorderKit exécute. MangaTracker spécialise. Japan-Alliance stocke.**
- Impact : STATE.md Phase 6.5 — commits Japan-Alliance (`84dd260`) + TricorderKit (ce commit)

### DEC-013 — Japan-Alliance vault-only strict : aucun fichier .py autorisé
- Date : 2026-05-22 | Statut : Acceptée
- Décision : Japan-Alliance est un vault Obsidian **pur** — aucun fichier `.py` (ni script, ni test, ni conftest) n'est autorisé dans ce repo. Seuls sont autorisés : Markdown (`.md`), YAML (`.yml`), JSON (`.json`), images et assets statiques.
- Raison :
  (1) Renforcement de DEC-012 : la règle vault-only doit être vérifiable mécaniquement (tout `.py` = violation).
  (2) Un conftest.py avait été créé par erreur dans `Japan-Alliance/plugins/deep-research-core/tests/` pour faire fonctionner des imports Python — cette violation a conduit à cette décision explicite.
  (3) Les tests Python et la logique d'orchestration appartiennent à MangaTracker (linked_project assistant IA), pas au vault.
- Règle d'application :
  - `conftest.py`, `test_*.py`, `*.py` → MangaTracker ou TricorderKit
  - Sources YAML (`trusted_sources.yml`, etc.) → Japan-Alliance autorisé (données)
  - CI recommandé : `find Japan-Alliance/ -name "*.py" | grep . && exit 1` dans pre-commit
- Impact : conftest.py supprimé de Japan-Alliance, déplacé dans `MangaTracker/plugins/deep-research-core/tests/` — commit 2026-05-22

### DEC-014 — Correctif routing vault JP : obsidian-notes-vault → obsidian-japan-alliance
- Date : 2026-05-29 | Statut : Acceptée
- Décision : Dans `plugins/obsidian-agent-layer/vault_router.py`, le `mcp_server` de `VaultId.NOTES` est corrigé de `"obsidian-notes-vault"` (serveur MCP inexistant) vers `"obsidian-japan-alliance"` (serveur réellement connecté).
- Raison :
  (1) `obsidian_client.py:155/183` construit la cible MCP à partir de `vault_config.mcp_server` ; tout le contenu JP (manga, anime, seiyuu, studio, mangaka, editeur, magazine, goodie, lieu, evenement) était donc routé vers un serveur fantôme → écriture agent vouée à l'échec / mauvais ciblage.
  (2) `manifest.yml:31` déclarait déjà la bonne valeur (`obsidian-japan-alliance`) — le routeur Python était désynchronisé du manifeste et de la topologie MCP vivante.
  (3) Validation : les tests `test_obsidian_agent_layer.py` assertent sur l'enum `VaultId.NOTES`, pas sur la string MCP → non impactés.
- Découvertes annexes (à arbitrer par Sébastien, non corrigées) :
  - `configs/local/linked_projects.yaml` pointe le vault lié vers `Projects/Japan-Alliance/japan-alliance_vault/` qui est un **dossier vide en lecture seule** (size 0, perms 444) ; le vault de contenu vivant (5421 notes) est en réalité `<vault-path>/Japan-Alliance`.
  - `linked_projects.yaml` active `allow_tricorderkit_write: true` alors que DEC-012/DEC-013 définissent Japan-Alliance comme vault **read-only** ; divergence de politique à trancher.
- Impact : fix local appliqué ; push GitHub en attente de validation (cf. E5).
- Résolution (2026-05-29, arbitrage Sébastien) :
  - Push : différé — le fix sera inclus dans un prochain commit groupé (non poussé seul).
  - `linked_projects.yaml` corrigé sur les deux points : `vault` repointé vers `C:/Users/sebas/Documents/obsidian/Japan-Alliance/` ; `allow_tricorderkit_write` repassé à `false` (conformité DEC-012/DEC-013, vault read-only ; écriture via MangaTracker uniquement).

*Dernière mise à jour : 2026-05-29 — DEC-014 routing fix vault JP + résolution config*

---

## DEC-015 — Enrichissement registre Sources_Officielles (audit Excel v1.6) — 2026-05-29

- **Contexte** : audit du classeur `japan-alliance_tables_sources_complet_v1.6_enriched.xlsx` (41 feuilles, registre normalisé 834 sources) contre les 32 fichiers `Sources_*_Master_v1.md` du vault Japan-Alliance.
- **Constat** : 780/834 sources déjà présentes (URL exacte ou domaine). Priorités #2 (amazon.co.jp) et #3 (LINE jp / LINE Manga / LINE Novel) **déjà couvertes**. Écart réel = 8 sources officielles manquantes (le reste = bruit : URLs `0`, `207`, `variable`).
- **Décision** : ajout des 8 sources officielles/institutionnelles manquantes, en respectant la priorité demandée (éditeurs/studios > amazon.co.jp > LINE). Ajouts datés `## Ajout 2026-05-29` en bas de chaque fichier cible, schémas de tableau respectés par fichier.
- **Sources ajoutées** :
  - Manga : K MANGA (Kodansha, https://kmanga.kodansha.com) · Manga UP! Global (Square Enix, https://global.manga-up.com)
  - Light Novel : Corona EX Global EN (TO Books, https://en.to-corona-ex.com)
  - Doujin/Indie : MANGA Plus Creators (Shueisha/MediBang, https://mangaplus-creators.jp)
  - API/RSS : なろうデベロッパー Syosetu Developer API (Hinaproject, https://dev.syosetu.com)
  - Goodies : 魂ウェブ Tamashii Web (Bandai Spirits, https://tamashiiweb.com)
  - Contrôle/ABJ : Japan ISBN Agency (https://isbn.jpo.or.jp) · MADB Lab (Bunka/MEXT, https://mediag.bunka.go.jp/madb_lab/)
- **Fiabilité** : toutes `confirmé` (opérateur officiel identifié, plateforme primaire). Exclusions strictes respectées (aucun scantrad/wiki/blog).
- **Validation** : 8/8 URLs re-vérifiées présentes dans les fichiers cibles après écriture (`Select-String`).
- **Statut** : Appliquée.

*Dernière mise à jour : 2026-05-29 — DEC-015 enrichissement sources v1.6*

---

## DEC-016 — Doctrine de routage des 3 dépôts + relocalisation du fix DEC-014 — 2026-05-29

- **Contexte** : Sébastien précise la répartition des dépôts GitHub (2026-05-29).
- **Règle de routage** :
  - **TricorderKit** (`github.com/GeekFamilyCorp/TricorderKit`) = framework installable « depuis zéro » + sauvegarde générique + cerveau d'orchestration (`.planning/`, `CLAUDE.md`, `AGENTS.md`, `docs/`, `core/`, plugins génériques, `.gitignore`).
  - **MangaTracker** (`github.com/GeekFamilyCorp/MangaTracker`) = repo du `linked_project` dédié Japon : code de liaison vault (`obsidian-agent-layer/`, `vault_router.py`, `vault_optimizer/`, `linked_projects.yaml`, `hermes/`, CLI/skills/pipelines vault).
  - **Japan-Alliance** (github à créer — **EN ATTENTE**) = sauvegarde du contenu du vault Obsidian Japan-Alliance.
- **Checkpoint de routage (token-light)** : déclenché en **fin d'action/tâche/mise à jour**. Suivre les fichiers touchés pendant la session (pas de scan complet du repo) → `git status --porcelain` du/des repo(s) concerné(s) uniquement → `git add` **ciblé** (jamais `-A`) → 1 commit conventionnel par repo → push. Sauter tout repo non touché.
- **Relocalisation du fix DEC-014** : la valeur `mcp_server="obsidian-japan-alliance"` est de la **spécialisation Japon**, déjà présente dans MangaTracker (`hermes/plugins/obsidian-agent-layer/vault_router.py`, L47). Le fix appliqué dans TricorderKit est donc **superseded** : `vault_router.py` y a été restauré à sa valeur générique (`obsidian-notes-vault`). DEC-014 reste valide pour MangaTracker ; sa portion TricorderKit est superseded par DEC-016.
- **Suivi ouvert** : le dossier `hermes/` de MangaTracker est **non suivi par git** (canonique mais non sauvegardé) → tâche de backup dédiée à arbitrer (volume important, traiter avec revue).
- **Statut** : Appliquée.

*Dernière mise à jour : 2026-05-29 — DEC-016 doctrine routage dépôts*

---

## DEC-017 — Assainissement vault Japan-Alliance : 4 chantiers (correction + back-fill + déduplication par archivage) — 2026-05-29

- **Contexte** : les cartes de filière (MOC franchises + IX000) ont révélé 4 anomalies systémiques dans le vault de contenu `<vault-path>/Japan-Alliance` (non versionné git → toute opération destructrice = HIGH risk → archivage réversible imposé).
- **Chantier 1 — Lien éditeur cassé** : `ED040_shueisha` → `[[ED039_shueisha]]` sur **41 fiches vivantes** (Shueisha). PowerShell déterministe, UTF-8 sans BOM, exclusion `99_Migration_Backups` + `03_Manifestes_Migration`. Vérif : 0 occurrence résiduelle.
  - ⚠️ **PIÈGE ÉVITÉ (leçon majeure)** : un remplacement global naïf `ED040`→`ED039` aurait corrompu `ED040_shufu_to_seikatsu_sha` (主婦と生活社, éditeur légitime distinct). Remplacement ciblé sur le **token complet** `ED040_shueisha` uniquement. → Règle gravée : **avant tout remplacement global d'ID, grep des collisions de préfixe et cibler le token entier**.
- **Chantier 2 — Back-fill relations frontmatter** : ajout `related_anime` sur MA001/MA008/MA017/MA011 + `adaptation_de` bidirectionnel sur AN004/AN005/AN006/AN007/AN010. Schéma **natif des fiches** respecté (≠ schéma idéalisé du MOC) pour éviter une duplication de schéma.
- **Chantier 3 — Déduplication studios (triplement `ST###`/`STU###`/`Par_Studio`)** : canonique = **`ST###`** (fiches riches, schéma propre, bloc validation, numérotation contiguë). 10 stubs `STU001→STU010` (« ## À compléter ») + doublon `ST037_Ufotable` archivés dans `99_Migration_Backups/_dedup_studios_2026-05-29/`. ufotable : `ST024` retenu canonique, **enrichi** du contenu factuel plus riche de `ST037` (fondateur Hikaru Kondō, productions détaillées, projets 2026+, affaire judiciaire) avant archivage. 9 fichiers vivants re-pointés `STU###`→`ST###`.
  - ⚠️ **CORRECTION d'une décision de session antérieure** : les MOC avaient choisi `STU###` comme canonique. La comparaison de **contenu** a montré l'inverse (STU### = stubs). → Règle gravée : **ne jamais déclarer un canonique sur la seule base de l'ID/récence ; comparer le contenu, le nombre de références entrantes et la contiguïté de numérotation**.
- **Chantier 4 — Déduplication LN `LN001`/`LN026` (Apothecary Diaries)** : contenu quasi identique. `LN001` retenu master (ID contigu inférieur + déjà référencé par AN010 et le MOC). Champs QA de `LN026` (qa_template_used, qa_checked_at…) portés dans LN001. `LN026` archivé dans `99_Migration_Backups/_dedup_ln_2026-05-29/`. MOC franchise + IX000 mis à jour.
- **Traçabilité** : claude-vault (Daily Log 2026-05-29 + HOT_CACHE + PATTERN-DEDUP-001) + auto-memory + cette décision. Cartes IX000 et MOC JJK/Apothecary marquées « anomalies résolues ».
- **Réversibilité** : aucune suppression dure. Tous les doublons sont récupérables depuis `99_Migration_Backups/`.
- **Statut** : Appliquée.

*Dernière mise à jour : 2026-05-29 — DEC-017 assainissement vault Japan-Alliance (4 chantiers)*

---

## DEC-018 — Améliorations post-assainissement (garde-fou CLI R29, réconciliation studios, ufotable, fiches Apothecary) + rollout studios planifié — 2026-05-29

- **Contexte** : suite à DEC-017, exécution des 4 améliorations proposées + mise en place d'un rollout quotidien de fiches studios depuis la liste Wikipedia « List of Japanese animation studios ».

- **Amélioration 1 — Garde-fou CLI R29 (anti-collision de préfixe d'ID)** : nouvelle commande déterministe `replace-id` dans `tools/obsidian-goat/obsidian_goat.py` (v0.1.0 → **v0.2.0**). Remplacement **borné au token complet** via lookbehind/lookahead `(?<![\w])…(?![\w])` : un préfixe nu (ex. `ED040`) ne peut plus corrompre un token plus long (`ED040_shueisha`, `ED040_shufu_to_seikatsu_sha`), qui sont détectés, listés `protected_prefix_tokens` et laissés intacts. **Dry-run par défaut**, écriture réelle sur `--apply` uniquement ; exclusion par défaut de `99_Migration_Backups`/`03_Manifestes_Migration`. 4 tests de contrat ajoutés (`tests/cli_contracts/test_obsidian_goat.py`) → **23/23 PASS**. Implémente durablement la règle R29 de DEC-017.

- **Amélioration 2 — Réconciliation de la 3ᵉ forme studio (`Par_Studio`)** : constat (challenge du cadrage initial) — il ne s'agit PAS de doublons mais de **3 formes complémentaires** : identité canonique `ST###` (`03_Production/01_Fiches/`), vue relationnelle `Par_Studio` (« non canonique », agrège les anime), fiche-source scraping (`05_Industrie_Sources/.../01_Studios_Animation/`). Réconciliation par **liaison** (colonne « Identité canonique » ajoutée à `01_Par_Studio/00_INDEX.md` + statut dans les vues OLM/TOHO) et gouvernance, **sans fusion destructive**. OLM, TOHO animation STUDIO, Telecom Animation Film signalés 🔴 (identité ST### à créer via le rollout) ; Studio Durian hors liste fournie.

- **Amélioration 3 — Conflit de siège ufotable (`ST024`)** : tranché par **source primaire** (page « About Us » de https://www.ufotable.com/en/, consultée 2026-05-29). Siège = **Shinjuku-ku** (Shinjuku Front Tower 31F, Kita-Shinjuku) ; le « Nakano-ku » antérieur était l'adresse du *café* ufotable. Effectif **256 (mars 2024)**, président Hikaru Kondo, fondation octobre 2000 — tous confirmés. Frontmatter + tableaux + bloc fiabilité mis à jour.

- **Amélioration 4 — Fiches Apothecary manquantes** (sources : Square Enix officiel + Anime News Network ; Wikipedia = file de noms uniquement) : création de **MG085 Natsu Hyuuga** (autrice LN ; naissance non divulguée → champs vides + ⚠️), **MA1100** (adaptation manga Square Enix / Big Gangan / Nekokurage / Itsuki Nanao, 16 vol.) et **MA1101** (adaptation Shogakukan / Sunday Gene-X / Minoji Kurata, sous-titre *Maomao no Koukyuu Nazotoki Techou*, 21 vol.). IDs `MG085`/`MA1100`/`MA1101` vérifiés libres dans tout le vault avant attribution (application de R29). MOC franchise mis à jour (maillons 1 et 4 ✅).

- **Rollout studios planifié** : file d'attente `02_Anime & Production/03_Production/01_Fiches/00_ROLLOUT_QUEUE_studios.md` générée par script déterministe (dédup par nom normalisé vs ST001–ST026) → **189 studios** (26 déjà fichés, **163 à créer** ST027→ST189). Tâche planifiée `rollout-studios-japan-alliance` (cron `0 7 * * *`, **10 fiches/jour**) : lit la file, anti-doublon, Wikipedia comme ébauche **recoupée sur sources officielles**, écrit les fiches `ST###` (gabarit `ST024`), met la file à jour, journalise. Politique source validée par Sébastien : Wikipedia sert à constituer/référencer la liste puis contrôle de l'exactitude sur source officielle.

- **Réversibilité / non-destructif** : aucune suppression ; réconciliations additives ; fiches nouvelles uniquement.
- **Routage (DEC-016)** : code CLI + tests + DECISIONS + CHANGELOG → repo **TricorderKit**. Contenu vault → Japan-Alliance (non versionné).
- **Statut** : Appliquée.

*Dernière mise à jour : 2026-05-29 — DEC-018 améliorations + rollout studios*

---

## DEC-019 — Rétrospective 28/29 mai + auto-améliorations (règles R32-R36, CLI next-id, patterns) — 2026-05-29

- **Contexte** : à la demande de Sébastien, analyse des 2 jours de travail (assainissement vault DEC-017, améliorations DEC-018, rollout studios, gouvernance accès) pour enregistrer erreurs/réussites et s'auto-améliorer.

- **Enregistrement (claude-vault)** : note `00_SYSTEM/04_Self_Learning/RETRO_2026-05-28_29.md` (réussites + erreurs + causes racines) ; entrée `SUCCESSES_INDEX` ; nouveau pattern `PATTERN-EDIT-DUALFS-001` (édition fichiers & git sur environnement composé mount≠FS réel) + `PATTERN-DEDUP-001` référencé dans `PATTERNS_INDEX`.

- **Anti-recréation respectée** : un skill de bilan (`rapport`) et la mémoire (`memory-boot`, `consolidate-memory`) existent déjà → non dupliqués. Le manque réel outillé était l'**allocation d'ID sûre**.

- **Auto-amélioration outillée** : `obsidian-goat` v0.2.1 — commande **`next-id`** (R34) : prochain ID libre + `--check` collision, scan noms+contenu sans exclure réservés. **28/28 tests PASS** (validés sur FS réel via `C:\Python314\python.exe`, le sandbox servant une copie tronquée — illustration vivante de PATTERN-EDIT-DUALFS-001).

- **Nouvelles règles de protection (tasks/lessons.md, LESSON-008→012)** :
  - **R32** : jamais d'édition au niveau octet d'un source ; après édition, valider par `ast.parse` + smoke-run avant de déclarer terminé.
  - **R33** : git sur ce poste = chemin complet `C:\Program Files\Git\cmd\git.exe` via Desktop Commander ; vérifier l'état via le sandbox (lecture fiable) ; rediriger la sortie vers fichier (capture DC non fiable) ; supprimer `index.lock` périmé avant add/commit.
  - **R34** : avant d'attribuer un nouvel ID, `obsidian-goat next-id <prefix>` (ou grep global) ; étend R29.
  - **R35** : vérifier la **nature** d'une entité (source officielle) avant de créer sa fiche ; si elle ne correspond pas au type cible, reclasser dans le bon dossier (aiguillage), ne pas forcer ni dupliquer.
  - **R36** : définir un cache CLI writable (`OBSIDIAN_GOAT_CACHE`) ; pour pytest sur mount, `-c /dev/null --basetemp=/tmp` ou copier hors repo.

- **Process** : aiguillage automatique des non-studios déjà inscrit dans la tâche planifiée rollout (étape 1bis).
- **Routage (DEC-016)** : code + tests + lessons + CHANGELOG + DECISIONS → repo **TricorderKit**. Notes d'analyse → claude-vault (non versionné).
- **Statut** : Appliquée.

*Dernière mise à jour : 2026-05-29 — DEC-019 rétrospective + auto-améliorations (R32-R36, next-id)*

---

## DEC-020 — Optimisation des tâches planifiées : fusion enrichissement SO + recadrage horaires (anti-chevauchement) — 2026-06-01

- **Contexte** : à la demande de Sébastien (économie tokens, heures d'affluence, non-chevauchement), audit des 5 tâches planifiées Japan-Alliance. Deux constats : (1) deux horaires « menteurs » — `analyse-japan-alliance` décrite « Bilan 18h » tournait en réalité à 02h (cron `0 2 * * *`), `weekly-ecosystem-audit` décrite « Dimanche 21h » tournait à 05h dim. (cron `0 5 * * 0`) ; (2) **doublon d'enrichissement SO** : le rapport matinal 07h ET le bilan exécutaient chacun un lot « 10 fiches SO », soit deux chargements complets du contexte vault par jour.

- **Challenge transparent (loggé)** : déplacer les horaires NE réduit PAS le coût en tokens (facturation au token, pas à l'heure) ; les tâches étaient déjà en heures creuses. Le seul vrai levier coût = suppression du doublon + réduction du volume. Heures creuses ≈ latence/rate-limit, pas prix.

- **Décisions appliquées** :
  1. **Fusion du doublon SO** : enrichissement retiré du rapport matinal `japan-alliance-tricorderkit-7h30` (devenu lecture seule : reporte le résultat de la nuit) ; passage d'enrichissement unique consolidé porté par `analyse-japan-alliance` (run nuit 02h) → **un seul chargement de contexte vault/jour** au lieu de deux.
  2. **Volume réduit 10+10 → 12** (et non 20) fiches/nuit, sur recommandation, pour limiter le coût par run. Conserve la file d'attente SO (ordre numérique croissant, champs `title_jp`/`author_jp`/`publisher_jp` manquants).
  3. **Dépendance corrigée** : le bilan tournant à 02h lit désormais le rapport matinal de la **VEILLE** (`RAPPORT_[DATE_HIER].md`) — le rapport du jour J n'existe pas encore à 02h.
  4. **Recadrage horaires (anti-chevauchement, fenêtre creuse 02h–07h)** :
     - `analyse-japan-alliance` : `0 2 * * *` (inchangé, description réalignée « Run nuit 02h »).
     - `japan-alliance-an-tracker` : `0 0 * * *` → **`0 5 * * *`** (minuit → 05h).
     - `weekly-ecosystem-audit` : `0 5 * * 0` → **`0 4 * * 0`** (05h → 04h dimanche).
     - `japan-alliance-tricorderkit-7h30` : `0 7 * * *` (inchangé, allégé).
     - `rollout-studios-japan-alliance` : `0 12 * * *` (inchangé — midi = creux US, isole la charge d'écriture).
     - Écarts mini ≥ 1h (dim. 04h→05h), jitter ~8 min absorbé → aucun chevauchement.

- **Gain** : ~1 chargement complet de contexte vault en moins/jour + 8 fiches/jour en moins (20→12) ; descriptions désormais conformes aux crons réels.
- **Routage (DEC-016)** : prompts des tâches planifiées = `<scheduled-path>/` (hors repo versionné) ; cette décision + journalisation → repo **TricorderKit**.
- **Statut** : Appliquée.

*Dernière mise à jour : 2026-06-01 — DEC-020 optimisation tâches planifiées (fusion SO + recadrage horaires)*

---

## DEC-021 — Durcissement du Registre Central (dédup vs Master Index complet + goat next-id) — 2026-06-01

- **Contexte** : audit des 5 fichiers d'amélioration (juin 2026). Vérification vault : le Registre Central existe déjà (`Japan-Alliance/00_System/03_Manifestes_Migration/99_MASTER_INDEX.md`, 1 232 entrées nocturnes, 0 anomalie) + index typés par rubrique + Registre de Liaison. Le fichier 02 ne propose donc rien à créer.
- **Risque identifié** : la règle « vérifier avant création » des `index.md` pointait vers un tableau **partiel** (« fiches clés ») ≠ Master Index exhaustif → faux négatif → doublon. ID attribué « dernier + 1 » manuel (ou figé, ex. « AN011 »), fragile car IDs épars.
- **Décision appliquée** : en-têtes et « règles d'ajout » des index de rubrique repointés vers `99_MASTER_INDEX.md` comme source de vérité dédup, et attribution d'ID via `goat next-id <PREFIXE>` (R34) au lieu de « dernier + 1 ». `AGENTS.md` (repo public) laissé **générique** : la règle spécifique vit dans le vault (anonymisation DEC-016).
- **Appliqué à** : `01_Mangas & Light Novels/index.md` (en-tête + étapes 1-2) et `02_Anime & Production/index.md` (en-tête + étapes 1-2, suppression de l'ID figé « AN011 »). Autres rubriques : même patch à répliquer (formulations propres à vérifier par fichier).
- **Reste à faire** : passe fuzzy romaji/JP dans le générateur du Master Index (MangaTracker) ; répliquer aux rubriques restantes (jeux vidéo, personnes, lieux, etc.).
- **Statut** : Appliquée (manga + anime) — extension en cours.

## DEC-022 — Routeur SLM local zero-token (Ollama/Qwen) en complément de model-router — 2026-06-01

- **Contexte** : `model-router` et `claude-code-router` décident côté Claude (facturé en tokens). Fichier 05 propose de déporter la décision de routage sur un SLM local gratuit.
- **Décision** : introduire un routeur local (PoC `TricorderKit/.planning/poc-local-router/`) — gateway Python → Ollama (Structured Outputs, `temperature=0`, `keep_alive=0`) → choix d'un profil MCP filtré. Profils génériques (episodic/domain/dev), aucun chemin perso en dur. Complément, non remplacement, de `model-router`.
- **Validation** : tests unitaires 6/6 PASS (repli sûr sans Ollama) ; harnais d'éval routage `eval_routing.py` sur jeu étiqueté = **9/9, accuracy 1.0** (classifieur de référence). Install Ollama réelle impraticable en sandbox (binaire + modèle 2 Go, éphémère) → exécution end-to-end côté poste.
- **MAJ 2026-06-01 (test réel via Ollama / Desktop Commander)** : install confirmée (`qwen:1.8b`, `qwen3.6:latest`, `nomic-embed-text` sur `:11434`). PoC repassé en **REST urllib (zéro dépendance pip)**, modèle défaut `qwen:1.8b`. **Bug trouvé et corrigé** : `keep_alive=0` rechargeait le modèle à froid à chaque appel → timeout ; passé à `keep_alive="5m"` + timeout 120 s (env-configurables). Stratégie modèles : routage=`qwen:1.8b`, raisonnement lourd offloadé=`qwen3.6`, embeddings (G3)=`nomic-embed-text`.
- **Résultat mesuré en réel (Desktop Commander, 2026-06-01)** : `qwen:1.8b` **seul** = 6/9 (0.667), latence 8-33 s/appel + 40 s de chargement à froid. → **Optimisation : routage HYBRIDE** mots-clés d'abord (déterministe, instantané, zéro token) + SLM en secours sur ambiguïté (marge < seuil). Mots-clés normalisés (accents strippés). **Résultat optimisé = 9/9 (accuracy 1.0), 9 prompts sur 9 routés en ~0 ms, zéro appel SLM.** Conclusion : pour CE routage, le SLM est plus lent et moins précis qu'un classifieur déterministe — il ne reste utile que comme filet sur les cas réellement ambigus.
- **Reste à faire (poste)** : remplir `mcp-configs/*.json` réels ; brancher la sortie du routeur sur le chargement effectif des profils MCP.
- **Statut** : Acceptée — testé et optimisé en réel (hybride 9/9). Industrialisation : câblage MCP restant.

## DEC-023 — Pipeline RAG hybride (dense+sparse+RRF+cross-encoder) dans graphify — 2026-06-01

- **Contexte** : `graphify` était doc-only (README/SKILL/manifest, aucun pipeline). Fichier 04 fournit une implémentation de référence.
- **Décision** : implémenter `plugins/graphify/scripts/hybrid_rag.py` — Qdrant (dense) + BM25 (sparse) → fusion RRF → re-ranking cross-encoder, n'injectant que le Top-N. Dépendances lourdes en lazy-import (module testable sans torch/HF).
- **Validation** : tests logique RRF 4/4 PASS + **test d'intégration end-to-end exécuté** (Qdrant `:memory:` réel + BM25 + RRF + rerank stand-in) — classe correctement les docs pertinents et écarte le bruit. Compatibilité API qdrant-client récente (`query_points`) + ancienne (`search`).
- **MAJ 2026-06-01 (test réel via Ollama / Desktop Commander)** : backend d'embeddings **Ollama `nomic-embed-text`** ajouté au livrable (`OllamaEmbedder`, REST urllib, zéro torch) ; `embed_backend="ollama"` par défaut. **Exécuté en réel sur le poste** : embeddings 768 dims, pipeline dense+sparse+RRF remonte correctement les 2 docs pertinents (X500+REF-9942) et écarte le bruit (`PERTINENCE_OK=True`). Bug `import json` manquant trouvé par le test et corrigé. Vérif livrable : RRF ok + instanciation ollama + embedding réel 768d = OK.
- **Reste à faire** : indexer le vault dans Qdrant `:6333` (collection dim 768) ; exposer `search_vault()` en tool MCP ; re-ranking cross-encoder optionnel (lourd) ou rerank lexical léger.
- **Statut** : Acceptée — pipeline validé en réel avec embeddings nomic-embed-text ; indexation Qdrant prod restante.

## DEC-024 — Hygiène MCP : audit descriptions (cap 2 Ko) + janitor d'archivage à froid — 2026-06-01

- **Contexte** : fichier 06 — « Tool Schema Bloat » et hygiène active non automatisée. Vérification : `claude-vault/60_ARCHIVE` + `ARCHIVE_INDEX.md` (règle « > 90 j », « jamais supprimer ») existent mais **archive vide, aucune automatisation**.
- **Décision** : outillage livré (`TricorderKit/.planning/poc-hygiene-mcp/`) — `mcp_desc_audit.py` (mesure descriptions, plafond 2 Ko) + `janitor.py` (dry-run par défaut, archive Daily Logs > 90 j vers `60_ARCHIVE/Processed`, jamais de suppression).
- **Validation** : `mcp_desc_audit.py` exécuté sur `.mcp.json` réel = 1 serveur, 113 o, sous plafond. Janitor exécuté (logique) sur le vrai `claude-vault` via MCP = Daily Logs 2026-04-04→06-01, **0 candidat** au seuil 90 j (vault trop jeune) — comportement correct, aucune action destructive.
- **Reste à faire** : planifier `janitor.py` en tâche hebdo (Temporal) quand des logs dépasseront 90 j ; compression en embeddings à brancher sur DEC-023.
- **Statut** : Acceptée — outillage livré et vérifié, planification différée.

*Dernière mise à jour : 2026-06-01 — DEC-021..024 intégration audit 5 fichiers (registre durci · routeur local · RAG hybride · hygiène MCP)*


### DEC-023 — MAJ 2026-06-01 (mise en production G3 + collaboration Antigravity)
- **Indexeur livré** : `plugins/graphify/scripts/index_vault.py` — lit le vault Japan-Alliance (5 533 .md), embeddings `nomic-embed-text` (768d) via REST urllib, collection `vault` (Cosine 768), payload {path,title,folder_top,kind,n_chars,text} → **découple search_vault de tout index positionnel**. IDs `uuid5(path)` (idempotent). Modes : `--dry-run`, `--limit`, **`--incremental`** (état mtime `index_state.json`, run nocturne léger). Validé : dry-run (5 533, dim 768) + upsert REST OK.
- **Contention Ollama identifiée** : sur 16 Go, Qwen (Hermes) évince `nomic` → embeddings 5-9 s/note au lieu de ~0,15 s à froid. Index complet diurne = plusieurs heures + ralentit la veille Hermes de 12h.
- **Décision de sérialisation** : indexation RAG **déportée la nuit (03:00 Europe/Paris)**, en incrémental, planifiée par Antigravity (tâche Windows `\Antigravity\TricorderKit_RAG_Index`). Premier run nocturne (état vide) = index complet à froid non contendu.
- **search_vault livré** : `plugins/graphify/scripts/search_vault.py` — recherche dense Qdrant, prefixe `search_query:`, texte lu depuis le payload. CLI + fonction importable (à exposer en tool MCP après index nocturne).
- **Reste** : e2e search après index nocturne ; exposition tool MCP ; rerank lexical léger optionnel.
- **Statut** : Appliquée (prod) — index sérialisé nocturne en place ; e2e + tool MCP après premier run.

## DEC-025 — Collaboration asynchrone avec Antigravity (Gemini) — 2026-06-01
- **Contexte** : un second agent, **Antigravity (Gemini)**, opère en parallèle (protocole `Japan-Alliance_Antigravity\Protocole_Antigravity_Claude.md`). Risque de divergence (cf. dossier `Openclaw Autonome\TricorderKit_v0.7` vs zone de travail courante).
- **Décision — séparation des responsabilités** : Antigravity = veilles/scraping/data-tracking, **crons & scheduling**, ops système PowerShell, flux Hermes. Claude = architecture, code complexe, RAG, fiches — **consommateur lecture seule** des sorties veille (`veille_fiches_detaillees_*.json`, `<source>/normalized_records.jsonl`), sans modifier scripts/schéma/crons d'Antigravity. Optimisation → **proposée** via handoff, jamais appliquée unilatéralement.
- **Passage de témoin par fichiers** (zone unique `TricorderKit Autonome\`) : `a_faire_par_antigravity.md` (Claude→Antigravity) ↔ `fait_par_antigravity.md` (Antigravity→Claude).
- **Consolidation zone de travail** : sortie de veille rapatriée dans `TricorderKit Autonome\tools\jp-scraper\runs\` via **jonction Windows** créée par Antigravity (backup `runs__pre_migration_bak`), schéma inchangé. Exécutée par Antigravity (sa voie), pas par Claude.
- **Pont d'ingestion** : `plugins/graphify/scripts/ingest_veille.py` (Claude, lecture seule) — parse fiches veille, classifie fiabilité Japan-Alliance (✅/🟡/🟠/🔴), dry-run par défaut, indexation RAG gated `--index` (exclut 🔴). Validé en dry-run.
- **Statut** : Acceptée — appliquée (consolidation + sérialisation + pont en dry-run). Reste : wiring écriture vault + dedup G1, e2e après index nocturne.

*Dernière mise à jour : 2026-06-01 — DEC-023 prod (index sérialisé nocturne, search_vault) + DEC-025 collaboration Antigravity*
