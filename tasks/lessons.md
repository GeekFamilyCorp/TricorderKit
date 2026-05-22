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
