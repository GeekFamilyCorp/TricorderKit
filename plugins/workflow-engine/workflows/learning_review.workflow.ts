/**
 * learning_review.workflow.ts — TricorderKit (DEC-046 / N7).
 *
 * Revue d'apprentissage (cadence hebdomadaire, declenchee par une Temporal
 * Schedule). Passe unique, consolidation cote Claude/CLI :
 *   compareStrategies -> extractLessons -> proposeSkillUpdate (draft) -> file de
 *   revue humaine. NE PROMEUT JAMAIS un skill (human_review_required par defaut).
 */
import { proxyActivities, log } from '@temporalio/workflow';
import type { SelfImprovingActivities } from '../activities/self_improving.activities';

export interface LearningReviewInput {
  task_type: string;
  min_confidence?: number;        // seuil d'extraction des lecons (defaut cote script)
  target_skill?: string;          // skill candidat a une proposition de draft
}

export interface LearningReviewResult {
  task_type: string;
  ranking: unknown;
  lessons: unknown;
  proposals: number;
  human_review_required: true;
}

const {
  compareStrategies, extractLessons, proposeSkillUpdate, logSelfImprovingCycle,
} = proxyActivities<SelfImprovingActivities>({
  startToCloseTimeout: '5 minutes',
  retry: { maximumAttempts: 3, initialInterval: '10 seconds', backoffCoefficient: 2 },
});

export async function learningReview(input: LearningReviewInput): Promise<LearningReviewResult> {
  log.info('learning_review demarre', { input });

  const ranking = await compareStrategies({ task_type: input.task_type });
  const lessons = await extractLessons({
    task_type: input.task_type, min_confidence: input.min_confidence,
  });

  let proposals = 0;
  const accepted: any[] = (lessons as any)?.output?.data?.lessons ?? [];
  if (input.target_skill) {
    for (const lesson of accepted.slice(0, 5)) {
      const lid = lesson?.lesson_id;
      if (!lid) continue;
      await proposeSkillUpdate({ lesson_id: lid, skill_name: input.target_skill });
      proposals++;
    }
  }

  const result: LearningReviewResult = {
    task_type: input.task_type, ranking, lessons,
    proposals, human_review_required: true,
  };
  await logSelfImprovingCycle({ workflow: 'learning_review', summary: { task_type: input.task_type, proposals } });
  log.info('learning_review termine', { proposals });
  return result;
}
