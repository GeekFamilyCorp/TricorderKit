"""
report_generator.py — Génération rapport Markdown + JSON
TricorderKit eval-lab v0.1.0

Produit un rapport lisible des résultats d'évaluation.
Output JSON conforme à skill_output.schema.json v1.0.0.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from schema_validator import SchemaValidationResult
from regression_checker import RegressionResult

# -- Chemins ------------------------------------------------------------------
_HERE = Path(__file__).parent
_REPO_ROOT = _HERE.parent.parent
REPORTS_DIR = _REPO_ROOT / "reports" / "eval-lab"

SKILL_NAME = "eval-lab"
SKILL_VERSION = "0.1.0"


# -- Dataclass résultat agrégé ------------------------------------------------

class EvalResult:
    """Résultat complet pour un skill évalué."""

    def __init__(
        self,
        skill_name: str,
        schema_result: SchemaValidationResult | None = None,
        regression_result: RegressionResult | None = None,
        output: dict | None = None,
        error: str | None = None,
    ) -> None:
        self.skill_name = skill_name
        self.schema_result = schema_result
        self.regression_result = regression_result
        self.output = output
        self.error = error

    @property
    def status(self) -> str:
        if self.error:
            return "error"
        schema_ok = self.schema_result is None or self.schema_result.valid
        regression_ok = self.regression_result is None or not self.regression_result.has_regressions
        if schema_ok and regression_ok:
            return "pass"
        return "fail"

    @property
    def has_critical(self) -> bool:
        if self.schema_result and self.schema_result.has_critical:
            return True
        if self.regression_result and self.regression_result.has_critical:
            return True
        return False

    def violations_count(self) -> int:
        return len(self.schema_result.violations) if self.schema_result else 0

    def regressions_count(self) -> int:
        return len(self.regression_result.regressions) if self.regression_result else 0


# -- Rapport Markdown ---------------------------------------------------------

def _severity_icon(severity: str) -> str:
    return {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")


def _status_icon(status: str) -> str:
    return {"pass": "✅", "fail": "❌", "error": "⚠️"}.get(status, "❓")


def generate_markdown_report(
    results: list[EvalResult],
    title: str = "Rapport Eval-Lab",
) -> str:
    """Génère un rapport Markdown lisible."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    errors = sum(1 for r in results if r.status == "error")
    total = len(results)

    lines: list[str] = [
        f"# {title}",
        f"> Généré le {now} — TricorderKit eval-lab v{SKILL_VERSION}",
        "",
        "---",
        "",
        "## Résumé",
        "",
        f"| Total | ✅ Pass | ❌ Fail | ⚠️ Error |",
        f"|---|---|---|---|",
        f"| {total} | {passed} | {failed} | {errors} |",
        "",
        "---",
        "",
        "## Détail par skill",
        "",
    ]

    for r in results:
        icon = _status_icon(r.status)
        lines.append(f"### {icon} `{r.skill_name}` — {r.status.upper()}")
        lines.append("")

        if r.error:
            lines.append(f"> ⚠️ **Erreur** : {r.error}")
            lines.append("")
            continue

        # Violations schéma
        if r.schema_result and r.schema_result.violations:
            lines.append("**Violations schéma :**")
            lines.append("")
            lines.append("| Champ | Message | Sévérité |")
            lines.append("|---|---|---|")
            for v in r.schema_result.violations:
                icon_s = _severity_icon(v.severity)
                lines.append(f"| `{v.path}` | {v.message} | {icon_s} {v.severity} |")
            lines.append("")
        elif r.schema_result:
            lines.append("✅ Schéma : conforme")
            lines.append("")

        # Régressions
        if r.regression_result and r.regression_result.regressions:
            lines.append("**Régressions détectées :**")
            lines.append("")
            lines.append(f"> Baseline v{r.regression_result.baseline_version} → Courant v{r.regression_result.current_version}")
            lines.append("")
            lines.append("| Champ | Type | Attendu | Observé | Sévérité |")
            lines.append("|---|---|---|---|---|")
            for reg in r.regression_result.regressions:
                icon_s = _severity_icon(reg.severity)
                lines.append(
                    f"| `{reg.path}` | {reg.kind} | `{reg.expected}` | `{reg.got}` | {icon_s} {reg.severity} |"
                )
            lines.append("")
        elif r.regression_result:
            lines.append("✅ Régression : aucune")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# -- Output JSON skill_output.schema.json -------------------------------------

