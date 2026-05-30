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
