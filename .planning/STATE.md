# STATE.md — TricorderKit v0.7

> État courant du projet. Mettre à jour à chaque session.

---

## Version courante

- **Version** : 0.7 (en cours)
- **Date** : 10/05/2026
- **Phase active** : Phase 2 — CLI-first

---

## Statut des phases

| Phase | Nom | Statut |
|---|---|---|
| 1 | Fondations (fichiers fondateurs) | ✅ Complétée |
| 2 | CLI-first (cli-forge + outils métier) | 🔶 En cours |
| 3 | Workflows persistants (Temporal) | 🔲 Pending |
| 4 | Deep Research | 🔲 Pending |
| 5 | Obsidian + sécurité + evals | 🔲 Pending |

---

## Outils CLI installés (10/05/2026)

| Outil | Chemin | Statut |
|---|---|---|
| mangatracker-cli v0.1.0 | `tools/mangatracker-cli/` | ✅ Opérationnel |
| jp-scraper v0.1.0 | `tools/jp-scraper/` | ✅ Opérationnel |
| vault-optimizer v0.1 | `scripts/vault_optimizer/` | ✅ Opérationnel |

---

## Statut des plugins

| Plugin | Statut | Priorité |
|---|---|---|
| memory-boot | 🔲 À migrer v0.7 | S |
| token-hygiene | 🔲 À migrer v0.7 | S |
| cli-forge | ✅ Scaffold + github-goat + source-watch-goat | S |
| workflow-engine | ✅ Scaffold + source_watch.workflow.ts | S |
| deep-research-core | ✅ Scaffold + sources + pipeline manga | S |
| agents-standard | 🔲 À créer | A |
| skill-registry | 🔲 À créer | A |

---

## Claude Code Integrations actives

| Intégration | Statut |
|---|---|
| `.claude/agents/` (5 agents) | ✅ Prêts |
| `.claude/commands/` (8 slash commands) | ✅ Prêts |
| `.claude/hooks/` (4 hooks PreToolUse) | ✅ Prêts |
| `.claude/skills/vault-token-optimizer/` | ✅ Prêt |
| `.claude/skills/open-source-jp-scraper/` | ✅ Prêt |
| `.tricorderkit/vault_optimizer.config.json` | ✅ Prêt |
| `.mcp.json` (kintone via env vars) | ✅ Prêt (secrets requis) |

---

## Infrastructure

| Service | Statut |
|---|---|
| Neo4j | 🔲 Non déployé |
| Qdrant | 🔲 Non déployé |
| Temporal | 🔲 Non déployé |
| Langfuse | 🔲 Non déployé |
| Docker Compose | 🔲 Non configuré |

---

## Blockers actifs

Aucun blocker critique identifié.

---

## Prochaine action recommandée

```text
Priority 1 — Implémenter les parseurs mangatracker-cli :
  Premier : manga/shonenjumpplus
  Ensuite : ln/syosetu, anime/comic-natalie

Priority 2 — Tester jp-scraper RSS live :
  jp-scraper scrape source comic-natalie --mode rss
  jp-scraper report summary --source comic-natalie

Priority 3 — Configurer kintone :
  Renseigner KINTONE_BASE_URL + KINTONE_API_TOKEN dans .env
```

---

*Dernière mise à jour : 10/05/2026*
