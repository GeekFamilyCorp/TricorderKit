/**
 * skill_eval.activities.ts — Temporal activities for the SkillEval workflow
 * TricorderKit v0.7 — Phase 3.5 Hook Layer
 *
 * Activities:
 *   - runCliContracts(targets)      : exécute pytest sur core/hooks/tests/test_hooks.py
 *   - runEvalLabScenarios(targets)  : lance les scénarios eval-lab (Phase 5, facultatif)
 *   - writeEvalResults(summary)     : écrit le rapport Markdown dans Obsidian + JSON-lines log
 */

import * as fs from 'fs';
import * as path from 'path';
import { spawnSync } from 'child_process';

// ─── Paths ────────────────────────────────────────────────────────────────────
const REPO_ROOT       = path.resolve(__dirname, '..', '..', '..');
const HOOKS_CACHE_DIR = path.join(REPO_ROOT, '.cache', 'hooks');
const EVAL_LOG        = path.join(HOOKS_CACHE_DIR, 'eval_results.log');
const TEST_DIR        = path.join(REPO_ROOT, 'core', 'hooks', 'tests');
const TEST_FILE       = path.join(TEST_DIR, 'test_hooks.py');
const EVAL_LAB_BIN    = path.join(REPO_ROOT, 'plugins', 'eval-lab', 'run_eval.py');

// ─── Types ────────────────────────────────────────────────────────────────────
export interface EvalResult {
  target:      string;       // skill / goat / workflow name
  test_name:   string;
  status:      'passed' | 'failed' | 'error' | 'skipped';
  duration_ms: number;
  error?:      string;
  source:      'cli_contracts' | 'eval_lab';
}

