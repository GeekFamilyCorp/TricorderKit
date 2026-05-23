"""
TricorderKit — Security Audit CLI (Phase 5)
security_runner.py

Commandes disponibles :
  scan        → Semgrep : détection injection de commandes OS
  secrets     → Gitleaks : fuite de tokens/clés API
  deps        → Trivy : vulnérabilités de dépendances
  docker      → Vérifie les binds Docker (0.0.0.0 vs 127.0.0.1)
  uuid        → Vérifie l'usage de SHA-1 vs UUID v4/v5 dans la codebase
  full-audit  → Exécute tous les checks en séquence

Chaque commande retourne un exit code 0 (OK) ou 1 (FAIL) → bloquable en CI/Pre-Execution Hook.
"""

import os
import platform
import subprocess
import sys
import re
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

app = typer.Typer(
    name="security-runner",
    help="TricorderKit Security Audit CLI -- Phase 5",
    add_completion=False,
)

# En contexte non-interactif (tâche planifiée, CI) : mode texte pur, sans couleurs,
# sans rendu legacy Windows qui bascule en cp1252 et plante sur les emoji Unicode.
_interactive = sys.stdout.isatty()
console = Console(
    force_terminal=_interactive,
    no_color=not _interactive,
    highlight=_interactive,
)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _run(cmd: list[str], cwd: Optional[Path] = None) -> tuple[int, str, str]:
    """Exécute une commande et retourne (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,                    # Toujours une liste — jamais shell=True
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd,
    )
    return result.returncode, result.stdout, result.stderr


def _check_tool(name: str) -> bool:
    """Vérifie qu'un outil est disponible dans le PATH (compatible Windows/Unix)."""
    cmd = ["where", name] if platform.system() == "Windows" else ["which", name]
    try:
        code, _, _ = _run(cmd)
        return code == 0
    except FileNotFoundError:
        return False


def _print_result(label: str, ok: bool, detail: str = "") -> None:
    if _interactive:
        status = "[green]OK  PASS[/green]" if ok else "[red]!! FAIL[/red]"
    else:
        status = "PASS" if ok else "FAIL"
    console.print(f"  {status}  {label}")
    if detail and not ok:
        console.print(f"         {detail}")


# ─────────────────────────────────────────────
# Commande : scan (Semgrep)
# ─────────────────────────────────────────────

@app.command()
def scan(
    path: Path = typer.Argument(Path("."), help="Répertoire à scanner"),
    config: str = typer.Option("auto", help="Config Semgrep (auto, p/python, p/command-injection, ou chemin local)"),
    custom_rules: bool = typer.Option(True, help="Inclure les règles custom .semgrep/"),
    strict: bool = typer.Option(True, help="Exit 1 si des findings sont détectés"),
):
    """🔍 Semgrep — détection d'injections OS et de shell=True."""
    console.print(Panel("[bold cyan]Semgrep Scan[/bold cyan]", expand=False))

    if not _check_tool("semgrep"):
        console.print("[yellow]⚠️  semgrep introuvable — skip. Installez-le : pip install semgrep[/yellow]")
        return

    cmd = ["semgrep", "--config", config, "--json", str(path)]

    # Ajout des règles custom si présentes
    custom_dir = path / ".semgrep"
    if custom_rules and custom_dir.exists():
        for rule_file in custom_dir.glob("*.yaml"):
            cmd += ["--config", str(rule_file)]

    code, stdout, stderr = _run(cmd)

    import json
    try:
        findings = json.loads(stdout).get("results", [])
    except json.JSONDecodeError:
        findings = []

    if not findings:
        _print_result("Aucune injection détectée", ok=True)
    else:
        _print_result(f"{len(findings)} finding(s) détecté(s)", ok=False)
        table = Table("Fichier", "Ligne", "Règle", "Code", show_header=True)
        for f in findings:
            table.add_row(
                f.get("path", "?"),
                str(f.get("start", {}).get("line", "?")),
                f.get("check_id", "?"),
                f.get("extra", {}).get("lines", "").strip()[:80],
            )
        console.print(table)

    if strict and findings:
        raise typer.Exit(1)


