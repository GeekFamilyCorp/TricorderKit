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

### DEC-010 — Pattern linked_project : séparation moteur / domaine
- Date : 17/05/2026 | Statut : Acceptée
- Décision : TricorderKit est un moteur générique anonymisé. Tout ce qui est domaine-spécifique (sources, scrapers, vocabulaire métier, vault privé) vit dans un linked_project privé séparé.
- Règle d'or : **TricorderKit exécute. Le projet lié spécialise.**
- Raison : (1) TricorderKit doit pouvoir être partagé publiquement sans fuites de données privées. (2) Séparer les cycles de vie — le moteur évolue indépendamment du contenu. (3) Permettre plusieurs linked_projects (Japan-Alliance, futurs projets) sur le même moteur.
- Implémentation :
  - `configs/local/linked_projects.yaml` (non versionné) — chemins réels locaux
  - `configs/local/linked_projects.example.yaml` (versionné) — template documentation
  - `docs/linked_projects.md` — convention officielle
  - `templates/linked_project_template/` — template reproductible
  - `tools/audit/linked_project_audit.py` — audit structure + git + config + secrets
  - `tools/audit/local_vs_github_audit.py` — sync local vs GitHub
  - CLI `tk project *` — commandes dédiées linked_project
- Linked projects actifs : **Japan-Alliance** (GeekFamilyCorp/Japan-Alliance — privé) + **MangaTracker** (GeekFamilyCorp/MangaTracker — privé)
- Isolation garantie par :
  - `.gitignore` TricorderKit exclut tous les fichiers locaux non génériques
  - `private_terms` dans `project_config/project.yaml` du linked_project
  - Scan secrets avant push via `linked_project_audit.py`
- Alternatives rejetées : monorepo (couplage fort, risque de fuite), sous-modules Git (complexité, friction workflow)
- Impact : Phase 6 complète — commits `5acec97` (TK) + `d8f8696` (JA)

### DEC-011 — VPS : extension optionnelle future (pas encore déployé)
- Date : 17/05/2026 | Statut : Acceptée — En préparation
- Décision : TricorderKit reste local-first. Un VPS pourra être ajouté comme extension optionnelle pour la persistance longue durée, le scheduling headless et le partage de rapports.
- Principe : le VPS ne remplace pas le local, il complète. La machine locale reste le point de vérité.
- État : `configs/vps/settings.yaml` créé comme template (status: PENDING — non déployé).
- Prochaines étapes VPS : choisir provider → configurer Docker Compose → configurer reverse proxy (Caddy) → sync sélectif reports/ uniquement.
- Alternatives rejetées : Cloud-only (dépendance, coût, latence) — aucune migration forcée.

### DEC-012 — Japan-Alliance = vault pur, MangaTracker = assistant CLI
- Date : 17/05/2026 | Statut : Acceptée
- Décision : Refonte complète de l’architecture linked_projects. Japan-Alliance devient un **vault Obsidian pur** (données uniquement, aucun code exécutable). MangaTracker devient l’**assistant IA dédié** qui absorbe l’intégralité du code, des CLIs, des skills et des pipelines.
- Raison :
  (1) Séparation nette données / logique : Japan-Alliance ne dépend plus d’aucun runtime.
  (2) Japan-Alliance doit être accessible en lecture à plusieurs LLMs (Claude, ChatGPT, Perplexity, Qwen) via API GitHub — un vault pur est plus simple à partager et documenter.
  (3) MangaTracker concentre la complexité opérationnelle et évolue indépendamment du vault.
  (4) Japan-Alliance a vocation à devenir un site web — une structure vault-only est directement exploitable pour la génération statique.
- Migration effectuée (2026-05-17) :
  - Tout le code Python, skills, pipelines, plugins migré vers MangaTracker
  - Japan-Alliance nettoyé : conserve uniquement `vault/`, `templates/`, `README.md`, `CONTEXT.md`
  - `CONTEXT.md` créé dans Japan-Alliance : guide de navigation pour Claude, ChatGPT, Perplexity, Qwen
  - `linked_projects.example.yaml` mis à jour : MangaTracker (type: ai_assistant) + Japan-Alliance (type: obsidian_vault, read_only: true)
- Règle d'or mise à jour : **TricorderKit exécute. MangaTracker spécialise. Japan-Alliance stocke.**
- Impact : STATE.md Phase 6.5 — commits Japan-Alliance (`84dd260`) + TricorderKit (ce commit)

*Dernière mise à jour : 17/05/2026*
