/**
 * trigger_workflow.ts — Déclencheur de workflow Temporal depuis connector_hub
 * TricorderKit v0.9
 *
 * Utilisé par dispatch_temporal.py (fallback TypeScript si SDK Python absent).
 *
 * Variables d'environnement :
 *   TEMPORAL_ADDRESS    — ex: localhost:7233
 *   TEMPORAL_NAMESPACE  — ex: default
 *   TEMPORAL_TASK_QUEUE — ex: tricorderkit-hooks
 *   WORKFLOW_NAME       — source-watch | usage-observer | skill-eval
 *   WORKFLOW_ID         — ID déterministe (ex: tricorderkit-source-watch-20260518)
 *   WORKFLOW_SOURCES    — csv ex: mangadex,anilist,jikan
 *   DRY_RUN             — 1 | 0
 *
 * Usage :
 *   npx ts-node trigger_workflow.ts
 */

import { Client, Connection } from '@temporalio/client';

const TEMPORAL_ADDRESS    = process.env['TEMPORAL_ADDRESS']    ?? 'localhost:7233';
const TEMPORAL_NAMESPACE  = process.env['TEMPORAL_NAMESPACE']  ?? 'default';
const TEMPORAL_TASK_QUEUE = process.env['TEMPORAL_TASK_QUEUE'] ?? 'tricorderkit-hooks';
const WORKFLOW_NAME       = process.env['WORKFLOW_NAME']       ?? 'source-watch';
const WORKFLOW_ID         = process.env['WORKFLOW_ID']         ?? `tricorderkit-${WORKFLOW_NAME}-${new Date().toISOString().slice(0,10).replace(/-/g,'')}`;
const WORKFLOW_SOURCES    = (process.env['WORKFLOW_SOURCES']   ?? 'mangadex,anilist').split(',');
const DRY_RUN             = process.env['DRY_RUN'] === '1';
const OBSIDIAN_VAULT      = process.env['OBSIDIAN_VAULT_PATH'] ?? 'C:/Users/sebas/Documents/Claude/claude-vault';

// Mapping nom → nom de fonction Temporal
const WORKFLOW_FN_MAP: Record<string, string> = {
  'source-watch':   'sourceWatch',
  'usage-observer': 'usageObserverWorkflow',
  'skill-eval':     'skillEvalWorkflow',
};

// Inputs par type de workflow
function buildInput(workflowName: string): unknown {
  if (workflowName === 'source-watch') {
    return {
      interval_minutes: 60,
      sources: WORKFLOW_SOURCES as ('mangadex' | 'anilist' | 'jikan')[],
      filters: { min_score: 70, languages: ['fr', 'en'] },
      obsidian_vault_path: OBSIDIAN_VAULT,
      token_budget: { max_tokens: 30000, on_budget_exceeded: 'pause_and_notify' },
    };
  }
  if (workflowName === 'usage-observer') {
    return { interval_hours: 6 };
  }
  return {};
}

async function main(): Promise<void> {
  const workflowFn = WORKFLOW_FN_MAP[WORKFLOW_NAME];
  if (!workflowFn) {
    console.error(JSON.stringify({
      status: 'error',
      message: `Workflow inconnu: ${WORKFLOW_NAME}. Disponibles: ${Object.keys(WORKFLOW_FN_MAP).join(', ')}`,
    }));
    process.exit(1);
  }

  const input = buildInput(WORKFLOW_NAME);

  if (DRY_RUN) {
    console.log(JSON.stringify({
      status: 'dry_run',
      workflow: WORKFLOW_NAME,
      workflow_fn: workflowFn,
      workflow_id: WORKFLOW_ID,
      task_queue: TEMPORAL_TASK_QUEUE,
      address: TEMPORAL_ADDRESS,
      input,
      message: 'Dry-run: aucun workflow déclenché',
    }, null, 2));
    return;
  }

  console.error(`[trigger_workflow] Connexion à Temporal ${TEMPORAL_ADDRESS}...`);

  let connection: Connection;
  try {
    connection = await Connection.connect({ address: TEMPORAL_ADDRESS });
  } catch (err) {
    console.error(JSON.stringify({
      status: 'error',
      message: `Impossible de se connecter à Temporal: ${err}`,
      suggestion: 'docker compose ps — vérifier service temporal',
    }));
    process.exit(1);
  }

  const client = new Client({ connection, namespace: TEMPORAL_NAMESPACE });

  try {
    const handle = await client.workflow.start(workflowFn as any, {
      args: [input],
      taskQueue: TEMPORAL_TASK_QUEUE,
      workflowId: WORKFLOW_ID,
    });

    console.log(JSON.stringify({
      status: 'success',
      workflow: WORKFLOW_NAME,
      workflow_id: handle.workflowId,
      run_id: handle.firstExecutionRunId,
      task_queue: TEMPORAL_TASK_QUEUE,
      ui_url: `http://localhost:8080/namespaces/${TEMPORAL_NAMESPACE}/workflows/${handle.workflowId}`,
    }, null, 2));

  } catch (err: any) {
    // WorkflowAlreadyStartedError = idempotence OK
    if (err?.name === 'WorkflowExecutionAlreadyStartedError') {
      console.log(JSON.stringify({
        status: 'success',
        workflow: WORKFLOW_NAME,
        workflow_id: WORKFLOW_ID,
        message: 'Workflow déjà en cours (idempotence Temporal OK)',
        ui_url: `http://localhost:8080/namespaces/${TEMPORAL_NAMESPACE}/workflows/${WORKFLOW_ID}`,
      }, null, 2));
    } else {
      console.error(JSON.stringify({
        status: 'error',
        workflow: WORKFLOW_NAME,
        message: String(err),
      }));
      process.exit(1);
    }
  } finally {
    await connection!.close();
  }
}

main();
