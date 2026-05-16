"""
security_runner.py — CLI principal security-audit-cli
TricorderKit security-audit-cli v0.1.0

Commandes :
  audit           Audit complet (secrets + anonymisation + patterns)
  scan-secrets    Scanner uniquement les secrets
  check-anon      Vérifier anonymisation avant push public
  check-patterns  Vérifier les anti-patterns de sécurité
  dry-run         Simuler un audit sans sortie persistée

Usage :
  python security_runner.py audit
  python security_runner.py audit --path plugins/
  python security_runner.py check-anon --path plugins/tk-orchestrator/
  python security_runner.py scan-secrets --path . --json
  python security_runner.py dry-run
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

from anonymization_checker import (
    AnonCheckResult,
    DEFAULT_PRIVATE_TERMS,
    check_anonymization,
)
from secret_scanner import SecretScanResult, scan_secrets
from pattern_checker import PatternCheckResult, check_patterns

# -- App -----------------------------------------------------------------------

app = typer.Typer(
    name="security-audit-cli",
    help="TricorderKit security-audit-cli — Audit de sécurité (secrets, anonymisation, patterns).",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

# -- Chemins ------------------------------------------------------------------

_HERE = Path(__file__).parent
_REPO_ROOT = _HERE.parent.parent
_REPORTS_DIR = _REPO_ROOT / "reports" / "security"

SKILL_NAME = "security-audit-cli"
SKILL_VERSION = "0.1.0"


# -- Helpers ------------------------------------------------------------------

def _print_section(title: str) -> None:
    typer.echo(f"\n{'─' * 60}")
    typer.echo(f"  {title}")
    typer.echo(f"{'─' * 60}")


def _print_anon_result(result: AnonCheckResult) -> None:
    if result.clean:
        typer.echo(f"✅ Anonymisation OK — {result.files_scanned} fichiers, aucun terme privé")
    else:
        typer.echo(f"🔴 {len(result.violations)} violation(s) d'anonymisation :")
        for term, viols in result.violations_by_term().items():
            typer.echo(f"  Terme '{term}' : {len(viols)} occurrence(s)")
            for v in viols[:3]:
                typer.echo(f"    {v.file_path}:{v.line_number}  →  {v.line_content}")
            if len(viols) > 3:
                typer.echo(f"    … +{len(viols) - 3} autres")


def _print_secret_result(result: SecretScanResult) -> None:
    if result.clean:
        typer.echo(f"✅ Secrets OK — {result.files_scanned} fichiers, aucun secret")
    else:
        typer.echo(f"🔴 {len(result.findings)} secret(s) détecté(s) :")
        for f in result.findings[:5]:
            icon = "🔴" if f.severity == "CRITICAL" else "🟠"
            typer.echo(f"  {icon} [{f.severity}] {f.file_path}:{f.line_number} — {f.description}")
        if len(result.findings) > 5:
            typer.echo(f"  … +{len(result.findings) - 5} autres")


def _print_pattern_result(result: PatternCheckResult) -> None:
    active = result.active_findings
    if result.clean:
        typer.echo(f"✅ Patterns OK — {result.files_scanned} fichiers, aucun anti-pattern")
    else:
        typer.echo(f"🟠 {len(active)} anti-pattern(s) :")
        for f in active[:5]:
            icon = {"HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(f.severity, "⚪")
            typer.echo(f"  {icon} [{f.severity}] {f.file_path}:{f.line_number} — {f.description}")
        if len(active) > 5:
            typer.echo(f"  … +{len(active) - 5} autres")


def _build_output(
    anon: AnonCheckResult | None,
    secrets: SecretScanResult | None,
    patterns: PatternCheckResult | None,
    dry_run: bool,
    duration_ms: int,
    report_path: str | None = None,
) -> dict:
    """Construit l'output conforme à skill_output.schema.json."""
    now = datetime.now(timezone.utc).isoformat()

    has_critical = (
        (anon and not anon.clean) or
        (secrets and secrets.has_critical)
    )
    has_high = (
        (secrets and not secrets.clean and not secrets.has_critical) or
        (patterns and not patterns.clean)
    )

    if dry_run:
        global_status = "dry_run"
    elif has_critical:
        global_status = "error"
    elif has_high:
        global_status = "partial"
    else:
        global_status = "success"

    secrets_found = len(secrets.findings) if secrets else 0
    anon_violations = len(anon.violations) if anon else 0
    pattern_warnings = len(patterns.active_findings) if patterns else 0
    files_scanned = (
        (secrets.files_scanned if secrets else 0)
        or (anon.files_scanned if anon else 0)
        or (patterns.files_scanned if patterns else 0)
    )

    summary_parts = []
    if secrets_found == 0 and anon_violations == 0 and pattern_warnings == 0:
        summary_parts.append("Audit OK")
    else:
        if secrets_found > 0:
            summary_parts.append(f"{secrets_found} secret(s)")
        if anon_violations > 0:
            summary_parts.append(f"{anon_violations} violation(s) anonymisation")
        if pattern_warnings > 0:
            summary_parts.append(f"{pattern_warnings} warning(s) pattern")

    summary = " — ".join(summary_parts) if summary_parts else "Audit terminé"

    next_steps: list[str] = []
    if anon and not anon.clean:
        first = anon.violations[0]
        next_steps.append(f"Corriger anonymisation : '{first.term}' dans {first.file_path}:{first.line_number}")
    if secrets and not secrets.clean:
        first = secrets.findings[0]
        next_steps.append(f"Corriger secret : {first.description} dans {first.file_path}:{first.line_number}")
    if patterns and not patterns.clean:
        first_active = patterns.active_findings
        if first_active:
            f = first_active[0]
            next_steps.append(f"Corriger pattern : {f.description} dans {f.file_path}:{f.line_number}")
    if not next_steps:
        next_steps.append("Aucune action requise — audit propre")

    output: dict = {
        "status": global_status,
        "skill_name": SKILL_NAME,
        "skill_version": SKILL_VERSION,
        "timestamp": now,
        "duration_ms": duration_ms,
        "tokens_used": {"input": 0, "output": 0, "total": 0},
        "output": {
            "summary": summary[:500],
            "data": {
                "secrets_found": secrets_found,
                "anonymization_violations": anon_violations,
                "pattern_warnings": pattern_warnings,
                "files_scanned": files_scanned,
                "has_critical": has_critical,
                "findings": {
                    "secrets": secrets.to_dict()["findings"] if secrets else [],
                    "anonymization": anon.to_dict()["violations"] if anon else [],
                    "patterns": patterns.to_dict()["findings"] if patterns else [],
                },
            },
            "files_created": [report_path] if report_path else [],
            "next_steps": next_steps[:5],
        },
    }

    if dry_run:
        output["dry_run_report"] = {
            "actions_that_would_run": [
                "Scanner secrets dans le repo",
                "Vérifier anonymisation termes privés",
                "Détecter anti-patterns de sécurité",
            ],
            "estimated_tokens": 0,
            "estimated_duration_ms": 2000,
            "risk_level": "LOW",
        }

    return output


