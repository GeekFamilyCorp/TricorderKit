# TricorderKit — Qu'est-ce que c'est ?

> Version 0.8 — 2026-05-18

---

## Définition

TricorderKit est un **Agentic Knowledge Operating System local-first**.

Il permet à un agent Claude (en Claude Code ou Cowork) de :
- comprendre des intentions complexes et les router vers les bons outils
- exécuter des workflows persistants et récupérables (Temporal)
- construire et interroger une mémoire relationnelle (Neo4j + Qdrant)
- produire des outputs structurés et contractuels (JSON + Markdown atomique)
- s'auto-améliorer via une boucle d'observation (Hook Layer + usage_observer)

---

## Problème adressé

Sans TricorderKit, un agent Claude :
- repart de zéro à chaque session (pas de mémoire inter-session)
- improvise ses outputs (pas de contrat, pas de validation)
- ne sait pas quels outils existent déjà (redécouverte constante)
- ne peut pas déléguer à des workflows durables (tout tient dans le contexte LLM)
- ne mesure pas son efficacité (pas d'observabilité)

---

## Les 4 principes fondateurs

### 1. CLI avant LLM

```text
CLI déterministe > appel LLM brut
```

Si une CLI `goat` peut répondre à la question, elle est exécutée.
Le LLM n'est sollicité que pour ce qu'aucune CLI ne peut faire.

### 2. Contrat JSON obligatoire

```text
Tout output de skill = JSON valide contre core/contracts/skill_output.schema.json
```

Pas d'improvisation. Pas de prose non structurée entre agents.

### 3. Mémoire relationnelle atomique

```text
1 idée = 1 node Obsidian = 1 node Neo4j
Taille : 100–500 tokens par note
```

### 4. Workflows persistants et récupérables

```text
Toute tâche > 30s → workflow Temporal
Durabilité native : reprise sur erreur, historique, signal externe
```

---

## Règle d'or

```
TricorderKit exécute. Le projet lié spécialise.
```

TricorderKit est un moteur générique anonymisé (repo public).
Japan-Alliance est le premier linked_project domaine-spécifique (repo privé GeekFamilyCorp).
D'autres linked_projects peuvent être ajoutés sans modifier le moteur.

---

## Architecture en une phrase

```
Intentions → MainBrain v1.5 → Hook Layer → Skills / CLIs / Workflows → Storage → Observabilité
```

---

## Cas d'usage concrets

1. **Recherche manga** : `/tk:deep-research "One Piece chapitre 1120"` → pipeline collect + score + export + index Qdrant
2. **Audit de code** : `/tk:security-scan` → Semgrep + Trivy + Gitleaks en un appel
3. **Synchronisation GitHub** : `python tools/github-goat/github_goat.py list-repos` → JSON structuré depuis cache SQLite
4. **Bilan de session** : `/tk:hook-stats` → tableau Markdown agrégé depuis .cache/hooks/
5. **Linked project** : `tk project status japan-alliance` → statut complet du projet lié

---

*TricorderKit v0.8 — GeekFamilyCorp — 2026-05-18*
