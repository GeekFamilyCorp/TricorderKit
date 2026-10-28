/**
 * self_improving.index.ts — Barrel des workflows d'auto-amelioration (N7).
 * TricorderKit (DEC-046).
 *
 * SEPARE de workflows/index.ts (le barrel du worker en production) a dessein :
 * activer ces workflows est une etape CONTROLEE (garde HIGH au moment des
 * promotions de skill). Pour les enregistrer, voir SELF_IMPROVING.md — il faut
 * aussi cabler self_improving.activities.ts dans le worker.
 */
export { learningReview } from './learning_review.workflow';
export { skillRegressionTest, approveSignal } from './skill_regression_test.workflow';
export { sourceFreshness } from './source_freshness.workflow';
export { toolScout } from './tool_scout.workflow';
