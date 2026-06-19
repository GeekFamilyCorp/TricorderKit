# Architecture — TricorderKit

> Vue d'ensemble. Référence de mapping : `docs/BLUEPRINT_AIOPS_GAP_2026-06-19.md`.

## Principe
**TricorderKit exécute · le projet lié spécialise · le vault stocke.** Le moteur est générique et anonymisé (public) ; la spécialisation domaine et les données vivent hors de ce dépôt.

## Couches
```
Gouvernance / mémoire   → AGENTS.md, CLAUDE.md, .planning/, vault mémoire (externe)
Décision                → core/ (MainBrain, hooks), routage modèle (plugin token-optimizer)
Compétences             → skills/ + plugins/ (cli-forge, deep-research-core, eval-lab…)
Connaissance / RAG      → plugin graphify (Neo4j + Qdrant) + mcp/servers (graph-server, vault-search)
Orchestration           → plugin workflow-engine (Temporal) + canal multi-agents
Connecteurs / MCP       → mcp/ (allowlist, gateway), plugin connector-hub
Observabilité           → Langfuse + core/hooks/langfuse_observer
Sécurité                → plugin security-audit-cli + gate frontière publique (R37)
Qualité                 → plugin eval-lab + tests/
Exécution déportée      → projet lié privé (infra/) + VPS (live)
```

## Flux type (veille → connaissance)
sources → collecte (déportée) → staging/quarantaine → QA/validation → graduation au canon (vault) → indexation RAG (graphify) → restitution.

## Frontières (DEC-016)
- Générique anonymisable → **ce dépôt (public)**.
- Domaine/exécution → **projet lié (privé)**.
- Données (fiches/notes) → **vault (Obsidian Sync)**, jamais en repo.

## Garde-fous
Gate frontière publique R37 (`scripts/check_public_boundary.py`) + sync `README`/`STATUS` (R38) à chaque push ; dry-run avant écriture externe ; secrets hors repo (`.env.example` + références).
