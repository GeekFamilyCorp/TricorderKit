"""
eval_runner.py — CLI principal eval-lab
TricorderKit eval-lab v0.1.0

Commandes :
  eval              Évalue un ou plusieurs skills (schema + régression)
  validate-schema   Valide un fichier JSON output contre le schéma
  report            Génère un rapport à partir de l'historique SQLite
  dry-run           Simule une évaluation sans écriture

Usage :
  python eval_runner.py eval mangatracker-lookup
  python eval_runner.py eval --all
  python eval_runner.py validate-schema output.json
  python eval_runner.py report --last 5
  python eval_runner.py dry-run mangatracker-lookup
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Optional

import typer

from baseline_store import BaselineStore
from regression_checker import check_regression
from report_generator import (
    EvalResult,
    build_output,
    generate_markdown_report,
    save_markdown_report,
)
from schema_validator import validate_output, validate_json_string

# -- App -----------------------------------------------------------------------

app = typer.Typer(
    name="eval-lab",
    help="TricorderKit eval-lab — Non-régression et validation contrat output.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

# -- Chemins ------------------------------------------------------------------
_HERE = Path(__file__).parent
_REPO_ROOT = _HERE.parent.parent
_FIXTURES_DIR = _HERE / "fixtures"
_DEFAULT_DB = _REPO_ROOT / "data" / "eval-lab" / "baselines.sqlite"

# -- Helpers ------------------------------------------------------------------


def _load_fixture(skill_name: str) -> dict | None:
    """Charge le fixture JSON pour un skill."""
    fixture_path = _FIXTURES_DIR / f"{skill_name}.json"
    if not fixture_path.exists():
        return None
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


def _eval_single(
    skill_name: str,
    store: BaselineStore,
    update_baseline: bool = False,
    dry_run: bool = False,
) -> EvalResult:
    """Evalue un skill : charge fixture, valide schema, verifie regression."""
    output = _load_fixture(skill_name)
    if output is None:
        return EvalResult(
            skill_name=skill_name,
            error=f"Fixture introuvable : {_FIXTURES_DIR / skill_name}.json",
        )

    # 1. Validation schema
    schema_result = validate_output(output)

    # 2. Regression (si baseline existe)
    regression_result = None
    baseline = store.get_baseline(skill_name)
    if baseline is not None:
        regression_result = check_regression(baseline.output, output)
    else:
        typer.echo(f"  ℹ️  Pas de baseline pour '{skill_name}' — premiere execution", err=True)

    result = EvalResult(
        skill_name=skill_name,
        schema_result=schema_result,
        regression_result=regression_result,
        output=output,
    )

    # 3. Log historique (sauf dry-run)
    if not dry_run:
        violations = [v.__dict__ for v in schema_result.violations] if schema_result else []
        regressions = [r.__dict__ for r in regression_result.regressions] if regression_result else []
        from baseline_store import BaselineStore as _BS
        output_hash = _BS._hash_output(output)
        store.log_eval(
            skill_name=skill_name,
            skill_version=output.get("skill_version", "0.0.0"),
            status=result.status,
            violations=violations,
            regressions=regressions,
            output_hash=output_hash,
        )

    # 4. Update baseline si demande et pass
    if not dry_run and update_baseline and result.status == "pass":
        store.save_baseline(skill_name, output)
        typer.echo(f"  ✅ Baseline mise a jour pour '{skill_name}'", err=True)

    return result


def _print_result_summary(result: EvalResult) -> None:
    """Affiche un resume lisible d'un resultat."""
    icon = {"pass": "✅", "fail": "❌", "error": "⚠️"}.get(result.status, "❓")
    typer.echo(f"{icon} {result.skill_name} — {result.status.upper()}")

    if result.error:
        typer.echo(f"   Erreur : {result.error}")
        return

    if result.schema_result and result.schema_result.violations:
        typer.echo(f"   Violations schema : {len(result.schema_result.violations)}")
        for v in result.schema_result.violations[:3]:
            typer.echo(f"     [{v.severity}] {v.path} — {v.message}")
        if len(result.schema_result.violations) > 3:
            typer.echo(f"     … +{len(result.schema_result.violations) - 3} autres")

    if result.regression_result and result.regression_result.regressions:
        typer.echo(f"   Regressions : {len(result.regression_result.regressions)}")
        for r in result.regression_result.regressions[:3]:
            typer.echo(f"     [{r.severity}] {r.path} ({r.kind}): attendu={r.expected}, observe={r.got}")


