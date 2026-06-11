/**
 * start_self_improving_worker.ts — Worker Temporal ISOLE pour les workflows
 * d'auto-amelioration (TricorderKit, DEC-046 / N7).
 *
 * SEPARE du worker de production (`start_worker.ts`, queue `tricorderkit-hooks`) :
 * ce worker tourne sur sa PROPRE task queue (`tricorderkit-self-improving`) et
 * n'enregistre QUE les workflows N7 + les activities self-improving. Le demarrer
 * n'affecte donc pas le worker en production.
 *
 * Activation = etape controlee (garde HIGH au moment des promotions de skill).
 *
 * Usage :
 *   TEMPORAL_ADDRESS=localhost:7233 \
 *   CANAL_AGENTS_DIR=<dir de dispatch> \
 *   npx ts-node plugins/workflow-engine/scripts/start_self_improving_worker.ts
 *
 * Variables :
 *   TEMPORAL_ADDRESS    — defaut localhost:7233
 *   TEMPORAL_NAMESPACE  — defaut default
 *   SELF_IMPROVING_TASK_QUEUE — defaut tricorderkit-self-improving
 *   CANAL_AGENTS_DIR    — repertoire de dispatch vers Antigravity/Hermes
 */
import { Worker, NativeConnection } from '@temporalio/worker';
import * as path from 'path';

import * as selfImprovingActivities from '../activities/self_improving.activities';

const TEMPORAL_ADDRESS = process.env['TEMPORAL_ADDRESS'] ?? 'localhost:7233';
const TEMPORAL_NAMESPACE = process.env['TEMPORAL_NAMESPACE'] ?? 'default';
const TASK_QUEUE = process.env['SELF_IMPROVING_TASK_QUEUE'] ?? 'tricorderkit-self-improving';

// Barrel ISOLE : ne charge que les 4 workflows d'auto-amelioration.
const WORKFLOWS_BARREL = path.join(__dirname, '..', 'workflows', 'self_improving.index');

async function main(): Promise<void> {
  console.log('[self-improving worker] Demarrage (ISOLE)...');
  console.log(`  Temporal  : ${TEMPORAL_ADDRESS}`);
  console.log(`  Namespace : ${TEMPORAL_NAMESPACE}`);
  console.log(`  TaskQueue : ${TASK_QUEUE}`);

  const connection = await NativeConnection.connect({ address: TEMPORAL_ADDRESS });

  const worker = await Worker.create({
    connection,
    namespace: TEMPORAL_NAMESPACE,
    taskQueue: TASK_QUEUE,
    workflowsPath: require.resolve(WORKFLOWS_BARREL),
    activities: selfImprovingActivities,
  });

  console.log('[self-improving worker] Worker cree — workflows N7 enregistres :');
  console.log('    - learningReview, skillRegressionTest, sourceFreshness, toolScout');
  await worker.run();
}

process.on('SIGINT', () => { console.log('\n[self-improving worker] SIGINT — arret.'); process.exit(0); });
process.on('SIGTERM', () => { console.log('\n[self-improving worker] SIGTERM — arret.'); process.exit(0); });

main().catch(err => {
  console.error('[self-improving worker] Erreur fatale :', err);
  process.exit(1);
});
