# QUEUE.md — Plan d'actions TricorderKit v0.9

> Exécution séquentielle. Cocher après chaque action + commit.
> Créé : 2026-05-22

---

## Légende
- `[DONE]` Complétée ✅
- `[TODO]` À faire
- `[WIP]`  En cours

---

## Action 1 — Mise à jour BOOT_SUMMARY.md post-M2

**Statut : [DONE] ✅**
**Résultat :** BOOT_SUMMARY.md à jour — 247 tests, v0.9 M2, commit `dd6902f`, session 2026-05-18.

---

## Action 2 — Push GitHub TricorderKit v0.9 M2

**Statut : [TODO]**
**Objectif :** Pousser tous les commits M2 locaux vers `origin/main`.
**Prérequis :** Actions 1 complétée.
**Validation :** `git push` OK + CI vert sur GitHub.

---

## Action 3 — Fix conftest conflit eval-lab / tk-orchestrator

**Statut : [TODO]**
**Objectif :** Résoudre les 10 tests failing pre-existing dus au conflit de fixtures conftest.
**Validation :** `pytest tests/` → 0 failures liées au conftest.

---

## Action 4 — Créer BOOT_SUMMARY_JA.md dans claude-vault

**Statut : [DONE] ✅**
**Destination :** `%USERPROFILE%\Documents\Claude\claude-vault\20_ENTITIES\Projects\BOOT_SUMMARY_JA.md`
**Contrainte :** ≤ 500 tokens.
**Source de vérité :** `BOOT_SUMMARY.md` (TricorderKit — 247 tests, v0.9 M2, commit `dd6902f`).

### Critères de validation
- [x] Fichier créé dans `claude-vault/20_ENTITIES/Projects/`
- [x] Contenu ≤ 500 tokens
- [x] Sections : Version/statut, Infrastructure, Tâches ouvertes, Complétés M2
- [x] Frontmatter YAML correct (project, version, commit, type)

---

## Action 5 — Générer vault/session_capsule_v0.9_JA.json

**Statut : [DONE] ✅**
**Sources :**
- `TricorderKit/vault/session_capsule_v0.9_JA.json` (fichier généré)
- Copie dans `%USERPROFILE%\Documents\Claude\claude-vault\` (racine)

**open_tasks alignés avec BOOT_SUMMARY.md :**
1. B3 — Tests live deep-research (MangaDex + AniList)
2. M4 — Observabilité bout-en-bout (Langfuse hooks)
3. FIX-CONF — Fix conftest eval-lab / tk-orchestrator (10 tests)
4. M3-LIVE — Pipeline rtk→docmancer test live
5. PUSH-M2 — Push GitHub TricorderKit v0.9 M2

### Critères de validation
- [x] JSON valide (schema, version, commit, tests_pass)
- [x] `open_tasks` aligné avec BOOT_SUMMARY.md (5 tâches)
- [x] Infrastructure complète (4 services)
- [x] Copié dans claude-vault

---

*Dernière mise à jour : 2026-05-22 — Actions 1, 4, 5 DONE*