# ─────────────────────────────────────────────
# Commande : secrets (Gitleaks)
# ─────────────────────────────────────────────

@app.command()
def secrets(
    path: Path = typer.Argument(Path("."), help="Répertoire à scanner"),
    strict: bool = typer.Option(True, help="Exit 1 si des secrets sont trouvés"),
):
    """🔑 Gitleaks — détection de fuites de tokens et clés API."""
    console.print(Panel("[bold cyan]Gitleaks Scan[/bold cyan]", expand=False))

    if not _check_tool("gitleaks"):
        console.print("[yellow]⚠️  gitleaks introuvable — skip.[/yellow]")
        return

    cmd = ["gitleaks", "detect", "--source", str(path), "--no-git", "--exit-code", "1"]
    code, stdout, stderr = _run(cmd)

    ok = (code == 0)
    detail = stderr.strip() if not ok else ""
    _print_result("Aucun secret détecté" if ok else "Secrets détectés", ok=ok, detail=detail)

    if not ok and strict:
        raise typer.Exit(1)


# ─────────────────────────────────────────────
# Commande : deps (Trivy)
# ─────────────────────────────────────────────

@app.command()
def deps(
    path: Path = typer.Argument(Path("."), help="Répertoire à scanner"),
    severity: str = typer.Option("HIGH,CRITICAL", help="Niveaux de sévérité à remonter"),
    strict: bool = typer.Option(True, help="Exit 1 si des CVEs sont trouvées"),
):
    """📦 Trivy — audit des dépendances (CVEs HIGH/CRITICAL)."""
    console.print(Panel("[bold cyan]Trivy Dependency Scan[/bold cyan]", expand=False))

    if not _check_tool("trivy"):
        console.print("[yellow]⚠️  trivy introuvable — skip.[/yellow]")
        return

    cmd = [
        "trivy", "fs", str(path),
        "--severity", severity,
        "--format", "table",
        "--exit-code", "1",
    ]
    code, stdout, stderr = _run(cmd)

    ok = (code == 0)
    _print_result(
        f"Aucune CVE {severity}" if ok else f"CVEs {severity} détectées",
        ok=ok,
        detail=stdout[:500] if not ok else "",
    )
    console.print(stdout[:1000])

    if not ok and strict:
        raise typer.Exit(1)


# ─────────────────────────────────────────────
# Commande : docker (bind check)
# ─────────────────────────────────────────────

@app.command()
def docker(
    compose_file: Path = typer.Argument(Path("docker-compose.yml"), help="Chemin du docker-compose.yml"),
    strict: bool = typer.Option(True, help="Exit 1 si des ports sont exposés sur 0.0.0.0"),
):
    """🐳 Docker — vérifie que les ports ne sont pas bindés sur 0.0.0.0."""
    console.print(Panel("[bold cyan]Docker Port Bind Check[/bold cyan]", expand=False))

    if not compose_file.exists():
        console.print(f"[yellow]⚠️  {compose_file} introuvable — skip.[/yellow]")
        return

    content = compose_file.read_text(encoding="utf-8", errors="replace")

    # Pattern : "- 3001:3001" ou "- 0.0.0.0:3001:3001" (sans bind explicite = risque)
    unsafe_pattern = re.compile(
        r'[-]\s+"?(?!127\.0\.0\.1:)(\d{2,5}:\d{2,5})"?',
        re.MULTILINE
    )
    exposed = re.compile(
        r'[-]\s+"?0\.0\.0\.0:\d+:\d+"?',
        re.MULTILINE
    )

    risky_lines = unsafe_pattern.findall(content) + exposed.findall(content)
    ok = len(risky_lines) == 0

    _print_result(
        "Tous les ports bindés sur 127.0.0.1" if ok else f"{len(risky_lines)} port(s) exposé(s) sur réseau",
        ok=ok,
        detail=f"Ports à risque : {risky_lines}" if not ok else "",
    )

    if not ok:
        console.print(
            "[yellow]💡 Fix : remplacez '- 3001:3001' par '- 127.0.0.1:3001:3001' dans docker-compose.yml[/yellow]"
        )

    if not ok and strict:
        raise typer.Exit(1)


