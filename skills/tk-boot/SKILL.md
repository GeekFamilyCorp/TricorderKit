# Skill : /tk:boot — TricorderKit v0.7

> Boot de session TricorderKit — charge état, mémoire, contexte et budget tokens.

---

## Déclencheur

```text
/tk:boot
```

Déclencher en début de chaque session Claude Code sur TricorderKit.

---

## Ce que fait ce skill

```text
1. Lire .planning/STATE.md          → état courant du projet
2. Lire .planning/TASKS.md          → tâches actives et backlog
3. Lire .planning/DECISIONS.md      → décisions déjà prises
4. Lire .planning/RISKS.md          → risques identifiés
5. Estimer le budget tokens courant → % fenêtre contexte utilisé
6. Vérifier les workflows actifs    → /tk:workflow-status (si Temporal up)
7. Afficher un résumé structuré     → état + tâche recommandée
```

---

## Instructions pour l'agent

### Étape 1 — Lire les fichiers de planning

Lire dans l'ordre :
1. `.planning/STATE.md`
2. `.planning/TASKS.md`
3. `.planning/DECISIONS.md` (résumé des 5 dernières entrées seulement)
4. `.planning/RISKS.md` (risques ouverts uniquement)

### Étape 2 — Estimer le budget tokens

Calculer approximativement :
- Tokens déjà utilisés dans le contexte courant
- Ratio utilisé / fenêtre max
- Niveau : SAFE (<50%) | WATCH (50–79%) | ALERT (80–99%) | CRITICAL (≥100%)

Si ALERT ou CRITICAL → recommander `/tk:pack-context` avant de continuer.

### Étape 3 — Identifier la prochaine action

Lire dans `.planning/TASKS.md` :
- Tâches "En cours" → les signaler
- Première tâche "Pending" dans la phase active → la recommander

### Étape 4 — Afficher le rapport de boot

Produire un rapport structuré au format suivant :

```markdown
## 🚀 TricorderKit Boot — [DATE]

**Phase active :** Phase X — [Nom]
**Tâches en cours :** N
**Risques ouverts :** N
**Budget tokens :** XX% — [SAFE|WATCH|ALERT|CRITICAL]

### Tâches actives
- [ ] Tâche 1
- [ ] Tâche 2

### Risques ouverts
- RISK-001 — [niveau] — [titre]

### Prochaine action recommandée
> [Action concrète à faire maintenant]

### Décisions récentes
- DEC-00X — [titre]
```

---

## Output contract

Respecter le schéma `core/contracts/skill_output.schema.json` :

```json
{
  "status": "success",
  "skill_name": "tk-boot",
  "skill_version": "0.1.0",
  "timestamp": "<ISO8601>",
  "output": {
    "summary": "Boot OK — Phase X, N tâches, budget XX%",
    "data": {
      "phase_active": "Phase X",
      "active_tasks": N,
      "open_risks": N,
      "token_budget_pct": XX,
      "token_budget_level": "SAFE|WATCH|ALERT|CRITICAL"
    },
    "next_steps": ["Action recommandée"]
  }
}
```

---

## Erreurs fréquentes et solutions

| Erreur | Cause | Solution |
|---|---|---|
| `.planning/STATE.md` introuvable | Phase 1 non complétée | Créer `.planning/STATE.md` en suivant le template |
| Budget tokens CRITICAL | Contexte trop chargé | Exécuter `/tk:pack-context` immédiatement |
| Workflows actifs non détectés | Temporal non démarré | Docker Compose up + start_worker.ts |

---

## Exemples

### Boot standard

```
/tk:boot
```

→ Charge l'état, affiche le rapport de boot, recommande la prochaine action.

### Boot avec vérification workflows

```
/tk:boot --check-workflows
```

→ Inclut le status des workflows Temporal actifs.

### Boot dry-run

```
/tk:dry-run /tk:boot
```

→ Simule le boot sans lire les fichiers.

---

*Version 0.1.0 — 10/05/2026*
