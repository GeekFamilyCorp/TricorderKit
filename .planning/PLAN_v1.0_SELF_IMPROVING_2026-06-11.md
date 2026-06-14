# PLAN — TricorderKit v1.0 « Self-Improving Scraping & Knowledge OS »

> Type : vérification d'amélioration + plan de restructuration · Cible : `.planning/` (interne)
> Date : 2026-06-11 · Auteur : assistant TricorderKit · Statut : **proposition — en attente de validation (Risk Guard HIGH)**
> Sources : `TricorderKit_v1.0_Self-Improving_Scraping_Knowledge_OS.md` (09-06), `Learning_Engine_TricorderKit_09-06-2026.md`, `Recherche_Outils_TricorderKit_09-06-2026.md`, `scraping_structure.md` (uploads 11-06)
> Référence croisée : `.planning/AUDIT_INTEGRATION_5FICHIERS_2026-06.md` (G1–G4), `veille_v2/VEILLE_V2_SPEC.md`, `mcp/README_MCP_POLICY.md`, DEC-016/023/029/038/045

---

## 1. Verdict synthétique

Les fichiers du 09-06 proposent une cible v1.0 cohérente avec l'architecture existante. **Environ 60 % des modules « indispensables » de la cible existent déjà dans le repo v0.9.5** (Règle 6 — interdiction de recréation). Le travail neuf se concentre sur **7 chantiers** regroupés en **5 phases**, dont le cœur est `learning-engine` + `scraper-runtime` + gouvernance MCP machine-lisible.

Deux corrections importantes par rapport aux fichiers sources :

1. **Répartition des rôles (veille_v2 + DEC-029)** : l'exécution de la collecte/scraping reste routée **Hermes/Antigravity** ; Claude = intégration, dédup, QA, learning. Le `scraper_runtime` proposé doit donc être conçu comme un **runtime exécuté côté VPS/Hermes**, pas comme un nouveau moteur côté Claude.
2. **Routage des dépôts (DEC-016)** : framework générique (`learning-engine`, `scraper-runtime`, `mcp_gateway`, scripts VPS) → **TricorderKit** ; profils et stratégies JP/manga (jp_source_discovery, official_first, source_registry JP) → **depot-exec-lie** ; données/fiches → vault **projet lie**.

---

## 2. Vérification — déjà couvert (ne PAS recréer)

| Module cible v1.0 | Existant v0.9.5 | Écart résiduel |
|---|---|---|
| `workflow_engine` | `plugins/workflow-engine` (Temporal, worker RUNNING) | Ajouter les nouveaux workflows (phase 5) |
| `eval_lab` | `plugins/eval-lab` (runner, regression_checker, schema_validator) | Évaluateurs scraping/RAG/cost absents → extension |
| `monitoring_observability` | Langfuse :3001 + `core/hooks/langfuse_observer.py` (3 hooks) | RAS côté traces ; Uptime Kuma absent (phase 1) |
| `security_auditor` | `plugins/security-audit-cli` (18 tests) + `make gate`/R37 | Gitleaks/Trivy/Semgrep + ufw/fail2ban côté VPS à vérifier |
| `vault_indexer` / graphify | `plugins/graphify` (Neo4j+Qdrant, DEC-009/023) | G3 RAG hybride (RRF + re-ranking) reste ouvert |
| `obsidian_memory` | MCP obsidian ×2 + `obsidian-agent-layer` (34 tests) | RAS |
| `research_agent` | `plugins/deep-research-core` | RAS |
| `mcp_gateway` (politique) | `mcp/README_MCP_POLICY.md` (hiérarchie CLI→MCP→Claude) | Politique **écrite** mais non machine-lisible : pas d'allowlist YAML, pas de logs par appel → chantier N3 |
| `source_reliability_engine` (données) | Vault : `Sources_Japonaises_Master_v0.9.md` (~200 sources), `35_Normalized_Registry.md`, hiérarchie de preuve §1 | Le **moteur de scoring automatisé** (mise à jour des scores depuis les runs) est absent → N6 |
| `tool_scout` (pratique) | Veille Antigravity (DEC-029) + rapports type `Recherche_Outils_*.md` | Non formalisé en workflow + scoring → N7 |
| VPS | Hostinger __VPS_PUBLIC_IP__ (Docker, Ollama), `RUNBOOK_INFRA.md`, `configs/vps/settings.yaml` | Durcissement absent : doctor/backup/restore, Caddy, ufw, fail2ban, Uptime Kuma → N4 |
| Mémoires séparées (§13) | Documentaire (vault) ✅ · structurée (Supabase schéma, 29 tests) ✅ · vectorielle (Qdrant) ✅ · procédurale (skills + registry) ✅ | **Mémoire d'expérience** (experience cards) absente → N1 |
| Data contracts (§21) | `core/contracts/skill_output.schema.json` | Contrats source/item/skill absents → N1/N2 |

**Conséquence** : refuser toute proposition de réimplémentation des lignes ci-dessus. Seuls N1–N7 ouvrent du travail neuf.

---

