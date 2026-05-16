// skill_eval.workflow.ts — Workflow Temporal pour évaluer skills/goats.
// Version : 0.2.0
//
// Améliorations v0.2.0 vs v0.1.0 :
// - Signal TERMINATE pour arrêt propre
// - Budget par phase (CLI contracts puis eval-lab)
// - Connexion à eval-lab via runEvalLabScenarios (Phase 5)
// - Résultats détaillés : passed, failed, skipped
// - Retour structuré EvalSummary

import {
  proxyActivities,
  log,
  setHandler,
  defineSignal,
} from '@temporalio/workflow';

export interface SkillEvalInput {
  targets: string[];
  token_budget?: number;
  run_eval_lab?: boolean;
}

export interface EvalResult {
  target: string;
  passed: boolean;
  skipped: boolean;
  details: string;
  tokens_used: number;
  duration_ms: number;
}

export interface EvalSummary {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  tokens_used: number;
  results: EvalResult[];
}

const terminateSignal = defineSignal('TERMINATE');

const { runCliContracts, runEvalLabScenarios, writeEvalResults } = proxyActivities<{
  runCliContracts(targets: string[]): Promise<EvalResult[]>;
  runEvalLabScenarios(targets: string[]): Promise<EvalResult[]>;
  writeEvalResults(summary: EvalSummary): Promise<void>;
}>({
  startToCloseTimeout: '10 minutes',
});

const DEFAULT_TOKEN_BUDGET  = 5_000;
const TOKENS_PER_CLI_TARGET = 150;

function buildSummary(results: EvalResult[]): Omit<EvalSummary, 'results'> {
  return {
    total:       results.length,
    passed:      results.filter(r => r.passed && !r.skipped).length,
    failed:      results.filter(r => !r.passed && !r.skipped).length,
    skipped:     results.filter(r => r.skipped).length,
    tokens_used: results.reduce((acc, r) => acc + (r.tokens_used ?? 0), 0),
  };
}

export async function skillEvalWorkflow(
  input: SkillEvalInput
): Promise<{ summary: EvalSummary; reason: string }> {

  const tokenBudget = input.token_budget ?? DEFAULT_TOKEN_BUDGET;
  const runEvalLab  = input.run_eval_lab  ?? true;
  let tokensUsed    = 0;
  let shouldStop    = false;

  setHandler(terminateSignal, () => {
    log.info('[skill_eval] TERMINATE signal received');
    shouldStop = true;
  });

  log.info('[skill_eval] started', { targets: input.targets, tokenBudget, runEvalLab });

  if (!input.targets || input.targets.length === 0) {
    const empty: EvalSummary = { total: 0, passed: 0, failed: 0, skipped: 0, tokens_used: 0, results: [] };
    return { summary: empty, reason: 'NO_TARGETS' };
  }

  let allResults: EvalResult[] = [];

  const cliResults = await runCliContracts(input.targets);
  tokensUsed += input.targets.length * TOKENS_PER_CLI_TARGET;
  allResults = allResults.concat(cliResults);

  log.info('[skill_eval] CLI contracts done', {
    count: cliResults.length,
    passed: cliResults.filter(r => r.passed).length,
    tokensUsed,
  });

  if (runEvalLab && !shouldStop && tokensUsed < tokenBudget) {
    const evalResults = await runEvalLabScenarios(input.targets);
    tokensUsed += evalResults.reduce((a, r) => a + (r.tokens_used ?? 100), 0);
    allResults = allResults.concat(evalResults);

    log.info('[skill_eval] eval-lab done', {
      count: evalResults.length,
      passed: evalResults.filter(r => r.passed).length,
      tokensUsed,
    });
  } else if (tokensUsed >= tokenBudget) {
    log.warn('[skill_eval] eval-lab skipped (budget exhausted)', { tokensUsed, tokenBudget });
  }

  const summary: EvalSummary = { ...buildSummary(allResults), results: allResults };
  await writeEvalResults(summary);

  log.info('[skill_eval] completed', summary);

  const reason = shouldStop ? 'TERMINATED' :
                 tokensUsed >= tokenBudget ? 'BUDGET_EXHAUSTED' : 'COMPLETED';

  return { summary, reason };
}
