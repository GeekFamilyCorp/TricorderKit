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

### DEC-010 - Standard Typer pour les nouvelles CLIs cli-forge
- Date : 13/05/2026 | Statut : Acceptee
- Decision : Toute nouvelle CLI cli-forge utilise Typer >= 0.12 et respecte
  le schema core/contracts/skill_output.schema.json (DEC-005). Les CLIs
  argparse existantes (github-goat, source-watch-goat) sont taggees
  `framework: argparse_legacy` dans registry.yml et migrent via PRs
  dediees. La conversion automatique argparse -> Typer est interdite.
- Raison : DEC-005 imposait deja un output schema obligatoire mais sans
  standard d'implementation. Phase 2 v0.7 marquee "terminee" sans
  templates Typer ni tests CliRunner. Consolidation necessaire.
- Impact : ajout `docs/cli_forge_typer_standard.md`,
  `plugins/cli-forge/templates/`, `plugins/cli-forge/SKILL.md`,
  `plugins/cli-forge/manifest.yml`. CLI Typer de reference :
  `tools/tk_installer/`.
- Alternatives rejetees : click direct (moins ergonomique), Fire (moins
  type), argparse pour les nouvelles CLIs (sortie JSON moins propre).

### DEC-011 - tools/tk_installer/ en snake_case (ecart spec)
- Date : 13/05/2026 | Statut : Acceptee
- Decision : Adopter `tools/tk_installer/` (snake_case) pour le package
  Python. Ecart documente vis-a-vis de TK_INSTALLER_SPEC_v0.1 sec 1 qui
  indiquait `tools/tk-installer/` (kebab-case). La commande shell publique
  reste `tk-installer` (kebab-case), exposable via `entry_point` dans
  `pyproject.toml`.
- Raison : Python interdit l'import d'un package contenant un tiret. Le
  kebab-case casse `from tools.tk-installer.tk_installer import app` et
  bloque les tests CliRunner ainsi que l'inscription dans
  `pyproject.toml [project.scripts]`.
- Impact : tests/cli_contracts/test_tk_installer.py + conftest.py qui
  injecte la racine repo dans sys.path. A repercuter dans une future
  TK_INSTALLER_SPEC_v0.2 (kebab-case = commande shell, snake_case =
  package Python).

### DEC-012 - Premiere CLI Typer = tk-installer minimal
- Date : 13/05/2026 | Statut : Acceptee
- Decision : Demarrer tk-installer v0.1 avec uniquement les commandes
  `status` et `diagnose`. Les commandes `plan`, `install`, `verify`,
  `repair` sont reportees a v0.2 post-Phase 2.5.
- Raison : Resout deux problemes en un seul livrable - valider le standard
  Typer (DEC-010) ET poser la fondation d'un outil deja specifie
  (TK_INSTALLER_SPEC). Alternatives rejetees : migration immediate de
  github-goat (introduit du risque de regression sur une CLI deja
  validee en dry-run), CLI jetable type tk-doctor (n'apporte rien).
- Impact : tools/tk_installer/tk_installer.py + 27 tests CliRunner.
  Inscription provisoire au registry avec `manifest: null` (l'extension
  du cli_manifest.schema.json pour categorie internal-tool fera l'objet
  d'une PR ulterieure).

*Derniere mise a jour : 13/05/2026*