# -- Commandes ----------------------------------------------------------------


@app.command("eval")
def cmd_eval(
    skills: Optional[list[str]] = typer.Argument(None, help="Nom(s) du/des skill(s) a evaluer"),
    all_skills: bool = typer.Option(False, "--all", help="Evaluer tous les skills ayant un fixture"),
    update_baseline: bool = typer.Option(False, "--update-baseline", help="Met a jour la baseline si pass"),
    output_json: bool = typer.Option(False, "--json", help="Sortie JSON conforme skill_output.schema.json"),
    report: bool = typer.Option(False, "--report", help="Genere un rapport Markdown"),
    db: Optional[Path] = typer.Option(None, "--db", help="Chemin custom vers la base SQLite"),
) -> None:
    """Evalue un ou plusieurs skills contre le schema et la baseline."""
    start = time.monotonic()
    store = BaselineStore(db or _DEFAULT_DB)

    if all_skills:
        fixtures = list(_FIXTURES_DIR.glob("*.json"))
        skill_list = [f.stem for f in fixtures]
        if not skill_list:
            typer.echo(f"⚠️  Aucun fixture trouve dans {_FIXTURES_DIR}", err=True)
            raise typer.Exit(1)
    elif skills:
        skill_list = list(skills)
    else:
        typer.echo("❌ Specifiez un skill ou utilisez --all", err=True)
        raise typer.Exit(1)

    typer.echo(f"🔬 Evaluation de {len(skill_list)} skill(s)…", err=True)

    results: list[EvalResult] = []
    for skill_name in skill_list:
        typer.echo(f"\n  → {skill_name}", err=True)
        result = _eval_single(skill_name, store, update_baseline=update_baseline)
        results.append(result)
        _print_result_summary(result)

    duration_ms = int((time.monotonic() - start) * 1000)

    report_path: str | None = None
    if report:
        md = generate_markdown_report(results)
        saved = save_markdown_report(md)
        report_path = str(saved)
        typer.echo(f"\n📄 Rapport : {saved}", err=True)

    output_data = build_output(results, duration_ms=duration_ms, report_path=report_path)

    if output_json:
        print(json.dumps(output_data, ensure_ascii=False, indent=2))

    store.close()

    has_critical = any(r.has_critical for r in results)
    has_fail = any(r.status in ("fail", "error") for r in results)

    if has_critical:
        raise typer.Exit(2)
    elif has_fail:
        raise typer.Exit(1)


