"""
TricorderKit - Security Audit CLI (Phase 5)
Architecture : logique dans _run_* pures, CLI Typer en facade.
"""
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

app = typer.Typer(name="security-runner", help="TricorderKit Security Audit CLI - Phase 5", add_completion=False)
console = Console()

# ── Helpers ──────────────────────────────────────────────────────────────────

def _run(cmd: list, cwd: Optional[Path] = None) -> tuple:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd,
                            encoding="utf-8", errors="replace")
    return result.returncode, result.stdout, result.stderr

def _check_tool(name: str) -> bool:
    code, _, _ = _run(["where", name])
    return code == 0

def _print_result(label: str, ok: bool, detail: str = "") -> None:
    status = "[green]PASS[/green]" if ok else "[red]FAIL[/red]"
    console.print(f"  {status}  {label}")
    if detail and not ok:
        console.print(f"         [dim]{detail[:200]}[/dim]")


# ── Logique pure (appelable sans Typer) ──────────────────────────────────────

def _run_scan(path: Path, config: str = "auto", custom_rules: bool = True, strict: bool = True):
    console.print(Panel("[bold cyan]Semgrep Scan[/bold cyan]", expand=False))
    if not _check_tool("semgrep"):
        console.print("[red]semgrep introuvable. Installez-le : pip install semgrep[/red]")
        raise typer.Exit(1)
    cmd = ["semgrep", "--config", config, "--json", str(path),
           "--exclude-dir", "tests", "--exclude-dir", "tmp-pytest",
           "--exclude-dir", ".pytest_cache", "--exclude-dir", "__pycache__"]
    custom_dir = path / ".semgrep"
    if custom_rules and custom_dir.exists():
        for rule_file in custom_dir.glob("*.yaml"):
            cmd += ["--config", str(rule_file)]
    _, stdout, _ = _run(cmd)
    try:
        findings = json.loads(stdout).get("results", [])
    except json.JSONDecodeError:
        findings = []
    if not findings:
        _print_result("Aucune injection detectee", ok=True)
    else:
        _print_result(f"{len(findings)} finding(s) detecte(s)", ok=False)
        table = Table("Fichier", "Ligne", "Regle", "Code", show_header=True)
        for f in findings:
            table.add_row(f.get("path", "?"), str(f.get("start", {}).get("line", "?")),
                          f.get("check_id", "?"), f.get("extra", {}).get("lines", "").strip()[:80])
        console.print(table)
    if strict and findings:
        raise typer.Exit(1)

def _run_secrets(path: Path, strict: bool = True):
    console.print(Panel("[bold cyan]Gitleaks Scan[/bold cyan]", expand=False))
    if not _check_tool("gitleaks"):
        console.print("[yellow]gitleaks introuvable - skip.[/yellow]")
        return
    cmd = ["gitleaks", "detect", "--source", str(path), "--no-git", "--exit-code", "1"]
    code, _, stderr = _run(cmd)
    ok = (code == 0)
    _print_result("Aucun secret detecte" if ok else "Secrets detectes", ok=ok,
                  detail=stderr.strip() if not ok else "")
    if not ok and strict:
        raise typer.Exit(1)

def _run_deps(path: Path, severity: str = "HIGH,CRITICAL", strict: bool = True):
    console.print(Panel("[bold cyan]Trivy Dependency Scan[/bold cyan]", expand=False))
    if not _check_tool("trivy"):
        console.print("[yellow]trivy introuvable - skip.[/yellow]")
        return
    cmd = ["trivy", "fs", str(path), "--severity", severity, "--format", "table", "--exit-code", "1"]
    code, stdout, _ = _run(cmd)
    ok = (code == 0)
    _print_result(f"Aucune CVE {severity}" if ok else f"CVEs {severity} detectees", ok=ok,
                  detail=stdout[:300] if not ok else "")
    if not ok and strict:
        raise typer.Exit(1)


def _run_docker(compose_file: Path, strict: bool = True):
    console.print(Panel("[bold cyan]Docker Port Bind Check[/bold cyan]", expand=False))
    if not compose_file.exists():
        console.print(f"[yellow]{compose_file} introuvable - skip.[/yellow]")
        return
    content = compose_file.read_text(encoding="utf-8", errors="replace")
    unsafe = re.compile(r'[-]\s+"?(?!127\.0\.0\.1:)(\d{2,5}:\d{2,5})"?', re.MULTILINE)
    exposed = re.compile(r'[-]\s+"?0\.0\.0\.0:\d+:\d+"?', re.MULTILINE)
    risky = unsafe.findall(content) + exposed.findall(content)
    ok = len(risky) == 0
    _print_result("Tous les ports sur 127.0.0.1" if ok else f"{len(risky)} port(s) exposes",
                  ok=ok, detail=f"Ports: {risky}" if not ok else "")
    if not ok:
        console.print("[yellow]Fix : remplacez '- 3001:3001' par '- 127.0.0.1:3001:3001'[/yellow]")
    if not ok and strict:
        raise typer.Exit(1)

