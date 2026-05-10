# README_FIRST — TricorderKit v0.7

> Lis ce fichier AVANT tout autre fichier du repo.

---

## Ce qu'est TricorderKit

TricorderKit est un **système d'exploitation agentique local-first**.

Il transforme les intentions utilisateur en workflows traçables, auditables et réutilisables.

```text
Ancienne définition (v0.6) : memory + skills + token hygiene + observability
Nouvelle définition (v0.7) : CLI-first Agentic OS + Temporal workflows + skill registry + deep research + Obsidian knowledge layer
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
Docker             → infra locale
Temporal           → orchestration workflows persistants
Langfuse           → observabilité tokens + traces
```

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

*Version 0.7 — 10/05/2026*
