/**
 * workflows/index.ts — Barrel export pour workflowsPath Temporal
 * TricorderKit v0.8 — Phase 3.5 Hook Layer
 *
 * OBLIGATOIRE : require.resolve(workflowsPath) cherche ce fichier.
 * Sans lui, le Worker plante avec "Cannot find module".
 */

export { usageObserverWorkflow } from './usage_observer.workflow';
export { skillEvalWorkflow }     from './skill_eval.workflow';
// source_watch.workflow.ts exclu : activities (scanMangaDex, scanJikan, etc.) non encore implémentées
