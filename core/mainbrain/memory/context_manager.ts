/**
 * TricorderKit — Context Manager
 * Étape 5 & 10 de l'algorithme MainBrain
 *
 * Lit et écrit le contexte session :
 * - Étape 5 : memory_resolver → consulte .planning/ et vault
 * - Étape 10 : memory_writer → logue décisions et risques
 */

import * as fs from 'fs';
import * as path from 'path';
import type { ExecutionResult, RiskAssessment } from '../types.js';

export interface SessionContext {
  state: string | null;
  tasks: string | null;
  decisions: string | null;
  risks: string | null;
  loaded_at: string;
}

export interface DecisionEntry {
  id: string;
  timestamp: string;
  command: string;
  summary: string;
  impact: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface RiskEntry {
  id: string;
  timestamp: string;
  command: string;
  level: string;
  reasons: string[];
  mitigated: boolean;
}

// ─── Context Manager ──────────────────────────────────────────────────────

export class ContextManager {
  private planningDir: string;

  constructor(planningDir = '.planning') {
    this.planningDir = planningDir;
  }

  // ── Étape 5 : Lire le contexte existant ──────────────────────────────

  load(): SessionContext {
    return {
      state:     this.readFile('STATE.md'),
      tasks:     this.readFile('TASKS.md'),
      decisions: this.readFile('DECISIONS.md'),
      risks:     this.readFile('RISKS.md'),
      loaded_at: new Date().toISOString(),
    };
  }

  hasRelevantMemory(command: string): boolean {
    const ctx = this.load();
    const searchable = [
      ctx.state ?? '',
      ctx.tasks ?? '',
      ctx.decisions ?? '',
    ].join(' ').toLowerCase();
    return searchable.includes(command.toLowerCase().replace('/tk:', ''));
  }

  // ── Étape 10 : Écrire les décisions et risques ───────────────────────

  logDecision(entry: DecisionEntry): void {
    const line = `\n## ${entry.id} — ${entry.timestamp}\n**Commande** : \`${entry.command}\`  \n**Impact** : ${entry.impact}  \n**Résumé** : ${entry.summary}\n`;
    this.appendFile('DECISIONS.md', line);
  }

  logRisk(entry: RiskEntry): void {
    const reasons = entry.reasons.map((r) => `- ${r}`).join('\n');
    const line = `\n## ${entry.id} — ${entry.timestamp}\n**Commande** : \`${entry.command}\`  \n**Niveau** : ${entry.level}  \n**Raisons** :  \n${reasons}  \n**Mitigé** : ${entry.mitigated ? 'Oui' : 'Non'}\n`;
    this.appendFile('RISKS.md', line);
  }

  persistResult(command: string, result: ExecutionResult, risk: RiskAssessment): void {
    const ts = new Date().toISOString();
    const id = `DEC-${Date.now().toString(36).toUpperCase()}`;

    if (result.status === 'success' || result.status === 'partial') {
      this.logDecision({
        id,
        timestamp: ts,
        command,
        summary: result.summary,
        impact: risk.level === 'LOW' ? 'LOW' : risk.level === 'MEDIUM' ? 'MEDIUM' : 'HIGH',
      });
    }

    if (risk.level !== 'LOW') {
      this.logRisk({
        id: `RISK-${Date.now().toString(36).toUpperCase()}`,
        timestamp: ts,
        command,
        level: risk.level,
        reasons: risk.reasons,
        mitigated: result.status === 'success',
      });
    }
  }

  // ── Helpers ──────────────────────────────────────────────────────────

  private readFile(filename: string): string | null {
    const filePath = path.join(this.planningDir, filename);
    try {
      return fs.readFileSync(filePath, 'utf-8');
    } catch {
      return null;
    }
  }

  private appendFile(filename: string, content: string): void {
    const filePath = path.join(this.planningDir, filename);
    try {
      fs.appendFileSync(filePath, content, 'utf-8');
    } catch {
      // Silencieux si .planning/ n'existe pas encore (env CI ou dry_run)
    }
  }
}
