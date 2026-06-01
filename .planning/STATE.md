# STATE.md — TricorderKit v0.9

> État courant du projet. Mettre à jour à chaque session.
> Dernière mise à jour : 2026-06-01

> **Session 2026-06-01** : optimisation des tâches planifiées Japan-Alliance (DEC-020) —
> fusion du doublon d'enrichissement SO (un seul chargement de contexte vault/jour),
> volume 10+10 → 12 fiches/nuit, recadrage horaires anti-chevauchement (fenêtre creuse 02h–07h),
> correction dépendance (bilan 02h lit le rapport de la veille). Voir section « Tâches planifiées ».

> **Session 2026-05-29 (E4)** : contrôle vault Japan-Alliance + liens modules.
> Connexion vivante OK (5421 notes, rapports TK du jour écrits). DEC-014 : fix routing
> `vault_router.py` (obsidian-notes-vault → obsidian-japan-alliance) — appliqué local, push
> différé (commit groupé). `linked_projects.yaml` corrigé : `vault` → `obsidian/Japan-Alliance/`,
> `allow_tricorderkit_write` → false. Nom de vault = **Japan-Alliance** (sans suffixe `_vault` ;
> `japan-alliance_vault/` était une erreur de nommage ChatGPT, dossier vide à supprimer).

---

## Version courante

- **Version** : 0.9.5 — Public-ready
- **Date** : 2026-06-01
- **Phase active** : v0.9.5 poussé (graphify RAG local-first DEC-023 + dédup G1) — prochaine étape : verrouiller frontière privé/public (Lot 2) + tag release v0.9.5

---

## Statut des phases

| Phase | Nom | Statut | Vérifié |
|---|---|---|---|
| 0 | Bootstrap | ✅ Verified | 2026-05-13 |
| 1 | Fondations (fichiers fondateurs) | ✅ Verified | 2026-05-10 |
| 2 | CLI-Forge | ✅ Verified | 2026-05-13 |
| 2.5 | QualityGuard | ✅ Verified | 2026-05-15 |
| 3 | Workflows persistants (Temporal) | ✅ Verified | 2026-05-15 |
| 3.5 | Hook Layer v0.2 | ✅ Complet | 2026-05-16 |
| 4 | Deep Research — B3 tests live 24/24 PASS | ✅ Complet | 2026-05-22 |
| 5 | Quality Loop | ✅ Complet | 2026-05-16 |
| 6 | Séparation linked_project | ✅ Complet | 2026-05-17 |
| 6.5 | Restructuration → vault pur | ✅ Complet | 2026-05-17 |
| **v0.9 M1** | Foundation v0.9 — memory-boot + token-optimizer + skills rtk + docmancer | ✅ Complet | 2026-05-18 |
| **v0.9 M2** | Orchestration — connector_hub + budget_guard + Supabase | ✅ Complet | 2026-05-22 |
| **v0.9 M3** | Pipeline rtk→docmancer live + observabilité Langfuse | ✅ Complet | 2026-05-22 |
| **v0.9 M4** | CLI tk doctor + rapport + INSTALL.md + security | ✅ Complet | 2026-05-22 |
| **v0.9 M5** | security-audit-cli 18/18 tests · sanitize_input.activity.ts (RISK-005) · index_qdrant uuid.uuid5 (ERR-T-001) · Full Audit 5/5 PASS · Windows deployment | ✅ Complet | 2026-05-23 |
| **v0.9 M6** | Public-ready docs — README · ROADMAP · STATUS · Makefile · install-menu · anonymization | ✅ Complet | 2026-05-23 |

---

## Tests

```
Total     : 503 PASS — 0 FAIL — 15 skipped (live)  (+6 tests graphify locaux à intégrer)
Commit HEAD : 124baba (01/06/2026 — graphify RAG local-first + dédup G1)
```

---

## Statut des plugins

| Plugin | Statut | Version |
|---|---|---|
| cli-forge | ✅ Actif | — |
| workflow-engine | ✅ Actif — worker RUNNING | — |
| deep-research-core | ✅ Actif — tests live PASS | — |
| hook-layer | ✅ Actif v0.2.0 | v0.2.0 |
| memory-boot | ✅ Migré v0.8 | v0.8 |
| token-optimizer | ✅ Migré v0.8 | v0.8 |
| connector-hub | ✅ Actif | v0.1.0 |
| eval-lab | ✅ Actif | — |
| obsidian-agent-layer | ✅ Actif (34 tests) | — |
| security-audit-cli | ✅ Actif (16 tests) | — |
| graphify | 🧪 WIP | — |

---

## Infrastructure

| Service | Statut |
|---|---|
| Neo4j | ✅ Actif :7474/7687 |
| Qdrant | ✅ Actif :6333 |
| Langfuse | ✅ Actif :3001 |
| Temporal | ✅ RUNNING — worker `tricorderkit-hooks` |

---

## Architecture linked_projects

```text
TricorderKit    = moteur générique anonymisé (public)
MangaTracker    = linked_project — CLIs, pipelines, skills, agents (privé)
Japan-Alliance  = vault Obsidian pur — données uniquement (privé)
```

Règle d'or : **TricorderKit exécute. Le projet lié spécialise. Le vault stocke.**

---

## Tâches planifiées (Japan-Alliance) — DEC-020, 2026-06-01

Fuseau : Europe/Paris. Prompts dans `%USERPROFILE%\Documents\Claude\Scheduled\` (hors repo versionné).

| Heure | Tâche | Cron | Rôle |
|---|---|---|---|
| 02h00 quotidien | `analyse-japan-alliance` | `0 2 * * *` | Bilan veille + Master Index + **enrichissement SO consolidé (12 fiches)** |
| 04h00 dimanche | `weekly-ecosystem-audit` | `0 4 * * 0` | Grand Audit écosystème (skills/plugins/MCPs) + 90_Templates |
| 05h00 quotidien | `japan-alliance-an-tracker` | `0 5 * * *` | Tracker complétion fiches Anime (AN) |
| 07h00 quotidien | `japan-alliance-tricorderkit-7h30` | `0 7 * * *` | Rapport matinal **allégé** (reporting run nuit, lecture seule) |
| 12h00 quotidien | `rollout-studios-japan-alliance` | `0 12 * * *` | Création 10 fiches studios ST### depuis la file |

Règles : enrichissement SO en **un seul passage nuit** (12 fiches) ; bilan 02h lit `RAPPORT_[DATE_HIER].md` ; écarts ≥ 1h, jitter ~8 min → aucun chevauchement.

---

## Blockers actifs

Aucun.

---

## Pre-push checklist (avant git push public)

```
[ ] tk security check-anon → [OK]
[ ] git grep "Users\<username>" → 0 résultats (hors configs/local/)
[ ] git grep "<nom-projet-lié>" → 0 résultats hors docs/ et .planning/
[ ] .env absent du diff
[ ] vault/*.json absent du diff (gitignored)
[ ] configs/local/ absent du diff (gitignored)
[ ] CHANGELOG.md entrée [0.9.0] ajoutée
[ ] make test → 0 FAIL
```

---

## Prochaines actions recommandées

```text
1. [COMMIT]   git add -A && git commit -m "feat: v0.9 public-ready — docs + anonymization + install"
2. [TEST]     make test → vérifier 0 FAIL
3. [SECURITY] tk security check-anon → [OK]
4. [PUSH]     git push origin main
5. [NEXT]     v0.9 M7 optionnel : VPS deployment (DEC-011 — local-first maintenu)
```

---

*Dernière mise à jour : 2026-06-01 — DEC-020 optimisation tâches planifiées (fusion SO + recadrage horaires, volume 12)*
