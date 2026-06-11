/**
 * tool_scout.workflow.ts — TricorderKit (DEC-046 / N7).
 *
 * Veille outillage : DEPECHE une mission de decouverte d'outils vers l'executeur
 * externe (Antigravity/Hermes) via canal_agents, puis enregistre la requete pour
 * consolidation ulterieure cote Claude (scoring + rapport). L'execution de la
 * veille n'a PAS lieu dans ce workflow (DEC-029) : il orchestre et trace.
 */
import { proxyActivities, log } from '@temporalio/workflow';
import type { SelfImprovingActivities } from '../activities/self_improving.activities';

export interface ToolScoutInput {
  topics: string[];                 // domaines a explorer (ex: ['rag', 'scraping'])
  max_candidates?: number;          // budget de candidats par topic
}

export interface ToolScoutResult {
  topics: string[];
  request_ids: string[];
  dispatched: number;
  [key: string]: unknown;   // serialisable pour le log d'activity
}

const { dispatchVeilleTask, logSelfImprovingCycle } =
  proxyActivities<SelfImprovingActivities>({
    startToCloseTimeout: '3 minutes',
    retry: { maximumAttempts: 3, initialInterval: '10 seconds', backoffCoefficient: 2 },
  });

export async function toolScout(input: ToolScoutInput): Promise<ToolScoutResult> {
  log.info('tool_scout demarre', { input });
  const request_ids: string[] = [];

  for (const topic of input.topics) {
    const d = await dispatchVeilleTask({
      kind: 'tool_scout',
      payload: { topic, max_candidates: input.max_candidates ?? 10 },
      requested_by: 'temporal/tool_scout',
    });
    request_ids.push(d.request_id);
  }

  const result: ToolScoutResult = {
    topics: input.topics, request_ids, dispatched: request_ids.length,
  };
  await logSelfImprovingCycle({ workflow: 'tool_scout', summary: result });
  log.info('tool_scout termine', result);
  return result;
}
