# ROADMAP TricorderKit v0.9

> Créé : 2026-05-18
> Source : docs/03_WHAT_TO_DO_NEXT.md + Session audit 2026-05-18
> Statut : En cours

---

## Jalons

### M1 — Foundation v0.9 (2026-05-25)

**Objectif :** Tout ce qui bloque les phases suivantes.

| Tâche | Statut | Preuve de fin |
|---|---|---|
| S3 — memory-boot manifest v0.8 | ✅ DONE | `plugins/memory-boot/manifest.yml` + 21 tests |
| S3 — token-optimizer manifest v0.8 | ✅ DONE | `plugins/token-optimizer/manifest.yml` + 31 tests |
| S4 — /tk:boot câblé `.claude/commands/` | ✅ DONE | `/tk:boot` exécutable nativement |
| W1 — skill rtk | ✅ DONE | `skills/rtk/SKILL.md` |
| W2 — skill docmancer | ✅ DONE | `skills/docmancer/SKILL.md` |
| W3 — obsidian-goat CLI | ✅ DONE | `tools/obsidian-goat/` + 19 tests |

---

### M2 — Orchestration v0.9 (2026-06-08)

**Objectif :** Fermer la boucle entre l'intention et l'exécution durable.

| Tâche | Priorité | Preuve de fin |
|---|---|---|
| S1 — Temporal → connector_hub.dispatch wiring | S | `tk dispatch source-watch` → run actif dans Temporal UI |
| S2 — tk-orchestrator budget_guard + router (phase 2) | S | `/tk:orchestrate "test"` → JSON contractuel, budget affiché |
| A1 — obsidian-goat intégration fin de session | A | `python obsidian_goat.py update-hot-cache` en fin de session auto |

---

### M3 — Japan-Alliance Phase 1 (2026-06-22)

**Objectif :** Base de données Japan-Alliance opérationnelle.

| Tâche | Priorité | Preuve de fin |
|---|---|---|
| A2 — Schéma Supabase Japan-Alliance | A | Tables `series`, `authors`, `publishers`, `volumes`, `ai_extractions`, `review_queue` créées |
| B3 — Tests live deep-research | B | `pytest tests/ --live` → MangaDex + AniList PASS |
| Pipeline rtk → docmancer → review_queue | B | Fiche manga auto-générée depuis recherche |

---

### M4 — Observabilité bout-en-bout (2026-07-06)

**Objectif :** Pipeline hooks → Obsidian câblé.

| Tâche | Priorité | Preuve de fin |
|---|---|---|
| B2 — Pipeline hook logs → Temporal → Obsidian | B | Erreurs apparaissent dans ERRORS.md automatiquement |
| Skills manquants : token-savior, claude-code_router | B | Skills dans `skills/` avec tests |

---

## Risques actifs v0.9

| ID | Niveau | Description | Mitigation |
|---|---|---|---|
| R-001 | MEDIUM | Tests live deep-research jamais exécutés | Priorité M3/B3 |
| R-004 | LOW | obsidian-goat non testé sur Windows réel (sandbox Linux) | Tester sur poste Sébastien |
| R-005 | LOW | Temporal worker doit être redémarré à chaque session Docker | Documenter dans BOOT_SUMMARY.md |

---

## Décisions architecturales v0.9

Référence : `.planning/DECISIONS.md` (DEC-001 à DEC-011)

Nouvelles décisions attendues :
- DEC-012 : Stratégie wiring Temporal → connector_hub
- DEC-013 : Schéma Supabase Japan-Alliance (choix colonnes + index)

---

## État au 2026-05-18

```
Tests totaux : 174 PASS (103 v0.8 + 71 nouveaux session 2026-05-18)
Skills créés cette session : rtk, docmancer
CLIs créées cette session  : obsidian-goat (v0.1.0, dry_run_validated)
Plugins migrés v0.8        : memory-boot, token-optimizer
```

---

*TricorderKit v0.8 → v0.9 — GeekFamilyCorp — 2026-05-18*
