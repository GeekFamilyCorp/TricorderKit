# Lessons Learned — TricorderKit
> Fichier initialisé le 2026-05-18 (Workflow Standard v1.0)
> Règle R12 : après toute correction utilisateur → mettre à jour ce fichier dans la même session.
> Ne jamais supprimer une leçon. Marquer [RÉSOLU] si la cause racine est éliminée dans le code.

---

## LESSON-001 — 2026-05-18
**Contexte :** Temporal worker non démarré alors que le scaffold existait (KI-004).
**Erreur :** Ne pas avoir vérifié `docker compose ps` avant de tester les workflows.
**Règle préventive :** Avant tout test d'un workflow Temporal, vérifier `docker compose ps | grep temporal`.
**Fichiers concernés :** `docker-compose.yml`, `plugins/workflow-engine/`
**Statut :** [RÉSOLU] — KI-004 résolu le 2026-05-16, worker RUNNING confirmé.

## LESSON-002 — 2026-05-18
**Contexte :** docs/02_WHAT_IS_IN_PLACE.md (v0.7) décrivait Temporal comme non démarré alors que RUNNING depuis 16/05.
**Erreur :** Pas de mise à jour du fichier d'inventaire après chaque session intensive.
**Règle préventive :** Après toute session qui change l'état d'un service ou d'un plugin, mettre à jour STATE.md avant de committer.
**Fichiers concernés :** `docs/`, `.planning/STATE.md`
**Statut :** [RÉSOLU] — STATE.md v0.8 à jour.

## LESSON-003 — 2026-05-18
**Contexte :** Audit post-v0.8 révèle docs/00→04 absents de la v0.8 (restés dans TricorderKit_v0.7/).
**Erreur :** Migration Phase 6 a déplacé les sources domaine-spécifiques mais pas migré les docs fondateurs.
**Règle préventive :** Toute migration de version doit inclure un checklist explicite : "docs fondateurs migré ? OUI/NON"
**Fichiers concernés :** `docs/`, `TricorderKit_v0.7/docs/`
**Statut :** ⬜ À corriger en v0.9 (créer docs/00→04 depuis TricorderKit_v0.7)

## LESSON-004 — 2026-05-18
**Contexte :** HOT_CACHE Obsidian 15 jours stale — aucun mécanisme automatique de mise à jour.
**Erreur :** Pas de wiring end-session vers le vault. Le skill memory-boot lit le HOT_CACHE mais ne l'écrit pas.
**Règle préventive :** Fin de session → toujours mettre à jour HOT_CACHE.md manuellement jusqu'à création obsidian-goat CLI.
**Fichiers concernés :** `00_SYSTEM/05_Hot_Cache/HOT_CACHE.md` (vault Obsidian)
**Statut :** ⬜ Fix immédiat dans cette session. Automatisation en v0.9.

## LESSON-005 — 2026-05-18
**Contexte :** Caveman mode (token-optimizer:caveman) jamais intégré dans le protocole TricorderKit.
**Erreur :** Outil disponible dans l'écosystème Cowork mais non référencé dans AGENTS.md ni les workflows.
**Règle préventive :** Toute sortie de sous-agent injectée dans le contexte principal doit être en caveman lite : JSON structuré ou Markdown tabulaire, jamais prose narrative.
**Fichiers concernés :** `AGENTS.md`, `skills/tk-orchestrator/SKILL.md`
**Statut :** ⬜ À implémenter dans AGENTS.md + tk-orchestrator v0.9.

## LESSON-006 — 2026-05-22
**Contexte :** Bump version dans STATE.md (0.8 → 0.9 M2) a cassé `tests/test_cli_local.py` : version "0.8" hardcodée, CLI `--version` stale.
**Erreur :** Mise à jour STATE.md sans grep des strings de version dans `tests/`.
**Règle préventive (R16) :** Tout bump de version dans STATE.md → grep obligatoire sur `tests/` avant commit :
```bash
grep -rn "\"0\.[0-9]" tests/
```
Corriger toute string hardcodée et bumper `cli/tk.py --version` en même temps.
**Fichiers concernés :** `tests/test_cli_local.py`, `cli/tk.py`, `.planning/STATE.md`
**Statut :** [RÉSOLU] — version "0.9 M2" alignée dans test + CLI. 359 PASS, 0 FAIL.

