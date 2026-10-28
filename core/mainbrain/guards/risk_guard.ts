/**
 * TricorderKit — Risk Guard
 * Étape 6 de l'algorithme MainBrain
 *
 * Évalue le niveau de risque d'une action avant exécution.
 * Règles : destructif > réseau > fichiers sensibles > injection > défaut LOW.
 */

import type { Intent, RiskAssessment, RiskLevel } from '../types.js';

// ─── Patterns de risque ───────────────────────────────────────────────────

const RISK_PATTERNS: Array<{
  pattern: RegExp | string[];
  level: RiskLevel;
  reason: string;
  rollback: boolean;
}> = [
  {
    pattern: ['delete', 'drop', 'destroy', 'rm', 'purge', 'truncate'],
    level: 'CRITICAL',
    reason: 'Opération destructive irréversible détectée',
    rollback: false,
  },
  {
    pattern: ['exec', 'eval', 'shell', 'bash', 'powershell', 'subprocess'],
    level: 'HIGH',
    reason: 'Exécution de commande shell détectée — risque injection',
    rollback: false,
  },
  {
    pattern: ['.env', 'api_key', 'password', 'secret', 'token', 'credential'],
    level: 'HIGH',
    reason: 'Accès à des fichiers ou variables sensibles détecté',
    rollback: true,
  },
  {
    pattern: /https?:\/\/|fetch|axios|http\.get/,
    level: 'MEDIUM',
    reason: 'Appel réseau externe détecté',
    rollback: true,
  },
  {
    pattern: ['write', 'create', 'update', 'push', 'commit', 'overwrite'],
    level: 'MEDIUM',
    reason: 'Opération d\'écriture ou modification détectée',
    rollback: true,
  },
];

// ─── Risk Guard ───────────────────────────────────────────────────────────

export class RiskGuard {
  private maxAllowed: RiskLevel;

  private readonly RISK_ORDER: RiskLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

  constructor(maxAllowed: RiskLevel = 'HIGH') {
    this.maxAllowed = maxAllowed;
  }

  assess(intent: Intent): RiskAssessment {
    const reasons: string[] = [];
    let highestLevel: RiskLevel = 'LOW';
    let rollback_available = true;

    const searchTarget = [
      intent.command,
      ...Object.values(intent.args).map(String),
    ]
      .join(' ')
      .toLowerCase();

    for (const rule of RISK_PATTERNS) {
      const matched = Array.isArray(rule.pattern)
        ? rule.pattern.some((kw) => searchTarget.includes(kw))
        : rule.pattern.test(searchTarget);

      if (matched) {
        reasons.push(rule.reason);
        if (this.RISK_ORDER.indexOf(rule.level) > this.RISK_ORDER.indexOf(highestLevel)) {
          highestLevel = rule.level;
        }
        if (!rule.rollback) rollback_available = false;
      }
    }

    const requires_confirmation =
      this.RISK_ORDER.indexOf(highestLevel) >=
      this.RISK_ORDER.indexOf(this.maxAllowed);

    return {
      level: highestLevel,
      reasons,
      requires_confirmation,
      rollback_available,
    };
  }

  isBlocked(assessment: RiskAssessment): boolean {
    return (
      this.RISK_ORDER.indexOf(assessment.level) >
      this.RISK_ORDER.indexOf(this.maxAllowed)
    );
  }
}
