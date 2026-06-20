# Matrice de routage longueur x type

Lookup rapide a appliquer apres extraction des signaux.

## Matrice principale

| Longueur input (tokens) | Tache simple | Tache standard | Tache complexe |
|-------------------------|--------------|----------------|----------------|
| < 500                   | Haiku        | Haiku          | Sonnet         |
| 500 - 1500              | Haiku        | Sonnet         | Sonnet         |
| 1500 - 5000             | Sonnet       | Sonnet         | Opus           |
| 5000 - 15000            | Sonnet       | Sonnet         | Opus           |
| 15000 - 50000           | Sonnet       | Opus           | Opus           |
| > 50000                 | Opus         | Opus           | Opus           |

## Modificateurs de tier

Apres lookup initial, appliquer +/- 1 tier selon :

- **+1 tier** si domaine sensible (legal, medical, securite, prod)
- **+1 tier** si code avec `critique`, `production`, `deploy`, `securite`
- **-1 tier** si budget mensuel > 80%
- **-1 tier** si brouillon / exploration / idee rapide
- **Forcer Opus** si explicitement demande par l'utilisateur ("utilise Opus", "je veux le meilleur")
- **Forcer Haiku** si explicitement demande ("utilise Haiku", "mode economique")

## Couts relatifs (ordre de grandeur avril 2026)

| Modele | Cout input relatif | Cout output relatif | Latence |
|--------|--------------------|----------------------|---------|
| Haiku 4.5 | 1x | 1x | tres rapide |
| Sonnet 4.6 | ~3x | ~5x | rapide |
| Opus 4.6 | ~15x | ~25x | moyen |

**Heuristique pratique** : 1000 taches T1 (Haiku) = 200 taches T2 (Sonnet) = 40 taches T3 (Opus) en equivalent budget.

Verifiez les prix a jour sur https://docs.claude.com/en/docs/about-claude/pricing avant de trancher des arbitrages critiques.
