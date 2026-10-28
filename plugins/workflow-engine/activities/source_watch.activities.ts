/**
 * source_watch.activities.ts — Activities Temporal pour source_watch.workflow.ts
 * TricorderKit v0.9 — M5 Temporal wiring
 *
 * Implémente les 6 activities consommées par source_watch.workflow.ts :
 *   - scanSource()            → connector_hub.py dispatch --source <nom>
 *   - deduplicateItems()      → deduplicate_findings.py
 *   - writeMarkdownReport()   → écrit un rapport .md dans vault/reports/
 *   - updateObsidianVault()   → obsidian_goat.py (ou écriture directe)
 *   - notifyBudgetExceeded()  → log dans .cache/hooks/budget_alerts.log
 *   - logWorkflowCycle()      → log dans .cache/hooks/workflow_cycles.log
 *
 * Architecture : une seule activity de scan, générique, délègue à
 * connector_hub.py via subprocess Python. Le connector_hub gère le routage
 * (trusted_sources.yml pour les sources core, bloc `dispatch:` du
 * sources.yaml pour les sources d'un linked_project) : aucune source
 * n'est câblée en dur ici.
 */

import * as fs        from 'fs';
import * as path      from 'path';
import * as child_process from 'child_process';

// ── Chemins ───────────────────────────────────────────────────────────────────

const REPO_ROOT       = path.resolve(__dirname, '..', '..', '..');
const HOOKS_CACHE_DIR = path.join(REPO_ROOT, '.cache', 'hooks');
const CONNECTOR_HUB   = path.join(REPO_ROOT, 'plugins', 'connector-hub', 'connector_hub.py');
const DEDUP_SCRIPT    = path.join(REPO_ROOT, 'plugins', 'deep-research-core', 'scripts', 'deduplicate_findings.py');
const PYTHON          = process.env['PYTHON'] || 'python';

// ── Helper : run Python subprocess ───────────────────────────────────────────

interface RunResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exitCode: number;
}

