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
  - `linked_projects.yaml` corrigé sur les deux points : `vault` repointé vers `<vault-path>/Japan-Alliance/` ; `allow_tricorderkit_write` repassé à `false` (conformité DEC-012/DEC-013, vault read-only ; écriture via MangaTracker uniquement).

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

## DEC-026 — Gate frontière publique APPLIQUÉ (cause racine fuites) — 2026-06-01

- **Contexte** : audit de la vitrine GitHub (v0.9.5). Le garde-fou d'anonymisation (`plugins/security-audit-cli/anonymization_checker.py` + `.check-anon-ignore`) **existait mais n'était jamais exécuté avant push** → fuites dans le repo public : capsules privées Japan-Alliance, doc d'architecture interne, dossiers legacy, et chemins personnels `C:\Users\<nom>\…` (back-slash ET forward-slash) dans scripts, `.planning/`, `.gitleaksignore`, TS. Trois défauts du checker existant : (1) scanne tout l'arbre de travail (faux positifs sur fichiers non suivis), (2) plante sous Windows (emoji cp1252), (3) jamais câblé à un hook/CI.
- **Décision** : nouveau gate `scripts/check_public_boundary.py` — scanne **uniquement les fichiers suivis** (`git ls-files`), détecte (a) termes privés hors whitelist `.check-anon-ignore`, (b) **chemins personnels absolus toujours bloquants** (jamais whitelistables) ; sortie 100 % ASCII ; `exit 1` si fuite. **Appliqué** via `.github/workflows/public-boundary.yml` (CI push/PR) + `.githooks/pre-push` (local, `make install-hooks`). Règle ajoutée à `AGENTS.md` : aucun push si le gate échoue.
- **Nettoyage associé (Lot 2)** : `git rm` legacy (`TricorderKit_v0.7/`, `TricorderKit_Project/`), capsules privées (`vault/session_capsule_*.json`), `Architecture_Adaptee_Instructions.md`, `data/mangatracker/` ; `skills/cowork-boot/` relocalisé vers MangaTracker (DEC-016) ; chemins perso anonymisés (`<vault-path>`, `<scheduled-path>`, `$PSScriptRoot`/`%~dp0` auto-localisants) ; `.check-anon-ignore` réconcilié.
- **Validation** : gate exécuté sur le poste = `[OK] aucune fuite` (exit 0) après corrections. 18 fuites réelles détectées puis corrigées (dont chemins forward-slash et `trigger_workflow.ts` qu'une simple relecture aurait manqués).
- **Reste à faire (différé)** : publier release `v0.9.5` + LICENSE ; arbitrer PR #2 (13/05) ; envisager de sortir le schéma Supabase `japan_alliance` du moteur (domaine) ; intégrer les 6 tests graphify à la suite committée.
- **Statut** : Appliquée.

## DEC-027 — Sync obligatoire « page centrale + modules » à chaque push — 2026-06-01

- **Contexte** : audit README (panneau Chrome + recoupement terrain). Sections jamais mises à jour depuis l'origine : `CLI Usage`, `Agent Commands`, `Repo Structure` → références à des CLIs disparus (`github-goat`/`your-scraper` cités sous `tools/` alors que github-goat vit dans `plugins/cli-forge/generated/`), omission de `graphify`, `obsidian-goat`, `tk doctor`, et **10 plugins réels** vs 7 listés.
- **Décision (règle R38, demande de Sébastien)** : tout push doit s'accompagner de la mise à jour de la **page centrale** (`README.md`) ET de **tous les modules** impactés (`STATUS.md` tableau des modules ; et le cas échéant `ROADMAP.md`, `CHANGELOG.md`, `.planning/`). Aucun commit de fonctionnalité n'est « terminé » si README + STATUS ne reflètent pas l'état réel (plugins, tools, CLIs, version, tests).
- **Appliqué (ce push)** : README `Quick Start` (INSTALL/Makefile), `CLI Usage` (tk + obsidian-goat + github-goat chemin réel), `Agent Commands` (9 slash réels), `Repo Structure` (10 plugins dont graphify, vrais `tools/`, fichiers racine), `Health Check` (tk doctor + gate) ; STATUS `graphify` 🧪WIP → 🔄Evolving/✅Actif (RAG livré).
- **Reste à faire** : envisager d'étendre le gate (`check_public_boundary` / un `docs-sync`) pour vérifier mécaniquement la cohérence README ↔ structure.
- **Statut** : Appliquée (règle active).

*Dernière mise à jour : 2026-06-01 — DEC-027 sync page centrale + modules à chaque push (R38) ; DEC-026 gate frontière publique appliqué*

*Dernière mise à jour : 2026-06-01 — DEC-023 prod (index sérialisé nocturne, search_vault) + DEC-025 collaboration Antigravity*


## DEC-028 — Gate docs-sync : vitrine <-> structure / version / tests — 2026-06-01

- **Contexte** : suite directe du « reste à faire » de DEC-027. Le gate frontière (DEC-026) bloque les fuites mais ne détecte pas la **désynchronisation documentaire** : README / STATUS / CHANGELOG ont déjà divergé (version, compte de tests, nombre de plugins) sans aucun contrôle mécanique avant push.
- **Décision** : nouveau gate `scripts/check_docs_sync.py` vérifiant trois familles — (1) **version** affichée (badge + pieds README/STATUS) contre la version canonique du CHANGELOG (premier `## [X.Y.Z]`) ; (2) **cohérence cross-document du compte de tests** (badge + mentions), avec option `--check-tests` confrontant à la collecte pytest réelle ; (3) **structure plugins** (tableau de bord STATUS + compte annoncé dans README) contre les sous-dossiers réels de `plugins/` — ni manquant ni fantôme — plus la cohérence arithmétique du bloc Résumé. Sortie 100 % ASCII, `exit 1` si désync. **Appliqué** en CI (`.github/workflows/docs-sync.yml`), en pre-push (chaîné après le boundary gate) et en Makefile (`make docs-sync`, `make gates`).
- **Validation** : 7 tests (`tests/test_check_docs_sync.py`) PASS. Dès la première exécution, a détecté une dérive réelle (titre H1 `STATUS.md` `v0.9` → corrigé `v0.9.5`). Boundary + docs-sync = verts.
- **Statut** : Appliquée.

*Dernière mise à jour : 2026-06-01 — DEC-028 gate docs-sync (clôt le reste-à-faire de DEC-027) ; R39 ajoutée*

---

## DEC-029 — Réallocation des veilles Claude → Antigravity (cible complète, pilote SO d'abord) — 2026-06-01

- **Contexte** : extension de DEC-025. Le système de coordination horaire `_sync_antigravity/` est opérationnel (Antigravity vérifie/complète les fiches via web, Claude intègre au vault). Constat de redondance coûteuse : plusieurs tâches planifiées Claude (modèle cher) font du *gathering web* en masse — enrichissement SO nuit 02h (12 fiches/nuit via `mangatracker-lookup`, cf. DEC-020), rollout création studios 12h (DEC-018), collecte AN 05h — alors qu'Antigravity (moins cher, propriétaire du scraping, horaire) est mieux placé. Boucle absurde identifiée : le rollout crée des fiches studios que Antigravity vérifie ensuite (Claude produit, Antigravity contrôle Claude).
- **Décision (arbitrage Sébastien, 2026-06-01)** :
  - **Cible** : confier à Antigravity le rôle « collecter + compléter via web » sur les 4 familles — (1) enrichissement SO, (2) collecte/brouillon création studios, (3) collecte fiches AN, (4) détection nouveautés/sorties. Claude conserve **intégration au vault + arbitrage des conflits + QA + architecture**. Antigravity n'écrit jamais dans les vaults ; il dépose des rapports, Claude intègre.
  - **Séquençage = PILOTE** : cette semaine, bascule de la **seule** tâche la plus sûre — **enrichissement SO** (champs `title_jp`/`author_jp`/`publisher_jp` des fiches `SO` de `01_Mangas & Light Novels/`). Métriques d'Antigravity accumulées en parallèle (durée/fiche, taux succès, taille de lot auto-scalée). Extension aux 3 autres familles la semaine prochaine **sur preuve**.
- **Application immédiate (pilote)** :
  1. Tâche `analyse-japan-alliance` (02h) : **Partie 3 (enrichissement SO) mise en PAUSE** (déléguée). Parties 1-2 (bilan + Master Index) inchangées. Rollback trivial = réactiver la Partie 3.
  2. Antigravity : nouvelle piste de veille « SO » définie dans `_sync_antigravity/claude_vers_antigravity.md` + file SO dans `ETAT_PARTAGE.md`. Auto-scaling et reporting de métriques déjà en place (GUIDE §8bis).
  3. Tâche horaire `sync-antigravity-fiches` (Claude, XX:01) : intègre désormais aussi les rapports SO (fiches `01_Mangas & Light Novels/`, champs JP), même règle de validation 2 sources.
- **Garde-fous** : règle des 2 sources et exclusion des sources interdites priment sur le volume (cf. catch `magicbusinc.com`, fiche ST104, 2026-06-01). On ne touche ni aux crons ni aux scripts d'Antigravity (DEC-025). Rollback du pilote = réactiver Partie 3 du run 02h.
- **Routage (DEC-016)** : prompts des tâches planifiées = `<scheduled-path>/` (hors repo) ; cette décision + journalisation → repo **TricorderKit** ; fichiers de coordination → `TricorderKit Autonome/_sync_antigravity/`.
- **Statut** : Acceptée — pilote SO appliqué ; extension conditionnée aux métriques.

---

## DEC-032 — Canal de commandes `_sync_antigravity/commands/` (communication quasi temps réel) — 2026-06-03

- **Contexte** : audit à froid de la collaboration Claude⇄Antigravity (tâche `audit-collab-claude-antigravity`). Friction identifiée : toute commande inter-agents attend le battement horaire (XX:01 / XX:10). Sébastien veut à terme une communication sans attente. Contrainte de fond : aucun des deux agents n'est « toujours à l'écoute » ; chacun ne s'exécute que sur déclencheur.
- **Décision** : créer un canal de commandes par fichiers, avec inbox dédiée par agent, lu en poll rapide (~1–2 min) de chaque côté. Latence cible 1–2 min, **zéro nouvelle infra**. Structure : `commands/{claude_inbox,antigravity_inbox,archive}/` + `commands/README.md` (contrat : nommage `AAAA-MM-JJThhmm__sujet.md`, frontmatter `from/to/priorite/statut`, cycle nouveau→en_cours→traite→archive).
- **Garde-fous** : chacun n'écrit que dans l'inbox de l'autre ; canal indépendant du verrou `ETAT_PARTAGE.md` (ne touche ni fiches, ni vault, ni journaux) ; aucune écriture vault via ce canal ; ne déclenche pas l'autre agent (mode poll pur tant que DEC-033/034 non validés) ; Claude ne câble jamais le cron d'Antigravity (DEC-025).
- **Application (run audit 2026-06-03)** : scaffold créé (`README.md` + 3 sous-dossiers avec `.gitkeep`). **Câblage des polls NON appliqué** : (a) côté Claude, lecture `claude_inbox/` à ajouter au prompt `sync-antigravity-fiches` (validation Sébastien) ; (b) côté Antigravity, poll de `antigravity_inbox/` à câbler par Sébastien/Antigravity. Édits des fichiers partagés (`claude_vers_antigravity.md`, `ETAT_PARTAGE.md`) reportés : verrou claude récent posé à l'heure du run.
- **Routage (DEC-016)** : décision + journalisation → repo **TricorderKit** ; fichiers de coordination → `TricorderKit Autonome/_sync_antigravity/commands/`.
- **Statut** : **Acceptée — scaffold appliqué (faible risque)** ; câblage des polls en attente de validation Sébastien.

## DEC-033 — Déclencheur événementiel (watcher local) pour comm temps réel — 2026-06-03 — PROPOSÉE

- **Contexte** : phase 2 du volet communication temps réel (suite DEC-032). Pour passer d'une latence de 1–2 min (poll) à ~secondes.
- **Proposition** : watcher local (PowerShell `FileSystemWatcher` ou Python `watchdog`) surveillant `commands/<inbox>/` et **lançant l'agent cible en headless** à chaque écriture.
- **Point critique non résolu** : Antigravity est-il **déclenchable de l'extérieur** (CLI / API / webhook) ? Côté Claude, le mode headless existe. Côté Antigravity : non vérifiable en autonome (Claude ne touche pas ses scripts). **Question ouverte à instruire avec Sébastien.** Si non, le côté Antigravity reste en poll rapide (DEC-032).
- **Risque** : MEDIUM (process résident, robustesse au redémarrage, lancement headless par agent).
- **Statut** : **Proposée** — conditionnée à la confirmation de déclenchabilité externe d'Antigravity. Pas d'implémentation sans validation.

## DEC-034 — Dispatch des commandes via Temporal — 2026-06-03 — PROPOSÉE

- **Contexte** : phase 3 du volet communication temps réel. Temporal est déjà dans la stack TricorderKit (`TEMPORAL_ADDRESS`, worker `tricorderkit-hooks`).
- **Proposition** : un workflow Temporal reçoit un signal « commande » et dispatche l'exécution de l'agent cible. Apporte durabilité, retry, et observabilité (Langfuse).
- **Point critique** : même dépendance que DEC-033 (déclenchabilité externe d'Antigravity).
- **Risque** : MEDIUM-HIGH (couplage stack, effort élevé).
- **Statut** : **Proposée** — go/no-go après DEC-033 et confirmation Sébastien.

> **Écart de traçabilité signalé (audit 2026-06-03)** : DEC-030 (réparation budget-tracking) et DEC-031 (routage token-optimizer par tier) sont référencés dans la mémoire persistante et les en-têtes de tâches planifiées, mais **absents de ce fichier** (dernière entrée loguée avant l'audit = DEC-029). Back-fill proposé, contenu à reconstituer avec Sébastien (ne pas inventer). Voir `_sync_antigravity/AUDIT_collab_2026-06-05.md`.

*Dernière mise à jour : 2026-06-03 — DEC-032 canal de commandes (appliqué, faible risque) + DEC-033/034 proposés (comm temps réel) ; écart DEC-030/031 signalé*


---

## DEC-030 — Réparation du tracking budget tokens (capture réelle via transcripts) — 2026-06-03

- **Contexte** : la commande « analyse mon budget » a révélé que `~/.token-optimizer/budget.json` était **figé** (schéma v1.0, mois `2026-05`, consommation et `events[]` à zéro) alors que `budget.py` est en v1.1. Diagnostic : le tracker n'avait **jamais** réussi à s'exécuter. Trois causes cumulées : (1) le hook `PostToolUse(Task)` appelle `python3 …` introuvable sous Windows (seul `C:\Python314\python.exe` existe) ; (2) bug plateforme connu `${CLAUDE_PLUGIN_ROOT}` non expansé dans les hooks Cowork ; (3) périmètre `matcher: "Task"` qui, même réparé, ne capturerait que les sous-agents — jamais la conso du fil principal (majoritaire). De plus la tâche planifiée matinale utilisait le `python3` du sandbox Linux → cible un `budget.json` différent (split-brain).
- **Décision** : abandonner la capture par hook (non fiable en Cowork) au profit d'une **ingestion depuis les transcripts de session**, source de vérité de la conso **facturée** (champs `message.usage` : `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `output_tokens`, `model`).
  - Nouveau script `scripts/track_usage.py` : scan des transcripts JSONL, agrégation par modèle, idempotent (état `~/.token-optimizer/track_state.json` par nb de lignes traitées), filtre mois courant, `--dry-run`. Pondération cache : `input_effectif = input + cache_creation + 0.1 × cache_read` (**arbitrage Sébastien** : inclure cache_read ×0,1, fidèle à la facturation).
  - `hooks/hooks.json` : **suppression** du hook `PostToolUse(Task)` budget (cassé + redondant ⇒ évite tout double comptage). `PreToolUse(Bash)` rtk inchangé. Backup `hooks.json.bak-<stamp>`.
  - `scheduled-tasks/daily-budget-morning-check/SKILL.md` : réécrit pour **ingérer d'abord** via `track_usage.py` exécuté en **python Windows** (Desktop Commander) — jamais le sandbox — puis lire `budget.py status`. Backup `.bak-<stamp>`. Écrivain unique = ce script, fichier canonique = `~/.token-optimizer/budget.json`.
  - **Recalibration** du plafond mensuel : `20 000 000` → `25 000 000 000` équiv-Haiku (**arbitrage Sébastien** : calé sur le rythme réel). L'ancien 20 M était un placeholder non validé (faux d'un facteur ~60–110×).
- **Validation** : `track_usage.py` compile, `hooks.json` parse OK. Ingestion juin (1–3) : 5 853 messages / 242 transcripts. `budget status` = 2,27 Md / 25 Md (9,1 %, OK) ; **Opus 88,2 % de son sous-budget [WARNING]** = facteur limitant. `budget_analyzer` : projection fin de mois 119 %, Opus = 97 % de la conso, 2 sorties longues non compressées détectées. Rollover `2026-05` → `2026-06` + migration v1.1 effectués.
- **Constat métier** : le `model-router` n'est dans les faits **pas appliqué** — ~97 % de la conso part en Opus (4 512 messages Opus vs 1 190 Sonnet, 144 Haiku sur 3 jours). Vrai gisement d'économie = router le simple vers Sonnet/Haiku + Session Rotation (réduire le cache_read). À traiter hors de cette décision.
- **Routage (DEC-016)** : scripts/hooks/SKILL du plugin = instance `rpm/` (chemins absolus assumés tant que bug `${CLAUDE_PLUGIN_ROOT}`) ; cette journalisation → repo **TricorderKit**. Copie durable de `track_usage.py` à reverser dans le repo plugin source.
- **Statut** : Appliquée.

*Dernière mise à jour : 2026-06-03 — DEC-030 réparation tracking budget (ingestion transcripts, recalibration 25 Md)*

---

## DEC-031 — Routage modèle token-optimizer appliqué aux tâches planifiées (Haiku/Sonnet/Opus par tier) — 2026-06-03

- **Contexte** : suite directe du gisement laissé ouvert par DEC-030 (« le model-router n'est pas appliqué : ~97 % de la conso part en Opus ; router le simple vers Sonnet/Haiku ; à traiter hors de cette décision »). Les 7 tâches planifiées tournaient toutes sur le modèle par défaut (Opus) quel que soit leur poids réel — y compris le battement horaire `sync-antigravity-fiches` (24 runs/j, majoritairement no-op) et les rapports de lecture quotidiens. Demande de Sébastien : « sélectionne Haiku, Sonnet ou Opus selon les tâches, optimise pour une meilleure gestion ».
- **Décision (arbitrage Sébastien)** : injecter dans le prompt de chaque tâche planifiée un **header standardisé « 🎚️ ROUTAGE TOKEN-OPTIMIZER »** déclarant le tier (T1/T2/T3), le modèle cible, le niveau caveman (compression sortie) et la politique Extended Thinking, aligné sur le skill `model-router` du plugin token-optimizer. Répartition retenue :
  - **T1 · Haiku 4.5 · caveman full** — `sync-antigravity-fiches` (horaire, no-op fast-exit), `japan-alliance-an-tracker` (05h), `japan-alliance-tricorderkit-7h30` (07h). Lecture/extraction/reporting sans raisonnement lourd.
  - **T2 · Sonnet 4.6 · caveman lite** — `analyse-japan-alliance` (02h, bilan + Master Index), `rollout-studios-japan-alliance` (12h, **caveman OFF sur le contenu** des fiches : anti-hallucination prioritaire), `weekly-ecosystem-audit` (dim 04h), `weekly-news-digest` (**nouvelle tâche**, lun 08h).
  - **T3 · Opus 4.6 · Extended Thinking ON · caveman OFF** — `audit-collab-claude-antigravity` (one-time 05/06, raisonnement multi-fichiers + DEC irréversibles).
- **Nouvelle tâche créée** : `weekly-news-digest` (lun 08h, Sonnet) — consolide la veille Antigravity des 7 derniers jours + recoupe les sorties manga/anime confirmées (règle 2 sources), produit un digest ≤200 mots archivé dans le vault. Complète DEC-029 (veille produite par Antigravity, consolidée par Claude).
- **Limite technique documentée** : les sous-agents exécuteurs du plugin (`haiku/sonnet/opus-executor`) **ne portent pas les MCP** (obsidian-japan-alliance, Windows-MCP). Pour les tâches liées au vault, le tier est donc appliqué comme **directive comportementale** (caveman + Extended Thinking OFF + token-light + no-op rapide) plutôt que par délégation dure à un sous-agent ; le vrai gain immédiat = compression sortie + lecture ciblée. La délégation `subagent_type` reste possible pour les tâches purement web/fichiers.
- **Contrôle continu** : `weekly-ecosystem-audit` (étape 2bis ajoutée) vérifie chaque dimanche que chaque tâche porte toujours son header de routage et que le tier est cohérent ; alerte si Opus repasse au-dessus de ~40 % de la conso mensuelle (signe de dérive du routage). Le suivi chiffré reste assuré par `budget.py`/`budget_analyzer` (DEC-030).
- **Réversibilité** : header purement additif en tête de prompt ; retrait = rollback trivial, aucune logique métier modifiée.
- **Routage (DEC-016)** : prompts des tâches planifiées = `<scheduled-path>` (hors repo) ; cette journalisation → repo **TricorderKit**.
- **Statut** : Appliquée (7 tâches re-routées + 1 créée le 2026-06-03).

*Dernière mise à jour : 2026-06-03 — DEC-031 routage modèle token-optimizer sur les tâches planifiées (clôt le gisement laissé par DEC-030)*

---

## DEC-035 — Politique de sourcing v2 : exhaustivité routée + sources non officielles en signal/cross-check — 2026-06-03

- **Contexte** : la base Japan-Alliance est le **noyau du futur site** (arbitrage Sébastien). Besoin de large captation des signaux sans abaisser le niveau de preuve des fiches publiées ; budget contraint (DEC-030 : ~97 % de la conso en Opus). Cette décision **amende les « Exclusions strictes »** des règles métier du projet.
- **Décision (arbitrage Sébastien, 2026-06-03)** :
  1. **Exhaustivité OBLIGATOIRE mais routée** : le *gathering* exhaustif (max résultats, **chaque source visitée**) est porté par **Antigravity/Hermes** (moins chers, propriétaires du scraping — DEC-025/029) ; Claude porte l'exhaustivité sur **intégration / dédup / QA / arbitrage / architecture** (lecture seule vaults).
  2. **Sources non officielles DÉBLOQUÉES** en deux rôles seulement : (a) **lead/surveillance** → classées `🟠 À vérifier`, déclenchent une recherche approfondie sur source officielle/primaire ; (b) **cross-check** = 2e source corroborante. **Jamais fondatrices d'un `✅ Confirmé` seules.**
  3. **Cadrage par source** : Wikipedia (cross-check/lead) ; X/Twitter = **comptes vérifiés/officiels uniquement** pour cross-check, comptes non vérifiés = lead `🟠` seulement ; MangaUpdates (cross-check métadonnées) ; **MangaDex = métadonnées et signaux de sortie uniquement** (listings, IDs, dates) — **jamais le contenu scanlé** (exclusion piratage maintenue sur le *contenu*).
  4. **Boucle d'auto-amélioration tri-agent** : après chaque run, chaque agent (Claude, Antigravity, Hermes) logge ses *gaps* (champ template récurremment vide, type d'entité sans gabarit, source jamais couverte) au format `_sync_antigravity/GAPS_LOG_FORMAT.md` et **propose** une MAJ template/registre-de-sources par handoff ; Claude intègre et arbitre. Alimente templates → fiches → sources en continu.
- **Inchangé et prioritaire sur le volume** : règle des **2 sources**, ossature validante **officielle/primaire**, classification `✅/🟡/🟠/🔴`, exclusion des sources de **contenu** piraté (cf. catch `magicbusinc.com`, ST104).
- **Risk Guard** : HIGH (élargit une règle système + délègue 3 flux). **Validé nominativement par Sébastien (2026-06-03).**
- **Routage (DEC-016)** : politique + journalisation → repo **TricorderKit** ; coordination/handoff → `_sync_antigravity/` ; fiches → **Japan-Alliance** (lecture seule).
- **Dry-run / rollback** : extension par famille avec **métrique de couverture** (seuil **validé Sébastien 2026-06-03** : ≥ 95 % sources visitées, **0** source de contenu interdite — en particulier **sites de scantrad / piratage** : la lecture des *annonces de nouveautés* est tolérée mais l'information doit être **contrôlée et recoupée impérativement** sur source officielle, jamais de citation de contenu piraté) ; rollback = revenir au pilote SO seul (DEC-029) + exclusions strictes d'origine.
- **Application en cours** : (a) câblage du rôle `🟠 → recherche officielle` dans `plugins/graphify/scripts/ingest_veille.py` ; (b) `GAPS_LOG_FORMAT.md` ; (c) handoff Antigravity (délégation scraping exhaustif + demande d'install MCP Japon/manga côté Hermes/Antigravity).
- **Reste à faire** : instrumenter la métrique de couverture par run ; reverser la liste MCP retenue dans le registre de sources. (Seuil de couverture **figé** le 2026-06-03.)
- **Statut** : **Acceptée — application en cours** (journalisation faite ; câblage + handoff en cours).

*Dernière mise à jour : 2026-06-03 — DEC-035 politique de sourcing v2 (exhaustivité routée + non-officiel en signal/cross-check + boucle auto-amélioration)*

---

## DEC-036 — Unification du schéma frontmatter des fiches œuvres : clés EN canoniques (`author_jp` / `title_jp`) — 2026-06-03

- **Contexte** : un audit déterministe (`audit_v2.ps1`, scan PowerShell des 1 313 fiches manga/LN via Desktop Commander, 2026-06-03) a révélé la **coexistence de deux schémas de frontmatter** dans `01_Mangas & Light Novels/` : schéma « migration BDD » (clés **FR** `auteur`/`artiste`/`titre_jp`/`editeur`, champ `record_status`) et schéma « Expert v1.0 » (clés **EN** `author_jp`/`artist_jp`/`title_jp`/`publisher_jp`, validation par `confidence_label`, **sans** `record_status`).
- **Impact mesuré (cause racine d'erreurs de comptage)** : tout décompte mono-schéma est faux. Exemple vécu pendant l'audit : « coquilles vides » comptées à **1 019** en ne lisant que les clés FR, **610** une fois les deux schémas pris en compte. Également : `record_status` présent sur **297** fiches seulement, `confidence_label` sur **1 067**, et **22 valeurs distinctes** de `confidence_label` (`à vérifier` 711, `à-valider` 212, `importé` 51, `vérifié` 40, + 18 one-off).
- **Décision (arbitrage Sébastien, 2026-06-03)** : **schéma canonique unique = clés ANGLAISES.** Table de migration des clés créateurs/titres :
  - `auteur` → `author_jp` · `artiste` → `artist_jp` · `titre_jp` → `title_jp` · `editeur` → `publisher_jp`.
  - Doublons de clés (`auteur_jp`/`artiste_jp` déjà présents ici ou là) → fusion vers `author_jp`/`artist_jp`.
  - **Champ de validation unifié** : `confidence_label` (schéma EN). `record_status` (FR) est migré/déprécié — valeur reportée dans `confidence_label` si plus riche, sinon archivée.
- **Exécution = chantier gardé, déterministe, NON appliqué par cette décision** : migration par **CLI** (`obsidian-goat` ou script dédié), jamais en édition LLM fiche par fiche (« CLI avant LLM »). Séquence imposée : `--dry-run` + diff → archivage réversible (`99_Migration_Backups/_schema_unif_2026/`) → écriture → **validation post-migration par re-scan `audit_v2.ps1`** (0 fiche en clé FR résiduelle ; comptes `author`/`title` stables avant/après).
- **Clés annexes à harmoniser — À ARBITRER (non figé)** : `status`/`statut`, `volumes`/`volume`, `isbn`/`isbn_13`, `prix`/`price_jpy`, `magazine`/`magazine_or_platform`, `demographie`/`demographic`. Élargir la table de mapping après un scan exhaustif de **toutes** les clés frontmatter du corpus.
- **Risk Guard : HIGH** (écriture de masse ~1 300 fiches sur vault **non versionné**). Vault read-only côté Claude → exécution **via MangaTracker** (DEC-012/013/016). Dry-run + diff + archivage obligatoires avant tout `--apply`.
- **Réversibilité** : archivage avant écriture ; rollback = restauration depuis `99_Migration_Backups/`.
- **Routage (DEC-016)** : cette décision + journalisation → repo **TricorderKit** ; script de migration → **MangaTracker** (liaison vault) ; contenu des fiches → **Japan-Alliance** (exécution via MangaTracker, non versionné).
- **Reste à faire** : (1) scan exhaustif des clés frontmatter → table de mapping complète ; (2) écrire le script de migration déterministe (dry-run par défaut, tests de contrat) ; (3) arbitrer les clés annexes ; (4) exécuter le chantier gardé puis re-scan de validation.
- **Statut** : **Acceptée — décision de schéma (clés EN `author_jp`/`title_jp`)** ; migration à exécuter en chantier gardé (dry-run), **non encore appliquée**.

*Dernière mise à jour : 2026-06-03 — DEC-036 unification schéma frontmatter (clés EN canoniques `author_jp`/`title_jp`) ; migration gardée à venir*

---

## DEC-037 — Politique de chargement MCP : noyau always-on minimal + à la demande + une couche par capacité — 2026-06-06

- **Contexte** : trois couches MCP coexistent sur le poste (Docker MCP Toolkit ~18 serveurs, connecteurs Claude Cowork, conteneurs locaux à rôle MCP) avec ~7 capacités dupliquées (GitHub, Obsidian, Airtable, Desktop Commander, context7, accès fichiers, web fetch). Double coût : **processus** (RAM/CPU des serveurs always-on) + **tokens** (le schéma de chaque outil est injecté dans le contexte à chaque tour, ~200-700 tokens/outil → 30-50k tokens de taxe permanente pour ~100 outils), aggravé par une conso quasi tout-Opus. Question de Sébastien : est-il pertinent de charger beaucoup de MCP en permanence plutôt que de filtrer à la demande ?
- **Décision (arbitrage Sébastien, 2026-06-06)** :
  1. **Noyau always-on minimal** (3-6 connecteurs haute-fréquence : 2 vaults Obsidian, Desktop Commander, GitHub, éventuellement le graphe).
  2. **Tout le reste à la demande** (chargement paresseux des schémas / deferred tools — modèle natif Cowork, pas un pis-aller).
  3. **Une seule couche par capacité** : le connecteur Claude natif est la source unique pour l'usage Cowork ; le Docker MCP Toolkit est réservé aux clients hors-Cowork.
  4. **Raisonner par profils d'usage** (veille, dev, infra) plutôt que par accumulation — transposition de « CLI avant LLM ».
  5. **Arbitrage latence vs token** : always-on uniquement si l'outil sert à chaque message ; sinon à la demande (cold-start accepté).
- **Appliqué le 2026-06-06** : 9 serveurs Toolkit redondants désactivés (`airtable`, `github-official`, `obsidian`, `desktop-commander`, `context7`, `filesystem`, `fetch`, `brave`, `wikipedia`) ; `registry.yaml` 18 → 9 ; `config.yaml` aligné (blocs orphelins `filesystem`/`desktop-commander` retirés ; bloc Airtable + PAT supprimés). 2 conteneurs `github-mcp` redondants arrêtés.
- **Incident & leçon** : l'un des conteneurs `github-mcp` était en réalité le **backend du connecteur GitHub** (pas un doublon inerte) → déconnexion du connecteur, reconnecté depuis. **Règle ajoutée** : ne jamais supprimer un conteneur « redondant » sans confirmer ce qu'il dessert (un connecteur peut être implémenté par un conteneur local).
- **Risk Guard** : MEDIUM (édition de configuration MCP, entièrement réversible). Backups `.bak` de `registry.yaml`/`config.yaml`.
- **Routage (DEC-016)** : politique + journalisation → repo **TricorderKit** ; hub de gestion détaillé (services, doublons, sécurité) → claude-vault `Infrastructure_Hub/`.
- **Réversibilité** : ré-ajout des entrées depuis les backups ; images présentes → conteneurs relançables.
- **Reste à faire** : trancher les serveurs Toolkit « à clarifier » (`dockerhub`, `hostinger`, `linkedin`, `mcp-python-refactoring`, `time`) et conditionnels (`git`, `markitdown`, `playwright`, `puppeteer`) ; définir les profils d'usage.
- **Statut** : **Acceptée — appliquée** (rationalisation MCP du 2026-06-06).

*Dernière mise à jour : 2026-06-06 — DEC-037 politique de chargement MCP (noyau + à la demande + une couche par capacité)*
---

## DEC-038 — Canal multi-agents unifie `canal_agents` (remplace `_sync_antigravity`) — 2026-06-07

- **Contexte** : le bus de coordination `_sync_antigravity` (binome Claude<->Antigravity) n'etait dans AUCUN repertoire autorise de Desktop Commander cote Cowork (acces : TricorderKit Autonome, vault Japan-Alliance, claude-vault, Scheduled, outputs). Claude ne pouvait pas y poster (handoff Codex bloque, cf. `Japan-Alliance-Audit-2026-06-06/05_HANDOFF_CODEX.md`). Recherche disque exhaustive (Documents, drives cloud, homes `.codex`/`.antigravity`/`.hermes`) : le dossier de 192 fichiers du rapport du 04/06 etait ephemere (outputs d'une session Cowork passee) et n'existe plus. Demande de Sebastien : fusionner les canaux Antigravity et Codex en un bus unique, rapide, avec dispatch par force et anti-doublon, deplacable dans TricorderKit, renomme generiquement.
- **Decision** :
  1. **Canal unique generique** `canal_agents/` cree DANS le depot TricorderKit (donc accessible a Claude sans relais). Remplace `_sync_antigravity` (nom neutre, 3 agents : claude/antigravity/codex).
  2. **Transport** append-only `bus/events.jsonl` + curseurs par agent (anti-staleness), CLI deterministe `scripts/sync_bus.py` (stdlib only, zero token LLM). Commandes : init/heartbeat/post/dispatch/read/inbox/health/status. `--dry-run` sur les ecritures.
  3. **Dispatcher par defaut = Claude** ; exclusivite de lane (anti-doublon). Forces : Claude=integration/QA/dedup-vault/archi ; Antigravity=enrichissement/veille/gathering-web/scraping ; Codex=dedup-oricon/refactor/scripts/data-transform/batch. (`canal_agents/ROUTING.md`)
  4. **R39** (bus unique) + **R40** (zone de tri unique) ajoutees a `AGENTS.md`. R40 : Antigravity/Codex deposent tout livrable dans `Japan-Alliance\97_A_Trier\05_A_Integrer\Fiches a trier - en attente\` + event `deliverable_ready` ; Claude seul corrige et classe dans le vault.
  5. **Embarquement** : `PROMPT_INITIAL_Codex.md` + `PROMPT_INITIAL_Antigravity.md` dans canal_agents ; pointeur ajoute a `%USERPROFILE%\.codex\AGENTS.md` (idempotent).
- **Verification** : bus initialise, genese postee, heartbeats des 3 agents, dispatch dry-run + reel du handoff `T-2026-06-06-DEDUP-ORICON` vers `inbox/codex/`, read cote Codex (4 non-lus, curseur avance), `health` = ok (5 events, 0 corrompu). Preuve observable (R11) OK.
- **Risk Guard** : MEDIUM (infrastructure de coordination, reversible — il suffit de supprimer `canal_agents/` et de retirer le bloc `<!-- canal_agents -->` de la config Codex).
- **Routage (DEC-016)** : canal + CLI + protocole + journalisation -> repo **TricorderKit** ; la zone de tri et les fiches livrees -> **Japan-Alliance** (vault).
- **Reste a faire** : (1) Antigravity adopte `canal_agents` a son prochain run (deprecier l'ancien chemin) ; (2) brancher `health --write-status` en scheduled task (poll minute) ; (3) Codex execute `T-2026-06-06-DEDUP-ORICON` et livre via la zone de tri.
- **Statut** : **Acceptee — appliquee** (canal_agents v1.0 en ligne, 2026-06-07).

## DEC-039 - Secrets MCP hors fichiers de config : Credential Manager + wrapper (hote Windows) - 2026-06-07
- **Contexte** : un PAT de connecteur MCP etait stocke en clair dans la config du client MCP cote hote Windows, et avait ete expose dans des transcriptions de session. L'audit du 06/06 (DEC-037) avait deja identifie le meme defaut sur un autre service (couche Docker Toolkit).
- **Decision** :
  1. **Aucun secret en clair** dans les fichiers de config des clients MCP. Stockage = Windows **Credential Manager** (credential generique), saisie par invite masquee (`cmdkey /generic:<nom> /user:token /pass`) - le secret ne transite jamais par une conversation LLM ni par l'historique shell.
  2. **Lancement via wrapper `.cmd`** : script PowerShell dedie lit le credential (CredRead/advapi32, stdout capture par `for /f`), injection en variable d'environnement process-local, puis exec du serveur (handles stdio bruts).
  3. **Contraintes techniques** (toutes verifiees) : appel PowerShell imbrique avec `^< nul` (sinon stdin JSON-RPC avale) ; ecriture de la config client en UTF-8 SANS BOM (sinon le client reinitialise sa config au redemarrage) ; test standalone du wrapper avant tout redemarrage.
  4. **Token expose = token revoque** : rotation + verification du rejet par l'API (401), purge des backups de config contenant l'ancien secret.
- **Verification** : handshake JSON-RPC `initialize` complet en standalone (stdin maintenu ouvert), connecteur fonctionnel apres redemarrage, ancien token rejete (401), scan des backups (aucun secret residuel).
- **Risk Guard** : MEDIUM (manipulation de secrets, reversible - le wrapper se substitue a la config initiale sans toucher au serveur).
- **Routage (DEC-016)** : patron generique anonymise -> repo TricorderKit (`RUNBOOK_INFRA.md` section 14 + R42 dans `tasks/lessons.md`) ; details operatoires -> vault prive (Infrastructure_Hub).
- **Statut** : **Acceptee - appliquee** (connecteur GitHub migre, ancien PAT revoque, 2026-06-07).

## DEC-040 - Externalisation .env + rotation des secrets DB + backups automatiques - 2026-06-07
- **Contexte** : mots de passe en dur dans docker-compose.yml (Postgres Temporal/Langfuse) et defauts faibles publics (Neo4j, NEXTAUTH_SECRET, SALT Langfuse) ; aucun backup automatique des volumes DB (plan A2).
- **Decision** :
  1. Compose 100% parametre via .env (gitignore) avec syntaxe stricte `${VAR:?message}` - echec explicite si variable absente, plus aucun defaut faible.
  2. Rotation complete : Neo4j (ALTER CURRENT USER), Postgres x2 (ALTER USER), NEXTAUTH_SECRET et SALT Langfuse. Secrets generes localement (28 car. alphanumeriques), jamais transmis via conversation. Rotation SALT = cles API Langfuse a regenerer (assume).
  3. Consommateur graph-server bascule sur le patron DEC-039 (wrapper lit le .env du repo) - plus de mot de passe en clair dans la config du client MCP.
  4. Backups : `scripts/backup_db.ps1` (pg_dump x2 + tar Qdrant a chaud + tar Neo4j avec arret bref + retention 14 j) + tache planifiee Windows quotidienne 03h30 (apres l'index RAG nocturne de 03h00).
- **Verification** : nouveaux mdp acceptes (cypher RETURN 1, psql SELECT 1 x2), ancien mdp Neo4j rejete (unauthorized), Langfuse health 200, temporal SERVING (tctl), backup reel 0 echec, restore a blanc 36 tables.
- **Risk Guard** : MEDIUM (stack locale, backups .bak des composes, .env.bak avant rotation).
- **Routage (DEC-016)** : compose + script + .env.example + RUNBOOK -> repo public (anonymises) ; valeurs reelles -> .env local uniquement.
- **Statut** : **Acceptee - appliquee** (2026-06-07). Reste : regeneration cles API Langfuse (login Sebastien requis).

## DEC-041 - Migration frontmatter Japan-Alliance executee (B1c/B1d, schema unifie EN) - 2026-06-07
- **Contexte** : DEC-036 (derive de schema FR/EN). B1a = scan 733 cles ; B1b = mapping arbitre par Sebastien (15 renommages + regle volume numerique) ; B1c = script deterministe + 28 tests de contrat (28/28 PASS) ; B1d = dry-run relu + arbitrage des conflits.
- **Decision** :
  1. Script `migrate_frontmatter.py` : edition ligne a ligne du seul bloc frontmatter (ordre des cles, CRLF, corps preserves), UTF-8 strict, idempotent, dry-run par defaut, backup R31 systematique vers `99_Migration_Backups/_schema_unif_2026/`.
  2. Arbitrage conflits (22 cas, 2 motifs homogenes : wikilink nu vs alias ; romaji vs kanji/duo complet) : **regle globale "cible prime"** (`--conflict-policy keep-target`) - la valeur EN, systematiquement plus riche, est conservee ; la cle FR est supprimee (originaux dans le backup R31).
  3. Fenetre `--apply` validee explicitement par Sebastien (Risk Guard HIGH respecte).
- **Verification** : apply = 5355 scannes, 2814 modifies, 6958 renommages, 18 dedups, 22 conflits resolus, 0 erreur ; re-dry-run post-apply = 0 changement (idempotence) ; backups = 2814 (egalite stricte) ; spot-check MA001 conforme.
- **Reste hors scope (passe separee)** : 85 `volumes` non numeriques ("En cours"...), normalisation des valeurs (`En cours`/`Actif`...), variantes `enrichi_jp*`, doublon de fiche `MA1105_Look_Back` (02_Termines + 03_One_shots).
- **Risk Guard** : HIGH (2814 ecritures vault) - mitige : dry-run relu, tests, backup integral, idempotence prouvee.
- **Routage (DEC-016)** : script + tests -> repo **MangaTracker** (acces DC non effectif ce jour : livrable en attente dans `claude-vault\Mise-a-jour_en-attente\_dev-queue\B1c_migration_frontmatter\`) ; rapports + backups -> vault Japan-Alliance.
- **Statut** : **Acceptee - appliquee** (2026-06-07). Reste : relocalisation MangaTracker + commit.

## DEC-042 - Plan de correction conformite templates (audit_v3) - 2026-06-07
- **Contexte** : audit_v3 (conformite doctrine double couche DEC-041) sur 4 448 fiches : 9,1 % conformes. Constats : template_used absent (3 155), sources absentes (2 995), confidence absent (2 368), cles canoniques manquantes (1 367), cles FR annexes (1 115), frontmatter absent (233), type vide (118), vocabulaire `type` dedouble (jeu_video/jeu-video...).
- **Decision** (arbitrages Sebastien) : (1) canon `type` EN (video_game, video_game_company, console_platform, magazine) ; (2) init mecanique template_used=MASTER cible + confidence_label=ROUGE sans source/ORANGE avec source, apply valide ; (3) reconstruction des 351 frontmatter/types -> Codex.
- **Execution** : `fix_conformity.py` (reutilise moteur B1c, 9/9 tests) - dry-run exact vs audit (1 642 types = somme des doublons ; 2 368 confidence = compte audit) puis **apply : 2 656 fiches, 0 erreur**, re-run = 0 changement, backup `99_Migration_Backups/_conformite_2026/`. Re-audit : vocabulaire unifie, confidence_absent eradique, template_used -781. Dispatch `T-2026-06-07-FRONTMATTER-REBUILD` (codex, lane data-transform, seq 53, 351 fiches, lots 25, zone de tri R40).
- **P5 differee - renumerotation dossiers** (constat Sebastien) : 27 collisions de prefixes inventoriees (`_collisions_numerotation.txt`) ; REPORTEE car 24 chemins du CSV Codex + specs (90_Templates) + audit_v2 referencent les zones en collision. Conditions : lots Codex integres + arbitrage fusions semantiques + script renommage avec reecriture des consommateurs de chemins.
- **Risk Guard** : HIGH (2 656 ecritures) - mitige : tests, dry-run chiffre exact, backup integral, idempotence.
- **Routage (DEC-016)** : scripts audit_v3/fix_conformity -> MangaTracker (en attente acces DC, dev-queue claude-vault) ; rapports/backups -> vault.
- **Statut** : **Acceptee - P0/P1 appliquees, P3 dispatchee** (2026-06-07). Reste : P2 (mapping B2), P4 (lots JV/studios), P5 (renumerotation, conditions ci-dessus).

## DEC-043 - Integration lots Codex + regle perimetre JP + P2a appliquee - 2026-06-07 (soir)
- **Contexte** : reprise handoff. Bus canal_agents : livrables DEDUP-ORICON pilot5 (dry-run), VEILLE-COLLECTOR, ENRICH-COQUILLES lots 1-2. Arbitrages Sebastien obtenus en session.
- **Decisions** :
  (1) **DEDUP-ORICON** : schema frontmatter `rankings` VALIDE ; SO fusionnees -> ARCHIVEES (99_Migration_Backups, R31, jamais delete) ; GO apply pilot 5 + batch 20 paires (dispatch seq 54, accepte par Codex).
  (2) **VEILLE-COLLECTOR** : livraison ACCEPTEE (script conforme WIN-001, tache 06:30 active) ; corrections mineures dispatchees (URLs dans rendu Markdown, doc 403 Oricon_US/Mantan_Web, pas de spoofing UA) - T-2026-06-08-VEILLE-COLLECTOR-FIX (seq 55, accepte).
  (3) **ENRICH-COQUILLES lot 1** : 9/10 fiches integrees au vault (script deterministe `integrate_lot1.py`, dry-run puis apply, backup `_enrich_coquilles_2026-06-07`, nettoyage des 6 cles non canoniques a N/A) ; MA081 REJETEE (source primaire MangaDex interdite) -> retraitement Codex.
  (4) **REGLE PERIMETRE JP (nouvelle)** : toute fiche dont la source primaire est non-japonaise (Kakao Page, Naver, HykeComic...) = HORS PERIMETRE Japan-Alliance -> gap `hors_perimetre_jp`, pas d enrichissement. Lot 2 (5 webtoons coreens MA1021/1029/1034/1038/1043) EXCLU et archive `_hors_perimetre_kr_2026-06-07` (enrichissements conserves pour une eventuelle base KR future ; originaux dans lot0_2026-06-06).
  (5) **B2/P2a APPLIQUEE** : 17 cles FR evidentes -> EN canon (`p2a_migrate.py`) : 5 378 scannes, 1 091 fiches modifiees, 1 755 renommages, 0 conflit, idempotence prouvee, backup `_schema_unif_2026/p2a_2026-06-07`. Pre-scan doublons (date_jp/editeur_jp/nom_japonais vs equivalents EN) = 0 co-presence -> P2b simplifie en renommages. Tableau P2b en attente arbitrage : `claude-vault\Mise-a-jour_en-attente\_dev-queue\Audit_Conformite_Templates\B2_ARBITRAGE_P2_2026-06-07.md`.
- **Incidents consignes (ERRORS.md claude-vault)** : collision seq bus (54/55 dupliques, mount sandbox perime - sans perte, posts suivants via DC/Windows) ; ecrasement nom identique lors de l archivage KR (originaux saufs dans lot0 ; regle candidate R41 : suffixe de provenance obligatoire en archivage multi-sources). **Bug watcher identifie** : tentatives de relance consommees pendant que codex_exec est occupe -> faux `task_failed` CREATEURS-MANQUANTS ; relance via seq 68 ; correctif watcher a planifier.
- **Risk Guard** : HIGH (1 091 + 9 ecritures vault) - mitige : dry-run chiffres exacts, apply en fenetre validee Sebastien, backups R31, idempotence verifiee.
- **Routage (DEC-016)** : `integrate_lot1.py` + `p2a_migrate.py` -> MangaTracker a la relocalisation (dev-queue claude-vault en attendant) ; rapports/backups -> vault ; aucun changement code TricorderKit (bus = donnees runtime).
- **Statut** : **Acceptee - appliquee** (2026-06-07 soir).

## DEC-044 - Suite reprise : lot 3 integre, watcher patche, P2b prepare (differe) - 2026-06-08 (nuit)
- **Contexte** : poursuite "jusqu au bout". Relecture bus : lot 3 ENRICH-COQUILLES livre + faux echecs watcher (4 taches marquees failed alors qu elles produisaient).
- **Decisions / actions** :
  (1) **Lot 3 ENRICH-COQUILLES integre** : 5/5 fiches (MA110, MA118, MA120, MA124, MA130) via `integrate_lot3.py` (meme moteur, dry-run -> apply, backups `_enrich_coquilles_2026-06-07`, nettoyage cles N/A). Precision perimetre : `to-corona-ex.com` = Corona EX (TO Books, JAPONAIS officiel) -> VALIDE. Liste blanche JP transmise a Codex (Alphapolis, Comic Walker, Comic Days, Corona EX, Gardo, Nicovideo Seiga, magazines editeurs) ; hors perimetre = Kakao/Naver/HykeComic/Webtoon/Tapas.
  (2) **Bug watcher corrige** (`inbox_watcher.ps1`) : avant de marquer `failed`, si un livrable outbox est plus recent que le dernier lancement -> reset du compteur (R44). 5 taches reassignees (seq 80-84) : ENRICH-COQUILLES, CREATEURS-MANQUANTS, DEDUP-ORICON-APPLY, FRONTMATTER-REBUILD, VEILLE-COLLECTOR-FIX.
  (3) **P2b PREPARE mais APPLY DIFFERE** : `p2b_migrate.py` + `p2b_migrate_body.py` ecrits et valides en logique (passe unique, regle no-overwrite stricte = renomme seulement si cible absente sinon conflit flagge ; `os.walk` avec elagage des dossiers exclus ; backup R31 ; idempotent ; garde-fou fichier vide). Decisions de mapping arbitrees (defauts recommandes, l UI d arbitrage ayant echoue) : URL canon = `official_url` ; 10 fusions standard ; `enrichi_*` -> `enriched_jp` ; `dossier_jeux_top10`->`top10_games_folder`, `source_relation`->`source_relationship`. **Apply NON execute** : poste sature (7 process python Codex concurrents + Ollama) + executeur Windows (DC deconnecte, Windows-MCP instable sous charge) -> risque d ecriture partielle. A lancer en fenetre calme : `C:\Python314\python.exe "...\Audit_Conformite_Templates\p2b_migrate.py"` (dry-run) puis `--apply` puis re-dry-run (idempotence).
  (4) **Quick wins** : R43 (suffixe provenance archivage) + R44 (watcher) ajoutees a `tasks/lessons.md`. Wikilinks des 5 IDs KR exclus : verifies, references uniquement en staging/backup, **aucun lien actif casse**. Doublon `MA1105_Look_Back` : **deja resolu** (une seule occurrence live en 02_Termines, wikilink AN008 ok).
- **Risk Guard** : P2b = HIGH non execute (differe par prudence). Lot 3 = MEDIUM applique (dry-run + backup + idempotence).
- **Routage (DEC-016)** : `integrate_lot3.py` + `p2b_migrate*.py` -> MangaTracker a la relocalisation (dev-queue) ; patch `inbox_watcher.ps1` -> TricorderKit (canal_agents, code outil) ; backups/rapports -> vault.
- **Statut** : **Acceptee - lot3 + watcher + P2b APPLIQUES** (2026-06-08).

### Addendum 2026-06-08 (matin) - P2b EXECUTE via la tache planifiee gardee
- Tache planifiee `TricorderKit_P2b_Apply` (schtasks, /SC MINUTE /MO 30) + wrapper `run_p2b_guarded.ps1` (garde Codex-idle : verrou codex_exec + python<=1 ; prend le verrou pendant l'apply ; dry-run -> garde-fous -> apply -> re-dry-run idempotence ; auto-suppression apres succes).
- **Fenetre calme atteinte des le 1er run reel (08:42)** : DRYRUN scanned=5313, to_modify=1378, renames=2636, conflicts=18, undecodable=1 -> APPLY 1378 fiches / 2636 renommages -> **idempotence verifiee (re-dry-run=0)** -> tache auto-supprimee. Backup `99_Migration_Backups/_schema_unif_2026/p2b_2026-06-08`.
- **18 conflits** = fiches portant a la fois `enrichi_jp` (renommee) et une variante `enrichi_phase2_jp`/`enrichi_jp_phase2`. Micro-passe `p2b_fix_variants.py` -> `enriched_jp_phase2` (18 fiches, idempotent, backup `_schema_unif_2026/p2b_variants_2026-06-08`).
- **Verification finale** (`verify_fr_keys.py`, 35 cles FR scannees, vault vivant hors backups/zone-tri) : **0 cle FR residuelle**. Migration frontmatter FR->EN (B1c + P2a + P2b) COMPLETE.
- `no_fm`=325 (fiches sans frontmatter, intactes - relevent de FRONTMATTER-REBUILD cote Codex) ; `undecodable`=1 (fichier non-UTF8 ignore, jamais reecrit).

## DEC-045 - Paperclip control plane : org chart metier Japan-Alliance cree + arbitrage n8n - 2026-06-09 (soir)
- **Contexte** : suite de l'addendum securite (PROP_Paperclip_VPS_OrgChart.md). Paperclip deja live (hVPS Hostinger, mode authenticated, Traefik HTTPS, securise le 09/06). Restait la config metier. Probe API/UI realise (prerequis) avant toute ecriture.
- **Probe (read-only, paramiko via tailnet <VPS_TAILNET_IP>)** : CLI `paperclipai` dans le conteneur ; app `/paperclip` ; API REST sous `/api`, auth = **better-auth** (`POST /api/auth/sign-in/email`, admin <USER_EMAIL>) ; mutations board exigent header **Origin de confiance** (`http://<VPS_HOST>`) sinon "Board mutation requires trusted browser origin". Pas de `company create`/`agent create` en CLI : creation par **`POST /api/companies`** et **`POST /api/companies/{id}/agents`** (route agents company-scoped). Import de package portable possible (`/api/companies/import[/preview]`) mais creation REST directe retenue (reversible, incrementale, verifiable).
- **Schemas confirmes** : `createCompanySchema{name, description?, budgetMonthlyCents}` ; `createAgentSchema{name, role∈[ceo,cto,cmo,cfo,engineer,designer,pm,qa,devops,researcher,general], title?, icon?, reportsTo(uuid)?, capabilities?, adapterType∈[process,http,claude_local,codex_local,gemini_local,opencode_local,pi_local,cursor,openclaw_gateway], adapterConfig(record, env bindings), runtimeConfig, budgetMonthlyCents, permissions{canCreateAgents}}`. Cles runtime via `POST /api/agents/{id}/keys{name}` ou `paperclipai agent local-cli <ref>` (installe skills cote poste Claude/Codex).
- **Realise (ecritures live, reversibles)** :
  (1) **Entreprise "Japan-Alliance"** creee. ID `4241dcaa-4e20-4280-a05a-6e4a1a97a2de`, prefixe issues `JAP`, budget 20000c/mois, `requireBoardApprovalForNewAgents=true`.
  (2) **Org chart = 14 noeuds** : **Mission Control** (ceo, claude_local, budget 5000c, canCreateAgents) en racine + **13 specialistes** reportsTo Mission Control. 8 domaines (Edition Manga&LN, Animation&Studios, Personnes&Culture, Musique JP, Jeux Video, Tourisme&Lieux, Goodies, Evenements - tous researcher/claude_local) + 5 transverses (Veille/Hermes=researcher/**http**, QA/Fiabilite=qa/claude_local, Janitor/Dedup=devops/**codex_local**, RAG Indexer=engineer/**process**, Editeur Site=engineer/claude_local). Perimetres vault inscrits dans `capabilities`. **Heartbeats OFF** sur tous (`runtimeConfig.heartbeat.enabled=false`) -> rien ne tourne ni ne depense tant que non active.
- **DECISION n8n vs routines Paperclip (tranche)** : **Paperclip = couche unique d'orchestration du travail des agents** (routines natives cron/webhook/API -> chaque execution cree une issue tracee + reveille l'agent assigne = ticketing + budget + audit). **n8n retrograde a l'ingress/glue d'integration** (webhooks tiers : Discord, RSS, mail ; transformation de payload) qui appelle ensuite un **trigger webhook/API d'une routine Paperclip**. Aucune logique d'orchestration d'agents dans n8n -> pas de doublon. Corollaire : les crons VPS de veille (2h/6h, engine 7h) migrent a terme en **routines Paperclip** assignees a l'agent Veille/Hermes ; ne PAS les dupliquer dans n8n.
- **Reste (enrolement runtimes - hors session, besoin Sebastien)** : (a) Claude/Codex : `paperclipai agent local-cli <url-key> -C 4241... --api-base https://<VPS_HOST>` a lancer **sur le poste** (installe skills ~/.claude, ~/.codex + cle agent) ; (b) Hermes : cabler `adapterConfig`/`env` de l'agent Veille vers l'endpoint Ollama/Hermes interne du VPS ; (c) **Antigravity** : endpoint webhook a fournir (non assigne a un noeud pour l'instant) ; (d) decision d'activation des heartbeats + confirmation budgets.
- **Risk Guard** : MEDIUM (ecritures application-level entierement reversibles : `company delete`, agents terminables ; aucun changement infra/reseau ; heartbeats off = zero execution/depense).
- **Routage (DEC-016)** : scripts probe/build (`_paperclip_*.py`) -> Agents-Hub (outillage runtime VPS) ; cette decision + journal -> TricorderKit/.planning ; etat live -> Paperclip.
- **Statut** : **Acceptee - entreprise + org chart 14 noeuds CREES (idle) ; enrolement runtimes + activation = a confirmer Sebastien**.

## DEC-046 — Cap v1.0 « Self-Improving Scraping & Knowledge OS » — 2026-06-11
- **Contexte** : 4 fichiers de cadrage du 09-06 (vision v1.0, Learning Engine, veille outils, format rapport scraping). Vérification d'amélioration menée le 11-06 : ~60 % des modules cibles déjà couverts par v0.9.5 (Règle 6 vérifiée — workflow-engine, eval-lab, graphify, security-audit-cli, deep-research-core, obsidian-agent-layer, politique MCP, registres sources vault).
- **Décision** : PROTOTYPER learning-engine + scraper-runtime + gouvernance MCP machine-lisible, avec durcissement VPS en phase dédiée. 7 chantiers N1–N7, 5 phases — plan détaillé : `.planning/PLAN_v1.0_SELF_IMPROVING_2026-06-11.md`.
- **Corrections vs fichiers sources** : exécution scraping/veille = Hermes/Antigravity (veille_v2 §rôles, DEC-029) ; routage DEC-016 (générique→TricorderKit, profils JP→MangaTracker, données→Japan-Alliance) ; n8n exclu de l'orchestration (DEC-045) ; arborescence retenue `plugins/learning-engine/` (convention repo) et non `modules/`.
- **Ordre d'exécution validé** : démarrage **Phase 3 (learning-engine, schemas-first)** — README + 5 schemas JSON avant toute logique d'exécution (§28) ; Phase 1 VPS ensuite.
- **Garde-fous** : promotion de skill = tests §16.4 + validation humaine obligatoire ; pas d'auto-modification du core/sécurité/secrets/vault/MCP/VPS ; dry-run avant toute écriture externe ; `make gate` avant push.
- **Risk Guard** : plan HIGH → validé explicitement par Sébastien le 2026-06-11. Création plugin schemas-only = LOW.
- **Statut** : **Validée — 2026-06-11 (Sébastien), démarrage Phase 3**.

## DEC-047 - project_scope generique dans learning-engine (frontiere publique) - 2026-06-11
- **Contexte** : le gate pre-push (anonymisation DEC-016/R37) a bloque le push du Lot A : les schemas `experience_card`/`strategy_variant` codaient `project_scope` en enum ferme `[tricorderkit, mangatracker, japan-alliance, agents-hub]`, et scripts/tests/README citaient les noms des projets lies. Double probleme : fuite d'anonymisation dans le depot public ET defaut de conception (le moteur generique ne doit pas nommer ses projets aval).
- **Decision** : `project_scope` devient une **chaine libre** (`{type:string, minLength:1}`) dans les deux schemas ; suppression de tout nom de projet aval dans le code/tests/docstrings/README du plugin (remplaces par des exemples generiques : `project-a`, `demo-skill`). Le moteur learning-engine reste 100% agnostique du domaine.
- **Portee** : changement de contrat mineur sur les schemas DEC-046 (cree le meme jour, non encore publie) ; aucun impact runtime (la validation acceptait deja ces valeurs, desormais toute chaine). Les scopes specifiques (japan-alliance, etc.) restent utilises cote integrateur/MangaTracker, jamais codes en dur dans le public.
- **Garde-fous** : 20 tests pytest re-passes ; `make gate`/`check_public_boundary` + check-anon re-verifies avant push ; pas de whitelist de noms de projet (la frontiere publique n'est pas affaiblie).
- **Risk Guard** : choix valide par Sebastien (option \"Generiser + DEC-047\"). Changement de contrat = MEDIUM, reversible.
- **Statut** : **Acceptee - 2026-06-11**.

*Derniere mise a jour : 2026-06-11 - DEC-047 project_scope generique (frontiere publique, deblocage push Lot A)*

## DEC-048 — Integration MarkItDown (plugin document-ingestion) ; Headroom + Supermemory ecartes — 2026-06-12
- **Contexte** : analyse du document `Integration_Headroom_MarkItDown_Supermemory_v1` (3 briques proposees). Verification croisee realisee (GitHub officiel + couverture tierce).
- **Decision** :
  (1) **MarkItDown : INTEGRE** (microsoft/markitdown, MIT, v0.1.6). Seul cas net : comble un vrai trou (conversion universelle PDF/DOCX/XLSX/HTML/EPUB/ZIP -> Markdown pour vault + RAG), mature, faible risque.
  (2) **Headroom : ECARTE a ce stade** — doublonne le plugin `token-optimizer` existant (cli-compress/rtk, context-compress, caveman) ; projet tres jeune ; risque sur ISBN/dates/noms JP. A reconsiderer seulement via benchmark chiffre vs rtk.
  (3) **Supermemory : EN ATTENTE** — recouvrement massif avec la stack deja deployee (Qdrant + Neo4j + Obsidian + MCP graphify) ; details techniques du document errones (port 6767/npx/endpoints non confirmes ; realite = binaire auto-contenu). Prerequis : note d'une page « Supermemory vs Qdrant+Neo4j » avant tout prototype.
- **Realise** : paquet installe sur le poste (Python 3.14, markitdown 0.1.6 + onnxruntime/magika/mammoth/pdfplumber/openpyxl). Adaptateur isole `plugins/document-ingestion/` (manifest.yml, config.example.yaml, scripts/tk_ingest_document.py, README.md, tests/). Garde-fous : original jamais supprime, pas d'ecrasement, liste blanche d'extensions, URLs distantes off, quarantaine sur echec, rollback `TK_MARKITDOWN_ENABLED=false`. **5/5 tests pytest verts** + conversion reelle validee (frontmatter + tableau ; rapport JSONL).
- **Risk Guard** : LOW (adaptateur isole, coeur TricorderKit non modifie, reversible par env).
- **Routage (DEC-016)** : plugin generique -> **TricorderKit**. Rien dans le vault.
- **Statut** : **Acceptee — MarkItDown integre (prototype fonctionnel) ; Headroom ecarte ; Supermemory en attente**.

## DEC-049 - Gate docs-sync etendu au ROADMAP (coherence vitrine indispensable, R46) - 2026-06-12
- **Probleme** : le push v1.0.0 a aligne README/STATUS/CHANGELOG mais laisse ROADMAP.md en v0.9.5 / 544 tests / 10 plugins ; le gate docs-sync (DEC-028) ne lisait pas ROADMAP -> derive non detectee. L'ajout du 13e plugin document-ingestion (DEC-048) sans MAJ de la vitrine releve de la meme classe d'erreur.
- **Decision** : etendre scripts/check_docs_sync.py (pas de recreation, regle §6) : (1) ROADMAP inspecte pour version + tests ; (2) compteurs de tests historiques ignores (faux positif "503 tests PASS" phase 8) ; (3) plugins comptes via `git ls-files` (un WIP non pousse ne bloque pas). Detail : .planning/DEC-049_docs_coherence.md.
- **Regle R46** : avant tout push public, version + nombre de tests + decompte plugins doivent etre IDENTIQUES dans README/STATUS/ROADMAP et concordants avec CHANGELOG (version canonique) et l'arborescence plugins/ ; tout ajout de plugin doit etre declare dans la vitrine (tableau STATUS + decompte README/ROADMAP + Resume). Gate bloquant en pre-push + CI.
- **Risk Guard** : LOW (controle documentaire, reversible). Gate vert apres realignement vitrine (v1.0.0 / 634 tests / 13 plugins).

*Derniere mise a jour : 2026-06-12 - DEC-049 gate docs-sync etendu au ROADMAP (R46) + vitrine realignee 13 plugins.*


## DEC-051 - Adaptation blueprint AI-Ops (00-16) vers l'ecosysteme - 2026-06-19
- **Contexte** : arborescence AI-Ops complete (16 blocs 00-16) proposee par l'utilisateur. Constat : c'est un blueprint d'INFRASTRUCTURE, pas une structure de vault-memoire. La copier telle quelle dans le vault violerait la regle "le vault stocke de l'intelligence, pas du code".
- **Decision** : ADAPTER (pas copier) selon le routage DEC-016 + regle "vault = memoire only, extend don't replace". 4 phases sequencees + validees.
  - Phase 1 (vault memoire) : couche gouvernance/policies/memoire en EXTENSION des dossiers existants (system-prompts, runbooks, entites contacts/preferences, MOC memoire) ; aucun renommage, rien deconnecte.
  - Phase 2 (TricorderKit public) : docs/architecture.md + gap-analysis. ~75% du blueprint DEJA couvert (graphify=RAG, workflow-engine=Temporal, eval-lab, security-audit-cli, docker-compose, Langfuse, hooks). Aucun composant net-new code.
  - Phase 3 (projet lie prive) : couche skills/ domaine documentant + mappant le code reel, sans deplacer le miroir de runtime (preserve la reproductibilite).
  - Phase 4 (VPS/donnees) : aligne, rien a creer (data/models/vector-db/observabilite/securite/backups deja en place).
- **Net-new ECARTES (roadmap, non engages)** : dashboard UI dedie, audio/multimodal, vLLM, prometheus/grafana/phoenix, orchestrateurs alternatifs (crewai/langgraph/autogen). A coder feature par feature sur GO ; scaffolder vide = pollution (R37/YAGNI).
- **Regle nouvelle R49** (MASTER_PROTOCOL vault, demande utilisateur) : tout changement (structure, skill, plugin, MCP, config, infra, decision) est consigne IMMEDIATEMENT dans le backup (_RECOVERY_KIT) + trace memoire. Objectif zero perte (cause racine du wipe MCP 2026-06-16).
- **Risk Guard** : MEDIUM (architectural, reversible). Valide par l'utilisateur (Adapter + tout l'ecosysteme sequence + push sur GO).
- **Routage (DEC-016)** : memoire -> vault ; generique -> TricorderKit ; domaine/execution -> projet lie ; donnees -> vault/VPS.
- **Statut** : **Acceptee - phases 1-4 livrees 2026-06-19**.

*Derniere mise a jour : 2026-06-19 - DEC-051 adaptation blueprint AI-Ops (4 phases livrees) + R49 backup systematique.*

## DEC-052 - Second Brain Routing Layer (memory-router) + Arbor en prototype isole - 2026-06-20
- **Contexte** : 2 specs utilisateur. (4.1) "Second Brain Routing Layer" = couche de routage memoire declarative. (4.2) "Reinstall TricorderKit + Arbor" = re-scaffold complet + boucle de recherche cumulative Arbor.
- **Verdict recoupe contre le repo reel** : (4.2) reinstall ECARTE - le repo est mature (13 plugins, cli/tk.py, docs 00-06, gates) et son arborescence src/tricorderkit idealisee ne correspond pas (plugin-based) ; le blueprint 00-16 est deja adapte (DEC-051). Le skill "grill-me" de (4.1) EXISTE deja sous skills/tk-grill (version superieure, sortie DEC-NNN) -> non duplique (R26).
- **Decision** :
  - **(4.1) memory-router** ADOPTE comme couche legere : `.tricorderkit/memory_router.yaml` + `.tricorderkit/context_sources.yaml` + `docs/07_SECOND_BRAIN_ROUTING.md` + `docs/08_CONTEXT_POLICY.md` + `docs/diagrams/memory_map.mmd`. Generique/anonyme (R37), ne duplique pas memory-boot/graphify/obsidian-agent-layer (pointe vers eux).
  - **(4.1) grill-me** : NON cree (= tk-grill existant).
  - **(4.2) Arbor** : PROTOTYPER en isolation stricte sous `experiments/arbor_adapter/` (allowed_to_modify_core=false). Worktrees gitignored. Promotion hors prototype = nouveau DEC apres benchmark.
- **Risk Guard** : LOW (docs + config declarative + experiment isole, tout reversible).
- **Routage (DEC-016)** : generique -> TricorderKit (public, anonyme).
- **Dry-run / rollback** : supprimer `.tricorderkit/memory_router.yaml`+`context_sources.yaml`, `docs/07`+`08`+`diagrams/memory_map.mmd`, `experiments/arbor_adapter/` ; garder la trace ici.
- **Reste a faire** : brancher memory_router au boot (cowork-boot/tk-boot) si valide a l'usage ; lancer un 1er benchmark Arbor controle avant toute promotion.
- **Statut** : **Acceptee - memory-router + Arbor prototype livres 2026-06-20**.

*Derniere mise a jour : 2026-06-20 - DEC-052 memory-router (4.1) + Arbor prototype isole (4.2) ; grill-me=tk-grill existant (non duplique).*

## DEC-053 - Skill god-mode (radar d'innovation) + roadmap PoC d'amelioration - 2026-06-22
- **Contexte** : fichiers utilisateur 8 (God Mode List : 9 sources de veille) + 9 (methode expert-IA : metacognition/explicabilite). Demande : god-mode = skill d'auto-apprentissage pour ameliorer TricorderKit.
- **Decision** : creer `skills/god-mode/` (SKILL.md + sources.yaml) = radar : scan sources tierees -> score (40 pertinence + 30 adoption + 20 recence + 10 faisabilite) -> mapping module TK -> PROPOSITION (100%, jamais d'adoption auto). N'duplique pas deep-research-core/learning-engine/tool_scout (les orchestre). Planifie hebdo (tache Cowork `godmode-radar-weekly`, theme tournant -> bus).
- **1ere passe radar** (4 recherches reelles) -> 4 candidats, roadmap ordonnee en **PoC isoles `experiments/` + DEC** :
  1. RAGAS dans eval-lab (~82) - eval RAG objective sans ground-truth. **PoC livre** : `experiments/ragas_eval/` (moteur proxy deterministe offline + chemin RAGAS lazy, selftest OK). Debloque la mesure du reste.
  2. Blocking embeddings dedup (~78) - etage embeddings (Qdrant/nomic) avant RapidFuzz. Scaffold `experiments/dedup_embeddings/`.
  3. Memoire temporelle Graphiti/Zep (~85) - graphe temporel sur Neo4j existant, vs memvid. Scaffold `experiments/temporal_memory/`.
  4. GraphRAG (~72) - recuperation entite-relation, mesure via RAGAS. Scaffold `experiments/graphrag/`.
  - **ECARTE (YAGNI)** : ColBERT/late-interaction (~35) - niche 2026, +1-2 ordres de grandeur stockage pour qualite equivalente au bi+cross-encoder existant.
- **Risk Guard** : LOW (skill + PoC isoles ; aucune modif du coeur ; promotion = DEC par PoC apres mesure).
- **Routage (DEC-016)** : generique -> TricorderKit (public, anonyme). Rapport radar = claude-vault (memoire).
- **Statut** : **Acceptee - skill + radar hebdo + PoC#1 livres 2026-06-22 ; PoC #2-4 scaffoldes (a developper un par un sur GO).**

*Derniere mise a jour : 2026-06-22 - DEC-053 god-mode radar + roadmap PoC (RAGAS livre, dedup/memoire/graphrag scaffoldes ; ColBERT ecarte).*

## DEC-054 - Gate docs-sync : detection de derive (fraicheur) - 2026-06-23

Contexte : la vitrine (README/STATUS/ROADMAP/CHANGELOG) est restee figee a v1.0.0 malgre ~200 commits
(skills/experiments/infra additifs). La gate docs-sync (DEC-028/049) ne verifiait que la COHERENCE
(version/tests/plugins identiques partout), pas la COMPLETUDE -> derive non detectee.

Decision : etendre check_docs_sync.py avec deux controles de FRAICHEUR en severite WARNING (non bloquants,
exit 0 conserve) : (1) nombre de commits depuis le tag de la version canonique > seuil (--max-drift, defaut 60)
-> "vitrine probablement perimee" ; (2) tout sous-dossier de skills/ suivi par git mais absent du texte de la
vitrine -> "skill present hors vitrine". Non bloquant par design (un WARNING nudge, ne casse pas un push de
hotfix). A fait ses preuves immediatement : a flague 4 skills hors vitrine (tk-grill, skill-creator,
skill-manager, consolidate-memory), ajoutes a la vitrine. Cap v1.1.0 publie (Release GitHub) en parallele.

## DEC-055 - Skills distribues/installes comme PLUGINS dedies - 2026-06-24

Regle (preference Sebastien, NON-NEGOCIABLE) : des qu'on cree un ENSEMBLE de skills, les REUNIR dans un
PLUGIN dedie (.plugin) plutot que skill par skill. Un .plugin s'installe en un clic (Reglages > Capacites) ;
un SKILL.md depose dans un repo ne s'auto-installe PAS dans Cowork.

Decoupage public/prive (R37) :
- skills generiques -> plugin PUBLIC versionne dans TricorderKit ;
- skills qui nomment la stack (Paperclip / n8n / open-webui / Hermes / VPS...) -> plugin PRIVE (vault ou
  MangaTracker). NE JAMAIS empaqueter un skill prive dans un plugin destine au repo public.

Outillage : tools/pack_plugin.py (stdlib zipfile -> entrees a separateurs '/', conforme ZIP, cross-plateforme).
Contexte : Compress-Archive (PowerShell) ecrivait des '\' non conformes -> installeur Cowork en echec ;
pack_plugin.py corrige ce piege.

Process a chaque nouvel ensemble de skills :
1) packager via pack_plugin.py (public et/ou prive selon R37) ;
2) METTRE A JOUR la sauvegarde (repo public pour le plugin public ; MangaTracker/vault pour le prive) ;
3) PUSH ;
4) consigner R49.

Premier plugin produit sous cette regle : tricorderkit-skills (8 skills, installe le 2026-06-24).
