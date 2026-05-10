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
| 2 | CLI-first (cli-forge) | 🔶 En cours |
| 3 | Workflows persistants (Temporal) | 🔲 Pending |
| 4 | Deep Research | 🔲 Pending |
| 5 | Obsidian + sécurité + evals | 🔲 Pending |

---

## Statut des plugins

| Plugin | Statut | Priorité |
|---|---|---|
| memory-boot | 🔲 À migrer v0.7 | S |
| token-hygiene | 🔲 À migrer v0.7 | S |
| cli-forge | ✅ Scaffold complet + github-goat + source-watch-goat | S |
| workflow-engine | ✅ Scaffold + source_watch.workflow.ts | S |
| deep-research-core | ✅ Scaffold + sources + pipeline manga | S |
| agents-standard | 🔲 À créer | A |
| skill-registry | 🔲 À créer | A |
| repo-pack | 🔲 À migrer v0.7 | A |
| usage-observer | 🔲 À créer | A |
| eval-lab | 🔲 À créer | A |
| obsidian-agent-layer | 🔲 À créer | B |
| security-audit-cli | 🔲 À créer | B |

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
Tester source-watch-goat en dry-run puis live :
  python plugins/cli-forge/generated/source-watch-goat/source_watch_goat.py --dry-run trending-manga
  python plugins/cli-forge/generated/source-watch-goat/source_watch_goat.py trending-manga --output table
Puis valider le manifest : python plugins/cli-forge/scripts/validate_cli_manifest.py --all
```

---

*Dernière mise à jour : 10/05/2026*
