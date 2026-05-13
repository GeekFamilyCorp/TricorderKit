"""TricorderKit phased installer (v0.1).

CLI Typer conforme à `core/contracts/skill_output.schema.json` (DEC-005)
et au standard implémentation `docs/cli_forge_typer_standard.md`.

Commandes :
  - status   : affiche l'état des phases TricorderKit (lit .tricorderkit/state.yml)
  - diagnose : diagnostique l'environnement et les fichiers TricorderKit clés
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

# ---------------------------------------------------------------------------
# Constantes (exportées pour les tests CliRunner)
# ---------------------------------------------------------------------------

CLI_NAME = "tk-installer"
CLI_VERSION = "0.1.0"

# Exit codes standardisés (cf. docs/cli_forge_typer_standard.md §3.6)
EXIT_OK = 0
EXIT_BUSINESS_ERROR = 1
EXIT_ENV_KO = 3
EXIT_GATE_BLOCKED = 4
EXIT_CONFLICT = 5

# Statuts conformes au schéma skill_output.schema.json
VALID_STATUSES = {"success", "partial", "error", "dry_run"}

# ---------------------------------------------------------------------------
# App Typer
# ---------------------------------------------------------------------------

app = typer.Typer(
    name=CLI_NAME,
    help="TricorderKit phased installer — status, diagnose (v0.1).",
    no_args_is_help=True,
    add_completion=False,
)

# rich envoyé sur stderr → stdout reste propre en mode --output json
console = Console(stderr=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso_utc_z() -> str:
    """Instant courant ISO 8601 UTC avec suffixe 'Z' (conforme JSON Schema)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _find_repo_root(start: Path | None = None) -> Path:
    """Remonte jusqu'à trouver la racine du repo TricorderKit.

    Critères acceptés (l'un suffit) :
      - présence d'un dossier .git
      - présence d'un dossier .tricorderkit
      - présence d'un dossier .planning
    """
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if any((candidate / marker).exists()
               for marker in (".git", ".tricorderkit", ".planning")):
            return candidate
    raise RuntimeError(
        f"Racine du repo introuvable depuis {here}. "
        "Aucun marqueur .git / .tricorderkit / .planning détecté."
    )


def _run_silent(cmd: list[str], timeout: int = 5) -> dict[str, Any]:
    """Lance une commande système sans lever d'exception."""
    if shutil.which(cmd[0]) is None:
        return {"available": False, "version": None}
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False,
        )
        version_lines = (result.stdout or result.stderr or "").strip().splitlines()
        return {
            "available": result.returncode == 0,
            "version": version_lines[0] if version_lines else None,
        }
    except (subprocess.TimeoutExpired, OSError):
        return {"available": False, "version": None}


def _load_state(repo_root: Path) -> dict[str, Any] | None:
    """Charge .tricorderkit/state.yml ou retourne None si absent/invalide."""
    state_file = repo_root / ".tricorderkit" / "state.yml"
    if not state_file.exists():
        return None
    try:
        with state_file.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return None


def emit_result(
    command: str,
    status: str,
    summary: str,
    data: dict[str, Any] | None = None,
    files_created: list[str] | None = None,
    next_steps: list[str] | None = None,
    error_details: dict[str, Any] | None = None,
    dry_run_report: dict[str, Any] | None = None,
    output_format: str = "pretty",
    duration_ms: int = 0,
    pretty_renderer: Any = None,
) -> int:
    """Émet un payload conforme à skill_output.schema.json.

    Retourne l'exit code adapté au status :
      - success → 0
      - partial → 1
      - dry_run → 0
      - error   → 1 par défaut (à overrider par typer.Exit(code=X) côté caller)
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Statut invalide : {status!r}. Attendu : {VALID_STATUSES}")
    if len(summary) > 500:
        # Le schéma impose maxLength=500 sur output.summary
        summary = summary[:497] + "..."

    # Payload conforme schema
    payload: dict[str, Any] = {
        "status": status,
        "skill_name": f"{CLI_NAME}.{command}",
        "skill_version": CLI_VERSION,
        "timestamp": _now_iso_utc_z(),
        "duration_ms": duration_ms,
        "output": {
            "summary": summary,
            "data": data or {},
            "files_created": files_created or [],
            "next_steps": (next_steps or [])[:5],  # schema maxItems=5
        },
    }
    if status == "error" and error_details:
        payload["error"] = error_details
    if status == "dry_run" and dry_run_report:
        payload["dry_run_report"] = dry_run_report

    # Émission
    if output_format == "json":
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
        sys.stdout.write("\n")
    else:
        color = {
            "success": "green", "partial": "yellow",
            "error": "red", "dry_run": "cyan",
        }[status]
        console.print(f"[{color}]{command} → {status}[/{color}]")
        console.print(summary)
        if pretty_renderer is not None:
            console.print(pretty_renderer)
        if data and pretty_renderer is None:
            console.print(data)
        if status == "error" and error_details:
            console.print(f"[red]Erreur: {error_details.get('message', '')}[/red]")
        if next_steps:
            console.print("[cyan]Prochaines étapes :[/cyan]")
            for step in next_steps[:5]:
                console.print(f"  • {step}")

    return EXIT_OK if status in ("success", "dry_run") else EXIT_BUSINESS_ERROR


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{CLI_NAME} {CLI_VERSION}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True,
        help="Affiche la version et quitte.",
    ),
) -> None:
    """Point d'entrée racine."""