def _save_report(output: dict) -> Path:
    """Sauvegarde le rapport JSON."""
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    path = _REPORTS_DIR / f"security_report_{date}.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# -- Commandes ----------------------------------------------------------------

@app.command("audit")
def cmd_audit(
    path: Path = typer.Option(_REPO_ROOT, "--path", "-p", help="Répertoire à auditer"),
    output_json: bool = typer.Option(False, "--json", help="Sortie JSON"),
    report: bool = typer.Option(False, "--report", help="Sauvegarder rapport JSON"),
    skip_secrets: bool = typer.Option(False, "--skip-secrets", help="Ignorer le scan de secrets"),
    skip_anon: bool = typer.Option(False, "--skip-anon", help="Ignorer la vérification d'anonymisation"),
    skip_patterns: bool = typer.Option(False, "--skip-patterns", help="Ignorer la vérification de patterns"),
) -> None:
    """Audit de sécurité complet (secrets + anonymisation + patterns)."""
    start = time.monotonic()
    typer.echo(f"🔒 Audit sécurité — {path}", err=True)

    anon_result: AnonCheckResult | None = None
    secret_result: SecretScanResult | None = None
    pattern_result: PatternCheckResult | None = None

    if not skip_anon:
        _print_section("Vérification anonymisation")
        anon_result = check_anonymization(path)
        _print_anon_result(anon_result)

    if not skip_secrets:
        _print_section("Scan de secrets")
        secret_result = scan_secrets(path)
        _print_secret_result(secret_result)

    if not skip_patterns:
        _print_section("Vérification anti-patterns")
        pattern_result = check_patterns(path)
        _print_pattern_result(pattern_result)

    duration_ms = int((time.monotonic() - start) * 1000)

    report_path: str | None = None
    output_data = _build_output(anon_result, secret_result, pattern_result, False, duration_ms)

    if report:
        saved = _save_report(output_data)
        report_path = str(saved)
        output_data["output"]["files_created"] = [report_path]
        typer.echo(f"\n📄 Rapport : {saved}", err=True)

    if output_json:
        print(json.dumps(output_data, ensure_ascii=False, indent=2))
    else:
        typer.echo(f"\n{'═' * 60}")
        typer.echo(f"  Statut global : {output_data['status'].upper()}")
        typer.echo(f"  Durée         : {duration_ms}ms")
        typer.echo(f"{'═' * 60}")

    has_critical = output_data["output"]["data"]["has_critical"]
    has_fail = output_data["status"] in ("error", "partial")

    if has_critical:
        raise typer.Exit(2)
    elif has_fail:
        raise typer.Exit(1)