@app.command("validate-schema")
def cmd_validate_schema(
    file: Optional[Path] = typer.Argument(None, help="Fichier JSON a valider (stdin si omis)"),
    output_json: bool = typer.Option(False, "--json", help="Sortie JSON"),
) -> None:
    """Valide un fichier output JSON contre skill_output.schema.json."""
    if file is not None:
        if not file.exists():
            typer.echo(f"❌ Fichier introuvable : {file}", err=True)
            raise typer.Exit(1)
        json_str = file.read_text(encoding="utf-8")
    else:
        typer.echo("📥 Lecture depuis stdin…", err=True)
        json_str = sys.stdin.read().strip()

    result = validate_json_string(json_str)

    if output_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        if result.valid:
            typer.echo(f"✅ Schema valide — {result.skill_name} v{result.skill_version}")
        else:
            typer.echo(f"❌ {len(result.violations)} violation(s) :")
            for v in result.violations:
                icon = {"❌": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(v.severity, "⚪")
                typer.echo(f"  {icon} [{v.severity}] {v.path} — {v.message}")

    sys.exit(0 if result.valid else (2 if result.has_critical else 1))


@app.command("report")
def cmd_report(
    skill: Optional[str] = typer.Argument(None, help="Skill specifique (tous si omis)"),
    last: int = typer.Option(10, "--last", help="Nombre d'entrees historique par skill"),
    output_json: bool = typer.Option(False, "--json", help="Sortie JSON de l'historique"),
    db: Optional[Path] = typer.Option(None, "--db", help="Chemin custom vers la base SQLite"),
) -> None:
    """Genere un rapport depuis l'historique SQLite."""
    store = BaselineStore(db or _DEFAULT_DB)

    skills_with_baselines = store.list_skills()
    if not skills_with_baselines:
        typer.echo("ℹ️  Aucune baseline en base — lancez d'abord `eval`.")
        store.close()
        return

    target_skills = [skill] if skill else skills_with_baselines

    report_data: dict = {"skills": {}}
    for sk in target_skills:
        history = store.get_history(sk, limit=last)
        if not history:
            typer.echo(f"ℹ️  Pas d'historique pour '{sk}'")
            continue

        if output_json:
            report_data["skills"][sk] = [
                {
                    "evaluated_at": h.evaluated_at,
                    "status": h.status,
                    "skill_version": h.skill_version,
                    "violations_count": len(h.violations),
                    "regressions_count": len(h.regressions),
                    "output_hash": h.output_hash[:8],
                }
                for h in history
            ]
        else:
            typer.echo(f"\n## {sk} (derniers {len(history)} evals)")
            typer.echo(f"{'Date':<25} {'Statut':<12} {'Version':<12} {'Violations':<12} {'Regressions'}")
            typer.echo("-" * 80)
            for h in history:
                icon = {"pass": "✅", "fail": "❌", "schema_error": "🔴"}.get(h.status, "❓")
                typer.echo(
                    f"{h.evaluated_at[:19]:<25} {icon} {h.status:<10} "
                    f"{h.skill_version:<12} {len(h.violations):<12} {len(h.regressions)}"
                )

    if output_json:
        print(json.dumps(report_data, ensure_ascii=False, indent=2))

    store.close()


@app.command("dry-run")
def cmd_dry_run(
    skills: Optional[list[str]] = typer.Argument(None, help="Skill(s) a simuler"),
    all_skills: bool = typer.Option(False, "--all", help="Simuler tous les skills"),
    db: Optional[Path] = typer.Option(None, "--db", help="Chemin custom vers la base SQLite"),
) -> None:
    """Simule une evaluation sans ecriture en base."""
    store = BaselineStore(db or _DEFAULT_DB)

    if all_skills:
        fixtures = list(_FIXTURES_DIR.glob("*.json"))
        skill_list = [f.stem for f in fixtures]
    elif skills:
        skill_list = list(skills)
    else:
        typer.echo("❌ Specifiez un skill ou utilisez --all", err=True)
        raise typer.Exit(1)

    typer.echo(f"🔍 DRY-RUN — {len(skill_list)} skill(s) simule(s)\n")

    results: list[EvalResult] = []
    for skill_name in skill_list:
        result = _eval_single(skill_name, store, update_baseline=False, dry_run=True)
        results.append(result)
        _print_result_summary(result)

    output_data = build_output(results, dry_run=True)

    typer.echo("\n--- dry_run_report ---")
    if "dry_run_report" in output_data:
        dr = output_data["dry_run_report"]
        typer.echo(f"Actions simulees : {len(dr['actions_that_would_run'])}")
        for a in dr["actions_that_would_run"]:
            typer.echo(f"  . {a}")
        typer.echo(f"Tokens estimes   : {dr['estimated_tokens']}")
        typer.echo(f"Duree estimee    : {dr['estimated_duration_ms']}ms")
        typer.echo(f"Niveau de risque : {dr['risk_level']}")

    store.close()


# -- Entree principale --------------------------------------------------------

if __name__ == "__main__":
    app()
