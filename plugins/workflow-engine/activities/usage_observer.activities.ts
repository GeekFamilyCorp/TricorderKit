/**
 * usage_observer.activities.ts — Activities Temporal pour observer l'usage des skills/goats.
 * Version : 0.1.0
 *
 * Implémente les 3 activities consommées par usage_observer.workflow.ts :
 *   - readHookLogs()       : lit .cache/hooks/*.log (JSON-lines) depuis le dernier checkpoint
 *   - aggregateStats()     : agrège par skill_or_goat (runs, failures, avg_tokens, latency)
 *   - writeUsageStats()    : écrit un rapport Markdown dans Obsidian + optionnellement Neo4j
 *
 * Conventions TricorderKit :
 *   - CLI-first : toute écriture externe passe par des appels directs aux fichiers locaux.
 *     L'intégration Neo4j se fait via graphify (graph-server MCP) — stub fourni.
 *   - Pas de side-effects destructifs.
 *   - Log JSON-lines dans .cache/hooks/usage_stats.log.
 */

import * as fs   from 'fs';
import * as path from 'path';
import * as readline from 'readline';

// ---------------------------------------------------------------------------
// Chemins
// ---------------------------------------------------------------------------

const REPO_ROOT       = path.resolve(__dirname, '..', '..', '..');
const HOOKS_CACHE_DIR = path.join(REPO_ROOT, '.cache', 'hooks');
const PRE_LOG         = path.join(HOOKS_CACHE_DIR, 'pre_execution.log');
const POST_LOG        = path.join(HOOKS_CACHE_DIR, 'post_execution.log');
const CHECKPOINT_FILE = path.join(HOOKS_CACHE_DIR, 'checkpoint.json');
const STATS_LOG       = path.join(HOOKS_CACHE_DIR, 'usage_stats.log');

// Dossier Obsidian pour les rapports (relatif à la racine repo — configurable)
const OBSIDIAN_REPORT_DIR = path.join(
  process.env.OBSIDIAN_VAULT_PATH ?? path.join(REPO_ROOT, '.cache', 'reports'),
  'HookReports',
);

// ---------------------------------------------------------------------------
// Types internes
// ---------------------------------------------------------------------------

interface HookLogRecord {
  hook_run_id: string | null;
  timestamp: string;
  plan?: Record<string, any>;
  result?: Record<string, any>;
  quality_score?: number | null;
  tokens_used?: number | null;
  plan_risk_hint?: string | null;
  result_keys?: string[];
}

interface Checkpoint {
  pre_offset:  number;
  post_offset: number;
  last_run:    string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function readJsonLines(filePath: string, fromByte: number): Promise<{ records: HookLogRecord[]; newOffset: number }> {
  if (!fs.existsSync(filePath)) {
    return { records: [], newOffset: 0 };
  }

  const stat = fs.statSync(filePath);
  if (stat.size <= fromByte) {
    return { records: [], newOffset: fromByte };
  }

  const stream = fs.createReadStream(filePath, { start: fromByte });
  const rl     = readline.createInterface({ input: stream, crlfDelay: Infinity });

  const records: HookLogRecord[] = [];
  for await (const line of rl) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try {
      records.push(JSON.parse(trimmed));
    } catch {
      // Ligne corrompue → ignorer
    }
  }

  return { records, newOffset: stat.size };
}

function loadCheckpoint(): Checkpoint {
  if (fs.existsSync(CHECKPOINT_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(CHECKPOINT_FILE, 'utf8'));
    } catch { /* checkpoint corrompu → reset */ }
  }
  return { pre_offset: 0, post_offset: 0, last_run: new Date(0).toISOString() };
}

function saveCheckpoint(cp: Checkpoint): void {
  fs.mkdirSync(HOOKS_CACHE_DIR, { recursive: true });
  fs.writeFileSync(CHECKPOINT_FILE, JSON.stringify(cp, null, 2), 'utf8');
}

function extractSkillOrGoat(record: HookLogRecord): string {
  const plan = record.plan ?? {};
  return (
    plan.skill    ??
    plan.goat     ??
    plan.workflow ??
    'unknown'
  );
}

// ---------------------------------------------------------------------------
// Activity 1 : readHookLogs
// Lit les logs depuis le dernier checkpoint. Retourne les enregistrements bruts.
// ---------------------------------------------------------------------------

export async function readHookLogs(): Promise<Record<string, any>[]> {
  const cp = loadCheckpoint();

  const { records: preRecs,  newOffset: newPre  } = await readJsonLines(PRE_LOG,  cp.pre_offset);
  const { records: postRecs, newOffset: newPost } = await readJsonLines(POST_LOG, cp.post_offset);

  saveCheckpoint({
    pre_offset:  newPre,
    post_offset: newPost,
    last_run:    new Date().toISOString(),
  });

  // On fusionne pre + post — le workflow les agrège par hook_run_id
  return [...preRecs, ...postRecs] as Record<string, any>[];
}

// ---------------------------------------------------------------------------
// Activity 2 : aggregateStats
// Agrège les enregistrements bruts en UsageStats[] par skill_or_goat.
// ---------------------------------------------------------------------------

