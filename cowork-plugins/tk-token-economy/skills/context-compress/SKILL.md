---
name: context-compress
description: >
  Compresse le contexte d'une conversation longue en un résumé structuré à cinq sections (objectif,
  décisions, fichiers touchés, état courant, prochaines étapes) qui préserve chemins, identifiants et
  contraintes négociées, après archivage daté du contexte complet. À utiliser quand l'utilisateur demande
  « compresse le contexte », « résume pour continuer », « fais un handoff », « le contexte est trop
  chargé », ou avant de passer une longue conversation à un sous-agent. Ne pas utiliser pour raccourcir
  une réponse (→ caveman) ni pour une sortie de commande shell (→ cli-compress).
license: MIT
metadata:
  version: "2.0"
  updated: "2026-09-07"
  author: GeekFamilyCorp
---

# Context Compress

Principe (Agent-Skills-for-Context-Engineering, muratcankoylan) : la métrique à optimiser est **tokens-par-tâche**, pas tokens-par-requête. Une compression qui perd un détail crucial oblige à redemander.

## Quand

- Le contexte actif dépasse ~60 % de la fenêtre du modèle.
- Demande explicite, ou handoff vers un sous-agent.
- En prévention, toutes les 20-30 interactions d'une session longue.

## Procédure

1. **Archiver d'abord** (NO-DROP, R31) le contexte complet — écrire l'export dans un fichier puis :

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_archive.py <fichier-export.md> --name <sujet>
   # ou : cat export.md | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_archive.py --stdin --name <sujet>
   # lister : python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_archive.py --list
   ```

   Le script copie vers `~/.tk-token-economy/context-archive/<AAAAMMJJ-HHMMSS>_<sujet>.md` et affiche le chemin. Si aucun export n'est possible (Cowork sans accès fichier), le dire et ne pas promettre d'archive.

2. **Produire le résumé** avec le gabarit ci-dessous.
3. **Faire valider** par l'utilisateur avant d'en faire l'unique source de vérité.
4. Mentionner aux agents suivants : « Contexte compressé — original archivé dans `<chemin>` ».

## Gabarit

```markdown
## Contexte compressé
### 1. Objectif
### 2. Décisions actées
### 3. Fichiers / ressources touchés
### 4. État courant
### 5. Prochaines étapes
```

## Règles

- Jamais compresser les **2 derniers tours**.
- Jamais perdre : chemins, identifiants, URLs, noms de variables critiques, contraintes négociées (budget, compatibilité, règles R..).
- Compresser fort : reformulations, diagnostics intermédiaires, échanges informatifs.
- Cible : 10-20 % du volume initial. Au-delà de 30 % : insuffisant ; sous 5 % : risque de perte.

## Exemple rempli

```markdown
## Contexte compressé — audit tk-token-economy (2026-09-07)
### 1. Objectif
Remettre le plugin tk-token-economy au référentiel Anthropic sept. 2026 (frontmatter, models.json, skills fusionnés).
### 2. Décisions actées
- task-classifier fusionné dans model-router ; budget-tracker/analyzer/auto-optimize → skill `budget` à 3 modes.
- Aucun identifiant de modèle en dur : alias fast/default/deep via models.json.
- NO-DROP : anciens skills en `_archive/` avec ARCHIVED.md.
### 3. Fichiers / ressources touchés
- `skills/model-router/SKILL.md` : réécrit v2.0, manuel.
- `scripts/budget.py` : sous-commande `log --model <alias> --in --out` ; cible antigravity retirée.
- `.mcp.json` : archivé (`_archive/mcp.json.2026-09-07`).
### 4. État courant
Scripts testés (classify --json OK, budget log/status OK). Reste : docs-fresh, README, validation.
### 5. Prochaines étapes
1. Réécrire docs-fresh sur le connecteur Context7 de session.
2. plugin.json 0.3.0 + README.
3. quick_validate.py sur les 6 skills.
```

## Changelog

- 2026-09-07 — v2.0 : §superpowers supprimé ; archive implémentée par `scripts/context_archive.py` ; exemple rempli ajouté.
- 2026-04 — v1.x : gabarit à cinq sections.
