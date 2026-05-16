/**
 * activities/index.ts — Barrel exports for all Temporal activities
 * TricorderKit v0.7 — Phase 3.5 Hook Layer
 *
 * Ce fichier est importé par les workflows via :
 *   import type { Activities } from '../activities/index';
 *   const { readHookLogs, aggregateStats, writeUsageStats } = proxyActivities<Activities>({ ... });
 *
 * Il est aussi utilisé par start_worker.ts pour enregistrer toutes les activities
 * dans le Worker Temporal.
 */

// ─── usage_observer activities ────────────────────────────────────────────────────────────────
export {
  readHookLogs,
  aggregateStats,
  writeUsageStats,
} from './usage_observer.activities';

// ─── skill_eval activities ────────────────────────────────────────────────────────────────
export {
  runCliContracts,
  runEvalLabScenarios,
  writeEvalResults,
} from './skill_eval.activities';

export type {
  EvalResult,
  EvalSummary,
} from './skill_eval.activities';

// ─── Activities type (used by proxyActivities) ────────────────────────────────────────────
import type {
  readHookLogs,
  aggregateStats,
  writeUsageStats,
} from './usage_observer.activities';

import type {
  runCliContracts,
  runEvalLabScenarios,
  writeEvalResults,
} from './skill_eval.activities';

/**
 * Union type de toutes les activities disponibles dans ce Worker.
 * Utiliser avec proxyActivities<Activities> dans les workflows Temporal.
 */
export type Activities = {
  readHookLogs:       typeof readHookLogs;
  aggregateStats:     typeof aggregateStats;
  writeUsageStats:    typeof writeUsageStats;
  runCliContracts:    typeof runCliContracts;
  runEvalLabScenarios: typeof runEvalLabScenarios;
  writeEvalResults:   typeof writeEvalResults;
};
