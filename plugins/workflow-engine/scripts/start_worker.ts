/**
 * start_worker.ts — Temporal Worker pour TricorderKit Hook Layer
 * TricorderKit v0.7 — Phase 3.5
 *
 * Lance un Worker Temporal qui enregistre :
 *   - Workflows : UsageObserverWorkflow, SkillEvalWorkflow, SourceWatchWorkflow
 *   - Activities : readHookLogs, aggregateStats, writeUsageStats,
 *                  runCliContracts, runEvalLabScenarios, writeEvalResults
 *
 * Usage :
 *   TEMPORAL_ADDRESS=localhost:7233 npx ts-node plugins/workflow-engine/scripts/start_worker.ts
 *
 * Variables d'environnement :
 *   TEMPORAL_ADDRESS      — adresse du serveur Temporal (défaut: localhost:7233)
 *   TEMPORAL_NAMESPACE    — namespace Temporal (défaut: default)
 *   TEMPORAL_TASK_QUEUE   — task queue (défaut: tricorderkit-hooks)
 *   OBSIDIAN_VAULT_PATH   — chemin vers le vault Obsidian (pour les rapports)
 */

import { Worker, NativeConnection } from '@temporalio/worker';
import * as path from 'path';

// Import de toutes les activities
import * as activities from '../activities/index';

// ─── Config ───────────────────────────────────────────────────────────────────
const TEMPORAL_ADDRESS    = process.env['TEMPORAL_ADDRESS']    ?? 'localhost:7233';
const TEMPORAL_NAMESPACE  = process.env['TEMPORAL_NAMESPACE']  ?? 'default';
const TEMPORAL_TASK_QUEUE = process.env['TEMPORAL_TASK_QUEUE'] ?? 'tricorderkit-hooks';

// Chemin vers le dossier workflows (compilé en JS par tsc)
const WORKFLOWS_PATH = path.join(__dirname, '..', 'workflows');

// ─── Main ─────────────────────────────────────────────────────────────────────
async function main(): Promise<void> {
  console.log('[TricorderKit Worker] Démarrage...');
  console.log(`  Temporal  : ${TEMPORAL_ADDRESS}`);
  console.log(`  Namespace : ${TEMPORAL_NAMESPACE}`);
  console.log(`  TaskQueue : ${TEMPORAL_TASK_QUEUE}`);
  console.log(`  Workflows : ${WORKFLOWS_PATH}`);

  // Connexion au serveur Temporal
  const connection = await NativeConnection.connect({
    address: TEMPORAL_ADDRESS,
  });

  // Création du Worker
  const worker = await Worker.create({
    connection,
    namespace:     TEMPORAL_NAMESPACE,
    taskQueue:     TEMPORAL_TASK_QUEUE,

    // Chemin vers les workflows compilés (ou source TS si ts-node)
    workflowsPath: require.resolve(WORKFLOWS_PATH),

    // Toutes les activities enregistrées
    activities,
  });

  console.log('[TricorderKit Worker] Worker créé — en attente de tâches...');
  console.log('  Activities enregistrées :');
  Object.keys(activities)
    .filter(k => typeof (activities as Record<string, unknown>)[k] === 'function')
    .forEach(k => console.log(`    - ${k}`));

  // Lancement (bloquant jusqu'à SIGINT/SIGTERM)
  await worker.run();
}

// ─── Graceful shutdown ────────────────────────────────────────────────────────
process.on('SIGINT',  () => {
  console.log('\n[TricorderKit Worker] SIGINT reçu — arrêt...');
  process.exit(0);
});
process.on('SIGTERM', () => {
  console.log('\n[TricorderKit Worker] SIGTERM reçu — arrêt...');
  process.exit(0);
});

main().catch(err => {
  console.error('[TricorderKit Worker] Erreur fatale :', err);
  process.exit(1);
});