export interface EvalSummary {
  timestamp:   string;       // ISO-8601 UTC
  total:       number;
  passed:      number;
  failed:      number;
  skipped:     number;
  tokens_used: number;
  results:     EvalResult[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function nowISO(): string {
  return new Date().toISOString();
}

/**
 * Parse pytest --tb=short -v output into EvalResult[]
 * Lines matching "PASSED"/"FAILED"/"ERROR"/"SKIPPED" are extracted.
 */
function parsePytestOutput(stdout: string, target: string): EvalResult[] {
  const results: EvalResult[] = [];
  const lines = stdout.split('\n');

  // Regex: "test_foo.py::TestClass::test_method PASSED"
  const lineRe = /^(.*::[\w:]+)\s+(PASSED|FAILED|ERROR|SKIPPED)\s*(?:\((.+?)\))?/;
  const durRe  = /(\d+\.\d+)s/;

  for (const line of lines) {
    const m = line.match(lineRe);
    if (!m) continue;

    const [, testPath, rawStatus] = m;
    const status = rawStatus.toLowerCase() as EvalResult['status'];
    const testName = testPath.split('::').slice(-1)[0] ?? testPath;

    const durMatch = line.match(durRe);
    const duration_ms = durMatch ? Math.round(parseFloat(durMatch[1]) * 1000) : 0;

    results.push({ target, test_name: testName, status, duration_ms, source: 'cli_contracts' });
  }

  // Synthetic error entry if nothing parsed
  if (results.length === 0) {
    results.push({
      target,
      test_name:   '(pytest parse error)',
      status:      'error',
      duration_ms: 0,
      error:       stdout.slice(0, 500),
      source:      'cli_contracts',
    });
  }

  return results;
}

/**
 * Append a JSON record to the eval log (JSON-lines format).
 */
function appendToLog(record: unknown): void {
  fs.mkdirSync(HOOKS_CACHE_DIR, { recursive: true });
  fs.appendFileSync(EVAL_LOG, JSON.stringify(record) + '\n', 'utf-8');
}

// ─── Activity 1: runCliContracts ──────────────────────────────────────────────

/**
 * Runs pytest on core/hooks/tests/test_hooks.py, optionally filtered by target.
 * Each target maps to a test class/function prefix (e.g. "pre_intent" → TestPreIntentHook).
 *
 * If targets is empty, runs the entire test suite.
 * Returns one EvalResult per test discovered.
 */
export async function runCliContracts(targets: string[]): Promise<EvalResult[]> {
  fs.mkdirSync(HOOKS_CACHE_DIR, { recursive: true });

  const kwFilter = targets.length > 0
    ? ['-k', targets.join(' or ')]
    : [];

  const t0 = Date.now();

  const result = spawnSync(
    'python3',
    [
      '-m', 'pytest',
      TEST_FILE,
      '--tb=short',
      '-v',
      '--no-header',
      ...kwFilter,
    ],
    {
      cwd:      REPO_ROOT,
      encoding: 'utf-8',
      timeout:  60_000,
    }
  );

  const elapsed = Date.now() - t0;

  const stdout   = result.stdout ?? '';
  const stderr   = result.stderr ?? '';
  const combined = stdout + (stderr ? '\n--- STDERR ---\n' + stderr : '');

  const allResults: EvalResult[] = targets.length > 0
    ? targets.flatMap(target => parsePytestOutput(combined, target))
    : parsePytestOutput(combined, 'all_hooks');

  appendToLog({
    event:        'cli_contracts_run',
    timestamp:    nowISO(),
    targets,
    exit_code:    result.status,
    elapsed_ms:   elapsed,
    result_count: allResults.length,
  });

  return allResults;
}

// ─── Activity 2: runEvalLabScenarios ─────────────────────────────────────────

/**
 * Runs eval-lab scenarios if the binary exists (Phase 5 feature).
 * Returns skipped results if eval-lab is not yet available.
 */
export async function runEvalLabScenarios(targets: string[]): Promise<EvalResult[]> {
  if (!fs.existsSync(EVAL_LAB_BIN)) {
    const skipped: EvalResult[] = (targets.length > 0 ? targets : ['(all)']).map(target => ({
      target,
      test_name:   'eval_lab_scenario',
      status:      'skipped' as const,
      duration_ms: 0,
      error:       `eval-lab not available at ${EVAL_LAB_BIN} — Phase 5 pending`,
      source:      'eval_lab' as const,
    }));

    appendToLog({
      event:     'eval_lab_skipped',
      timestamp: nowISO(),
      reason:    'Phase 5 not deployed',
    });

    return skipped;
  }

  const t0 = Date.now();

  const result = spawnSync(
    'python3',
    [EVAL_LAB_BIN, '--targets', JSON.stringify(targets), '--format', 'json'],
    {
      cwd:      REPO_ROOT,
      encoding: 'utf-8',
      timeout:  120_000,
    }
  );

  const elapsed = Date.now() - t0;

  let evalResults: EvalResult[] = [];
  try {
    const parsed = JSON.parse(result.stdout ?? '[]');
    evalResults = Array.isArray(parsed) ? parsed.map((r: Record<string, unknown>) => ({
      target:      String(r['target']   ?? 'unknown'),
      test_name:   String(r['name']     ?? 'eval_lab'),
      status:      (r['status'] as EvalResult['status']) ?? 'error',
      duration_ms: typeof r['duration_ms'] === 'number' ? r['duration_ms'] : elapsed,
      error:       r['error'] ? String(r['error']) : undefined,
      source:      'eval_lab' as const,
    })) : [];
  } catch {
    evalResults = [{
      target:      'eval_lab',
      test_name:   '(json parse error)',
      status:      'error',
      duration_ms: elapsed,
      error:       (result.stdout ?? '').slice(0, 500),
      source:      'eval_lab',
    }];
  }

  appendToLog({
    event:        'eval_lab_run',
    timestamp:    nowISO(),
    targets,
    exit_code:    result.status,
    elapsed_ms:   elapsed,
    result_count: evalResults.length,
  });

  return evalResults;
}

// ─── Activity 3: writeEvalResults ────────────────────────────────────────────

/**
 * Writes an Eval report:
 *   - Markdown table → Obsidian vault (OBSIDIAN_VAULT_PATH/HookReports/YYYY-MM-DD_eval_report.md)
 *   - JSON-lines summary → .cache/hooks/eval_results.log
 *
 * TODO(Phase 6): Neo4j — create (:eval_run) nodes linked to (:hook_run) via [:validated_by]
 */
export async function writeEvalResults(summary: EvalSummary): Promise<void> {
  const date = summary.timestamp.slice(0, 10);

  const passRate = summary.total > 0
    ? ((summary.passed / summary.total) * 100).toFixed(1)
    : '0.0';

  const statusEmoji: Record<string, string> = {
    passed:  '✅',
    failed:  '❌',
    error:   '🔴',
    skipped: '⏭️',
  };

  const tableRows = summary.results.map(r => {
    const emoji = statusEmoji[r.status] ?? '❓';
    const error = r.error ? `\`${r.error.replace(/`/g, "'").slice(0, 80)}\`` : '—';
    return `| ${r.target} | ${r.test_name} | ${emoji} ${r.status} | ${r.duration_ms} ms | ${r.source} | ${error} |`;
  }).join('\n');

  const markdown = `# Eval Report — ${date}

**Généré le :** ${summary.timestamp}

## Résumé

| Métrique         | Valeur |
|------------------|--------|
| Total            | ${summary.total} |
| ✅ Passés         | ${summary.passed} |
| ❌ Échoués        | ${summary.failed} |
| ⏭️ Ignorés        | ${summary.skipped} |
| Taux de réussite | **${passRate}%** |
| Tokens estimés   | ${summary.tokens_used} |

## Détail des tests

| Target | Test | Statut | Durée | Source | Erreur |
|--------|------|--------|-------|--------|--------|
${tableRows}

---
*TricorderKit Hook Layer v0.2.0 — auto-généré par skill_eval.activities.ts*
`;

  const vaultPath = process.env['OBSIDIAN_VAULT_PATH'];
  if (vaultPath) {
    const reportsDir = path.join(vaultPath, 'HookReports');
    const reportFile = path.join(reportsDir, `${date}_eval_report.md`);
    fs.mkdirSync(reportsDir, { recursive: true });
    fs.writeFileSync(reportFile, markdown, 'utf-8');
  }

  appendToLog({
    event:       'eval_summary',
    timestamp:   summary.timestamp,
    total:       summary.total,
    passed:      summary.passed,
    failed:      summary.failed,
    skipped:     summary.skipped,
    tokens_used: summary.tokens_used,
    pass_rate:   parseFloat(passRate),
  });
}
