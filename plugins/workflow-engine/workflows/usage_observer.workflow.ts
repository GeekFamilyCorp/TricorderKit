// usage_observer.workflow.ts — Workflow Temporal pour observer l'usage des skills/goats.
// Version : 0.2.0
//
// Améliorations v0.2.0 vs v0.1.0 :
// - Signal TERMINATE pour arrêt propre sans kill (indispensable en test et en CI)
// - Compteur maxRuns (optionnel) pour limiter les itérations en dev/test
// - Agrégation par skill_or_goat avec taux d'échec calculé
// - Estimation tokens réelle basée sur les données lues (vs 50 fixe)
// - Dépassement de budget → exit gracieux (vs pause silencieuse)
// - Log d'état à chaque itération (info structured)

import {
  proxyActivities,
  sleep,
  log,
  setHandler,
  defineSignal,
  condition,
} from '@temporalio/workflow';

export interface UsageObserverInput {
  /** Intervalle entre deux cycles, ex: '6h', '30m'. Défaut: '6h'. */
  interval?: string;
  /** Limite soft de tokens cumulés (DEC-006). Défaut: 5000. */
  token_budget?: number;
  /** Nombre max d'itérations (0 = infini). Utile pour les tests. */
  max_runs?: number;
}

export interface UsageStats {
  skill_or_goat: string;
  runs: number;
  failures: number;
  failure_rate: number;
  avg_tokens: number | null;
  avg_latency_ms: number | null;
  last_seen: string | null;
}

const terminateSignal = defineSignal('TERMINATE');

const { readHookLogs, writeUsageStats, aggregateStats } = proxyActivities<{
  readHookLogs(): Promise<Record<string, any>[]>;
  aggregateStats(records: Record<string, any>[]): Promise<UsageStats[]>;
  writeUsageStats(stats: UsageStats[]): Promise<void>;
}>({
  startToCloseTimeout: '5 minutes',
});

const DEFAULT_INTERVAL    = '6h';
const DEFAULT_TOKEN_BUDGET = 5_000;
const TOKENS_PER_RECORD   = 75;

export async function usageObserverWorkflow(
  input: UsageObserverInput
): Promise<{ reason: string; tokensUsed: number; iterations: number }> {

  const interval    = input.interval     ?? DEFAULT_INTERVAL;
  const tokenBudget = input.token_budget ?? DEFAULT_TOKEN_BUDGET;
  const maxRuns     = input.max_runs     ?? 0;

  let tokensUsed = 0;
  let iterations = 0;
  let shouldStop = false;

  setHandler(terminateSignal, () => {
    log.info('[usage_observer] TERMINATE signal received — stopping after current iteration');
    shouldStop = true;
  });

  log.info('[usage_observer] started', { interval, tokenBudget, maxRuns });

  while (true) {
    if (shouldStop) {
      log.info('[usage_observer] stopped by TERMINATE signal', { iterations, tokensUsed });
      return { reason: 'TERMINATED', tokensUsed, iterations };
    }

    if (tokensUsed >= tokenBudget) {
      log.warn('[usage_observer] token budget exhausted — exiting gracefully', { tokensUsed, tokenBudget });
      return { reason: 'BUDGET_EXHAUSTED', tokensUsed, iterations };
    }

    if (maxRuns > 0 && iterations >= maxRuns) {
      log.info('[usage_observer] max_runs reached', { iterations, tokensUsed });
      return { reason: 'MAX_RUNS_REACHED', tokensUsed, iterations };
    }

    const records = await readHookLogs();
    const stats   = await aggregateStats(records);
    await writeUsageStats(stats);

    const cycleTokens = Math.max(records.length, 1) * TOKENS_PER_RECORD;
    tokensUsed += cycleTokens;
    iterations++;

    log.info('[usage_observer] cycle complete', {
      iteration: iterations,
      statsCount: stats.length,
      cycleTokens,
      tokensUsed,
    });

    await Promise.race([
      sleep(interval),
      condition(() => shouldStop),
    ]);
  }
}