# ---------------------------------------------------------------------------
# Commande : status
# ---------------------------------------------------------------------------

@app.command("status")
def status_cmd(
    output: str = typer.Option(
        "pretty", "--output", "-o", help="Format de sortie : pretty ou json.",
    ),
) -> None:
    """Affiche l'état des phases TricorderKit (lit .tricorderkit/state.yml)."""
    start = time.perf_counter()

    try:
        repo_root = _find_repo_root()
    except RuntimeError as exc:
        duration = int((time.perf_counter() - start) * 1000)
        emit_result(
            command="status", status="error",
            summary="Racine du repo TricorderKit introuvable.",
            error_details={
                "code": "REPO_ROOT_NOT_FOUND",
                "message": str(exc),
                "recoverable": True,
                "rollback_available": False,
            },
            next_steps=["Se placer à la racine du repo TricorderKit avant de lancer."],
            output_format=output, duration_ms=duration,
        )
        raise typer.Exit(code=EXIT_ENV_KO)

    state = _load_state(repo_root)
    if state is None:
        duration = int((time.perf_counter() - start) * 1000)
        emit_result(
            command="status", status="error",
            summary=".tricorderkit/state.yml absent ou invalide.",
            data={"repo_root": str(repo_root)},
            error_details={
                "code": "STATE_FILE_MISSING",
                "message": "Le fichier .tricorderkit/state.yml est absent ou ne parse pas.",
                "recoverable": True,
                "rollback_available": False,
            },
            next_steps=["Créer .tricorderkit/state.yml (bootstrap Phase 0)."],
            output_format=output, duration_ms=duration,
        )
        raise typer.Exit(code=EXIT_BUSINESS_ERROR)

    phases = state.get("phases", {}) or {}
    blockers: list[str] = []
    next_actions: list[str] = []
    verified_count = 0
    total_count = len(phases)

    for phase_key, phase_data in phases.items():
        pd = phase_data or {}
        if pd.get("verified"):
            verified_count += 1
        if pd.get("status") == "blocked":
            blocked_by = pd.get("blocked_by", []) or []
            blockers.append(f"{phase_key} ← {', '.join(blocked_by) or 'unknown'}")
        if not next_actions and pd.get("status") in ("pending", "in_progress"):
            next_actions.append(f"Avancer sur {phase_key}.")

    # Rendu pretty
    table = Table(title=f"TricorderKit v{state.get('version', '?')} — Phases")
    table.add_column("Phase", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Verified", style="green")
    table.add_column("Blocked by", style="yellow")
    for phase_key, phase_data in phases.items():
        pd = phase_data or {}
        blocked_by = ", ".join(pd.get("blocked_by", []) or [])
        table.add_row(
            phase_key, str(pd.get("status", "?")),
            "OK" if pd.get("verified") else "--",
            blocked_by,
        )

    summary = f"{verified_count}/{total_count} phases verified. {len(blockers)} blocker(s)."
    duration = int((time.perf_counter() - start) * 1000)

    emit_result(
        command="status", status="success", summary=summary,
        data={
            "version": state.get("version"),
            "install_status": state.get("install_status"),
            "phases": phases,
            "blockers": blockers,
            "verified_count": verified_count,
            "total_count": total_count,
        },
        next_steps=next_actions or ["Toutes les phases gérées sont actives."],
        output_format=output, duration_ms=duration, pretty_renderer=table,
    )
    raise typer.Exit(code=EXIT_OK)


# ---------------------------------------------------------------------------
# Commande : diagnose
# ---------------------------------------------------------------------------

@app.command("diagnose")
def diagnose_cmd(
    output: str = typer.Option(
        "pretty", "--output", "-o", help="Format de sortie : pretty ou json.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="N'écrit aucun rapport sur disque.",
    ),
    force: bool = typer.Option(
        False, "--force", help="Écrase un rapport existant (avec backup).",
    ),
) -> None:
    """Diagnostique l'environnement et la présence des fichiers TricorderKit clés."""
    start = time.perf_counter()

    try:
        repo_root = _find_repo_root()
    except RuntimeError as exc:
        duration = int((time.perf_counter() - start) * 1000)
        emit_result(
            command="diagnose", status="error",
            summary="Racine du repo TricorderKit introuvable.",
            error_details={
                "code": "REPO_ROOT_NOT_FOUND",
                "message": str(exc),
                "recoverable": True,
                "rollback_available": False,
            },
            output_format=output, duration_ms=duration,
        )
        raise typer.Exit(code=EXIT_ENV_KO)

    # Détection environnement
    env_info = {
        "os": platform.system(),
        "os_release": platform.release(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "git": _run_silent(["git", "--version"]),
        "docker": _run_silent(["docker", "--version"]),
        "node": _run_silent(["node", "--version"]),
    }

    # Vérification fichiers clés
    expected_files = [
        ".tricorderkit/state.yml",
        ".tricorderkit/phase_gates.yml",
        ".tricorderkit/install_profile.yml",
        "scripts/validate_repo.py",
        "scripts/health_check.py",
        ".planning/STATE.md",
    ]
    files_status = {p: (repo_root / p).exists() for p in expected_files}
    missing = [p for p, present in files_status.items() if not present]

    # Mode dry-run : émettre un dry_run_report
    if dry_run:
        duration = int((time.perf_counter() - start) * 1000)
        emit_result(
            command="diagnose", status="dry_run",
            summary=f"Simulation: {len(expected_files) - len(missing)}/{len(expected_files)} fichiers présents.",
            data={
                "repo_root": str(repo_root),
                "environment": env_info,
                "files": files_status,
                "missing": missing,
            },
            dry_run_report={
                "actions_that_would_run": [
                    "Écrire reports/install/diagnose_YYYY-MM-DD.md",
                ],
                "estimated_tokens": 0,
                "estimated_duration_ms": 50,
                "risk_level": "LOW",
            },
            next_steps=["Relancer sans --dry-run pour générer le rapport."],
            output_format=output, duration_ms=duration,
        )
        raise typer.Exit(code=EXIT_OK)

    # Mode normal : écrire le rapport
    reports_dir = repo_root / "reports" / "install"
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y-%m-%d")
    report_path = reports_dir / f"diagnose_{date_tag}.md"

    # Anti-écrasement
    if report_path.exists() and not force:
        duration = int((time.perf_counter() - start) * 1000)
        emit_result(
            command="diagnose", status="error",
            summary=f"Rapport {report_path.name} existe déjà. --force requis.",
            error_details={
                "code": "FILE_EXISTS",
                "message": f"{report_path} existe déjà. Utiliser --force pour écraser (backup auto).",
                "recoverable": True,
                "rollback_available": True,
            },
            next_steps=[
                f"Relancer avec --force",
                f"Ou supprimer {report_path}",
            ],
            output_format=output, duration_ms=duration,
        )
        raise typer.Exit(code=EXIT_CONFLICT)

    # Backup si écrasement
    if report_path.exists() and force:
        backup_dir = reports_dir / "backups" / date_tag
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_name = f"{report_path.stem}_{int(time.time())}.md"
        shutil.copy2(report_path, backup_dir / backup_name)

    # Écriture du rapport Markdown
    lines = [
        f"# Diagnose Report — {date_tag}", "",
        f"- Repo root : `{repo_root}`",
        f"- OS : {env_info['os']} {env_info['os_release']}",
        f"- Python : {env_info['python']}",
        f"- Git : {env_info['git'].get('version') or 'absent'}",
        f"- Docker : {env_info['docker'].get('version') or 'absent'}",
        f"- Node : {env_info['node'].get('version') or 'absent'}",
        "", "## Fichiers attendus", "",
    ]
    for p, present in files_status.items():
        lines.append(f"- {'OK' if present else '--'} `{p}`")
    if missing:
        lines += ["", "## Manquants", ""] + [f"- {m}" for m in missing]
    report_path.write_text("\n".join(lines), encoding="utf-8")

    overall_status = "success" if not missing and env_info["git"]["available"] else "partial"
    summary = f"Diagnose: {len(expected_files) - len(missing)}/{len(expected_files)} files, "
    summary += f"git={'ok' if env_info['git']['available'] else 'absent'}."

    duration = int((time.perf_counter() - start) * 1000)
    emit_result(
        command="diagnose", status=overall_status, summary=summary,
        data={
            "repo_root": str(repo_root),
            "environment": env_info,
            "files": files_status,
            "missing": missing,
        },
        files_created=[str(report_path)],
        next_steps=["tk-installer status"] if not missing
                   else [f"Créer : {m}" for m in missing[:3]],
        output_format=output, duration_ms=duration,
    )
    raise typer.Exit(code=EXIT_OK if overall_status == "success" else EXIT_BUSINESS_ERROR)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