export async function aggregateStats(
  records: Record<string, any>[],
): Promise<Record<string, any>[]> {

  interface Accumulator {
    skill_or_goat: string;
    runs:          number;
    failures:      number;
    total_tokens:  number;
    token_count:   number;
    timestamps:    number[];   // epoch ms, pour latence inter-run
    last_seen:     string | null;
  }

  const map = new Map<string, Accumulator>();

  for (const rec of records as HookLogRecord[]) {
    const key = extractSkillOrGoat(rec);
    if (!map.has(key)) {
      map.set(key, {
        skill_or_goat: key, runs: 0, failures: 0,
        total_tokens: 0, token_count: 0,
        timestamps: [], last_seen: null,
      });
    }
    const acc = map.get(key)!;

    // Compter uniquement les enregistrements POST (qui ont quality_score)
    if ('quality_score' in rec && rec.quality_score !== undefined) {
      acc.runs++;
      if (rec.quality_score !== null && rec.quality_score < 0.5) acc.failures++;
      if (rec.tokens_used != null && rec.tokens_used > 0) {
        acc.total_tokens += rec.tokens_used;
        acc.token_count++;
      }
      if (rec.timestamp) {
        const ts = new Date(rec.timestamp).getTime();
        if (!isNaN(ts)) acc.timestamps.push(ts);
        acc.last_seen = rec.timestamp;
      }
    }
  }

  return Array.from(map.values()).map(acc => {
    const failure_rate = acc.runs > 0 ? +(acc.failures / acc.runs).toFixed(4) : 0;
    const avg_tokens   = acc.token_count > 0
      ? Math.round(acc.total_tokens / acc.token_count)
      : null;

    // Latence moyenne : écart entre les runs consécutifs
    let avg_latency_ms: number | null = null;
    if (acc.timestamps.length >= 2) {
      const sorted = acc.timestamps.slice().sort((a, b) => a - b);
      const diffs  = sorted.slice(1).map((t, i) => t - sorted[i]);
      avg_latency_ms = Math.round(diffs.reduce((a, b) => a + b, 0) / diffs.length);
    }

    return {
      skill_or_goat: acc.skill_or_goat,
      runs:           acc.runs,
      failures:       acc.failures,
      failure_rate,
      avg_tokens,
      avg_latency_ms,
      last_seen:      acc.last_seen,
    };
  });
}

// ---------------------------------------------------------------------------
// Activity 3 : writeUsageStats
// Écrit un rapport Markdown + log JSON-lines + optionnellement Neo4j.
// ---------------------------------------------------------------------------

export async function writeUsageStats(stats: Record<string, any>[]): Promise<void> {
  const now    = new Date().toISOString();
  const date   = now.slice(0, 10);

  // ── Rapport Markdown ──────────────────────────────────────────────────────
  const rows = stats
    .sort((a, b) => (b.runs ?? 0) - (a.runs ?? 0))
    .map(s => {
      const rate = s.failure_rate != null ? `${(s.failure_rate * 100).toFixed(1)}%` : '—';
      const tok  = s.avg_tokens   != null ? `${s.avg_tokens}` : '—';
      const lat  = s.avg_latency_ms != null ? `${(s.avg_latency_ms / 1000).toFixed(1)}s` : '—';
      return `| ${s.skill_or_goat} | ${s.runs ?? 0} | ${s.failures ?? 0} | ${rate} | ${tok} | ${lat} | ${s.last_seen ?? '—'} |`;
    })
    .join('\n');

  const report = `---
type: usage-stats
tags: [#hook-layer, #usage-observer, #auto-amélioration]
generated: ${now}
---

# Usage Stats — Hook Layer — ${date}

| Skill / Goat | Runs | Failures | Failure Rate | Avg Tokens | Avg Latency | Last Seen |
|---|---|---|---|---|---|---|
${rows || '| — | — | — | — | — | — | — |'}

> Généré par \`usage_observer.workflow.ts\` — TricorderKit v0.8
`;

  fs.mkdirSync(OBSIDIAN_REPORT_DIR, { recursive: true });
  const reportPath = path.join(OBSIDIAN_REPORT_DIR, `${date}_usage_stats.md`);
  fs.writeFileSync(reportPath, report, 'utf8');

  // ── Log JSON-lines (STATS_LOG) ─────────────────────────────────────────────
  const logRecord = { timestamp: now, stats_count: stats.length, report_path: reportPath };
  fs.appendFileSync(STATS_LOG, JSON.stringify(logRecord) + '\n', 'utf8');

  // ── Neo4j via graphify (stub) ──────────────────────────────────────────────
  // TODO : appeler le graph-server MCP pour créer des nœuds usage_stat
  // Exemple :
  //   await graphify_store({ id: `usage_stat_${date}`, type: 'usage_stat', title: `Usage ${date}`, properties: { stats } })
  // Actuellement non disponible depuis un worker Temporal — à router via une activity dédiée
  // ou via l'orchestrateur LLM.
}
