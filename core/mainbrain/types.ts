/**
 * TricorderKit — MainBrain Types
 * Version : 1.4
 */

// ─── Intent ───────────────────────────────────────────────────────────────

export type IntentCategory =
  | 'boot'
  | 'status'
  | 'plan'
  | 'skill'
  | 'cli'
  | 'workflow'
  | 'research'
  | 'vault'
  | 'security'
  | 'memory'
  | 'report'
  | 'unknown';

export interface Intent {
  raw: string;
  command: string;
  args: Record<string, unknown>;
  category: IntentCategory;
  context: Record<string, unknown>;
}

// ─── Resolution ───────────────────────────────────────────────────────────

export interface Resolution {
  type: 'skill' | 'cli' | 'workflow' | 'memory' | 'direct' | 'unknown';
  name: string | null;
  path: string | null;
  found: boolean;
}

// ─── Guards ───────────────────────────────────────────────────────────────

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface RiskAssessment {
  level: RiskLevel;
  reasons: string[];
  requires_confirmation: boolean;
  rollback_available: boolean;
}

export interface TokenBudget {
  estimated_input: number;
  estimated_output: number;
  context_pct: number;          // % de la fenêtre contexte utilisé
  budget_ok: boolean;           // false si > 80%
  recommendation: string | null;
}

// ─── Execution ────────────────────────────────────────────────────────────

export type ExecutionStatus = 'success' | 'partial' | 'error' | 'dry_run' | 'blocked';

export interface ExecutionResult {
  status: ExecutionStatus;
  summary: string;
  data: Record<string, unknown>;
  files_created: string[];
  decisions_logged: string[];
  risks_logged: string[];
  next_steps: string[];
  error?: {
    code: string;
    message: string;
    recoverable: boolean;
  };
}

// ─── MainBrain ────────────────────────────────────────────────────────────

export interface MainBrainInput {
  command: string;
  args: Record<string, unknown>;
  context: Record<string, unknown>;
}

export interface MainBrainOutput {
  intent: Intent;
  resolution: Resolution;
  risk: RiskAssessment;
  tokens: TokenBudget;
  result: ExecutionResult;
  dry_run: boolean;
  duration_ms: number;
  timestamp: string;
}

export interface MainBrainOptions {
  dryRun: boolean;
  maxRiskLevel?: RiskLevel;           // bloquer au-delà de ce seuil
  tokenBudgetThreshold?: number;      // défaut : 80 (%)
  planningDir?: string;               // défaut : '.planning'
}
