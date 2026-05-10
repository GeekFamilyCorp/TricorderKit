#!/usr/bin/env python3
"""
health_check.py — TricorderKit v0.7
Dashboard santé système : vérifie Docker services + CLIs + registry + planning.
Usage :
    python scripts/health_check.py
    python scripts/health_check.py --output json
    python scripts/health_check.py --output html   # génère un rapport HTML
Output : pretty (défaut) | json | html
"""

import argparse
import json
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ── Services Docker à vérifier ─────────────────────────────────────────────
SERVICES = [
    {"name": "Neo4j",    "host": "localhost", "port": 7474, "url": "http://localhost:7474"},
    {"name": "Qdrant",   "host": "localhost", "port": 6333, "url": "http://localhost:6333/healthz"},
    {"name": "Temporal", "host": "localhost", "port": 7233, "url": None},
    {"name": "Langfuse", "host": "localhost", "port": 3000, "url": "http://localhost:3000"},
]


# ── Checks ──────────────────────────────────────────────────────────────────
def check_port(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def check_services() -> list:
    results = []
    for svc in SERVICES:
        up = check_port(svc["host"], svc["port"])
        results.append({
            "name":   svc["name"],
            "port":   svc["port"],
            "status": "up" if up else "down",
            "url":    svc.get("url"),
        })
    return results


def check_cli_registry() -> dict:
    registry = ROOT / "plugins" / "cli-forge" / "registry.yml"
    generated = ROOT / "plugins" / "cli-forge" / "generated"

    if not registry.exists():
        return {"status": "missing", "clis": []}

    clis = []
    if generated.exists():
        for d in sorted(generated.iterdir()):
            if d.is_dir():
                scripts = list(d.glob("*.py"))
                manifest = d / "manifest.yml"
                clis.append({
                    "name":          d.name,
                    "has_script":    bool(scripts),
                    "has_manifest":  manifest.exists(),
                    "status":        "ready" if scripts and manifest.exists() else "incomplete",
                })
    return {
        "status":     "ok" if registry.exists() else "missing",
        "total_clis": len(clis),
        "ready":      sum(1 for c in clis if c["status"] == "ready"),
        "clis":       clis,
    }


def check_planning() -> dict:
    planning = ROOT / ".planning"
    if not planning.exists():
        return {"status": "missing", "files": {}}

    expected = ["STATE.md", "TASKS.md", "DECISIONS.md", "RISKS.md"]
    files = {f: (planning / f).exists() for f in expected}
    roadmap = bool(list(planning.glob("ROADMAP*.md")))
    files["ROADMAP.md"] = roadmap

    complete = all(files.values())
    return {
        "status": "complete" if complete else "partial",
        "files":  files,
        "score":  round(sum(files.values()) / len(files) * 100),
    }


def check_plugins() -> dict:
    plugins_dir = ROOT / "plugins"
    if not plugins_dir.exists():
        return {"status": "missing", "plugins": []}

    plugins = []
    for d in sorted(plugins_dir.iterdir()):
        if d.is_dir():
            has_readme = (d / "README.md").exists()
            has_skill  = (d / "SKILL.md").exists()
            plugins.append({
                "name":   d.name,
                "readme": has_readme,
                "skill":  has_skill,
                "status": "complete" if (has_readme and has_skill) else "partial",
            })
    return {
        "status":   "ok",
        "total":    len(plugins),
        "complete": sum(1 for p in plugins if p["status"] == "complete"),
        "plugins":  plugins,
    }


def check_docker() -> dict:
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
            containers = []
            for line in lines:
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            running = [c for c in containers if c.get("State") == "running"]
            return {"status": "ok", "containers": len(containers),
                    "running": len(running), "details": containers}
        return {"status": "docker_compose_error", "error": result.stderr.strip()}
    except FileNotFoundError:
        return {"status": "docker_not_found"}
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}


# ── Score global ───────────────────────────────────────────────────────────
def compute_global_score(services, cli, planning, plugins) -> int:
    services_up   = sum(1 for s in services if s["status"] == "up")
    services_score = services_up / len(services) * 100 if services else 0
    cli_score      = (cli["ready"] / cli["total_clis"] * 100) if cli["total_clis"] else 50
    planning_score = planning.get("score", 0)
    plugins_score  = (plugins["complete"] / plugins["total"] * 100) if plugins["total"] else 50

    return round((services_score * 0.3 + cli_score * 0.2 +
                  planning_score * 0.3 + plugins_score * 0.2))


