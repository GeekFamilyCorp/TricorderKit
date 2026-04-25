---
name: rapport
description: "Skill de bilan et rapport de session. Genere un resume des accomplissements, projets actifs, taches ouvertes et 3 suggestions d'amelioration. Declencher avec : 'rapport', 'status', 'bilan', 'qu est-ce qu on a fait', 'resume', 'avancees', 'ou en est-on', 'rapport de session', 'rapport du projet'."
---

# rapport — Skill de Bilan & Rapport de Session

> Skill complementaire de `memory-boot`. La ou `boot` charge le contexte,
> `rapport` genere le bilan de ce qui a ete accompli.

---

## DECLENCHEUR

Mots-cles : "rapport", "status", "bilan", "qu'est-ce qu'on a fait", "resume", "avancees",
"rapport de session", "rapport du projet", "qu'est-ce qui a marche", "ou en est-on"

---

## ETAPE 1 — Lecture des donnees (une seule passe)

Lire via `mcp__obsidian-claude-vault__read_multiple_notes` :

1. `00_SYSTEM/05_Hot_Cache/HOT_CACHE.md`
2. `00_SYSTEM/06_Successes/SUCCESSES_INDEX.md`
3. Daily Logs des 7 derniers jours : `10_INBOX/Daily_Logs/YYYY-MM-DD.md`

Si l'utilisateur mentionne un projet specifique, lire aussi la fiche
dans `00_SYSTEM/06_Successes/projects/` et `20_ENTITIES/Projects/`.

---

## ETAPE 2 — Generation du rapport

Produire un rapport structure en prose naturelle.

### En-tete
- Date et heure du rapport
- Periode couverte

### Projets actifs
Pour chaque projet actif detecte dans HOT_CACHE :
- Etat courant
- Derniere avancee documentee
- Prochaine etape identifiee

### Reussites recentes
- Skills ou plugins crees ou ameliores (source : SUCCESSES_INDEX + Daily Logs)
- Decisions importantes prises
- Problemes resolus

### Taches ouvertes prioritaires
- Top 3 avec contexte (source : HOT_CACHE TACHES OUVERTES)
- Signaler si une tache est ouverte depuis > 7 jours sans avancement

### 3 Suggestions d'amelioration
Basees sur les donnees reelles du vault :
- Pattern d'erreur recurrent → suggestion concrete
- Tache qui stagne → challenger l'utilisateur directement
- Gap de logging ou de documentation → nommer le probleme sans detour

Les suggestions doivent etre directes et challengeantes, pas flatteuses.

---

## ETAPE 3 — Log du rapport dans le Daily Log

Appender dans `10_INBOX/Daily_Logs/YYYY-MM-DD.md` (date du jour) :

```markdown
## RAPPORT GENERE — HH:MM
- Projets couverts : N
- Reussites recentes : N items
- Taches ouvertes : N
- Suggestion principale : [1 ligne]
```

---

## REGLES INVARIANTES

1. Ne jamais produire un rapport vague — chaque section doit contenir des donnees reelles
2. Si `SUCCESSES_INDEX` absent : signaler et proposer de l'initialiser
3. Si aucun Daily Log recent (> 3 jours sans log) : alerter — signal d'alarme protocole
4. Les suggestions doivent challenger l'utilisateur, pas le rassurer
5. Si rapport sur projet specifique : focaliser les 3 sections sur ce projet uniquement

---

## SIGNAL D'ALARME

Si ERRORS.md ou Daily Logs inertes depuis > 3 jours :
> ALERTE — Gap de logging detecte depuis X jours.
> Derniere entree : YYYY-MM-DD. Le protocole de fin de session n'est pas respecte.

---

## LIENS
- [[00_SYSTEM/05_Hot_Cache/HOT_CACHE.md]]
- [[00_SYSTEM/06_Successes/SUCCESSES_INDEX.md]]
- [[10_INBOX/Daily_Logs/]]
- [[40_ERRORS/Patterns/PATTERNS_INDEX.md]]
