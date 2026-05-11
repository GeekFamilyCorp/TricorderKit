# DECISIONS.md — TricorderKit v0.7

> Log des decisions architecturales. Ne jamais supprimer une entree.

### DEC-001 — Temporal comme moteur de workflows
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Temporal pour tous les workflows longs (>30s). Local-first, reprise sur erreur.
- Alternatives rejetees : n8n, Activepieces, scripts cron

### DEC-002 — cli-forge avant obsidian-agent-layer
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Phase 2 CLI-first avant Phase 5 obsidian-agent-layer

### DEC-003 — Neo4j pour le graph
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Neo4j comme base graph
- Alternatives rejetees : Memgraph, ArangoDB

### DEC-004 — Qdrant pour le vector
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Qdrant comme base vectorielle
- Alternatives rejetees : ChromaDB, LanceDB

### DEC-005 — Output schema JSON obligatoire
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Chaque skill expose un output.schema.json valide avant usage prod

### DEC-006 — Rate limiting token par workflow
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Chaque workflow definit un token_budget max

### DEC-007 — Regle atomique : 1 idee = 1 node
- Date : 10/05/2026 | Statut : Acceptee
- Decision : Notes Obsidian atomiques 100-500 tokens

### DEC-008 — LangGraph pour les boucles agentiques
- Date : 11/05/2026 | Statut : Acceptee
- Decision : LangGraph pour workflows agentiques courts (<30s). Temporal pour workflows longs (>30s).
- Raison : Temporal = durabilite/reprise. LangGraph = etat agentique, cycles reflect/act/observe. Synergie native avec Neo4j/Graphify.
- Alternatives rejetees : LangGraph seul (pas de durabilite), CrewAI (moins flexible)
- Impact : plugins/workflow-engine/ + plugins/graphify/ state API

### DEC-009 — Graphify : architecture hybride graph+vector
- Date : 11/05/2026 | Statut : Acceptee
- Decision : Interface hybride Neo4j (traversal) + Qdrant (semantique) via point d'entree unique
- Raison : Neo4j = liens structurels. Qdrant = similarite semantique. Les deux sont non-substituables.
- Impact : core/contracts/graph.schema.json + sync automatique Neo4j vers Qdrant a chaque ecriture

*Derniere mise a jour : 11/05/2026*