def _run_uuid(path: Path, strict: bool = True):
    console.print(Panel("[bold cyan]UUID / SHA-1 Check[/bold cyan]", expand=False))
    sha1_pat = re.compile(r"hashlib\.sha1|\.sha1\(|sha1\s*=", re.IGNORECASE)
    findings = []
    EXCLUDED = {".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "tests", "tmp-pytest"}
    for py_file in path.rglob("*.py"):
        try:
            rel_parts = py_file.relative_to(path).parts
        except ValueError:
            rel_parts = py_file.parts
        if any(p in EXCLUDED for p in rel_parts):
            continue
        for i, line in enumerate(py_file.read_text(errors="ignore").splitlines(), 1):
            if sha1_pat.search(line):
                findings.append((str(py_file), i, line.strip()))
    ok = len(findings) == 0
    _print_result("Aucun SHA-1 detecte" if ok else f"{len(findings)} SHA-1 detecte(s)", ok=ok)
    if not ok:
        table = Table("Fichier", "Ligne", "Code", show_header=True)
        for f, l, c in findings:
            table.add_row(f, str(l), c[:80])
        console.print(table)
        console.print("[yellow]Fix : uuid.uuid4() ou uuid.uuid5(uuid.NAMESPACE_DNS, name)[/yellow]")
    if not ok and strict:
        raise typer.Exit(1)


# ── Facade CLI Typer ──────────────────────────────────────────────────────────

@app.command()
def scan(path: Path = typer.Argument(Path(".")), config: str = typer.Option("auto"),
         custom_rules: bool = typer.Option(True), strict: bool = typer.Option(True)):
    """Semgrep - detection injections OS et shell=True."""
    _run_scan(path=path, config=config, custom_rules=custom_rules, strict=strict)

@app.command()
def secrets(path: Path = typer.Argument(Path(".")), strict: bool = typer.Option(True)):
    """Gitleaks - detection fuites de tokens et cles API."""
    _run_secrets(path=path, strict=strict)

@app.command()
def deps(path: Path = typer.Argument(Path(".")), severity: str = typer.Option("HIGH,CRITICAL"),
         strict: bool = typer.Option(True)):
    """Trivy - audit dependances CVEs HIGH/CRITICAL."""
    _run_deps(path=path, severity=severity, strict=strict)

@app.command()
def docker(compose_file: Path = typer.Argument(Path("docker-compose.yml")),
           strict: bool = typer.Option(True)):
    """Docker - verifie ports non binded sur 0.0.0.0."""
    _run_docker(compose_file=compose_file, strict=strict)

@app.command()
def uuid(path: Path = typer.Argument(Path(".")), strict: bool = typer.Option(True)):
    """UUID - detecte SHA-1 pour generation d IDs."""
    _run_uuid(path=path, strict=strict)

@app.command(name="full-audit")
def full_audit(path: Path = typer.Argument(Path(".")), strict: bool = typer.Option(False)):
    """Full Audit - scan + secrets + deps + docker + uuid en sequence."""
    console.print(Panel(f"[bold white]TricorderKit - Full Security Audit[/bold white]\n"
                        f"[dim]Cible : {path.resolve()}[/dim]", style="bold blue", expand=False))
    results: dict = {}
    checks = [
        ("scan",    lambda: _run_scan(path=path, strict=True)),
        ("secrets", lambda: _run_secrets(path=path, strict=True)),
        ("deps",    lambda: _run_deps(path=path, strict=True)),
        ("docker",  lambda: _run_docker(compose_file=path / "docker-compose.yml", strict=True)),
        ("uuid",    lambda: _run_uuid(path=path, strict=True)),
    ]
    for name, fn in checks:
        try:
            fn()
            results[name] = True
        except SystemExit as e:
            results[name] = (int(e.code) == 0)
        except Exception as ex:
            console.print(f"[red]Erreur {name} : {ex}[/red]")
            results[name] = False
        console.print()
    console.print(Panel("[bold]Resume Full Audit[/bold]", expand=False))
    table = Table("Check", "Statut", show_header=True)
    all_ok = True
    for name, ok in results.items():
        table.add_row(name, "[green]PASS[/green]" if ok else "[red]FAIL[/red]")
        if not ok:
            all_ok = False
    console.print(table)
    if strict and not all_ok:
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
