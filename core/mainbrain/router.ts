/**
 * TricorderKit — MainBrain Router
 * Point d'entrée — Algorithme de décision v1.4 (10 étapes)
 *
 * Étapes :
 *  1. intent_router     → classifier l'intention
 *  2. skill_resolver    → skill documenté ?
 *  3. cli_resolver      → CLI déterministe ?
 *  4. workflow_resolver → workflow Temporal ?
 *  5. memory_resolver   → mémoire projet / vault ?
 *  6. risk_guard        → niveau de risque
 *  7. token_guard       → budget tokens
 *  8. executor          → action minimale
 *  9. reporter          → rapport Markdown court
 * 10. memory_writer     → mémoriser décisions utiles
 */

import type {
  Intent,
  IntentCategory,
  MainBrainInput,
  MainBrainOutput,
  MainBrainOptions,
  Resolution,
  ExecutionResult,
} from './types.js';

import { RiskGuard } from './guards/risk_guard.js';
import { TokenGuard } from './guards/token_guard.js';
import { ContextManager } from './memory/context_manager.js';

// ─── Intent Routing Map ───────────────────────────────────────────────────

const COMMAND_CATEGORY_MAP: Record<string, IntentCategory> = {
  '/tk:boot':           'boot',
  '/tk:status':         'status',
  '/tk:plan':           'plan',
  '/tk:audit-skills':   'skill',
  '/tk:eval-skill':     'skill',
  '/tk:cli-forge':      'cli',
  '/tk:cli-audit':      'cli',
  '/tk:workflow-start': 'workflow',
  '/tk:workflow-status':'workflow',
  '/tk:deep-research':  'research',
  '/tk:vault-audit':    'vault',
  '/tk:security-scan':  'security',
  '/tk:pack-context':   'memory',
  '/tk:token-hygiene':  'memory',
  '/tk:report':         'report',
  '/tk:health':         'status',
  '/tk:dry-run':        'unknown',
  '/tk:changelog':      'report',
};

// ─── Known Registries (stub — à brancher sur cli-forge/registry.yml) ─────

const KNOWN_SKILLS    = ['tk-boot', 'skill-creator', 'skill-manager', 'consolidate-memory'];
const KNOWN_CLIS      = ['cli-forge', 'mangatracker'];
const KNOWN_WORKFLOWS = ['daily-report', 'vault-sync', 'deep-research'];

// ─── MainBrain ────────────────────────────────────────────────────────────

export class MainBrain {
  private options: Required<MainBrainOptions>;
  private riskGuard: RiskGuard;
  private tokenGuard: TokenGuard;
  private contextManager: ContextManager;

  constructor(options: MainBrainOptions) {
    this.options = {
      dryRun: options.dryRun,
      maxRiskLevel: options.maxRiskLevel ?? 'HIGH',
      tokenBudgetThreshold: options.tokenBudgetThreshold ?? 80,
      planningDir: options.planningDir ?? '.planning',
    };
    this.riskGuard      = new RiskGuard(this.options.maxRiskLevel);
    this.tokenGuard     = new TokenGuard(this.options.tokenBudgetThreshold);
    this.contextManager = new ContextManager(this.options.planningDir);
  }

  async process(input: MainBrainInput): Promise<MainBrainOutput> {
    const start = Date.now();

    // ── Étape 1 : Intent Router ──────────────────────────────────────────
    const intent = this.routeIntent(input);

    // ── Étape 2-4 : Resolvers ────────────────────────────────────────────
    const resolution = this.resolve(intent);

    // ── Étape 5 : Memory Resolver ────────────────────────────────────────
    const hasMemory = this.contextManager.hasRelevantMemory(intent.command);
    if (hasMemory && resolution.type === 'unknown') {
      resolution.type = 'memory';
      resolution.found = true;
    }

    // ── Étape 6 : Risk Guard ─────────────────────────────────────────────
    const risk = this.riskGuard.assess(intent);

    // ── Étape 7 : Token Guard ────────────────────────────────────────────
    const tokens = this.tokenGuard.estimate(intent);

    // ── Étape 8 : Executor ───────────────────────────────────────────────
    let result: ExecutionResult;

    if (this.options.dryRun) {
      result = this.dryRunResult(intent, resolution, risk, tokens.estimated_input);
    } else if (this.riskGuard.isBlocked(risk)) {
      result = this.blockedResult(intent, risk);
    } else if (!tokens.budget_ok) {
      result = this.tokenBlockedResult(tokens.recommendation ?? '');
    } else {
      result = await this.execute(intent, resolution);
    }

    // ── Étape 9 : Reporter (ajout next_steps si vide) ────────────────────
    if (result.next_steps.length === 0) {
      result.next_steps = this.defaultNextSteps(intent.category);
    }

    // ── Étape 10 : Memory Writer ─────────────────────────────────────────
    if (!this.options.dryRun) {
      this.contextManager.persistResult(intent.command, result, risk);
    }

    return {
      intent,
      resolution,
      risk,
      tokens,
      result,
      dry_run: this.options.dryRun,
      duration_ms: Date.now() - start,
      timestamp: new Date().toISOString(),
    };
  }

