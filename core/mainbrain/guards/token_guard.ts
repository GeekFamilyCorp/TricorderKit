/**
 * TricorderKit — Token Hygiene Guard
 * Étape 7 de l'algorithme MainBrain
 *
 * Évalue le budget tokens avant d'exécuter une action.
 * Seuil par défaut : alerte à 80%, bloquage à 95%.
 */

import type { Intent, TokenBudget, IntentCategory } from '../types.js';

// ─── Estimations par catégorie d'intent (tokens input) ───────────────────

const CATEGORY_ESTIMATES: Record<IntentCategory, number> = {
  boot:      800,
  status:    300,
  plan:      400,
  skill:    1200,
  cli:      1000,
  workflow: 1500,
  research: 4000,
  vault:     800,
  security: 1200,
  memory:    500,
  report:    600,
  unknown:   500,
};

const OUTPUT_RATIO = 0.25; // output ≈ 25% de l'input estimé

// ─── Token Guard ─────────────────────────────────────────────────────────

export class TokenGuard {
  private threshold: number; // % alerte
  private hardLimit: number; // % bloquage
  private contextWindowSize: number;
  private currentContextUsed: number;

  constructor(
    threshold = 80,
    hardLimit = 95,
    contextWindowSize = 200_000,
    currentContextUsed = 0
  ) {
    this.threshold = threshold;
    this.hardLimit = hardLimit;
    this.contextWindowSize = contextWindowSize;
    this.currentContextUsed = currentContextUsed;
  }

  estimate(intent: Intent): TokenBudget {
    const estimated_input = CATEGORY_ESTIMATES[intent.category] ?? 500;
    const estimated_output = Math.round(estimated_input * OUTPUT_RATIO);
    const total_new = estimated_input + estimated_output;

    const context_pct = Math.round(
      ((this.currentContextUsed + total_new) / this.contextWindowSize) * 100
    );

    const budget_ok = context_pct < this.hardLimit;

    let recommendation: string | null = null;
    if (context_pct >= this.hardLimit) {
      recommendation = 'BLOQUÉ — fenêtre contexte > 95%. Lancer /tk:pack-context avant de continuer.';
    } else if (context_pct >= this.threshold) {
      recommendation = `ATTENTION — contexte à ${context_pct}%. Envisager /tk:pack-context.`;
    }

    return {
      estimated_input,
      estimated_output,
      context_pct,
      budget_ok,
      recommendation,
    };
  }

  updateContext(tokensUsed: number): void {
    this.currentContextUsed += tokensUsed;
  }

  reset(): void {
    this.currentContextUsed = 0;
  }
}