## LESSON-007 — 2026-05-22
**Contexte :** `tk doctor` signalait ANTHROPIC_API_KEY et OPENAI_API_KEY comme secrets dans le repo, alors qu'il s'agissait de faux positifs dans `.env.example`, `*.md` et `cli/tk.py` lui-même.
**Erreur :** Le glob `*.example` dans git grep ne matche pas `.env.example` (le `*` ne couvre pas le préfixe `.env`). Les fichiers `.md` et le fichier source qui définit les patterns n'étaient pas exclus.
**Règle préventive (R17) :** Avant tout push public d'un scanner de secrets, valider la whitelist git grep sur trois cas :
1. `.env.example` (glob `*.example` insuffisant → ajouter `:!.env.example` explicitement)
2. Fichiers `*.md` (documentation avec variable sans valeur)
3. Le fichier source lui-même si les patterns y sont définis en dur (auto-référence)
```bash
git grep -l "ANTHROPIC_API_KEY=" -- ":!.env" ":!.env.example" ":!*.example" ":!*.md" ":!cli/tk.py"
```
**Fichiers concernés :** `cli/tk.py` (`_check_secrets`, `_SECRETS_EXCLUDE`)
**Statut :** [RÉSOLU] — whitelist étendue, `tk doctor` affiche `[OK] Aucun secret dans le repo`.

## LESSON-008 — 2026-05-29
**Contexte :** « Réparation » au niveau octet de `tools/obsidian-goat/obsidian_goat.py` (decode/encode surrogateescape) → fichier tronqué (perte de `main()`) puis octet `\xe2` sauté → UTF-8 invalide.
**Erreur :** Édition binaire d'un fichier source à encodage mixte (CRLF/UTF-8), sans validation post-édition.
**Règle préventive (R32) :** Ne jamais éditer un fichier source au niveau octet. Utiliser l'outil Edit, puis **valider avant de déclarer terminé** : `python -c "import ast; ast.parse(open(F,encoding='utf-8').read())"` + un smoke-run (`--version`/test).
**Fichiers concernés :** tout fichier source (`*.py`, `*.ts`).
**Statut :** [RÉSOLU] — fichier restauré, 23/23 tests PASS. Voir vault `PATTERN-EDIT-DUALFS-001`.

## LESSON-009 — 2026-05-29
**Contexte :** Commits via Desktop Commander avec sortie muette ; `git status` sandbox ≠ FS réel ; `git n'est pas reconnu` ; `index.lock` périmé.
**Erreur :** Supposer un environnement de fichiers unique et faire confiance à la capture stdout de DC.
**Règle préventive (R33) :** Sur ce poste Windows : git par **chemin complet** `C:\Program Files\Git\cmd\git.exe` via Desktop Commander (shell déjà PowerShell, ne pas préfixer `powershell`). **Vérifier l'état via le sandbox** (lecture git fiable) ; rediriger la sortie git vers un fichier si la capture DC est vide ; supprimer tout `index.lock` périmé (FS réel) avant add/commit.
**Fichiers concernés :** workflow git, `.git/`.
**Statut :** [RÉSOLU] — commit `c0c88b2` poussé ; PATH user complété (effectif au redémarrage app).