  // ── Étape 1 : Classifier l'intention ─────────────────────────────────

  private routeIntent(input: MainBrainInput): Intent {
    const command = input.command.trim().toLowerCase();
    const category: IntentCategory = COMMAND_CATEGORY_MAP[command] ?? 'unknown';
    return {
      raw: input.command,
      command,
      args: input.args,
      category,
      context: input.context,
    };
  }

  // ── Étapes 2-4 : Resolvers ────────────────────────────────────────────

  private resolve(intent: Intent): Resolution {
    const name = intent.command.replace('/tk:', '');

    const matchingSkill = KNOWN_SKILLS.find((s) => s.includes(name) || name.includes(s));
    if (matchingSkill) {
      return { type: 'skill', name: matchingSkill, path: `skills/${matchingSkill}/SKILL.md`, found: true };
    }

    const matchingCli = KNOWN_CLIS.find((c) => name.includes(c));
    if (matchingCli) {
      return { type: 'cli', name: matchingCli, path: `plugins/cli-forge/registry.yml`, found: true };
    }

    const matchingWorkflow = KNOWN_WORKFLOWS.find((w) => name.includes(w));
    if (matchingWorkflow) {
      return { type: 'workflow', name: matchingWorkflow, path: `plugins/workflow-engine/workflows/${matchingWorkflow}.ts`, found: true };
    }

    return { type: 'unknown', name: null, path: null, found: false };
  }

  // ── Étape 8 : Execute (stub — à implémenter par chaque skill/CLI) ─────

  private async execute(intent: Intent, resolution: Resolution): Promise<ExecutionResult> {
    // Stub d'exécution — chaque skill/CLI/workflow implémente son propre executor
    // Ce switch sera remplacé par un dynamic import depuis le registre
    switch (intent.category) {
      case 'boot':
        return {
          status: 'success',
          summary: 'Boot MainBrain v1.4 — état chargé',
          data: { resolution_type: resolution.type, resolution_found: resolution.found },
          files_created: [],
          decisions_logged: [],
          risks_logged: [],
          next_steps: [],
        };
      default:
        return {
          status: 'partial',
          summary: `Intent "${intent.command}" reçu — executor non encore implémenté pour cette catégorie (${intent.category})`,
          data: { resolution },
          files_created: [],
          decisions_logged: [],
          risks_logged: [],
          next_steps: [`Implémenter l'executor pour la catégorie : ${intent.category}`],
        };
    }
  }

  // ── Résultats spéciaux ────────────────────────────────────────────────

  private dryRunResult(
    intent: Intent,
    resolution: Resolution,
    risk: { level: string; reasons: string[] },
    estimatedTokens: number
  ): ExecutionResult {
    return {
      status: 'dry_run',
      summary: `[DRY RUN] Commande : ${intent.command} | Résolution : ${resolution.type} | Risque : ${risk.level} | ~${estimatedTokens} tokens`,
      data: { intent, resolution, risk },
      files_created: [],
      decisions_logged: [],
      risks_logged: [],
      next_steps: ['Relancer sans --dry-run pour exécuter'],
    };
  }

  private blockedResult(
    intent: Intent,
    risk: { level: string; reasons: string[] }
  ): ExecutionResult {
    return {
      status: 'blocked',
      summary: `BLOQUÉ — Niveau de risque ${risk.level} dépasse le seuil autorisé`,
      data: { command: intent.command, reasons: risk.reasons },
      files_created: [],
      decisions_logged: [],
      risks_logged: [],
      next_steps: ['Confirmer explicitement l\'action ou ajuster maxRiskLevel'],
      error: {
        code: 'RISK_BLOCKED',
        message: `Risque ${risk.level} — ${risk.reasons.join('; ')}`,
        recoverable: true,
      },
    };
  }

  private tokenBlockedResult(recommendation: string): ExecutionResult {
    return {
      status: 'blocked',
      summary: 'BLOQUÉ — Budget tokens insuffisant',
      data: { recommendation },
      files_created: [],
      decisions_logged: [],
      risks_logged: [],
      next_steps: [recommendation],
      error: {
        code: 'TOKEN_BUDGET_EXCEEDED',
        message: recommendation,
        recoverable: true,
      },
    };
  }

  // ── Defaults ─────────────────────────────────────────────────────────

  private defaultNextSteps(category: IntentCategory): string[] {
    const map: Partial<Record<IntentCategory, string[]>> = {
      boot:     ['Vérifier .planning/TASKS.md', 'Lancer /tk:status'],
      status:   ['Consulter .planning/STATE.md'],
      skill:    ['Lancer /tk:audit-skills pour valider le registre'],
      cli:      ['Vérifier plugins/cli-forge/registry.yml'],
      workflow: ['Vérifier plugins/workflow-engine/workflows/'],
      research: ['Consulter le rapport généré dans vault/'],
      unknown:  ['Préciser la commande ou consulter AGENTS.md'],
    };
    return map[category] ?? [];
  }
}
