# STATE.md — TricorderKit v0.9

> État courant du projet. Mettre à jour à chaque session.
> Dernière mise à jour : 2026-06-11

> **Session 2026-06-11** : vérification d'amélioration v1.0 + plan de restructuration.
> Analyse des 4 fichiers de cadrage du 09-06 (vision v1.0 Self-Improving Scraping & Knowledge OS,
> Learning Engine, veille outils, format rapport scraping) → **~60 % des modules cibles déjà couverts**
> (Règle 6 vérifiée : workflow-engine, eval-lab, graphify, security-audit-cli, obsidian-agent-layer,
> deep-research-core, politique MCP, registres sources vault). 7 chantiers neufs N1–N7 identifiés
> (learning-engine, scraper-runtime, allowlist MCP machine-lisible, durcissement VPS, extension eval-lab,
> source reliability engine, workflows d'auto-amélioration).
> Livrables : `.planning/PLAN_v1.0_SELF_IMPROVING_2026-06-11.md` (5 phases) ;
> **DEC-046 VALIDÉE (Sébastien, 2026-06-11)** → démarrage **Phase 3** :
> `plugins/learning-engine/` créé (README + manifest + **5 schemas JSON**, parse OK, schemas-first §28,
> aucune logique d'exécution). Prochaine étape : scripts record/compare/extract/propose/promote + tests,
> puis Phase 1 (durcissement VPS).

> **Session 2026-06-03** : audit déterministe du vault (1 313 fiches manga/LN, `audit_v2.ps1`) →
> **DEC-036** : dérive de schéma frontmatter (clés FR vs EN) tranchée → **canon = clés EN**
> (`author_jp`/`title_jp`/`artist_jp`/`publisher_jp`, validation `confidence_label`).
> Chiffres fiables : 226 validées, 692 avec auteur, **610 coquilles vides**, **319 fiches créateurs manquantes**.
> Migration EN = **chantier gardé** (CLI dry-run + archivage, exécution via MangaTracker) — **non encore exécutée**.
> Mission de nettoyage déposée pour Antigravity (`_sync_antigravity/commands/antigravity_inbox/`).
> Outils livrés (dossier projet) : `audit_v2.ps1`, `audit_fiches_raw.csv`, `createurs_manquants.csv`.

> **Session 2026-06-01** : optimisation des tâches planifiées Japan-Alliance (DEC-020) —
> fusion du doublon d'enrichissement SO (un seul chargement de contexte vault/jour),
> volume 10+10 → 12 fiches/nuit, recadrage horaires anti-chevauchement (fenêtre creuse 02h–07h),
> correction dépendance (bilan 02h lit le rapport de la veille). Voir section « Tâches planifiées ».

> **Session 2026-05-29 (E4)** : contrôle vault Japan-Alliance + liens modules.
> Connexion vivante OK (5421 notes, rapports TK du jour écrits). DEC-014 : fix routing
> `vault_router.py` (obsidian-notes-vault → obsidian-japan-alliance) — appliqué local, push
> différé (commit groupé). `linked_projects.yaml` corrigé : `vault` → `obsidian/Japan-Alliance/`,
> `allow_tricorderkit_write` → false. Nom de vault = **Japan-Alliance** (sans suffixe `_vault` ;
> `japan-alliance_vault/` était une erreur de nommage ChatGPT, dossier vide à supprimer).

---

## Version courante

- **Version** : 0.9.5 — Public-ready
- **Date** : 2026-06-01
- **Phase active** : v0.9.5 poussé (graphify RAG local-first DEC-023 + dédup G1) — prochaine étape : verrouiller frontière privé/public (Lot 2) + tag release v0.9.5

---

## Statut des phases

| Phase | Nom | Statut | Vérifié |
|---|---|---|---|
| 0 | Bootstrap | ✅ Verified | 2026-05-13 |
| 1 | Fondations (fichiers fondateurs) | ✅ Verified | 2026-05-10 |
| 2 | CLI-Forge | ✅ Verified | 2026-05-13 |
| 2.5 | QualityGuard | ✅ Verified | 2026-05-15 |
| 3 | Workflows persistants (Temporal) | ✅ Verified | 2026-05-15 |
| 3.5 | Hook Layer v0.2 | ✅ Complet | 2026-05-16 |
| 4 | Deep Research — B3 tests live 24/24 PASS | ✅ Complet | 2026-05-22 |
| 5 | Quality Loop | ✅ Complet | 2026-05-16 |
| 6 | Séparation linked_project | ✅ Complet | 2026-05-17 |
| 6.5 | Restructuration → vault pur | ✅ Complet | 2026-05-17 |
| **v0.9 M1** | Foundation v0.9 — memory-boot + token-optimizer + skills rtk + docmancer | ✅ Complet | 2026-05-18 |
| **v0.9 M2** | Orchestration — connector_hub + budget_guard + Supabase | ✅ Complet | 2026-05-22 |
| **v0.9 M3** | Pipeline rtk→docmancer live + observabilité Langfuse | ✅ Complet | 2026-05-22 |
| **v0.9 M4** | CLI tk doctor + rapport + INSTALL.md + security | ✅ Complet | 2026-05-22 |
| **v0.9 M5** | security-audit-cli 18/18 tests · sanitize_input.activity.ts (RISK-005) · index_qdrant uuid.uuid5 (ERR-T-001) · Full Audit 5/5 PASS · Windows deployment | ✅ Complet | 2026-05-23 |
| **v0.9 M6** | Public-ready docs — README · ROADMAP · STATUS · Makefile · install-menu · anonymization | ✅ Complet | 2026-05-23 |

---

## Tests

```
Total     : 503 PASS — 0 FAIL — 15 skipped (live)  (+6 tests graphify locaux à intégrer)
Commit HEAD : 124baba (01/06/2026 — graphify RAG local-first + dédup G1)
```

---

## Statut des plugins

| Plugin | Statut | Version |
|---|---|---|
| cli-forge | ✅ Actif | — |
| workflow-engine | ✅ Actif — worker RUNNING | — |
| deep-research-core | ✅ Actif — tests live PASS | — |
| hook-layer | ✅ Actif v0.2.0 | v0.2.0 |
| memory-boot | ✅ Migré v0.8 | v0.8 |
| token-optimizer | ✅ Migré v0.8 | v0.8 |
| connector-hub | ✅ Actif | v0.1.0 |
| eval-lab | ✅ Actif | — |
| obsidian-agent-layer | ✅ Actif (34 tests) | — |
| security-audit-cli | ✅ Actif (16 tests) | — |
| graphify | 🧪 WIP | — |

---

## Infrastructure

| Service | Statut |
|---|---|
| Neo4j | ✅ Actif :7474/7687 |
| Qdrant | ✅ Actif :6333 |
| Langfuse | ✅ Actif :3001 |
| Temporal | ✅ RUNNING — worker `tricorderkit-hooks` |

---

## Architecture linked_projects

```text
TricorderKit    = moteur générique anonymisé (public)
MangaTracker    = linked_project — CLIs, pipelines, skills, agents (privé)
Japan-Alliance  = vault Obsidian pur — données uniquement (privé)
```

Règle d'or : **TricorderKit exécute. Le projet lié spécialise. Le vault stocke.**

---

## Tâches planifiées (Japan-Alliance) — DEC-020, 2026-06-01

Fuseau : Europe/Paris. Prompts dans `<scheduled-path>/` (hors repo versionné).

| Heure | Tâche | Cron | Rôle |
|---|---|---|---|
| 02h00 quotidien | `analyse-japan-alliance` | `0 2 * * *` | Bilan veille + Master Index + **enrichissement SO consolidé (12 fiches)** |
| 04h00 dimanche | `weekly-ecosystem-audit` | `0 4 * * 0` | Grand Audit écosystème (skills/plugins/MCPs) + 90_Templates |
| 05h00 quotidien | `japan-alliance-an-tracker` | `0 5 * * *` | Tracker complétion fiches Anime (AN) |
| 07h00 quotidien | `japan-alliance-tricorderkit-7h30` | `0 7 * * *` | Rapport matinal **allégé** (reporting run nuit, lecture seule) |
| 12h00 quotidien | `rollout-studios-japan-alliance` | `0 12 * * *` | Création 10 fiches studios ST### depuis la file |

Règles : enrichissement SO en **un seul passage nuit** (12 fiches) ; bilan 02h lit `RAPPORT_[DATE_HIER].md` ; écarts ≥ 1h, jitter ~8 min → aucun chevauchement.

---

## Blockers actifs

Aucun.

---

## Pre-push checklist (avant git push public)

```
[ ] tk security check-anon → [OK]
[ ] git grep "Users\<username>" → 0 résultats (hors configs/local/)
[ ] git grep "<nom-projet-lié>" → 0 résultats hors docs/ et .planning/
[ ] .env absent du diff
[ ] vault/*.json absent du diff (gitignored)
[ ] configs/local/ absent du diff (gitignored)
[ ] CHANGELOG.md entrée [0.9.0] ajoutée
[ ] make test → 0 FAIL
```

---

## Prochaines actions recommandées

```text
1. [COMMIT]   git add -A && git commit -m "feat: v0.9 public-ready — docs + anonymization + install"
2. [TEST]     make test → vérifier 0 FAIL
3. [SECURITY] tk security check-anon → [OK]
4. [PUSH]     git push origin main
5. [NEXT]     v0.9 M7 optionnel : VPS deployment (DEC-011 — local-first maintenu)
```

---

*Dernière mise à jour : 2026-06-03 — DEC-036 unification schéma frontmatter (canon clés EN `author_jp`/`title_jp`) ; audit déterministe vault + mission Antigravity déposée*

---

## Canal multi-agents (2026-06-07 — DEC-038)

`canal_agents/` EN LIGNE (remplace _sync_antigravity). Bus tri-agent claude/antigravity/codex, CLI `canal_agents/scripts/sync_bus.py`, zero token LLM. Handoff `T-2026-06-06-DEDUP-ORICON` poste dans inbox/codex. Regles R39 (bus unique) + R40 (zone de tri `97_A_Trier\05_A_Integrer\Fiches a trier - en attente`) actives dans AGENTS.md.
A faire : Antigravity bascule sur canal_agents ; `health --write-status` en scheduled task ; Codex execute la lane dedup-oricon.

---

## Phase 3 — Learning Engine — Lot A LIVRE (2026-06-11 — DEC-046)

`plugins/learning-engine/scripts/` : 5 scripts livres + valides.

- `record_experience.py` — run (run_experience) -> experience card validee (collision d'ID corrigee : date+task+strategie+suffixe run_id).
- `compare_strategies.py` — cartes -> classement strategy_variant + rapport MD (degrade en `partial` si < 2 variantes).
- `extract_lessons.py` — cartes -> lecons (status `observed`, `human_review_required:true`, seuil de confiance parametrable).
- `propose_skill_update.py` — lecons acceptees -> draft de proposition (jamais le skill actif ; 8 tests initialises `pending`).
- `promote_skill.py` — gate des 8 tests + validation humaine + rollback/backup ; **dry-run par defaut**, refus explicite sinon.
- `_common.py` — contrat skill_output, validation jsonschema Draft 2020-12, UTF-8 (utf-8-sig tolere le BOM Windows).

Tests : `plugins/learning-engine/tests/` — **20/20 PASS** (Windows + sandbox). E2E complet OK (record->compare->lessons->propose->gate refuse). `make gate` / `check_public_boundary.py` = OK (aucune fuite). CLI cable : `tk learning record|compare-strategies|review|propose-skill-update|promote-skill` (argparse REMAINDER, parse OK).

Conventions : CLI **argparse** (pas typer) — zero dep pip hors `jsonschema`, sur sous Windows (cf. feedback_typer_windows_cli) et coherent avec `cli/tk.py`.

A faire (hors Lot A) : commit cible TricorderKit (`plugins/learning-engine/`, `cli/tk.py`, `.planning/STATE.md`) via DC, git add cible (jamais -A) ; puis Lots B-E (VPS, scraper-runtime, gouvernance MCP, workflows) ; brancher les 8 tests reels sur eval-lab (N5).

*Derniere mise a jour : 2026-06-11 — Lot A learning-engine livre (DEC-046, Phase 3).*

---

## Phase 1 — Durcissement VPS — Lot B SCRIPTS LIVRES (2026-06-11 — DEC-046, N4)

`scripts/vps/` : 3 scripts shell + README, ecrits et **valides en syntaxe** (`bash -n` x3 OK ; smoke `vps_doctor.sh` = rapport + JSON propres). **Non executes sur le VPS** (frontiere d'execution live = feu vert requis).

- `vps_doctor.sh` — diagnostic lecture seule (Docker, ports loopback, RAM/disque, Tailscale, ufw, fail2ban) ; sortie texte + JSON ; exit 1 si check critique.
- `backup.sh` — Borg chiffre (zstd), init idempotent, retention/prune ; **dry-run par defaut** (Regle 4) ; secrets via env (DEC-039), zero IP/secret en dur.
- `restore_test.sh` — extraction vers repertoire jetable + temoins + `borg check` ; ne touche jamais le live (critere « reboot sans perte »).
- `README.md` — exploitation paramiko/Tailscale, prealables (debannissement fail2ban du 11/06, ne durcir que le manquant — durcissement 09/06 deja fait), Uptime Kuma a deployer.

**Prealables avant run live (Risk Guard MEDIUM/HIGH — feu vert Sebastien)** : (1) verifier debannissement fail2ban du poste ; (2) une seule session SSH reutilisee (paramiko/Tailscale) ; (3) installer borgbackup + Uptime Kuma cote VPS ; (4) passphrase Borg via coffre. `vps_doctor.sh` confirme l'etat reel avant de durcir quoi que ce soit.

A faire (suite) : exécuter `vps_doctor.sh` sur le VPS (diagnostic), puis backup réel + restore_test ; Uptime Kuma ; Lots C-E.

*Derniere mise a jour : 2026-06-11 — Lot B scripts VPS livres (non executes), en attente feu vert run live.*

---

## Phase 1 VPS — Lot B EXECUTE EN LIVE + Phase 2 — Lot C LIVRE (2026-06-11 soir — DEC-046)

**Lot B live (VPS japan-alliance-vps via paramiko tailnet <VPS_TAILNET_IP>)** :
- ⚠️ **Cause racine des « auth timeout » trouvee** : Tailscale SSH etait en `action: check` (ré-auth navigateur) → **corrige en `accept`** (Sébastien). Debloque aussi la tache horaire `vps-scraping-engine-build` qui echouait ~23x.
- `vps_doctor.sh` execute : FAIL=0, VPS sain (Docker 6 conteneurs, 13,8 Go RAM, disque 29%, Ollama+ufw OK).
- **fail2ban + borgbackup installes** ; jail sshd active avec `ignoreip <TAILNET_CIDR>/10` (anti-lockout tailnet).
- `backup.sh` (dry-run + reel) + `restore_test.sh` **valides en prod** : archive `agents-hub-*` creee, restauration verifiee (`borg check` OK). Passphrase generee, stockee `/root/.borg-passphrase` (600) + Google Drive utilisateur (jamais en memoire agent).

**Lot C — scraper-runtime (N2)** : `plugins/scraper-runtime/` livre.
- 3 profils YAML : `static_html`, `markdown_rag`, `dynamic_browser` (+ quand l'utiliser, fetch/extraction/garde-fous).
- Contrat de run `schemas/run_contract.schema.json` (pipeline raw→normalized→validated→indexed→report + metrics + reliability ; `project_scope` string libre, executor deporte).
- `scripts/gen_source_registry.py` : genere `source_registry.yaml` depuis un registre normalise (lecture seule), zero dep pip, **4 tests PASS**. Aucun nom de projet en dur.
- Garde-fous : contenu scrape non fiable, execution deportee VPS/Hermes (DEC-029), registre genere jamais ecrit a la main.

Vitrine MAJ : **12 plugins** (README arbre/compte + STATUS dashboard/resume). Gates publics OK.

A faire : Lots D (gouvernance MCP machine-lisible, N3) + E (workflows Temporal auto-amelioration, N7/N6) ; brancher les profils scraper-runtime au pipeline VPS existant ; eval-lab N5.

*Derniere mise a jour : 2026-06-11 soir — Lot B live (VPS durci + backup prouve) + Lot C scraper-runtime livre (DEC-046).*


---

## Phase 4 — Gouvernance MCP (Lot D, N3) + Phase 5 — Reliability + Workflows (Lot E, N6/N7) LIVRES (2026-06-11 soir — DEC-046)

**Lot D — gouvernance MCP machine-lisible (N3)** : `mcp/` (pas un plugin → vitrine reste 12).
- `mcp/registry_allowlist.yaml` — **deny-by-default** : serveurs (vault-search, graph-server) + tools + permissions + rate limits + patterns de tools bannis ; secrets en references `${VAR}` uniquement (DEC-039).
- `mcp/scripts/mcp_gateway.py` — `list` / `audit` (`.mcp.json` vs allowlist : serveurs non declares, secrets en clair, tools bannis) / `allowlist-check` ; journal par appel `mcp/logs/mcp_calls.jsonl` (gitignore) ; sortie `skill_output`.
- `cli/tk.py` : `tk mcp list | audit | allowlist-check`. **13 tests PASS** (`tests/test_mcp_gateway.py`).
- Audit du `.mcp.json` reel = **OK** (2 serveurs declares, aucun secret en clair).

**Lot E — source reliability engine (N6) + workflows auto-amelioration (N7)** :
- `plugins/scraper-runtime/scripts/source_reliability_engine.py` — score composite des sources (officialite/fiabilite/fraicheur/extractabilite/dedup) depuis l'historique des runs, **dry-run strict** (lecture seule ; ecriture deleguee au writer aval, routage DEC-016, archivage R31). **8 tests PASS**.
- `plugins/workflow-engine/workflows/` : `learning_review`, `skill_regression_test` (gate + approbation humaine avant promotion), `source_freshness`, `tool_scout` — execution veille **deportee** Antigravity/Hermes via canal_agents (DEC-029). Activities `self_improving.activities.ts` + barrel `self_improving.index.ts` **isoles du worker en prod** (activation = etape controlee, doc `SELF_IMPROVING.md`). TypeScript : mes 4 fichiers typecheckent propre (`tsc --noEmit`).

Garde-fous respectes : aucun plugin ajoute (vitrine 12 intacte) ; dry-run par defaut ; pas d'auto-modification core/secrets/MCP ; zero nom prive dans le code public (gates frontiere+docs-sync OK) ; collection pytest 617 tests, 0 erreur.

A faire (suite) : enregistrer les workflows N7 dans un worker (etape controlee) + Temporal Schedules ; alimenter le reliability engine depuis les runs reels ; brancher eval-lab N5 ; calibrate-quota-governor 14/06.

*Derniere mise a jour : 2026-06-11 soir — Lots D (gouvernance MCP) + E (reliability N6 + workflows N7) livres (DEC-046).*
