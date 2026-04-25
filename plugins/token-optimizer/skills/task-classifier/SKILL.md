---
name: task-classifier
description: >
  Classifie une requete utilisateur en tier de complexite (T1 simple, T2 standard, T3 complexe)
  pour alimenter le model-router. Expose un score numerique 0-100 et une explication.
  Se declenche quand l'utilisateur demande "classifie cette demande", "evalue la complexite",
  "quel est le niveau de cette tache", ou quand le skill model-router en a besoin.
---

# Task Classifier

Analyse la complexite cognitive d'une requete et retourne un tier avec justification.

## Entrees

Le prompt de l'utilisateur, eventuellement enrichi du contexte precedent.

## Dimensions evaluees

1. **Longueur input** (0-30 pts)
   - < 500 tokens : 0
   - 500-1500 : 5
   - 1500-5000 : 10
   - 5000-15000 : 20
   - > 15000 : 30

2. **Longueur output attendue** (0-20 pts)
   - Reponse courte (< 300 mots) : 0
   - Reponse moyenne (300-1500 mots) : 10
   - Reponse longue (> 1500 mots ou code > 200 lignes) : 20

3. **Profondeur de raisonnement** (0-25 pts)
   - Factuel / extraction : 0
   - Analyse simple : 10
   - Raisonnement multi-etapes : 20
   - Architecture / trade-offs / preuve : 25

4. **Domaine sensible** (0-15 pts)
   - Aucun : 0
   - Technique standard : 5
   - Legal / medical / securite / financier / production : 15

5. **Contexte multi-sources** (0-10 pts)
   - Mono-source : 0
   - 2-3 sources : 5
   - > 3 sources ou multi-fichier : 10

## Score final → Tier

- 0-25 pts : **T1 Haiku**
- 26-60 pts : **T2 Sonnet**
- 61-100 pts : **T3 Opus**

## Usage programmatique

Pour une classification deterministe, appeler :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/classify.py --prompt "<prompt>" --json
```

Sortie :

```json
{
  "score": 42,
  "tier": "T2",
  "model": "claude-sonnet-4-6",
  "dimensions": {
    "input_length": 10,
    "output_length": 10,
    "reasoning_depth": 20,
    "sensitive_domain": 0,
    "multi_source": 2
  },
  "explanation": "Tache de redaction moyenne avec analyse..."
}
```

## Sortie a restituer a l'utilisateur

Format court :

```
Score : 42/100 -> T2 Sonnet 4.6
Raison : redaction moyenne avec analyse documentaire (input 3k, output ~1k, analyse multi-etapes).
```
