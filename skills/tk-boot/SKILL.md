# Skill : /tk:boot — TricorderKit v0.8

> Boot de session TricorderKit — charge état, mémoire, contexte et budget tokens.
> Mis à jour : 2026-05-18 — BOOT_SUMMARY.md (lazy-load) + Workflow Standard v1.0 (R8→R15)

---

## Déclencheur

```text
/tk:boot
```

Déclencher en début de chaque session Claude Code sur TricorderKit.

---

## Stratégie de boot (lazy-load — économie tokens)

```text
TIER 1 — Toujours charger (~500 tokens)
  1. BOOT_SUMMARY.md            → résumé exécutif : version, tâches, patterns, décisions

TIER 2 — Charger si BOOT_SUMMARY ne suffit pas (~2 500 tokens)
  2. tasks/lessons.md            → règles préventives actives (R12)
  3. .planning/STATE.md          → état détaillé si phase ou infra à vérifier
  4. .planning/TASKS.md          → items pending/in_progress SEULEMENT (exclure ✅)
  5. .planning/DECISIONS.md      → 5 dernières entrées seulement

TIER 3 — Charger à la demande uniquement (~10 000 tokens)
  - .planning/RISKS.md           → si risque actif à gérer
  - docs/00_WHAT_IS_TRICORDERKIT.md → si doute sur la vision
  - docs/01_HOW_IT_WORKS.md      → si debug architecture
  - docs/02_WHAT_IS_IN_PLACE.md  → si inventaire à vérifier
  - docs/03_WHAT_TO_DO_NEXT.md   → si backlog à reprioriser
  - docs/04_LLM_OPERATING_GUIDE.md → si nouvel agent ou règles complexes
  - docs/06_workflow_standard.md → si règles R8→R15 à rappeler
```

> **Règle d'or :** Si BOOT_SUMMARY + lessons.md suffisent pour comprendre le contexte
> et démarrer la tâche → **ne pas charger les Tier 2/3**. Aller directement à l'action.

---

## Instructions pour l'agent

### Étape 1 — Lire BOOT_SUMMARY.md (obligatoire, Tier 1)

Lire `BOOT_SUMMARY.md` en premier. Extraire :
- Version + commit HEAD
- Prochaine tâche prioritaire
- Patterns d'erreurs actifs
- Statut Docker

### Étape 2 — Évaluer si Tier 2 est nécessaire

Charger `tasks/lessons.md` systématiquement (règles préventives actives).
Charger `STATE.md` uniquement si :
- La phase active n'est pas claire depuis BOOT_SUMMARY
- Un blocker est signalé dans BOOT_SUMMARY
- La tâche demandée touche l'infrastructure ou un plugin

### Étape 3 — Estimer le budget tokens

Calculer approximativement :
- Tokens déjà utilisés dans le contexte courant
- Ratio utilisé / fenêtre max
- Niveau : SAFE (<50%) | WATCH (50–79%) | ALERT (80–99%) | CRITICAL (≥100%)

Si ALERT ou CRITICAL → recommander `/tk:pack-context` avant de continuer.

### Étape 4 — Identifier la prochaine action

Depuis BOOT_SUMMARY section "Prochaines tâches" :
- Tâche #1 de la liste → la recommander
- Si tâche en cours dans le contexte → la reprioriser

### Étape 5 — Afficher le rapport de boot

```markdown
## 🚀 TricorderKit Boot — [DATE]

**Version :** vX.X | **Commit :** xxxxxxx | **Budget :** XX% [SAFE|WATCH|ALERT|CRITICAL]
**Phase active :** [nom] | **Blockers :** Aucun / [liste]

### Prochaine action recommandée
> [Action concrète — une ligne]

### Patterns actifs à surveiller
- [CODE] — [règle courte]

### Tâches en cours (si applicable)
- [ ] [tâche]
```

### Étape 6 — Mettre à jour BOOT_SUMMARY.md (fin de session)

En fin de session, mettre à jour `BOOT_SUMMARY.md` :
- Version + commit HEAD si changé
- Tâches cocher/décocher
- Ajouter nouveaux patterns si applicable
- Mettre à jour "Dernière session"

---

## Output contract

Respecter le schéma `core/contracts/skill_output.schema.json` :

```json
{
  "status": "success",
  "skill_name": "tk-boot",
  "skill_version": "0.2.0",
  "timestamp": "<ISO8601>",
  "output": {
    "summary": "Boot OK — vX.X, tâche: [nom], budget XX%",
    "data": {
      "version": "0.8",
      "commit_head": "xxxxxxx",
      "next_task": "description",
      "active_patterns": ["CODE1", "CODE2"],
      "token_budget_pct": 12,
      "token_budget_level": "SAFE",
      "tier_loaded": [1, 2]
    },
    "next_steps": ["Action recommandée"]
  }
}
```

---

## Erreurs fréquentes et solutions

| Erreur | Cause | Solution |
|---|---|---|
| `BOOT_SUMMARY.md` introuvable | Fichier non encore créé | Créer depuis ce template ou lancer `/tk:boot --rebuild-summary` |
| `tasks/lessons.md` introuvable | Workflow Standard non initialisé | Créer avec structure vide (voir `docs/06_workflow_standard.md`) |
| Budget tokens CRITICAL | Contexte trop chargé | Exécuter `/tk:pack-context` immédiatement |
| Workflows actifs non détectés | Temporal non démarré | `docker compose up -d temporal` + `npx ts-node plugins/workflow-engine/scripts/start_worker.ts` |

---

## Commandes variantes

```bash
/tk:boot                    # Boot standard — Tier 1 + 2 si nécessaire
/tk:boot --summary-only     # Lire BOOT_SUMMARY uniquement (ultra-léger)
/tk:boot --check-workflows  # Inclut /tk:workflow-status
/tk:boot --update-summary   # Mettre à jour BOOT_SUMMARY.md depuis STATE.md
/tk:dry-run /tk:boot        # Simule sans lire les fichiers
```

---

*Version 0.2.0 — 2026-05-18 — Lazy-load Tier 1/2/3 + BOOT_SUMMARY.md*
