/**
 * self_improving.activities.ts — Activities Temporal pour les workflows
 * d'auto-amelioration (TricorderKit, DEC-046 / N7).
 *
 * Principe (corrige par le plan v1.0) : la collecte / veille est DEPORTEE vers
 * Antigravity / Hermes via canal_agents — ces activities ne scrappent pas. Elles :
 *   1. deposent une requete de dispatch (dispatchVeilleTask) que l'executeur
 *      externe consomme (execution deportee, DEC-029) ;
 *   2. consolident cote Claude/CLI en deleguant aux scripts Python existants
 *      (learning-engine, source_reliability_engine) — jamais d'ecriture vault
 *      directe, dry-run par defaut.
 *
 * Ce module expose son PROPRE type `SelfImprovingActivities` et n'est pas cable
 * dans le worker en production (activities/index.ts) : l'activation est une etape
 * controlee (garde HIGH au moment des promotions). Voir SELF_IMPROVING.md.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as child_process from 'child_process';

// ── Chemins ───────────────────────────────────────────────────────────────────
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..');
const PYTHON = process.env['PYTHON'] || 'python';
const HOOKS_CACHE_DIR = path.join(REPO_ROOT, '.cache', 'hooks');
// Repertoire de dispatch vers les executeurs externes (Antigravity/Hermes).
// Configurable (machine-specifique) : jamais de chemin perso en dur.
const DISPATCH_DIR = process.env['CANAL_AGENTS_DIR']
  || path.join(REPO_ROOT, '.cache', 'canal_dispatch');

const LEARNING = path.join(REPO_ROOT, 'plugins', 'learning-engine', 'scripts');
const RELIABILITY = path.join(REPO_ROOT, 'plugins', 'scraper-runtime', 'scripts',
  'source_reliability_engine.py');

// ── Helpers ───────────────────────────────────────────────────────────────────
interface RunResult { success: boolean; stdout: string; stderr: string; exitCode: number; }

function runPython(args: string[]): RunResult {
  try {
    const env = { ...process.env, PYTHONUTF8: '1' };
    const r = child_process.spawnSync(PYTHON, args, {
      encoding: 'utf8', timeout: 120_000, cwd: REPO_ROOT, env,
    });
    return { success: r.status === 0, stdout: r.stdout ?? '', stderr: r.stderr ?? '', exitCode: r.status ?? 1 };
  } catch (err: any) {
    return { success: false, stdout: '', stderr: String(err), exitCode: 1 };
  }
}

function ensureDir(dir: string): void {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function appendJsonLine(file: string, record: object): void {
  ensureDir(path.dirname(file));
  fs.appendFileSync(file, JSON.stringify(record) + '\n', 'utf8');
}

function parseSkillOutput(stdout: string): any {
  try { return JSON.parse(stdout); } catch { return null; }
}


// ── Types partages ────────────────────────────────────────────────────────────
export interface DispatchInput {
  kind: 'tool_scout' | 'source_rescrape' | 'freshness_probe';
  payload: Record<string, unknown>;
  requested_by: string;        // ex: 'temporal/tool_scout'
}

export interface DispatchResult {
  request_id: string;
  path: string;
  dispatched_at: string;
}

export interface CompareInput { task_type: string; cards_dir?: string; }
export interface LessonsInput { task_type: string; min_confidence?: number; }
export interface ProposeInput { lesson_id: string; skill_name: string; }
export interface RegressionInput { skill_name: string; tests_path: string; }
export interface RegressionResult { passed: number; failed: number; gate_ok: boolean; detail: string; }
export interface ScoreSourcesInput { observations_path: string; registry?: string; }
export interface PromoteInput { skill_name: string; approved: boolean; gate_ok: boolean; live?: boolean; }
export interface CycleLogInput { workflow: string; summary: object; }

// ── Activity : dispatch vers executeur externe (deporte) ──────────────────────
export async function dispatchVeilleTask(input: DispatchInput): Promise<DispatchResult> {
  ensureDir(DISPATCH_DIR);
  const ts = new Date().toISOString();
  const request_id = `${input.kind}_${ts.replace(/[:.]/g, '-')}`;
  const file = path.join(DISPATCH_DIR, `${request_id}.json`);
  const request = {
    request_id, kind: input.kind, payload: input.payload,
    requested_by: input.requested_by, status: 'pending', dispatched_at: ts,
  };
  fs.writeFileSync(file, JSON.stringify(request, null, 2), 'utf8');
  console.log(`[dispatchVeilleTask] requete deposee : ${file}`);
  return { request_id, path: file, dispatched_at: ts };
}

// ── Activity : comparer les strategies (consolidation Claude/CLI) ─────────────
export async function compareStrategies(input: CompareInput): Promise<any> {
  const args = [path.join(LEARNING, 'compare_strategies.py'), '--task-type', input.task_type];
  if (input.cards_dir) args.push('--cards-dir', input.cards_dir);
  const r = runPython(args);
  return parseSkillOutput(r.stdout) ?? { status: 'error', stderr: r.stderr.slice(0, 300) };
}

// ── Activity : extraire les lecons ────────────────────────────────────────────
export async function extractLessons(input: LessonsInput): Promise<any> {
  const args = [path.join(LEARNING, 'extract_lessons.py'), '--task-type', input.task_type];
  if (input.min_confidence != null) args.push('--min-confidence', String(input.min_confidence));
  const r = runPython(args);
  return parseSkillOutput(r.stdout) ?? { status: 'error', stderr: r.stderr.slice(0, 300) };
}

// ── Activity : proposer une mise a jour de skill (draft seulement) ────────────
export async function proposeSkillUpdate(input: ProposeInput): Promise<any> {
  const r = runPython([
    path.join(LEARNING, 'propose_skill_update.py'),
    '--lesson-id', input.lesson_id, '--skill-name', input.skill_name,
  ]);
  return parseSkillOutput(r.stdout) ?? { status: 'error', stderr: r.stderr.slice(0, 300) };
}


// ── Activity : test de regression skill (gate des 8 tests) ────────────────────
export async function runSkillRegression(input: RegressionInput): Promise<RegressionResult> {
  // basetemp HORS du repo (R36) : evite le verrou Windows de .pytest_tmp qui
  // ferait echouer le gate par erreur d'environnement plutot que par un vrai FAIL.
  const basetemp = path.join(os.tmpdir(), `tk_gate_${Date.now()}`);
  const r = runPython(['-m', 'pytest', input.tests_path, '-q', '--no-header',
                       '-p', 'no:cacheprovider', '--basetemp', basetemp]);
  try { fs.rmSync(basetemp, { recursive: true, force: true }); } catch { /* best-effort */ }
  const blob = r.stdout + r.stderr;
  const mp = blob.match(/(\d+)\s+passed/);
  const mf = blob.match(/(\d+)\s+failed/);
  const passed = mp ? parseInt(mp[1], 10) : 0;
  const failed = mf ? parseInt(mf[1], 10) : 0;
  // Gate : au moins 8 tests verts ET aucun echec (cf. plan §16.4).
  const gate_ok = r.success && failed === 0 && passed >= 8;
  return { passed, failed, gate_ok, detail: blob.slice(-300) };
}

