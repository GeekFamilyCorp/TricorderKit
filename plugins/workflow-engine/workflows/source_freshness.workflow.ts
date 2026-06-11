/**
 * source_freshness.workflow.ts — TricorderKit (DEC-046 / N7).
 *
 * Verifie la fraicheur des sources a partir de leurs observations (scoreSources,
 * N6, dry-run) et, pour les sources dont le score de fraicheur tombe sous le
 * seuil, DEPECHE un re-scrape vers l'executeur externe (Antigravity/Hermes) via
 * canal_agents. N'ecrit jamais dans le vault.
 */
import { proxyActivities, log } from '@temporalio/workflow';
import type { SelfImprovingActivities } from '../activities/self_improving.activities';

export interface SourceFreshnessInput {
  observations_path: string;
  registry?: string;
  freshness_threshold?: number;    // 0..100, defaut 50
}

export interface SourceFreshnessResult {
  checked: number;
  stale: string[];
  dispatched: number;
  [key: string]: unknown;   // serialisable pour le log d'activity
}

const { scoreSources, dispatchVeilleTask, logSelfImprovingCycle } =
  proxyActivities<SelfImprovingActivities>({
    startToCloseTimeout: '5 minutes',
    retry: { maximumAttempts: 3, initialInterval: '10 seconds', backoffCoefficient: 2 },
  });

export async function sourceFreshness(
  input: SourceFreshnessInput,
): Promise<SourceFreshnessResult> {
  log.info('source_freshness demarre', { input });
  const threshold = input.freshness_threshold ?? 50;

  const scored = await scoreSources({
    observations_path: input.observations_path, registry: input.registry,
  });
  const proposals: any[] = (scored as any)?.output?.data?.proposals ?? [];

  const stale: string[] = [];
  let dispatched = 0;
  for (const p of proposals) {
    const fresh = p?.sub_scores?.freshness ?? 100;
    if (fresh < threshold) {
      stale.push(p.source);
      await dispatchVeilleTask({
        kind: 'source_rescrape',
        payload: { source: p.source, freshness: fresh, reason: 'below_threshold' },
        requested_by: 'temporal/source_freshness',
      });
      dispatched++;
    }
  }

  const result: SourceFreshnessResult = { checked: proposals.length, stale, dispatched };
  await logSelfImprovingCycle({ workflow: 'source_freshness', summary: result });
  log.info('source_freshness termine', result);
  return result;
}