def build_output(
    results: list[EvalResult],
    dry_run: bool = False,
    duration_ms: int = 0,
    report_path: str | None = None,
) -> dict:
    """
    Construit l'output conforme à skill_output.schema.json.
    """
    now = datetime.now(timezone.utc).isoformat()
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    errors = sum(1 for r in results if r.status == "error")
    total = len(results)
    has_critical = any(r.has_critical for r in results)

    if dry_run:
        global_status = "dry_run"
    elif errors > 0 and passed == 0:
        global_status = "error"
    elif failed > 0 or errors > 0:
        global_status = "partial"
    else:
        global_status = "success"

    all_regressions = []
    all_violations = []
    for r in results:
        if r.regression_result:
            for reg in r.regression_result.regressions:
                all_regressions.append({
                    "skill": r.skill_name,
                    "path": reg.path,
                    "kind": reg.kind,
                    "expected": str(reg.expected),
                    "got": str(reg.got),
                    "severity": reg.severity,
                })
        if r.schema_result:
            for viol in r.schema_result.violations:
                all_violations.append({
                    "skill": r.skill_name,
                    "path": viol.path,
                    "message": viol.message,
                    "severity": viol.severity,
                })

    summary = (
        f"Eval {passed}/{total} skills OK"
        + (f" — {failed} régression(s)" if failed > 0 else "")
        + (f" — {errors} erreur(s)" if errors > 0 else "")
        + (" — CRITIQUE" if has_critical else "")
    )

    output: dict[str, Any] = {
        "status": global_status,
        "skill_name": SKILL_NAME,
        "skill_version": SKILL_VERSION,
        "timestamp": now,
        "duration_ms": duration_ms,
        "tokens_used": {"input": 0, "output": 0, "total": 0},
        "output": {
            "summary": summary[:500],
            "data": {
                "skills_evaluated": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "has_critical": has_critical,
                "schema_violations": all_violations,
                "regressions": all_regressions,
                "baseline_updated": False,
            },
            "files_created": [report_path] if report_path else [],
            "next_steps": _build_next_steps(results),
        },
    }

    if dry_run:
        output["dry_run_report"] = {
            "actions_that_would_run": [
                f"Évaluer {r.skill_name}" for r in results
            ],
            "estimated_tokens": total * 200,
            "estimated_duration_ms": total * 1000,
            "risk_level": "LOW",
        }

    return output


def _build_next_steps(results: list[EvalResult]) -> list[str]:
    """Construit les prochaines étapes à partir des résultats."""
    steps: list[str] = []
    failed = [r for r in results if r.status in ("fail", "error")]
    for r in failed[:3]:
        if r.schema_result and not r.schema_result.valid:
            critical = [v for v in r.schema_result.violations if v.severity == "CRITICAL"]
            if critical:
                steps.append(f"Corriger `{r.skill_name}` : champ obligatoire manquant `{critical[0].path}`")
        if r.regression_result and r.regression_result.regressions:
            reg = r.regression_result.regressions[0]
            steps.append(f"Corriger `{r.skill_name}` régression : `{reg.path}` ({reg.kind})")
    if not steps:
        steps.append("Tous les skills sont conformes — mettre à jour les baselines si nécessaire")
    return steps[:5]


# -- Sauvegarde rapport -------------------------------------------------------

def save_markdown_report(content: str, filename: str | None = None) -> Path:
    """Sauvegarde le rapport Markdown dans reports/eval-lab/."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if filename is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        filename = f"eval_report_{date}.md"
    path = REPORTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path