// ── Activity : scorer les sources (N6, dry-run strict) ────────────────────────
export async function scoreSources(input: ScoreSourcesInput): Promise<any> {
  const args = [RELIABILITY, '--input', input.observations_path];
  if (input.registry) args.push('--registry', input.registry);
  const r = runPython(args);
  return parseSkillOutput(r.stdout) ?? { status: 'error', stderr: r.stderr.slice(0, 300) };
}

// ── Activity : promotion de skill (gardee) ────────────────────────────────────
export async function promoteSkill(input: PromoteInput): Promise<any> {
  // Garde-fou : jamais de promotion sans approbation humaine ET gate vert.
  if (!input.approved || !input.gate_ok) {
    return { status: 'refused', reason: 'approbation humaine + gate des tests requis' };
  }
  const args = [path.join(LEARNING, 'promote_skill.py'), '--skill-name', input.skill_name];
  if (input.live) args.push('--apply');   // sinon dry-run par defaut
  const r = runPython(args);
  return parseSkillOutput(r.stdout) ?? { status: 'error', stderr: r.stderr.slice(0, 300) };
}

// ── Activity : log d'un cycle d'auto-amelioration ─────────────────────────────
export async function logSelfImprovingCycle(input: CycleLogInput): Promise<void> {
  appendJsonLine(path.join(HOOKS_CACHE_DIR, 'self_improving_cycles.log'), {
    event: 'self_improving_cycle', workflow: input.workflow,
    summary: input.summary, timestamp: new Date().toISOString(),
  });
}

// ── Type Activities (pour proxyActivities dans les workflows) ─────────────────
export type SelfImprovingActivities = {
  dispatchVeilleTask: typeof dispatchVeilleTask;
  compareStrategies: typeof compareStrategies;
  extractLessons: typeof extractLessons;
  proposeSkillUpdate: typeof proposeSkillUpdate;
  runSkillRegression: typeof runSkillRegression;
  scoreSources: typeof scoreSources;
  promoteSkill: typeof promoteSkill;
  logSelfImprovingCycle: typeof logSelfImprovingCycle;
};