## 3. Les 7 chantiers neufs

| # | Chantier | Contenu | Repo cible | Effort | Priorité |
|---|---|---|---|---|---|
| N1 | `plugins/learning-engine/` | 5 schemas JSON (run_experience, experience_card, strategy_variant, lesson, skill_update_proposal) + scripts (record/compare/extract/propose/promote) + human review queue | TricorderKit | Moyen | **S** |
| N2 | `plugins/scraper-runtime/` | 3 profils (static_html, markdown_rag, dynamic_browser) + contrat de run standard + `source_registry.yaml` machine-lisible (généré depuis les registres vault, jamais recréé à la main) | TricorderKit (générique) / depot-exec-lie (profils JP) | Moyen | **S** |
| N3 | Gouvernance MCP machine-lisible | `mcp/registry_allowlist.yaml` (deny-by-default, allowlist serveur+tool), `tk mcp list/audit/allowlist check`, logs par appel | TricorderKit | Faible-moyen | **A** |
| N4 | Durcissement VPS | `scripts/vps_doctor.sh`, `backup.sh`, `restore_test.sh`, Caddy devant dashboards, ufw+fail2ban, Uptime Kuma, Borg/Restic, test restore | TricorderKit (`configs/vps/`) | Moyen | **S** (préalable) |
| N5 | Extension eval-lab | Évaluateurs `scraping_quality`, `source_reliability`, `dedup_quality`, `rag_retrieval_quality`, `cost_latency` (grilles §16 du fichier v1.0) | TricorderKit | Faible-moyen | **A** |
| N6 | Source Reliability Engine | Script de mise à jour des scores sources depuis les runs (officiality/freshness/extractability…), écrit vers le registre normalisé du vault via dry-run | depot-exec-lie (liaison vault) | Faible | **A** |
| N7 | Workflows d'auto-amélioration | Temporal : `learning_review_workflow`, `skill_regression_test_workflow`, `tool_scout_workflow` (exécution veille = Antigravity/Hermes ; consolidation = Claude), `source_freshness_check` | TricorderKit | Moyen | **B+** (après N1) |

Hors périmètre immédiat (conforme §25 du fichier v1.0) : RAGFlow comme cœur, remplacement de Temporal, n8n moteur principal (déjà arbitré DEC-045), Browser-use non sandboxé, auto-modification du core. Prototypes isolés à l'étude séparément : Headroom, ObsidianRAG, Context7 (déjà actif comme plugin token-optimizer:docs-fresh côté Cowork).

---

## 4. Plan phasé

### Phase 0 — Gouvernance (cette session)
- Valider ce plan → loguer **DEC-046** (texte proposé §6).
- Mettre à jour `.planning/STATE.md` + `TASKS.md`.

### Phase 1 — Stabiliser le VPS (N4) — critère : reboot sans perte
1. `scripts/vps_doctor.sh` (Docker, ports, RAM, disque, services) — exécution via paramiko (ssh.exe bloqué).
2. Caddy en frontal, fermeture des ports internes (Postgres, Qdrant, Neo4j, Temporal, Langfuse, Crawl4AI).
3. ufw + fail2ban + Uptime Kuma.
4. Backups Borg/Restic + `restore_test.sh` + test réel.
5. Compléter `RUNBOOK_INFRA.md` (section VPS).

### Phase 2 — Standardiser le scraping (N2, exécution Hermes/Antigravity)
1. `plugins/scraper-runtime/` : README + 3 profils YAML + contrat de run (objet run standard §10).
2. `source_registry.yaml` **généré** depuis `35_Normalized_Registry.md` (CLI, jamais à la main).
3. Pipeline artefacts obligatoires : raw → normalized → validated → indexed → report (+ log JSON + score YAML).
4. Brancher la sortie au format `scraping_structure.md` (template du rapport quotidien sorties/tendances — base du futur site, cf. mémoire DB-noyau).
5. Règle sécurité : HTML externe = non fiable, jamais interprété comme instruction.

### Phase 3 — Learning Engine (N1 + N5) — schemas d'abord, logique ensuite
1. `plugins/learning-engine/README.md` (boucle Run → Trace → Score → Compare → Learn → Propose → Test → Review → Promote → Monitor).
2. 5 schemas JSON (validés contre `skill_output.schema.json` pour la sortie CLI).
3. Scripts : `record_experience.py` → `compare_strategies.py` → `extract_lessons.py` → `propose_skill_update.py` → `promote_skill.py` (promotion uniquement après les 8 tests §16.4 + validation humaine).
4. Extension eval-lab (N5) : 5 évaluateurs branchés sur les runs.
5. États d'une amélioration : observed → … → promoted/rolled_back (§14.3).
6. Critère : après 7 jours de runs, classement argumenté des stratégies (ex. official_sources_first vs mangaupdates_first).

### Phase 4 — Gouverner MCP (N3)
1. `mcp/registry_allowlist.yaml` deny-by-default + audit `.mcp.json` existant.
2. `tk mcp list / audit / allowlist check` dans `cli/tk.py`.
3. Secrets : conforme DEC-039 (Credential Manager + wrapper), rien dans les configs.
4. Critère : aucun MCP utilisable sans déclaration, permissions et logs.