## LESSON-010 — 2026-05-29
**Contexte :** Attribution d'IDs de fiches (MG085, MA1100, MA1101) faite par grep manuel du vault.
**Erreur :** Pas d'outil déterministe pour le prochain ID libre → risque de collision.
**Règle préventive (R34) :** Avant d'attribuer un nouvel ID (`MA/MG/AR/ED/LN/ST…`), exécuter `obsidian-goat next-id <prefix>` (ou, à défaut, grep global du token) pour garantir l'unicité. Étend R29.
**Fichiers concernés :** `tools/obsidian-goat/obsidian_goat.py`.
**Statut :** [RÉSOLU] — commande `next-id` ajoutée.

## LESSON-011 — 2026-05-29
**Contexte :** « Fine Films » et « Aniplex » créés comme studios alors qu'ils sont distributeur / producteur.
**Erreur :** Créer une fiche d'un type donné sans vérifier la **nature réelle** de l'entité.
**Règle préventive (R35) :** Avant de créer une fiche d'entité, vérifier sa nature sur source officielle. Si elle ne correspond pas au type cible, **reclasser dans le bon dossier** (aiguillage producteur/éditeur/jeux/seiyū/goodies/non-classé), ne jamais forcer. Croiser une fiche existante d'une autre facette plutôt que dupliquer.
**Fichiers concernés :** vault Japan-Alliance ; tâche planifiée `rollout-studios-japan-alliance` (étape 1bis).
**Statut :** [RÉSOLU] — règle inscrite dans la tâche planifiée + reclassements effectués.

## LESSON-012 — 2026-05-29
**Contexte :** `obsidian-goat` → `sqlite disk I/O error` (cache au cwd non inscriptible) ; pytest bloqué par perms sur `.pytest_tmp`.
**Erreur :** Dépendre du cwd pour le cache et du dossier tmp du repo pour pytest.
**Règle préventive (R36) :** Définir un cache writable explicite (`OBSIDIAN_GOAT_CACHE=/tmp/...`) avant d'exécuter une CLI goat. Pour pytest sur mount : `-c /dev/null --basetemp=/tmp` ou copier le test hors repo.
**Fichiers concernés :** `tools/obsidian-goat/`, `tests/`.
**Statut :** [RÉSOLU].


## LESSON-013 — 2026-06-01
**Contexte :** Audit vitrine v0.9.5 — README/STATUS/CHANGELOG divergeaient (version, compte de tests, nombre de plugins) sans détection. DEC-026 (boundary) ne couvre pas la cohérence documentaire.
**Erreur :** Aucun contrôle mécanique « docs ↔ réalité du dépôt » avant push → la vitrine dérive silencieusement (ex. titre H1 STATUS.md resté en `v0.9`).
**Règle préventive (R39) :** Avant tout push public, exécuter `make gates` — boundary **et** docs-sync — qui doivent tous deux être verts. Le docs-sync (`scripts/check_docs_sync.py`) vérifie version (CHANGELOG canonique), compte de tests cross-doc, et structure plugins (STATUS/README vs `plugins/` réel). Complète R37 (boundary vert) et R38 (sync page centrale + modules).
**Fichiers concernés :** `scripts/check_docs_sync.py`, `.github/workflows/docs-sync.yml`, `.githooks/pre-push`, `Makefile`, `README.md`, `STATUS.md`.
**Statut :** [RÉSOLU] — gate appliqué (CI + pre-push), 7 tests PASS, dérive STATUS corrigée.

## LESSON-014 — 2026-06-02
**Contexte :** Configuration de la tâche planifiée "Daily News Mangas" (dans l'interface de l'application Antigravity, planifiée chaque soir vers 20h00-20h30) pour générer le rapport quotidien de veille de l'écosystème japonais (manga / LN / anime) à partir des sources situées dans `<antigravity-sources>` (dossier local hors repo).
**Erreur :** Oubli potentiel de vérification de l'exécution et des résultats de cette tâche lors de l'exécution automatique d'Antigravity de 21h10.
**Règle préventive (R40) :** Lors du run automatique d'Antigravity à 21h10, l'agent doit systématiquement lire le rapport de veille produit par la tâche "Daily News Mangas" (à 20h30), en synthétiser les points marquants et consigner cette synthèse dans la section « Veille Quotidienne JP » du rapport `antigravity_vers_claude.md`.
**Fichiers concernés :** `tasks/lessons.md`, `_sync_antigravity/antigravity_vers_claude.md`.
**Statut :** [RÉSOLU] — Règle de reporting pour "Daily News Mangas" intégrée.

