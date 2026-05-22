# README_FIRST — TricorderKit v0.9

> Lis ce fichier AVANT tout autre fichier du repo.

---

## Ce qu'est TricorderKit

TricorderKit est un **système d'exploitation agentique local-first**.

Il transforme les intentions utilisateur en workflows traçables, auditables et réutilisables.

```text
v0.6 : memory + skills + token hygiene + observability
v0.7 : CLI-first Agentic OS + Temporal workflows + skill registry + deep research + Obsidian knowledge layer
v0.8 : linked_project architecture + hook layer + quality loop + CLI tk + audit tools
v0.9 : orchestration M1+M2 + budget_guard T1/T2/T3 + observabilité + Japan-Alliance Phase 1
```

---

## Règle d'or

Un agent ne doit jamais improviser s'il peut utiliser :

1. une skill documentée
2. une CLI déterministe (cli-forge)
3. un workflow Temporal (workflow-engine)
4. une mémoire projet (vault / Obsidian)
5. une évaluation de non-régression (eval-lab)

---

## Par où commencer

```text
1. Lire ce fichier (README_FIRST.md) ← tu es là
2. Lire AGENTS.md si tu es un agent Claude
3. Lire CLAUDE.md si tu travailles avec Claude Code
4. Lire .planning/STATE.md pour l'état courant
5. Lire .planning/TASKS.md pour le backlog actif
```

---

## Stack

```text
Claude Code        → agent principal
Obsidian           → vault knowledge (local-first)
MCP                → connecteurs services
Neo4j              → graph relationnel
Qdrant             → vector search / RAG
Docker             → infra locale (DEV — voir docker-compose.yml)
Temporal           → orchestration workflows persistants
Langfuse           → observabilité tokens + traces (:3001)
```

---

## Architecture linked_projects

```text
TricorderKit    → moteur générique (ce repo)
MangaTracker    → linked_project agent CLI (privé)
Japan-Alliance  → vault Obsidian pur, données uniquement (privé)
```

> **TricorderKit exécute. MangaTracker spécialise. Japan-Alliance stocke.**

---

## Commande de démarrage

```bash
/tk:boot
```

Cette commande charge l'état courant, la mémoire projet et le contexte Obsidian.

---

## Principe de base

```text
Structure > Documents
Knowledge > Context Window
Reasoning > Retrieval Simple
Déterminisme > Improvisation
```

---

*Version 0.9 M2 — 2026-05-22*