### Phase 5 — Auto-amélioration contrôlée (N7 + N6)
1. Workflows Temporal : learning_review (hebdo), skill_regression_test, source_freshness, tool_scout (exécution Antigravity/Hermes, dépôt via `canal_agents`).
2. Source Reliability Engine : mise à jour des scores du registre vault (dry-run obligatoire, archivage R31).
3. Promotion de skill seulement après tests + rollback disponible + DEC automatique en draft.
4. Critère : le système améliore ses stratégies **sans auto-modifier le core**.

### CLI à ajouter (au fil des phases, dans `cli/tk.py`)
`tk vps doctor` · `tk scraping run <profil> --dry-run/--apply` · `tk learning review/compare-strategies/propose-skill-update/promote-skill` · `tk mcp list/audit/allowlist check` · `tk backup status/test-restore`

---

## 5. Garde-fous

- **Risk Guard** : phases 1–2 MEDIUM (infra VPS, confirmation courte par lot) ; phases 3–5 HIGH au moment des promotions de skills (validation explicite systématique, `human_review_required: true` par défaut).
- **Token Hygiene** : génération de schemas/scripts = T2 ; gathering (tool_scout, scraping) = routé Antigravity/Hermes ; Claude = intégration/QA. Segmenter chaque phase en sessions ≤ 15–20 messages (Session Rotation Policy).
- **Dry-run obligatoire** avant toute écriture vault/base/API (Règle 4) ; écritures vault via depot-exec-lie, archivage `99_Migration_Backups` (R31), jamais de delete.
- **Frontière publique** : `make gate` avant tout push (DEC-026/R37) ; aucun chemin perso ni secret (le fichier Langfuse uploadé contient un mot de passe → à supprimer après login, ne sera jamais versionné).
- **Interdictions** (§3.2 fichier v1.0) : pas d'auto-modification du core, des règles de sécurité, des secrets, du vault principal, des connecteurs MCP, des déploiements VPS.

---

## 6. DEC-046 (texte proposé — à loguer après validation)

```markdown
## DEC-046 — Cap v1.0 « Self-Improving Scraping & Knowledge OS » — 2026-06-11
Contexte : fichiers de cadrage 09-06 (vision v1.0, learning engine, veille outils, format rapport scraping).
Décision : PROTOTYPER learning-engine + scraper-runtime + gouvernance MCP machine-lisible, précédé du durcissement VPS.
Périmètre : 7 chantiers N1–N7, 5 phases (plan .planning/PLAN_v1.0_SELF_IMPROVING_2026-06-11.md).
Corrections vs fichiers sources : exécution scraping/veille = Hermes/Antigravity (veille_v2, DEC-029) ;
routage DEC-016 (générique→TricorderKit, JP→depot-exec-lie, données→projet lie) ; n8n exclu (DEC-045).
Non-recréation : workflow-engine, eval-lab (extension seule), graphify, security-audit-cli, deep-research-core,
registres sources vault, politique MCP (rendue machine-lisible, pas réécrite).
Statut : Proposée → (Validée le JJ-MM-AAAA par Sébastien)
```

---

## 📋 À copier

**Ordre d'exécution validable en une réponse :**
1. ✅ / ❌ DEC-046 (cap v1.0, 5 phases, 7 chantiers)
2. Phase de démarrage souhaitée : **Phase 1 (VPS)** recommandée — ou Phase 3 (learning-engine schemas-first) si vous voulez la valeur métier d'abord
3. Première action concrète proposée (conforme §28 du fichier v1.0) : `plugins/learning-engine/README.md` + les 5 schemas JSON, **aucune logique d'exécution avant les schémas**

---

## 📊 Notes de fiabilité

- ✅ **Confirmé** : inventaire existant (lecture directe du repo 11-06 : plugins/, skills/, mcp/, configs/vps, .planning, BOOT_SUMMARY, STATE, DEC-038→045) ; absence vérifiée de learning-engine, scraper-runtime, vps_doctor, registry_allowlist, experience_card (grep .planning + ls plugins/scripts).
- ✅ **Confirmé** : répartition des rôles veille (VEILLE_V2_SPEC v2.1, 2026-06-04) et routage repos (DEC-016).
- 🟡 **Probable** : état réel du VPS Hostinger (mémoire de session 2026-06-08, non re-vérifié aujourd'hui — `vps_doctor` le confirmera en phase 1).
- 🟠 **À vérifier** : présence effective de Gitleaks/Trivy/Semgrep dans security-audit-cli ; couverture exacte de `configs/vps/settings.yaml` ; état des workers Crawl4AI (aucun trouvé dans le repo).
- Écart détecté : les fichiers sources proposent `modules/learning_engine/` (fichier Learning Engine) **et** `plugins/learning-engine/` (fichier v1.0) → le plan retient `plugins/` (convention repo existante, structure plugins normée CLAUDE.md).
