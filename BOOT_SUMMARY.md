# BOOT_SUMMARY — TricorderKit
> Fichier de boot condensé. Régénérer en fin de session (skill `rapport` / `/tk:boot --update-summary`).
> Objectif : remplacer ~13 500 tokens de chargement par ~500 tokens au boot.

---

## Version & statut

| Champ | Valeur |
|---|---|
| Version | **v1.0.0** (Self-Improving DEC-046 — 7 chantiers N1-N7 code-complete) |
| Commit HEAD | `94fef64` |
| Release | `v1.0.0` = Latest (GitHub) |
| Dernière session | 2026-06-14 |
| Tests | **634 collected** (544 green @ v0.9.5 ; ajouts v1.0 verts ; suite validée en CI) |
| Plugins | **13** |
| Blockers actifs | Docker Desktop / Temporal **DOWN** en local (port 7233) → worker self-improving + schedules réels bloqués (reboot requis) |

---

## Infrastructure Docker (local)

| Service | Port | Statut |
|---|---|---|
| Neo4j | 7474/7687 | ⚠️ Dépend de Docker (down local) |
| Qdrant | 6333 | ⚠️ Dépend de Docker (down local) |
| Langfuse | 3001 | ⚠️ Dépend de Docker (down local) |
| Temporal | 7233 | ❌ DOWN (engine 500) — worker self-improving bloqué |

> VPS Hostinger : control plane Paperclip + Hermes/Ollama actifs (runbook `ACCES_VPS_HOSTINGER`, côté vault).

---

## Plugins actifs (13)

`cli-forge` · `workflow-engine` · `deep-research-core` · `connector-hub v0.1.0`
`eval-lab` · `obsidian-agent-layer` · `security-audit-cli` · `graphify`
`learning-engine v0.1.0` (DEC-046) · `scraper-runtime v0.1.0` (DEC-046)
`document-ingestion v0.1.0` (DEC-048) · `memory-boot v0.8` · `token-optimizer v0.8`

Prêts production : 3/13 (deep-research-core, token-optimizer, security-audit-cli) · Partiels : 10/13 · Non prêts : 0.

---

## Cap v1.0 (DEC-046) — Self-Improving

- **learning-engine** : runs → experience cards → leçons → propositions de skill *gardées* (drafts ; promotion = 8 tests verts + revue humaine).
- **MCP governance** : deny-by-default, `mcp/registry_allowlist.yaml` + `tk mcp audit`.
- **scraper-runtime** : profils + run contract + registre + moteur de fiabilité des sources (dry-run, read-only).
- **eval-lab** : 5 évaluateurs qualité (scraping, fiabilité source, dedup, RAG, coût/latence).
- **4 workflows Temporal** self-improvement (learning review, skill regression, source freshness, tool scout) — exécution déportée.
- Gate de régression : pytest `--basetemp` hors repo (R36) ; candidat de référence learning-engine 20/20 → gate_ok.

---

## Patterns d'erreurs actifs

| Code | Règle |
|---|---|
| ARCH-001 | Hooks Cowork inertes → comportement auto dans SKILL.md orchestrateur |
| ARCH-002 | System prompt Cowork côté serveur → estimation uniquement |
| ENV-001 | MSIX paths → LOCALAPPDATA pour fichiers Claude Desktop externes |
| OPS-001 | Scheduled tasks → prompt ≤ 300 tokens |
| WIN-ENCODING | I/O Windows → forcer UTF-8 (stdout / read_text / subprocess) |
| EDIT-DUALFS | git par chemin réel + sortie redirigée ; jamais édition octet d'un source |

---

## Dernières décisions

| Code | Résumé |
|---|---|
| DEC-049 | Gate docs-sync vérifie ROADMAP (R46) ; renumérotation collision DEC-047 |
| DEC-048 | Plugin document-ingestion (MarkItDown) — 13e plugin |
| DEC-047 | `project_scope` générique (learning-engine) |
| DEC-046 | v1.0 Self-Improving — 7 chantiers N1-N7 code-complete |
| DEC-016 | Routage 3 dépôts : générique → TricorderKit ; exécutable / données → dépôts liés privés |

---

## CLI unifiée (`tk`)

`tk status / health / doctor / skill / workflow / vault / research / project / security / obsidian / rapport / mcp`

---

## Pour aller plus loin (lazy-load)

| Besoin | Fichier |
|---|---|
| Vision produit | `docs/00_WHAT_IS_TRICORDERKIT.md` |
| Architecture interne | `docs/01_HOW_IT_WORKS.md` |
| Inventaire opérationnel | `docs/02_WHAT_IS_IN_PLACE.md` |
| Backlog détaillé | `docs/03_WHAT_TO_DO_NEXT.md` |
| Self-Improving (v1.0) | `SELF_IMPROVING.md` |
| Règles agents | `AGENTS.md` |
| Décisions / Risques | `.planning/DECISIONS.md` · `.planning/RISKS.md` |
| Exploitation v1.0 | `.planning/RUNBOOK_EXPLOITATION_v1.0_2026-06-11.md` |

---

*Auto-régénérable — TricorderKit v1.0.0 — HEAD `94fef64` — 2026-06-14 — 634 tests collected, 0 FAIL.*
