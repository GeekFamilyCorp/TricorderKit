/**
 * skill_regression_test.workflow.ts — TricorderKit (DEC-046 / N7).
 *
 * Teste un skill candidat AVANT toute promotion : execute le gate des tests
 * (>= 8 verts, 0 echec) puis, seulement si un signal d'approbation humaine est
 * recu ET que le gate est vert, declenche la promotion (sinon refus).
 *
 * Garde-fou : sans approbation explicite, le workflow s'arrete sur le rapport de
 * test — il n'auto-modifie jamais un skill.
 */
import {
  proxyActivities, log, defineSignal, setHandler, condition,
} from '@temporalio/workflow';
import type { SelfImprovingActivities } from '../activities/self_improving.activities';

export interface SkillRegressionInput {
  skill_name: string;
  tests_path: string;
  live?: boolean;                  // applique reellement la promotion si true
  approval_timeout?: string;       // ex: '24 hours' (defaut)
}

export interface SkillRegressionResult {
  skill_name: string;
  gate_ok: boolean;
  passed: number;
  failed: number;
  promoted: boolean;
  reason: string;
  [key: string]: unknown;   // serialisable pour le log d'activity
}

export const approveSignal = defineSignal('approve');

const { runSkillRegression, promoteSkill, logSelfImprovingCycle } =
  proxyActivities<SelfImprovingActivities>({
    startToCloseTimeout: '10 minutes',
    retry: { maximumAttempts: 2, initialInterval: '15 seconds', backoffCoefficient: 2 },
  });

export async function skillRegressionTest(
  input: SkillRegressionInput,
): Promise<SkillRegressionResult> {
  log.info('skill_regression_test demarre', { input });

  const gate = await runSkillRegression({ skill_name: input.skill_name, tests_path: input.tests_path });
  const base: SkillRegressionResult = {
    skill_name: input.skill_name, gate_ok: gate.gate_ok,
    passed: gate.passed, failed: gate.failed, promoted: false, reason: '',
  };

  if (!gate.gate_ok) {
    base.reason = `gate echoue (${gate.passed} passed / ${gate.failed} failed) — promotion bloquee`;
    await logSelfImprovingCycle({ workflow: 'skill_regression_test', summary: base });
    return base;
  }

  // Attente d'approbation humaine (HIGH risk). Pas d'approbation -> pas de promotion.
  let approved = false;
  setHandler(approveSignal, () => { approved = true; log.info('approbation recue'); });
  await condition(() => approved, (input.approval_timeout ?? '24 hours') as `${number} hours`);

  if (!approved) {
    base.reason = 'gate vert mais aucune approbation humaine recue dans le delai';
    await logSelfImprovingCycle({ workflow: 'skill_regression_test', summary: base });
    return base;
  }

  const promo = await promoteSkill({
    skill_name: input.skill_name, approved: true, gate_ok: true, live: input.live ?? false,
  });
  base.promoted = (promo?.status === 'success' || promo?.status === 'dry_run');
  base.reason = `promotion ${input.live ? 'appliquee' : 'dry-run'} : ${promo?.status ?? 'inconnu'}`;
  await logSelfImprovingCycle({ workflow: 'skill_regression_test', summary: base });
  log.info('skill_regression_test termine', base);
  return base;
}
