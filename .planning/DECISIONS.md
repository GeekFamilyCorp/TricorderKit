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
  - `configs/local/linked_projects.yaml` pointe le vault lié vers `Projects/Japan-Alliance/japan-alliance_vault/` qui est un **dossier vide en lecture seule** (size 0, perms 444) ; le vault de contenu vivant (5421 notes) est en réalité `%USERPROFILE%\Documents\obsidian\Japan-Alliance`.
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

- **Contexte** : les cartes de filière (MOC franchises + IX000) ont révélé 4 anomalies systémiques dans le vault de contenu `%USERPROFILE%\Documents\obsidian\Japan-Alliance` (non versionné git → toute opération destructrice = HIGH risk → archivage réversible imposé).
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
