---
name: memory-boot
description: "Boot de session Claude — lit le HOT_CACHE, les patterns d'erreurs actifs et le log d'erreurs, puis log le demarrage dans le Daily Log du jour. Declencher en debut de chaque conversation Cowork : 'boot', 'reprends le contexte', 'charge ta memoire', 'hot cache', 'memoire', ou au debut de tout projet ou conversation longue."
---

# memory-boot — Protocole de Demarrage Session

> Ce skill initialise la memoire de travail a partir du vault Obsidian.
> Il doit etre invoque EN PREMIER, avant toute autre action.

---

## ETAPE 1 — Lecture du contexte (dans cet ordre)

Lire les fichiers suivants via `mcp__obsidian-claude-vault__read_multiple_notes` en une seule passe :

1. `00_SYSTEM/05_Hot_Cache/HOT_CACHE.md` — contexte vivant, taches ouvertes, dernieres decisions
2. `40_ERRORS/Patterns/PATTERNS_INDEX.md` — patterns d'erreurs actifs a eviter
3. `40_ERRORS/Error_Log/ERRORS.md` — erreurs recentes non resolues

Si la demande touche un projet specifique, lire aussi la fiche dans `20_ENTITIES/Projects/`.

---

## ETAPE 2 — Resume de demarrage

Produire un resume court (5-8 lignes max) :
- Date + heure de la session
- Projets actifs detectes
- Taches ouvertes prioritaires (3 max)
- Patterns d'erreurs actifs a surveiller (3 max)
- Derniere decision importante

---

## ETAPE 3 — Log du demarrage dans le Daily Log

Creer ou appender dans `10_INBOX/Daily_Logs/YYYY-MM-DD.md` (date du jour) :

```markdown
## SESSION START — HH:MM
- HOT_CACHE lu : oui
- Patterns charges : N actifs
- Contexte : [projet ou sujet de la conversation]
```

Si le fichier du jour n'existe pas, le creer avec ce frontmatter :
```yaml
---
type: log
tags: ["#claude-memory", "#daily-log"]
status: raw
created: "YYYY-MM-DD"
author: claude
---
# Daily Log — YYYY-MM-DD
```

---

## PROTOCOLE DE LOGGING EN COURS DE SESSION

### A chaque erreur detectee — appender dans `40_ERRORS/Error_Log/ERRORS.md`

```markdown
## [YYYY-MM-DD HH:MM] ERREUR — ERR-X

**Description :** [ce qui s'est passe]
**Contexte :** [projet / conversation]
**Correction appliquee :** [ce que j'ai fait]
**Pattern possible :** Non / Oui
**Recurrence :** Xeme fois
```

Codes d'erreur : ERR-C (comprehension), ERR-F (format), ERR-K (contenu), ERR-P (protocole), ERR-L (lien)

### A chaque action reussie significative — appender dans le Daily Log du jour

```
| [action] | [resultat court] | OK |
```

---

## ETAPE 4 — Fin de session (OBLIGATOIRE)

### 4a — Logger les reussites dans 06_Successes/

Si un skill, plugin ou projet a ete cree ou ameliore pendant la session :

1. **Nouveau skill** → creer ou mettre a jour `00_SYSTEM/06_Successes/skills/SKILL_NOM.md`
2. **Nouveau plugin** → creer ou mettre a jour `00_SYSTEM/06_Successes/plugins/PLUGIN_NOM.md`
3. **Nouveau projet** → creer ou mettre a jour `00_SYSTEM/06_Successes/projects/PROJECT_NOM.md`
4. **Mettre a jour** `00_SYSTEM/06_Successes/SUCCESSES_INDEX.md`

Format de fiche minimum :
```markdown
## Ce qui a fonctionne
[description courte]

## Decisions cles
[1-3 decisions]

## Localisation
[chemins ou liens]
```

### 4b — Cloturer le Daily Log

Appender dans `10_INBOX/Daily_Logs/YYYY-MM-DD.md` :
```markdown
## CLOTURE — HH:MM
- Skills/plugins crees : [liste ou "aucun"]
- Actions reussies : [liste ou "aucune"]
- Prochaine session : [priorite principale]
```

### 4c — Mettre a jour HOT_CACHE.md

Via `mcp__obsidian-claude-vault__patch_note` sur `00_SYSTEM/05_Hot_Cache/HOT_CACHE.md` :
- `last_session` -> date du jour
- Ajouter entree dans `## DERNIERES DECISIONS` si decision structurelle prise
- Cocher taches faites dans `## TACHES OUVERTES`
- Sync `## ERREURS RECENTES` avec PATTERNS_INDEX si nouveau pattern

---

## REGLES INVARIANTES

1. Ne jamais sauter l'ETAPE 1 — sans HOT_CACHE on travaille a l'aveugle
2. Toujours logger les erreurs immediatement, pas en fin de session
3. Si HOT_CACHE absent ou > 7 jours : prevenir l'utilisateur avant de continuer
4. Si ERRORS.md inerte depuis > 3 jours : signaler comme alerte
5. ETAPE 4 obligatoire si session productive (creation, decision, livraison)

---

## LIENS
- [[00_SYSTEM/05_Hot_Cache/HOT_CACHE.md]]
- [[00_SYSTEM/06_Successes/SUCCESSES_INDEX.md]]
- [[40_ERRORS/Patterns/PATTERNS_INDEX.md]]
- [[40_ERRORS/Error_Log/ERRORS.md]]
- [[00_SYSTEM/MASTER_PROTOCOL.md]]