# ── HTML Report ────────────────────────────────────────────────────────────
def generate_html(data: dict) -> str:
    ts       = data["timestamp"]
    score    = data["global_score"]
    color    = "#22c55e" if score >= 80 else ("#f59e0b" if score >= 50 else "#ef4444")

    svc_rows = "".join(
        f'<tr><td>{s["name"]}</td>'
        f'<td style="color:{"#22c55e" if s["status"]=="up" else "#ef4444"}">'  
        f'{"🟢 UP" if s["status"]=="up" else "🔴 DOWN"}</td>'
        f'<td>{s["port"]}</td></tr>'
        for s in data["services"]
    )
    cli_rows = "".join(
        f'<tr><td>{c["name"]}</td>'
        f'<td style="color:{"#22c55e" if c["status"]=="ready" else "#f59e0b"}">'  
        f'{"✅ ready" if c["status"]=="ready" else "⚠️ incomplete"}</td></tr>'
        for c in data["cli"]["clis"]
    )
    plugin_rows = "".join(
        f'<tr><td>{p["name"]}</td>'
        f'<td style="color:{"#22c55e" if p["status"]=="complete" else "#f59e0b"}">'  
        f'{"✅" if p["status"]=="complete" else "⚠️"} {p["status"]}</td></tr>'
        for p in data["plugins"]["plugins"]
    )
    plan_rows = "".join(
        f'<tr><td>{f}</td>'
        f'<td style="color:{"#22c55e" if ok else "#ef4444"}">'  
        f'{"✅" if ok else "❌"}</td></tr>'
        for f, ok in data["planning"]["files"].items()
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>TricorderKit Health — {ts[:10]}</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background:#0f172a; color:#e2e8f0; margin:0; padding:20px; }}
  h1   {{ color:#7dd3fc; }} h2 {{ color:#94a3b8; border-bottom:1px solid #334155; padding-bottom:6px; }}
  .score {{ font-size:3rem; color:{color}; font-weight:bold; }}
  .grid  {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:20px; margin-top:20px; }}
  .card  {{ background:#1e293b; border-radius:8px; padding:16px; }}
  table  {{ width:100%; border-collapse:collapse; }}
  td,th  {{ padding:6px 10px; text-align:left; border-bottom:1px solid #334155; }}
  th     {{ color:#7dd3fc; font-size:.85rem; }}
  .ts    {{ color:#64748b; font-size:.8rem; }}
</style>
</head>
<body>
<h1>🚀 TricorderKit Health Dashboard</h1>
<p class="ts">Généré : {ts}</p>
<div class="score">{score}%</div>
<p>Status : <strong>{data["status"].upper()}</strong></p>

<div class="grid">

<div class="card">
<h2>🐳 Services Docker</h2>
<table><tr><th>Service</th><th>Status</th><th>Port</th></tr>
{svc_rows}
</table>
</div>

<div class="card">
<h2>⚡ CLIs Enregistrées</h2>
<p>{data["cli"]["ready"]}/{data["cli"]["total_clis"]} prêtes</p>
<table><tr><th>CLI</th><th>Status</th></tr>
{cli_rows}
</table>
</div>

<div class="card">
<h2>🔌 Plugins</h2>
<p>{data["plugins"]["complete"]}/{data["plugins"]["total"]} complets</p>
<table><tr><th>Plugin</th><th>Status</th></tr>
{plugin_rows}
</table>
</div>

<div class="card">
<h2>📋 Planning ({data["planning"]["score"]}%)</h2>
<table><tr><th>Fichier</th><th>Présent</th></tr>
{plan_rows}
</table>
</div>

</div>
</body>
</html>"""


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="health_check — TricorderKit v0.7")
    parser.add_argument("--output", choices=["pretty", "json", "html"], default="pretty")
    args = parser.parse_args()

    services = check_services()
    cli      = check_cli_registry()
    planning = check_planning()
    plugins  = check_plugins()
    docker   = check_docker()
    score    = compute_global_score(services, cli, planning, plugins)

    data = {
        "timestamp":    datetime.utcnow().isoformat() + "Z",
        "global_score": score,
        "status":       "healthy" if score >= 80 else ("partial" if score >= 50 else "critical"),
        "services":     services,
        "cli":          cli,
        "planning":     planning,
        "plugins":      plugins,
        "docker":       docker,
    }

    if args.output == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.output == "html":
        html = generate_html(data)
        out  = ROOT / "vault" / "reports" / f"health_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print(f"✅ Rapport HTML généré : {out}")
        args.output = "pretty"

    if args.output == "pretty":
        icon = {"healthy": "✅", "partial": "⚠️", "critical": "❌"}.get(data["status"], "?")
        print(f"\n{icon}  TricorderKit Health — {data['global_score']}% ({data['status'].upper()})")
        print(f"   {data['timestamp']}\n")

        print("🐳 Docker Services")
        for s in services:
            ico = "🟢" if s["status"] == "up" else "🔴"
            print(f"   {ico} {s['name']:12} port {s['port']}")

        print(f"\n⚡ CLIs : {cli['ready']}/{cli['total_clis']} prêtes")
        for c in cli.get("clis", []):
            ico = "✅" if c["status"] == "ready" else "⚠️"
            print(f"   {ico} {c['name']}")

        print(f"\n🔌 Plugins : {plugins['complete']}/{plugins['total']} complets")

        p = planning
        print(f"\n📋 Planning : {p.get('score',0)}% — {p['status']}")
        print()

    sys.exit(0 if data["status"] != "critical" else 1)


if __name__ == "__main__":
    main()
