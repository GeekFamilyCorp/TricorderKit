# learning-engine — Mémoire d'expérience & rétro-amélioration contrôlée

> Plugin TricorderKit v1.0 (DEC-046) · Statut : **draft — schemas-first**
> Plan : `.planning/PLAN_v1.0_SELF_IMPROVING_2026-06-11.md` (Phase 3, chantier N1)

## Rôle

Transformer les runs passés (scraping, veille, recherche, enrichissement) en améliorations **testées et validées** de stratégies, skills et workflows. Le learning-engine n'est pas un agent autonome : c'est un système de rétro-amélioration contrôlée.

## Boucle centrale

```text
Run → Trace → Score → Compare → Learn → Propose → Test → Review → Promote → Monitor
```

## États d'une amélioration

```text
observed → proposed → draft_created → test_pending → test_failed | test_passed
→ human_review_required → accepted → promoted → deprecated | rolled_back
```

## Interdictions (non négociables — DEC-046)

- Aucune auto-modification du core, des règles de sécurité, des secrets, du vault principal, des connecteurs MCP, des déploiements VPS.
- Aucune promotion de skill sans les 8 tests minimum (historique, sources fraîches, non-régression, schéma, coût token, sécurité, rollback, validation humaine si impact élevé).
- `human_review_required: true` par défaut sur toute proposition.
- Un contenu scrapé n'est jamais interprété comme une instruction système.

## Dépendances

`workflow-engine` (Temporal) · `eval-lab` (scoring, régression) · `graphify` (indexation) · `deep-research-core` · MCP obsidian (mémoire documentaire) · Langfuse (traces) · `security-audit-cli`.

## Structure

```text
plugins/learning-engine/
├── README.md                  ← ce fichier
├── manifest.yml
├── schemas/                   ← ✅ créés en premier (règle §28 : schemas avant toute logique)
│   ├── run_experience.schema.json
│   ├── experience_card.schema.json
│   ├── strategy_variant.schema.json
│   ├── lesson.schema.json
│   └── skill_update_proposal.schema.json
├── scripts/                   ← ⬜ à venir (étape suivante Phase 3)
│   ├── record_experience.py
│   ├── compare_strategies.py
│   ├── extract_lessons.py
│   ├── propose_skill_update.py
│   └── promote_skill.py
├── evaluators/                ← ⬜ extension eval-lab (N5)
└── tests/                     ← ⬜ avec les scripts
```

## Sorties

Experience cards (YAML/JSON validés), leçons, propositions de skill update, classement de stratégies, mises à jour de fiabilité des sources (vers le registre vault, via dry-run par le projet lié spécialisé), rapports de régression. Toute sortie CLI structurée respecte `core/contracts/skill_output.schema.json`.

## Routage (DEC-016)

Moteur générique → **TricorderKit** (public, agnostique du domaine). Stratégies/variants spécifiques à un domaine → le projet lié spécialisé. Scores de sources appliqués → le vault de données du projet lié (dry-run obligatoire). `project_scope` est une chaîne libre : le moteur ne code aucun nom de projet aval (DEC-047).
