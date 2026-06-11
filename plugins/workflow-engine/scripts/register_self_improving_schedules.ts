/**
 * register_self_improving_schedules.ts — Enregistre les Temporal Schedules des
 * workflows d'auto-amelioration (TricorderKit, DEC-046 / N7).
 *
 * DRY-RUN PAR DEFAUT : sans `DRY_RUN=0`, le script IMPRIME le plan des schedules
 * sans se connecter ni rien creer (Regle 4). Mettre `DRY_RUN=0` pour creer
 * reellement les schedules sur le serveur Temporal.
 *
 * `skill_regression_test` n'a PAS de schedule : il est declenche a la demande
 * (avant une promotion), avec approbation humaine.
 *
 * Usage :
 *   npx ts-node plugins/workflow-engine/scripts/register_self_improving_schedules.ts        # dry-run
 *   DRY_RUN=0 npx ts-node plugins/workflow-engine/scripts/register_self_improving_schedules.ts
 *
 * Variables : TEMPORAL_ADDRESS, TEMPORAL_NAMESPACE, SELF_IMPROVING_TASK_QUEUE,
 *   SELF_IMPROVING_TASK_TYPE (defaut 'scraping'), OBSERVATIONS_PATH, SCOUT_TOPICS.
 */
import { Client, Connection } from '@temporalio/client';

const TEMPORAL_ADDRESS = process.env['TEMPORAL_ADDRESS'] ?? 'localhost:7233';
const TEMPORAL_NAMESPACE = process.env['TEMPORAL_NAMESPACE'] ?? 'default';
const TASK_QUEUE = process.env['SELF_IMPROVING_TASK_QUEUE'] ?? 'tricorderkit-self-improving';
const TASK_TYPE = process.env['SELF_IMPROVING_TASK_TYPE'] ?? 'scraping';
const OBSERVATIONS_PATH = process.env['OBSERVATIONS_PATH'] ?? './reports/observations.json';
const SCOUT_TOPICS = (process.env['SCOUT_TOPICS'] ?? 'rag,scraping,dedup').split(',');
const DRY_RUN = process.env['DRY_RUN'] !== '0';
const TIMEZONE = 'Europe/Paris';

interface ScheduleSpec {
  scheduleId: string;
  cron: string;
  workflowType: string;
  args: unknown[];
}

const SCHEDULES: ScheduleSpec[] = [
  {
    scheduleId: 'self-improving-learning-review',
    cron: '0 4 * * 1',                 // lundi 04:00 (hebdo)
    workflowType: 'learningReview',
    args: [{ task_type: TASK_TYPE }],
  },
  {
    scheduleId: 'self-improving-source-freshness',
    cron: '0 5 * * *',                 // quotidien 05:00
    workflowType: 'sourceFreshness',
    args: [{ observations_path: OBSERVATIONS_PATH, freshness_threshold: 50 }],
  },
  {
    scheduleId: 'self-improving-tool-scout',
    cron: '0 6 * * 1',                 // lundi 06:00 (hebdo)
    workflowType: 'toolScout',
    args: [{ topics: SCOUT_TOPICS, max_candidates: 10 }],
  },
];

async function main(): Promise<void> {
  if (DRY_RUN) {
    console.log(JSON.stringify({
      status: 'dry_run',
      message: 'Aucun schedule cree (DRY_RUN). Mettre DRY_RUN=0 pour appliquer.',
      task_queue: TASK_QUEUE, namespace: TEMPORAL_NAMESPACE, timezone: TIMEZONE,
      schedules: SCHEDULES.map(s => ({ id: s.scheduleId, cron: s.cron, workflow: s.workflowType })),
      note: 'skill_regression_test = a la demande (pas de schedule), approbation humaine requise',
    }, null, 2));
    return;
  }

  const connection = await Connection.connect({ address: TEMPORAL_ADDRESS });
  const client = new Client({ connection, namespace: TEMPORAL_NAMESPACE });

  for (const s of SCHEDULES) {
    try {
      await client.schedule.create({
        scheduleId: s.scheduleId,
        spec: { cronExpressions: [s.cron], timezone: TIMEZONE },
        action: {
          type: 'startWorkflow',
          workflowType: s.workflowType,
          taskQueue: TASK_QUEUE,
          args: s.args,
        },
      });
      console.log(`[schedule] cree : ${s.scheduleId} (${s.cron} -> ${s.workflowType})`);
    } catch (err: any) {
      if (String(err?.name).includes('AlreadyExists')) {
        console.log(`[schedule] deja present : ${s.scheduleId} (idempotent)`);
      } else {
        console.error(`[schedule] echec ${s.scheduleId} : ${err}`);
      }
    }
  }
  await connection.close();
}

main().catch(err => {
  console.error('[register_self_improving_schedules] erreur fatale :', err);
  process.exit(1);
});
