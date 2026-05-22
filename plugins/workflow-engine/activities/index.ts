/**
 * activities/index.ts — Barrel exports for all Temporal activities
 * TricorderKit v0.9 — M5 Temporal wiring
 *
 * Ce fichier est importé par les workflows via :
 *   import type { Activities } from '../activities/index';
 *
 * Il est aussi utilisé par start_worker.ts pour enregistrer toutes les activities.
 */

// ─── usage_observer activities ────────────────────────────────────────────────
export {
  readHookLogs,
  aggregateStats,
  writeUsageStats,
} from './usage_observer.activities';

// ─── skill_eval activities ────────────────────────────────────────────────────
export {
  runCliContracts,
  runEvalLabScenarios,
  writeEvalResults,
} from './skill_eval.activities';

export type {
  EvalResult,
  EvalSummary,
} from './skill_eval.activities';

// ─── source_watch activities (connector_hub wiring) ──────────────────────────
export {
  scanMangaDex,
  scanAniList,
  scanJikan,
  deduplicateItems,
  writeMarkdownReport,
  updateObsidianVault,
  notifyBudgetExceeded,
  logWorkflowCycle,
} from './source_watch.activities';

export type {
  ScanFilters,
  ScanResult,
  DeduplicateResult,
} from './source_watch.activities';

// ─── Activities type (used by proxyActivities) ────────────────────────────────

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

import type {
  scanMangaDex,
  scanAniList,
  scanJikan,
  deduplicateItems,
  writeMarkdownReport,
  updateObsidianVault,
  notifyBudgetExceeded,
  logWorkflowCycle,
} from './source_watch.activities';

/**
 * Union type de toutes les activities disponibles dans ce Worker.
 * Utiliser avec proxyActivities<Activities> dans les workflows Temporal.
 */
export type Activities = {
  // usage_observer
  readHookLogs:           typeof readHookLogs;
  aggregateStats:         typeof aggregateStats;
  writeUsageStats:        typeof writeUsageStats;
  // skill_eval
  runCliContracts:        typeof runCliContracts;
  runEvalLabScenarios:    typeof runEvalLabScenarios;
  writeEvalResults:       typeof writeEvalResults;
  // source_watch → connector_hub
  scanMangaDex:           typeof scanMangaDex;
  scanAniList:            typeof scanAniList;
  scanJikan:              typeof scanJikan;
  deduplicateItems:       typeof deduplicateItems;
  writeMarkdownReport:    typeof writeMarkdownReport;
  updateObsidianVault:    typeof updateObsidianVault;
  notifyBudgetExceeded:   typeof notifyBudgetExceeded;
  logWorkflowCycle:       typeof logWorkflowCycle;
};
