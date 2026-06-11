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

## Activation (etape controlee)

Ces workflows ne sont **pas** cables dans le worker de production
(`workflows/index.ts` / `activities/index.ts`) : leur barrel est isole
(`workflows/self_improving.index.ts`) et leurs activities aussi
(`activities/self_improving.activities.ts`, type `SelfImprovingActivities`).

Pour les activer :

1. Enregistrer les activities du module `self_improving.activities.ts` dans le
   `Worker.create({ activities })` (en plus des activities existantes).
2. Pointer un second worker (ou etendre `workflowsPath`) vers
   `self_improving.index.ts`.
3. Creer les Temporal Schedules (hebdo / quotidien) qui declenchent chaque
   workflow avec ses inputs.
4. Definir `CANAL_AGENTS_DIR` vers le repertoire de dispatch reel des executeurs.

Tant que cette etape n'est pas faite, les definitions restent inertes — par
conception (la mise en production des promotions de skill est un point de
controle HIGH).
