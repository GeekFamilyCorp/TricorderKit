/**
 * source_watch.workflow.ts — TricorderKit v0.8
 * Workflow générique de veille sources (configurable par linked_project)
 *
 * Temporal workflow persistant :
 * - interroge les sources du registre connector_hub (trusted_sources.yml
 *   + sources.yaml des linked_projects actifs), une activity scanSource par source
 * - filtre les nouvelles sorties
 * - écrit dans le vault du linked_project actif
 * - génère un rapport Markdown
 * - respecte le budget tokens
 */

import { proxyActivities, sleep, condition, log, defineSignal, setHandler } from '@temporalio/workflow';
import type { Activities } from '../activities/index';

// ── Types ──────────────────────────────────────────────────────────────────────
interface SourceWatchInput {
  interval_minutes: number;       // Ex: 60
  sources: string[];              // Noms du registre connector_hub, ex: ['arXiv API', 'GitHub API']
  filters: {
    query?: string;               // Ex: 'local-first software'
    min_score?: number;           // 0–100
    languages?: string[];         // Ex: ['fr', 'en']
    topics?: string[];
  };
  obsidian_vault_path: string;
  token_budget: {
    max_tokens: number;           // Ex: 30000
    on_budget_exceeded: 'pause_and_notify' | 'stop';
  };
}

interface WatchCycle {
  cycle_number: number;
  started_at: string;
  items_found: number;
  items_new: number;
  tokens_used: number;
  report_path: string;
}

// ── Signals ───────────────────────────────────────────────────────────────────────
export const pauseSignal   = defineSignal('pause');
export const resumeSignal  = defineSignal('resume');
export const stopSignal    = defineSignal('stop');

// ── Activities proxy ───────────────────────────────────────────────────────────────────
const {
  scanSource,
  deduplicateItems,
  writeMarkdownReport,
  updateObsidianVault,
  notifyBudgetExceeded,
  logWorkflowCycle,
} = proxyActivities<Activities>({
  startToCloseTimeout: '5 minutes',
  retry: {
    maximumAttempts: 3,
    initialInterval: '10 seconds',
    backoffCoefficient: 2,
  },
});

// ── Workflow ─────────────────────────────────────────────────────────────────────────
export async function sourceWatch(input: SourceWatchInput): Promise<void> {
  let paused  = false;
  let stopped = false;
  let totalTokensUsed = 0;
  let cycleNumber = 0;

  setHandler(pauseSignal,  () => { paused  = true;  log.info('Workflow pause'); });
  setHandler(resumeSignal, () => { paused  = false; log.info('Workflow repris'); });
  setHandler(stopSignal,   () => { stopped = true;  log.info('Workflow arrete'); });

  log.info('source_watch demarre', { input });

  while (!stopped) {
    if (paused) {
      await condition(() => !paused || stopped, '24 hours');
      if (stopped) break;
    }

    cycleNumber++;
    const cycleStart = new Date().toISOString();
    log.info(`Cycle ${cycleNumber} demarre`);

    try {
      const rawItems: any[] = [];

      for (const source of input.sources) {
        const items = await scanSource({ source, filters: input.filters });
        rawItems.push(...items);
      }

      const { newItems, tokensUsed } = await deduplicateItems({
        items: rawItems,
        vault_path: input.obsidian_vault_path,
      });

      totalTokensUsed += tokensUsed;

      // Budget guard
      if (totalTokensUsed > input.token_budget.max_tokens) {
        log.warn('Budget tokens depasse', { totalTokensUsed, max: input.token_budget.max_tokens });
        await notifyBudgetExceeded({ workflow: 'source_watch', tokens_used: totalTokensUsed });

        if (input.token_budget.on_budget_exceeded === 'stop') {
          stopped = true;
          break;
        } else {
          paused = true;
          await condition(() => !paused || stopped, '24 hours');
          if (stopped) break;
          totalTokensUsed = 0;
        }
      }

      if (newItems.length > 0) {
        const reportPath = await writeMarkdownReport({
          items: newItems, cycle: cycleNumber, vault_path: input.obsidian_vault_path,
        });
        await updateObsidianVault({
          items: newItems, vault_path: input.obsidian_vault_path, report_path: reportPath,
        });
        const cycle: WatchCycle = {
          cycle_number: cycleNumber, started_at: cycleStart,
          items_found: rawItems.length, items_new: newItems.length,
          tokens_used: tokensUsed, report_path: reportPath,
        };
        await logWorkflowCycle({ workflow: 'source_watch', cycle });
        log.info(`Cycle ${cycleNumber} termine`, { ...cycle });
      } else {
        log.info(`Cycle ${cycleNumber} — rien de nouveau`);
      }
    } catch (err) {
      log.error(`Cycle ${cycleNumber} echoue`, { error: String(err) });
    }

    if (!stopped) {
      log.info(`Prochain cycle dans ${input.interval_minutes} minutes`);
      await sleep(`${input.interval_minutes} minutes`);
    }
  }

  log.info('source_watch termine', { cycles: cycleNumber, total_tokens: totalTokensUsed });
}