@app.command("check-anon")
def cmd_check_anon(
    path: Path = typer.Argument(..., help="Répertoire ou fichier à vérifier"),
    terms: Optional[list[str]] = typer.Option(None, "--term", "-t", help="Terme privé supplémentaire"),
    output_json: bool = typer.Option(False, "--json", help="Sortie JSON"),
) -> None:
    """Vérifie l'anonymisation avant push vers le repo public."""
    all_terms = DEFAULT_PRIVATE_TERMS + list(terms or [])
    typer.echo(f"🔍 Vérification anonymisation — {len(all_terms)} termes : {all_terms}", err=True)

    result = check_anonymization(path, all_terms)

    if output_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_anon_result(result)
        typer.echo(f"\n  {result.files_scanned} fichiers scannés, {result.files_skipped} ignorés")

    raise typer.Exit(0 if result.clean else 2)


@app.command("scan-secrets")
def cmd_scan_secrets(
    path: Path = typer.Argument(_REPO_ROOT, help="Répertoire ou fichier à scanner"),
    output_json: bool = typer.Option(False, "--json", help="Sortie JSON"),
) -> None:
    """Scanne les secrets hardcodés dans le code source."""
    typer.echo(f"🔍 Scan secrets — {path}", err=True)
    result = scan_secrets(path)

    if output_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_secret_result(result)
        typer.echo(f"\n  {result.files_scanned} fichiers scannés, {result.files_skipped} ignorés")

    raise typer.Exit(0 if result.clean else (2 if result.has_critical else 1))


@app.command("check-patterns")
def cmd_check_patterns(
    path: Path = typer.Argument(_REPO_ROOT, help="Répertoire ou fichier à analyser"),
    output_json: bool = typer.Option(False, "--json", help="Sortie JSON"),
) -> None:
    """Vérifie les anti-patterns de sécurité dans le code source."""
    typer.echo(f"🔍 Vérification patterns — {path}", err=True)
    result = check_patterns(path)

    if output_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_pattern_result(result)
        typer.echo(f"\n  {result.files_scanned} fichiers scannés")

    raise typer.Exit(0 if result.clean else 1)


@app.command("dry-run")
def cmd_dry_run(
    path: Path = typer.Option(_REPO_ROOT, "--path", "-p", help="Répertoire cible"),
) -> None:
    """Simule un audit complet sans persistance."""
    typer.echo(f"🔍 DRY-RUN sécurité — {path}\n")
    output_data = _build_output(None, None, None, dry_run=True, duration_ms=0)

    if "dry_run_report" in output_data:
        dr = output_data["dry_run_report"]
        typer.echo("Actions qui seraient exécutées :")
        for a in dr["actions_that_would_run"]:
            typer.echo(f"  • {a}")
        typer.echo(f"\nDurée estimée    : {dr['estimated_duration_ms']}ms")
        typer.echo(f"Niveau de risque : {dr['risk_level']}")


# -- Entrée principale --------------------------------------------------------

if __name__ == "__main__":
    app()