## LESSON-015 — 2026-06-03
**Contexte :** 7 battements consécutifs crashés la nuit du 03/06 (00:02→06:02 Paris). Pattern : verrou `claude` posé, aucun log, aucune intégration, verrou jamais libéré. Backlog accumulé à ~120 fiches Phase 2.
**Cause racine :** Overflow de contexte composé au démarrage de chaque run :
- `ETAT_PARTAGE.md` : 205 lignes (~8 000 tokens), croissance illimitée
- `antigravity_vers_claude.md` : 265 lignes (~6 000 tokens), accumulation non bornée
- Répertoire `rapports/` : 221 fichiers à énumérer
- Total ≈ 20 000+ tokens avant tout travail → crash après prise de verrou, avant le journal.
**Règle préventive (R41) :** Pour toute tâche planifiée lisant des fichiers de coordination :
1. Imposer une **limite stricte de taille** sur chaque fichier lu (max 100 lignes pour ETAT_PARTAGE.md, 60 lignes pour les fichiers de rapport). Archiver l'excédent dans un fichier archive AVANT d'écrire.
2. Imposer un **plafond de traitement par run** (MAX 10 fiches/battement) indépendamment du backlog réel.
3. Lire les fichiers en **mode ciblé** (frontmatter + sections actives uniquement, jamais l'historique complet).
**Fichiers concernés :** `_sync_antigravity/ETAT_PARTAGE.md`, `_sync_antigravity/antigravity_vers_claude.md`, `Scheduled/sync-antigravity-fiches/SKILL.md`.
**Statut :** [RÉSOLU] — Fichiers archivés + SKILL.md mis à jour (garde-fous + plafond 10 fiches). Voir `_sync_antigravity/journal_archive.md`.


## R42 - Wrappers MCP a secret : .cmd + stdin protege + config client sans BOM (2026-06-07)
**Contexte :** migration d'un PAT (connecteur GitHub MCP) du fichier de config en clair vers le Credential Manager Windows, via wrapper de lancement.
**Trois pieges rencontres :**
1. Wrapper PowerShell pur -> le serveur stdio recoit EOF immediat (PowerShell consomme le pipe au lieu de le transmettre au natif). Wrapper `.cmd` obligatoire (handles bruts).
2. `for /f` (capture du secret) fait heriter stdin au PowerShell imbrique qui l'avale -> `^< nul` obligatoire sur l'appel imbrique.
3. `Set-Content -Encoding UTF8` (PS 5.1) ecrit un BOM -> le client MCP ne parse plus sa config au redemarrage et la REINITIALISE (perte de toute la section serveurs). Toujours `[IO.File]::WriteAllText` + `UTF8Encoding($false)`. Generalise la lecon git du 06-01 (commit -F en ASCII) a TOUTE config JSON consommee par une app.
**Regle preventive :** tester un wrapper MCP en STANDALONE (pipe JSON-RPC initialize, stdin maintenu ouvert via `(type f & ping)`) avant tout redemarrage du client ; ne jamais valider via la session MCP courante (elle reflete l'etat d'avant redemarrage).
**Statut :** [RESOLU] - patron documente dans RUNBOOK_INFRA.md section 14 (DEC-039).


## R43 - Archivage multi-sources : suffixe de provenance obligatoire (2026-06-07)
**Contexte :** exclusion du lot 2 (webtoons coreens) hors Japan-Alliance. Original (01_En_cours) et copie enrichie (zone de tri R40) portaient le MEME nom de fichier. Un `shutil.move` sequentiel des deux vers le meme dossier d'archive a ecrase l'original par l'enrichie.
**Consequence :** aucune perte reelle (originaux egalement presents dans `99_Migration_Backups/lot0_2026-06-06`), mais perte de la version originale DANS le dossier d'archive cible.
**Regle preventive :** tout script d'archivage qui regroupe des fichiers de PLUSIEURS sources (vault + zone de tri, ou plusieurs lots) DOIT suffixer chaque fichier par sa provenance (`_orig`, `_r40`, `_lotN`) OU echouer explicitement sur collision de nom. Jamais d'ecrasement silencieux lors d'un move/copy d'archivage. Documenter la provenance dans un `_README_provenance.md` du dossier d'archive.
**Statut :** [RESOLU] - provenance documentee, DEC-043.

## R44 - Watcher multi-lots : progres = reset du compteur de tentatives (2026-06-08)
**Contexte :** une tache Codex multi-lots reste `in_progress` ENTRE les lots. Le watcher comptait une tentative a chaque tick ou `codex_exec` etait occupe par une autre tache, epuisant MAX_ATTEMPTS et marquant la tache `failed` alors qu'elle PRODUISAIT des livrables (faux echec : CREATEURS-MANQUANTS, ENRICH-COQUILLES, DEDUP-ORICON-APPLY, FRONTMATTER-REBUILD le 07/06).
**Regle preventive :** avant de marquer `failed` sur depassement de tentatives, verifier si un livrable/rapport outbox du task est PLUS RECENT que le dernier lancement -> si oui, le run a produit : remettre le compteur a 0, ne pas echouer. Ne compter une tentative que sur lancement effectif, pas sur tick "occupe".
**Statut :** [RESOLU] - `inbox_watcher.ps1` patche (garde-fou PROGRES detecte), DEC-043 ; 5 taches reassignees seq 80-84.

## R45 - Encodage Python sous Windows : PYTHONIOENCODING="utf-8" obligatoire pour les emojis (2026-06-10)
**Contexte :** Exécution de commandes ou scripts Python sous Windows (comme `sync_bus.py read`) traitant du texte riche contenant des emojis (ex: 🟡).
**Erreur :** `UnicodeEncodeError: 'charmap' codec can't encode character...` car l'interpréteur Python hérite du codage cp1252 par défaut sous Windows lors de l'écriture vers stdout.
**Regle preventive :** Toujours préfixer ou définir la variable d'environnement `$env:PYTHONIOENCODING="utf-8"` (ou `PYTHONUTF8=1`) lors de l'exécution de commandes Python traitant des caractères non-ASCII ou emojis sur le terminal Windows.
**Statut :** [RESOLU] - Appliqué lors de la résolution de l'erreur d'encodage du bus multi-agents.


## R46 - Coherence de la vitrine avant push (docs-sync etendu au ROADMAP) (2026-06-12)
**Contexte :** le push v1.0.0 a aligne README/STATUS/CHANGELOG mais laisse ROADMAP.md en v0.9.5 / 544 tests / 10 plugins ; le gate docs-sync (DEC-028) ne lisait pas ROADMAP -> derive non detectee. Meme classe d'erreur : ajout du 13e plugin document-ingestion (DEC-048) sans MAJ de la vitrine.
**Regle preventive :** avant tout push public, version + nombre de tests + decompte plugins doivent etre IDENTIQUES dans README.md / STATUS.md / ROADMAP.md, concordants avec CHANGELOG.md (version canonique) et l'arborescence plugins/ suivie par git. Tout ajout de plugin = declaration dans le tableau de bord STATUS + decompte README/ROADMAP + bloc Resume. Verifier avec `python scripts/check_docs_sync.py` (bloquant en pre-push + CI).
**Statut :** [RESOLU] - gate check_docs_sync.py etendu au ROADMAP + comptage git-tracked + exclusion compteurs historiques (DEC-049) ; vert apres realignement 13 plugins.
