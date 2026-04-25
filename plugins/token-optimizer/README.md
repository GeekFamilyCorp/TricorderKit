# token-optimizer

Plugin Claude Cowork pour l'optimisation automatique de la consommation de tokens. Route chaque requête vers le modèle le plus économique compatible avec sa complexité.

## Architecture

```
token-optimizer/
├── skills/
│   ├── model-router/       # Orchestrateur central — classe et délègue
│   ├── task-classifier/    # Score 0-100 → tier T1/T2/T3
│   ├── budget-tracker/     # Suivi mensuel, alertes 50/80/95%
│   ├── context-compress/   # Compression structurée du contexte long
│   ├── docs-fresh/         # Injection de docs via MCP Context7
│   └── cli-compress/       # Compression des sorties shell via rtk
├── agents/
│   ├── haiku-executor.md   # Sous-agent T1 — Haiku 4.5
│   ├── sonnet-executor.md  # Sous-agent T2 — Sonnet 4.6
│   └── opus-executor.md    # Sous-agent T3 — Opus 4.6
└── scripts/
    ├── budget.py           # CLI budget tracker (status / log / reset)
    └── classify.py         # Classificateur déterministe (score + tier)
```

## Modèles et tiers

| Tier | Modèle | Score | Cas d'usage |
|------|--------|-------|-------------|
| T1 | Claude Haiku 4.5 | 0–25 | FAQ, traduction, extraction simple, reformulation |
| T2 | Claude Sonnet 4.6 | 26–60 | Rédaction, analyse, code non-critique, refactor |
| T3 | Claude Opus 4.6 | 61–100 | Architecture, sécurité, debug complexe, planification |

## Installation

1. Copier le dossier `plugins/token-optimizer/` dans votre répertoire de plugins Claude Cowork
2. Activer le plugin depuis les paramètres Cowork
3. Le skill `model-router` se déclenche automatiquement sur toute requête non triviale

## Scripts Python

```bash
# Statut du budget mensuel
python3 scripts/budget.py status

# Classifier un prompt
python3 scripts/classify.py --prompt "votre requête" --json

# Enregistrer une consommation
python3 scripts/budget.py log --model sonnet --input 3200 --output 1800
```

## Dépendances optionnelles

- **Context7 MCP** (`@upstash/context7-mcp`) — pour le skill `docs-fresh`
- **rtk** (Rust Token Killer) — pour le skill `cli-compress`

## Économies estimées

- Routage automatique T1/T2/T3 : **40–60% de réduction** vs Opus par défaut
- Compression contexte : **80–90%** sur les contextes longs
- CLI compress (rtk) : **60–90%** sur les sorties shell verbeuses
