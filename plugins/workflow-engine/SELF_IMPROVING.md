# Workflows d'auto-amelioration (DEC-046 / N7)

Quatre workflows Temporal orchestrent la boucle d'auto-amelioration. Conformement
au plan v1.0 et a DEC-029, **l'execution de la collecte / veille est deportee**
vers les executeurs externes (Antigravity / Hermes) via `canal_agents` ; ces
workflows **orchestrent, consolident et tracent** — ils ne scrappent pas et
n'ecrivent jamais dans le vault.

| Workflow | Fichier | Cadence type | Role |
|---|---|---|---|
| `learningReview` | `workflows/learning_review.workflow.ts` | hebdo (Schedule) | compare strategies -> extrait lecons -> propose des drafts de skill (jamais de promotion) |
| `skillRegressionTest` | `workflows/skill_regression_test.workflow.ts` | a la demande | gate des tests (>= 8 verts, 0 echec) + signal d'approbation humaine avant promotion |
| `sourceFreshness` | `workflows/source_freshness.workflow.ts` | quotidien | score de fraicheur (dry-run, N6) -> depeche un re-scrape des sources perimees |
| `toolScout` | `workflows/tool_scout.workflow.ts` | hebdo | depeche une mission de veille outillage par topic, trace les requetes |

## Garde-fous

- **Promotion gardee** : `skillRegressionTest` ne promeut un skill que si le gate
  est vert ET qu'un signal `approve` est recu (sinon il s'arrete sur le rapport).
  `promoteSkill` refuse par defaut (dry-run) ; `live: true` requis pour appliquer.
- **Dry-run par defaut** : le scoring de sources (`scoreSources` -> N6) est en
  lecture seule ; l'ecriture du registre est deleguee au writer du projet aval
  (routage DEC-016) avec archivage R31.
- **Execution deportee** : `dispatchVeilleTask` depose une requete JSON dans
  `CANAL_AGENTS_DIR` (defaut `.cache/canal_dispatch`, configurable) — un executeur
  externe la consomme. Aucun scraping cote worker.
- **Pas d'auto-modification du core** : ces workflows ne touchent ni le core, ni
  les secrets, ni les connecteurs MCP, ni les deploiements.

## Gate de regression (skill_regression_test)

L'activity `runSkillRegression` execute `pytest <tests_path>` et calcule
`gate_ok = success && failed === 0 && passed >= 8`. Elle force `--basetemp` HORS
du repo (R36) pour eviter que le verrou Windows de `.pytest_tmp` ne fasse echouer
le gate par erreur d'environnement plutot que par un vrai FAIL.

**Candidat de reference (verifie 2026-06-11)** :

| Champ | Valeur |
|---|---|
| `skill_name` | `learning-engine` |
| `tests_path` | `plugins/learning-engine/tests` |
| Resultat | **20 passed / 0 failed** (>= 8) -> `gate_ok = true` avec `--basetemp` hors repo |

Sans approbation humaine (`approve`), le workflow s'arrete sur ce rapport meme
gate vert : aucune promotion automatique.

## Activation (etape controlee)

Ces workflows ne sont **pas** cables dans le worker de production
(`workflows/index.ts` / `activities/index.ts`) : leur barrel est isole
(`workflows/self_improving.index.ts`) et leurs activities aussi
(`activities/self_improving.activities.ts`, type `SelfImprovingActivities`).

Le scaffolding d'activation est livre, **isole du worker de production** :

| Etape | Script | Effet |
|---|---|---|
| 1. Worker dedie | `scripts/start_self_improving_worker.ts` | worker sur sa PROPRE task queue `tricorderkit-self-improving` (n'affecte pas `tricorderkit-hooks`) ; enregistre les 4 workflows + les activities self-improving |
| 2. Schedules | `scripts/register_self_improving_schedules.ts` | **dry-run par defaut** ; `DRY_RUN=0` cree les Temporal Schedules (learning_review hebdo, source_freshness quotidien, tool_scout hebdo ; `skill_regression_test` reste a la demande) |

```bash
# 1. Demarrer le worker isole (laisser tourner)
TEMPORAL_ADDRESS=localhost:7233 CANAL_AGENTS_DIR=<dir> \
  npx ts-node plugins/workflow-engine/scripts/start_self_improving_worker.ts

# 2. Voir le plan des schedules (dry-run), puis l'appliquer
npx ts-node plugins/workflow-engine/scripts/register_self_improving_schedules.ts
DRY_RUN=0 npx ts-node plugins/workflow-engine/scripts/register_self_improving_schedules.ts
```

Tant que ces deux commandes ne sont pas lancees explicitement, les definitions
restent inertes — par conception (la mise en production des promotions de skill
est un point de controle HIGH ; aucune auto-activation).
