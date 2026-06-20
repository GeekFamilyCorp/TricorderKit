# experiments/arbor_adapter — Prototype isolé (Arbor)

> **Laboratoire de recherche cumulative.** Arbor explore plusieurs hypothèses d'amélioration
> (prompts, scrapers, workflows, agents), conserve branches réussies **et** échouées, et produit
> des rapports de benchmark. **Prototype strictement isolé** : il n'écrit jamais dans le cœur
> de TricorderKit et peut être supprimé sans rien casser.

## Statut
- Décision : **PROTOTYPER** (cf. `.planning/DECISIONS.md` → DEC-052).
- `allowed_to_modify_core: false`.
- Tant que non benchmarké, ne rien intégrer au cœur (`src`/`plugins`).

## Boucle (cible)
```
hypothesis_tree → observe → ideate → select → dispatch_executors → backpropagate_insights → decide → export
```
Rattachement conceptuel : module `research_agent` (boucle de recherche), sans dépendance cœur.

## Contenu
- `research_config.tricorderkit.yaml` — cas de test, critères de succès, rollback.
- `DECISION.md` — pointeur vers la décision DEC-052.
- `test_github_audit_task.md`, `test_scraping_optimizer_task.md` — cas contrôlés.
- `hypothesis_trees/`, `executor_outputs/`, `benchmark_reports/` — artefacts (gitkeep).
- `worktrees/` — **gitignored** (worktrees Git isolés, jamais committés).

## Garde-fous
- Ne pas modifier `src/`, `plugins/`, `core/`, `cli/`.
- Sorties = uniquement sous `experiments/arbor_adapter/` et `reports/benchmarks/`.
- Réversible : supprimer ce dossier + les benchmarks liés ; garder la trace dans `.planning/DECISIONS.md`.

## Critère d'intégration (gate)
Promotion hors prototype **uniquement** après un benchmark Markdown exploitable montrant un gain
net sur ≥1 cas réel, et une décision explicite (nouveau DEC). Sinon : rester `SURVEILLER` ou `REJETER`.