function runPython(args: string[], cwd?: string): RunResult {
  try {
    const env = { ...process.env, PYTHONUTF8: '1' };
    const result = child_process.spawnSync(PYTHON, args, {
      encoding: 'utf8',
      timeout: 60_000,
      cwd: cwd ?? REPO_ROOT,
      env,
    });
    return {
      success: result.status === 0,
      stdout:  result.stdout ?? '',
      stderr:  result.stderr ?? '',
      exitCode: result.status ?? 1,
    };
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

// ── Types partagés ────────────────────────────────────────────────────────────

export interface ScanFilters {
  query?: string;         // requête de veille (sources core) → --query
  min_score?: number;
  languages?: string[];
  topics?: string[];
}

export interface ScanSourceInput {
  source: string;         // id, nom, type ou domaine du registre connector_hub
  filters: ScanFilters;
}

export interface ScanResult {
  source: string;
  items: object[];
  total: number;
  status: string;
  error?: string;
}

export interface DeduplicateInput {
  items: object[];
  vault_path: string;
}

export interface DeduplicateResult {
  newItems: object[];
  tokensUsed: number;
  deduplicated: number;
}

export interface ReportInput {
  items: object[];
  cycle: number;
  vault_path: string;
}

export interface VaultUpdateInput {
  items: object[];
  vault_path: string;
  report_path: string;
}

export interface BudgetAlertInput {
  workflow: string;
  tokens_used: number;
}

export interface CycleLogInput {
  workflow: string;
  cycle: object;
}

// ── Activities : scan via connector_hub ───────────────────────────────────────

/**
 * Arguments connector_hub pour une source donnée (exporté pour les tests).
 * Dry-run par défaut ; TEMPORAL_DISPATCH_LIVE=1 active l'appel réel.
 */
export function buildScanArgs(input: ScanSourceInput, live: boolean): string[] {
  const args = [CONNECTOR_HUB, 'dispatch', '--source', input.source, '--format', 'json'];
  const query = input.filters?.query;
  if (query) args.push('--query', query);
  if (!live) args.push('--dry-run');
  return args;
}

/**
 * Déclenche la collecte d'une source via connector_hub.py dispatch.
 * Retourne les résultats (JSON) ou [] si erreur.
 */
export async function scanSource(input: ScanSourceInput): Promise<object[]> {
  const live = process.env['TEMPORAL_DISPATCH_LIVE'] === '1';
  const r = runPython(buildScanArgs(input, live));

  if (!r.success) {
    console.warn(`[scanSource:${input.source}] connector_hub erreur:`, r.stderr.slice(0, 300));
    return [];
  }
  try {
    const data = JSON.parse(r.stdout);
    if (data?.error) {
      console.warn(`[scanSource:${input.source}]`, data.error);
      return [];
    }
    const items: object[] = data?.output?.results ?? data?.results ?? [];
    console.log(`[scanSource:${input.source}] ${items.length} résultats`);
    return items;
  } catch {
    return [];
  }
}

// ── Activity : déduplication ──────────────────────────────────────────────────

/**
 * Déduplique les items via deduplicate_findings.py.
 * Retourne les items nouveaux + estimation de tokens consommés.
 */
export async function deduplicateItems(input: DeduplicateInput): Promise<DeduplicateResult> {
  const { items } = input;
  if (!items.length) {
    return { newItems: [], tokensUsed: 0, deduplicated: 0 };
  }

  // Écriture fichier tmp
  const tmpFile = path.join(HOOKS_CACHE_DIR, `dedup_tmp_${Date.now()}.json`);
  ensureDir(HOOKS_CACHE_DIR);
  fs.writeFileSync(tmpFile, JSON.stringify(items), 'utf8');

  try {
    const r = runPython([DEDUP_SCRIPT, '--input', tmpFile, '--output', 'json']);
    if (r.success) {
      const deduped = JSON.parse(r.stdout);
      const newItems = Array.isArray(deduped) ? deduped : items;
      return {
        newItems,
        tokensUsed: Math.ceil(JSON.stringify(newItems).length * 1.3 / 4),
        deduplicated: items.length - newItems.length,
      };
    }
  } finally {
    if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile);
  }

  // Fallback : tous les items sont considérés nouveaux
  return {
    newItems: items,
    tokensUsed: Math.ceil(JSON.stringify(items).length * 1.3 / 4),
    deduplicated: 0,
  };
}

// ── Activity : rapport Markdown ───────────────────────────────────────────────

/**
 * Génère un rapport Markdown des nouveaux items dans vault/reports/.
 * Retourne le chemin du rapport créé.
 */
export async function writeMarkdownReport(input: ReportInput): Promise<string> {
  const { items, cycle, vault_path } = input;
  const ts   = new Date().toISOString().slice(0, 19).replace('T', '_').replace(/:/g, '-');
  const dir  = path.join(vault_path, 'reports');
  const file = path.join(dir, `source_watch_cycle${cycle}_${ts}.md`);

  ensureDir(dir);

  const lines = [
    `---`,
    `type: source_watch_report`,
    `cycle: ${cycle}`,
    `date: ${new Date().toISOString().slice(0, 10)}`,
    `items_count: ${items.length}`,
    `generated_by: temporal/source_watch`,
    `---`,
    `# Source Watch — Cycle ${cycle}`,
    ``,
    `> Généré automatiquement le ${new Date().toLocaleString('fr-FR')}`,
    ``,
    `## Nouveaux éléments (${items.length})`,
    ``,
    ...items.slice(0, 20).map((item: any, i) => {
      const title = item.title ?? item.name ?? `Item ${i + 1}`;
      const src   = item.source ?? '?';
      const url   = item.url ?? item.source_url ?? '';
      return `${i + 1}. **${title}** (${src})${url ? ` — [lien](${url})` : ''}`;
    }),
    items.length > 20 ? `\n_...et ${items.length - 20} autres._` : '',
  ].join('\n');

  fs.writeFileSync(file, lines, 'utf8');
  console.log(`[writeMarkdownReport] Rapport écrit : ${file}`);
  return file;
}

// ── Activity : mise à jour vault ──────────────────────────────────────────────

/**
 * Copie le rapport dans le vault Obsidian actif.
 * Si obsidian_goat est disponible, l'utilise ; sinon copie directement.
 */
export async function updateObsidianVault(input: VaultUpdateInput): Promise<void> {
  const { report_path, vault_path } = input;

  if (!fs.existsSync(report_path)) {
    console.warn('[updateObsidianVault] Rapport introuvable:', report_path);
    return;
  }

  const targetDir = path.join(vault_path, '10_INBOX', 'source_watch');
  ensureDir(targetDir);
  const target = path.join(targetDir, path.basename(report_path));

  try {
    fs.copyFileSync(report_path, target);
    console.log(`[updateObsidianVault] Note copiée dans vault : ${target}`);
  } catch (err) {
    console.warn('[updateObsidianVault] Copie échouée:', String(err));
  }
}

// ── Activity : alerte budget ──────────────────────────────────────────────────

/**
 * Log une alerte budget dépassé dans .cache/hooks/budget_alerts.log.
 */
export async function notifyBudgetExceeded(input: BudgetAlertInput): Promise<void> {
  const record = {
    event: 'budget_exceeded',
    workflow: input.workflow,
    tokens_used: input.tokens_used,
    timestamp: new Date().toISOString(),
  };
  appendJsonLine(path.join(HOOKS_CACHE_DIR, 'budget_alerts.log'), record);
  console.warn('[notifyBudgetExceeded] Budget dépassé :', record);
}

// ── Activity : log cycle ──────────────────────────────────────────────────────

/**
 * Log un cycle de workflow dans .cache/hooks/workflow_cycles.log.
 */
export async function logWorkflowCycle(input: CycleLogInput): Promise<void> {
  const record = {
    event: 'workflow_cycle',
    workflow: input.workflow,
    cycle: input.cycle,
    timestamp: new Date().toISOString(),
  };
  appendJsonLine(path.join(HOOKS_CACHE_DIR, 'workflow_cycles.log'), record);
  console.log('[logWorkflowCycle] Cycle loggé :', (input.cycle as any).cycle_number);
}
