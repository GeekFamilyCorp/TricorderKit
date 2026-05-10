# DECISIONS.md — TricorderKit v0.7

> Log des décisions architecturales. Ne jamais supprimer une entrée — amender si changement.

---

## Format

```markdown
### DEC-XXX — Titre
- **Date** : JJ/MM/AAAA
- **Statut** : Acceptée | Révoquée | En discussion
- **Décision** : ...
- **Raison** : ...
- **Alternatives rejetées** : ...
- **Impact** : ...
```

---

### DEC-001 — Temporal comme moteur de workflows
- **Date** : 10/05/2026
- **Statut** : Acceptée
- **Décision** : Utiliser Temporal (temporalio/sdk-typescript) pour tous les workflows longs
- **Raison** : Local-first, code as config, reprise native sur erreur, pas de dépendance cloud
- **Alternatives rejetées** : n8n (trop visuel, moins adapté code-first), Activepieces (moins mature), scripts cron (pas de reprise sur erreur)
- **Impact** : Tous les workflows > 30s ou répétables doivent passer par Temporal

---

### DEC-002 — cli-forge avant obsidian-agent-layer
- **Date** : 10/05/2026
- **Statut** : Acceptée
- **Décision** : Implémenter cli-forge (Phase 2) avant obsidian-agent-layer (Phase 5)
- **Raison** : Réduire le bruit agentique est prioritaire. Une CLI bien conçue économise plus de tokens qu'une couche Obsidian enrichie
- **Alternatives rejetées** : Démarrer par obsidian-agent-layer (vision séduisante mais moins d'impact immédiat)
- **Impact** : Obsidian-agent-layer reporté en Phase 5

---

### DEC-003 — Neo4j pour le graph (pas Memgraph)
- **Date** : 10/05/2026
- **Statut** : Acceptée
- **Décision** : Utiliser Neo4j comme base graph
- **Raison** : Maturité (15+ ans), MCP existant, support GraphQL natif, documentation abondante
- **Alternatives rejetées** : Memgraph (plus performant mais moins mature, moins de docs), ArangoDB (multi-modèle mais complexité inutile)
- **Impact** : MCP Neo4j à créer dans `mcp/servers/graph-server/`

---

### DEC-004 — Qdrant pour le vector (pas ChromaDB)
- **Date** : 10/05/2026
- **Statut** : Acceptée
- **Décision** : Utiliser Qdrant comme base vectorielle
- **Raison** : Performances supérieures, filtrage metadata avancé, API REST propre, Rust (stable)
- **Alternatives rejetées** : ChromaDB (plus simple mais moins performant à grande échelle), LanceDB (trop récent)
- **Impact** : MCP Qdrant à créer dans `mcp/servers/vector-server/`

---

### DEC-005 — Output schema JSON obligatoire pour tout skill
- **Date** : 10/05/2026
- **Statut** : Acceptée
- **Décision** : Chaque skill expose un `output.schema.json` vérifié automatiquement avant usage prod
- **Raison** : Prévenir les cascades d'erreurs silencieuses entre skills. Un skill dont l'output change sans préavis peut casser tous les skills aval
- **Alternatives rejetées** : Tests manuels uniquement (trop fragile)
- **Impact** : Ajouter `core/contracts/skill_output.schema.json` et validation dans eval-lab

---

### DEC-006 — Rate limiting token par workflow
- **Date** : 10/05/2026
- **Statut** : Acceptée
- **Décision** : Chaque workflow Temporal définit un `token_budget` max et un comportement `on_budget_exceeded`
- **Raison** : Prévenir les boucles infinies coûteuses. Un workflow de veille manga mal configuré peut consommer des milliers de tokens inutilement
- **Alternatives rejetées** : Monitoring post-facto uniquement (trop tard, le coût est déjà engagé)
- **Impact** : Ajouter `token_budget` dans le manifest de chaque workflow

---

### DEC-007 — Règle atomique : 1 idée = 1 node (100–500 tokens)
- **Date** : 10/05/2026
- **Statut** : Acceptée (héritée v0.6)
- **Décision** : Toute note Obsidian doit contenir une seule idée atomique
- **Raison** : Optimise le retrieval RAG, évite les chunks trop larges ou trop étroits
- **Impact** : Template `30_ATOMIC/` dans Claude Vault

---

*Dernière mise à jour : 10/05/2026*