# ─────────────────────────────────────────────
# Commande : uuid (SHA-1 detection)
# ─────────────────────────────────────────────

@app.command()
def uuid(
    path: Path = typer.Argument(Path("."), help="Répertoire à scanner"),
    strict: bool = typer.Option(True, help="Exit 1 si SHA-1 détecté pour les IDs"),
):
    """🔢 UUID — détecte l'usage de SHA-1 pour la génération d'IDs (→ risque de collision)."""
    console.print(Panel("[bold cyan]UUID / SHA-1 Check[/bold cyan]", expand=False))

    sha1_pattern = re.compile(
        r"hashlib\.sha1|\.sha1\(|sha1\s*=|digest\(\).*sha1",
        re.IGNORECASE
    )

    findings = []
    for py_file in path.rglob("*.py"):
        # Exclure venvs et node_modules
        if any(p in py_file.parts for p in [".venv", "venv", "node_modules", "__pycache__", "tests"]):
            continue
        lines = py_file.read_text(errors="ignore").splitlines()
        for i, line in enumerate(lines, start=1):
            if sha1_pattern.search(line):
                findings.append((str(py_file), i, line.strip()))

    ok = len(findings) == 0
    _print_result(
        "Aucun SHA-1 pour IDs détecté" if ok else f"{len(findings)} usage(s) de SHA-1 détecté(s)",
        ok=ok,
    )

    if not ok:
        table = Table("Fichier", "Ligne", "Code", show_header=True)
        for f, l, code in findings:
            table.add_row(f, str(l), code[:80])
        console.print(table)
        console.print("[yellow]💡 Fix : remplacez sha1 par uuid.uuid4() ou uuid.uuid5(uuid.NAMESPACE_DNS, name)[/yellow]")

    if not ok and strict:
        raise typer.Exit(1)


# ─────────────────────────────────────────────
# Commande : full-audit
# ─────────────────────────────────────────────

@app.command(name="full-audit")
def full_audit(
    path: Path = typer.Argument(Path("."), help="Répertoire racine du projet"),
    strict: bool = typer.Option(False, help="Exit 1 global si au moins un check échoue"),
):
    """🛡️  Full Audit — exécute scan + secrets + deps + docker + uuid en séquence."""
    console.print(Panel(
        "[bold white]TricorderKit — Full Security Audit[/bold white]\n"
        f"[dim]Cible : {path.resolve()}[/dim]",
        style="bold blue",
        expand=False,
    ))

    results: dict[str, bool] = {}

    # En full-audit, chaque check tourne en mode strict=True
    # pour qu'un Exit(1) soit levé en cas de finding → capturé ici
    checks = [
        ("scan",    lambda: scan(path=path, config="auto", custom_rules=True, strict=True)),
        ("secrets", lambda: secrets(path=path, strict=True)),
        ("deps",    lambda: deps(path=path, severity="HIGH,CRITICAL", strict=True)),
        ("docker",  lambda: docker(compose_file=path / "docker-compose.yml", strict=True)),
        ("uuid",    lambda: uuid(path=path, strict=True)),
    ]

    for name, fn in checks:
        try:
            fn()
            results[name] = True
        except (SystemExit, typer.Exit) as e:
            # typer.Exit utilise .exit_code (v0.12+), SystemExit utilise .code
            raw = getattr(e, "exit_code", None) if isinstance(e, typer.Exit) else getattr(e, "code", 1)
            results[name] = (int(raw or 0) == 0)
        except Exception as ex:
            console.print(f"[red]Erreur sur {name} : {ex}[/red]")
            results[name] = False
        console.print()

    # Résumé final
    console.print(Panel("[bold]Résumé du Full Audit[/bold]", expand=False))
    table = Table("Check", "Statut", show_header=True)
    all_ok = True
    for name, ok in results.items():
        if _interactive:
            status_cell = "[green]PASS[/green]" if ok else "[red]FAIL[/red]"
        else:
            status_cell = "PASS" if ok else "FAIL"
        table.add_row(name, status_cell)
        if not ok:
            all_ok = False
    console.print(table)

    if strict and not all_ok:
        raise typer.Exit(1)


# ─────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app()
