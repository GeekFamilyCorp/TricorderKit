#!/usr/bin/env python3
"""
generate_status.py — TricorderKit v0.9
Génère STATUS.md (racine du repo) + optionnellement un rapport Markdown daté.

Usage :
    python scripts/generate_status.py
    python scripts/generate_status.py --output json
    python scripts/generate_status.py --report          # + reports/status_YYYY-MM-DD.md
    python scripts/generate_status.py --no-status-md    # rapport seul (pas de STATUS.md)

Données collectées :
  - Services Docker (ping socket)
  - Méta repo (version, commit, branch)
  - Statistiques hooks (.cache/hooks/*.log)
  - Cycles workflow (.cache/hooks/workflow_cycles.log)
  - Alertes budget (.cache/hooks/budget_alerts.log)
  - Plugins actifs (plugins/ + skills/)
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Chemins ────────────────────────────────────────────────────────────────────
ROOT            = Path(__file__).resolve().parent.parent
HOOKS_CACHE_DIR = ROOT / ".cache" / "hooks"
BOOT_SUMMARY    = ROOT / "BOOT_SUMMARY.md"
STATUS_MD       = ROOT / "STATUS.md"
REPORTS_DIR     = ROOT / "reports"

# ── Services ───────────────────────────────────────────────────────────────────
SERVICES = [
    {"name": "Neo4j",    "port": 7474, "url": "http://localhost:7474"},
    {"name": "Qdrant",   "port": 6333, "url": "http://localhost:6333/healthz"},
    {"name": "Langfuse", "port": 3001, "url": "http://localhost:3001"},
    {"name": "Temporal", "port": 7233, "url": None},
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def _check_port(port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection(("localhost", port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, cwd=ROOT, timeout=5
        ).stdout.strip()
    except Exception:
        return ""

def _load_jsonl(path: Path, last_n: int | None = None) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if last_n is not None:
        lines = lines[-last_n:]
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return result

def _boot_summary_value(key: str) -> str:
    """Extrait une valeur de BOOT_SUMMARY.md (format tableau Markdown)."""
    if not BOOT_SUMMARY.exists():
        return "unknown"
    for line in BOOT_SUMMARY.read_text(encoding="utf-8").splitlines():
        if f"| {key} |" in line or f"| **{key}**" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            return parts[-1].strip("*") if len(parts) >= 2 else "unknown"
    return "unknown"


# ── Collecteurs de données ──────────────────────────────────────────────────────

def collect_services() -> list[dict]:
    results = []
    for svc in SERVICES:
        up = _check_port(svc["port"])
        results.append({
            "name": svc["name"],
            "port": svc["port"],
            "url":  svc.get("url"),
            "up":   up,
            "status": "up" if up else "down",
        })
    return results


def collect_repo_meta() -> dict:
    commit = _git("rev-parse", "--short", "HEAD")
    branch = _git("branch", "--show-current")
    version = _boot_summary_value("Version")
    tests   = _boot_summary_value("Tests")
    return {
        "version": version,
        "commit":  commit or "unknown",
        "branch":  branch or "main",
        "tests":   tests,
        "generated_at": _now(),
    }


def collect_hook_stats(last_n: int = 200) -> dict:
    """Agrège les logs pre/post_execution par skill."""
    post_log  = HOOKS_CACHE_DIR / "post_execution.log"
    pre_log   = HOOKS_CACHE_DIR / "pre_execution.log"
    intent_log = HOOKS_CACHE_DIR / "pre_intent.log"

    post_records  = _load_jsonl(post_log, last_n)
    pre_records   = _load_jsonl(pre_log, last_n)
    intent_records = _load_jsonl(intent_log, last_n)

    # Agréger post_execution par skill
    by_skill: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "runs": 0, "quality_scores": [], "tokens": [], "errors": 0
    })
    for rec in post_records:
        skill = (rec.get("skill") or rec.get("plan", {}).get("skill")
                 or rec.get("skill_id") or "unknown")
        s = by_skill[skill]
        s["runs"] += 1
        qs = rec.get("quality_score")
        if qs is not None:
            s["quality_scores"].append(float(qs))
        tok = rec.get("tokens_used") or rec.get("token_cost") or 0
        if tok:
            s["tokens"].append(int(tok))
        if rec.get("status") == "error" or (qs is not None and float(qs) < 0.4):
            s["errors"] += 1

    skills_summary = []
    for skill, data in sorted(by_skill.items()):
        scores = data["quality_scores"]
        tokens = data["tokens"]
        skills_summary.append({
            "skill":         skill,
            "runs":          data["runs"],
            "avg_score":     round(sum(scores) / len(scores), 2) if scores else None,
            "error_rate":    round(data["errors"] / data["runs"], 2) if data["runs"] else 0,
            "total_tokens":  sum(tokens),
            "avg_tokens":    round(sum(tokens) / len(tokens)) if tokens else 0,
        })

    return {
        "post_records":   len(post_records),
        "pre_records":    len(pre_records),
        "intent_records": len(intent_records),
        "skills":         skills_summary,
        "total_runs":     sum(s["runs"] for s in skills_summary),
    }


def collect_workflow_cycles(last_n: int = 50) -> dict:
    records = _load_jsonl(HOOKS_CACHE_DIR / "workflow_cycles.log", last_n)
    by_wf: dict[str, dict] = defaultdict(lambda: {"cycles": 0, "last_run": None})
    for rec in records:
        wf = rec.get("workflow", "unknown")
        by_wf[wf]["cycles"] += 1
        ts = rec.get("timestamp")
        if ts:
            prev = by_wf[wf]["last_run"]
            by_wf[wf]["last_run"] = ts if not prev or ts > prev else prev

    return {
        "total_records": len(records),
        "workflows":     [{"name": k, **v} for k, v in sorted(by_wf.items())],
    }


def collect_budget_alerts(last_n: int = 20) -> dict:
    records = _load_jsonl(HOOKS_CACHE_DIR / "budget_alerts.log", last_n)
    return {
        "total_alerts": len(records),
        "recent":       records[-5:] if records else [],
    }


def collect_plugins() -> dict:
    plugins_dir = ROOT / "plugins"
    plugins = []
    if plugins_dir.exists():
        for d in sorted(plugins_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                has_manifest = (d / "manifest.yml").exists()
                has_skill    = (d / "SKILL.md").exists()
                plugins.append({
                    "name": d.name,
                    "has_manifest": has_manifest,
                    "has_skill":    has_skill,
                })
    skills_dir = ROOT / "skills"
    skills = []
    if skills_dir.exists():
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir():
                skills.append(d.name)
    return {"plugins": plugins, "skills": skills}


# ── Formateurs ─────────────────────────────────────────────────────────────────

def _svc_icon(up: bool) -> str:
    return "🟢" if up else "🔴"

def _score_icon(score: float | None) -> str:
    if score is None: return "—"
    if score >= 0.8:  return "🟢"
    if score >= 0.5:  return "🟡"
    return "🔴"


def format_status_md(data: dict) -> str:
    meta       = data["meta"]
    services   = data["services"]
    hooks      = data["hooks"]
    workflows  = data["workflows"]
    budget     = data["budget"]
    plugins    = data["plugins"]

    services_all_up = all(s["up"] for s in services)
    overall_icon    = "🟢" if services_all_up else "🔴"

    lines = [
        "---",
        f"generated: {meta['generated_at']}",
        f"version: {meta['version']}",
        f"commit: {meta['commit']}",
        f"branch: {meta['branch']}",
        "---",
        "",
        "# TricorderKit — STATUS",
        "",
        f"> Auto-généré le {meta['generated_at'][:10]}. Actualiser : `python cli/tk.py report generate`",
        "",
        f"## {overall_icon} Vue d'ensemble",
        "",
        f"| Champ | Valeur |",
        f"|---|---|",
        f"| Version | `{meta['version']}` |",
        f"| Commit | `{meta['commit']}` ({meta['branch']}) |",
        f"| Tests | {meta['tests']} |",
        f"| Généré | {meta['generated_at'][:16].replace('T', ' ')} UTC |",
        "",
        "## 🐳 Services Docker",
        "",
        "| Service | Port | Statut |",
        "|---------|------|--------|",
    ]
    for svc in services:
        icon = _svc_icon(svc["up"])
        url  = f" [{svc['url']}]({svc['url']})" if svc.get("url") else ""
        lines.append(f"| {svc['name']} | {svc['port']} | {icon} {svc['status']}{url} |")

    lines += [
        "",
        "## 🪝 Hooks — statistiques",
        "",
        f"Données : {hooks['post_records']} enregistrements post-execution "
        f"/ {hooks['intent_records']} intents.",
        "",
    ]

    if hooks["skills"]:
        lines += [
            "| Skill | Runs | Avg Score | Erreurs | Tokens totaux |",
            "|-------|------|-----------|---------|---------------|",
        ]
        for s in hooks["skills"][:15]:
            score_s = f"{_score_icon(s['avg_score'])} {s['avg_score']}" if s["avg_score"] is not None else "—"
            err_s   = f"{s['error_rate']*100:.0f}%"
            lines.append(
                f"| `{s['skill']}` | {s['runs']} | {score_s} | {err_s} | {s['total_tokens']:,} |"
            )
    else:
        lines.append("_Aucun enregistrement dans .cache/hooks/post_execution.log_")

    lines += [
        "",
        "## ⏱️ Cycles workflow",
        "",
    ]
    if workflows["workflows"]:
        lines += [
            "| Workflow | Cycles | Dernier run |",
            "|----------|--------|-------------|",
        ]
        for wf in workflows["workflows"]:
            last = (wf["last_run"] or "—")[:16].replace("T", " ") if wf["last_run"] else "—"
            lines.append(f"| `{wf['name']}` | {wf['cycles']} | {last} |")
    else:
        lines.append("_Aucun cycle dans .cache/hooks/workflow_cycles.log_")

    lines += ["", "## 💰 Alertes budget", ""]
    if budget["total_alerts"] == 0:
        lines.append("✅ Aucune alerte budget.")
    else:
        lines.append(f"⚠️ **{budget['total_alerts']} alerte(s)** au total.")
        if budget["recent"]:
            lines += ["", "| Workflow | Tokens | Date |", "|----------|--------|------|"]
            for a in budget["recent"]:
                ts = (a.get("timestamp") or "")[:16].replace("T", " ")
                lines.append(
                    f"| `{a.get('workflow', '?')}` | {a.get('tokens_used', '?'):,} | {ts} |"
                )

    lines += ["", "## 🔌 Plugins actifs", ""]
    if plugins["plugins"]:
        active = [p["name"] for p in plugins["plugins"] if p["has_manifest"] or p["has_skill"]]
        lines.append(f"`{'` · `'.join(active)}`" if active else "_Aucun plugin actif_")
    if plugins["skills"]:
        lines += ["", f"**Skills** : `{'` · `'.join(plugins['skills'])}`"]

    lines += [
        "",
        "---",
        "",
        f"*Généré automatiquement — TricorderKit v0.9 — {meta['generated_at'][:10]}*",
    ]

    return "\n".join(lines) + "\n"


def format_report_md(data: dict) -> str:
    """Rapport Markdown plus détaillé pour reports/."""
    meta = data["meta"]
    header = f"""---
type: observability_report
date: {meta['generated_at'][:10]}
version: {meta['version']}
commit: {meta['commit']}
generated_by: generate_status.py
---

# Rapport d'observabilité — TricorderKit {meta['version']}

> Généré le {meta['generated_at'][:16].replace('T', ' ')} UTC · commit `{meta['commit']}`

"""
    return header + format_status_md(data).split("# TricorderKit — STATUS\n", 1)[-1]


# ── Collecteur principal ───────────────────────────────────────────────────────

def collect_all() -> dict:
    return {
        "meta":      collect_repo_meta(),
        "services":  collect_services(),
        "hooks":     collect_hook_stats(),
        "workflows": collect_workflow_cycles(),
        "budget":    collect_budget_alerts(),
        "plugins":   collect_plugins(),
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="generate_status.py — TricorderKit dashboard")
    parser.add_argument("--output",       choices=["pretty", "json", "md"], default="pretty")
    parser.add_argument("--report",       action="store_true",
                        help="Générer aussi un rapport daté dans reports/")
    parser.add_argument("--no-status-md", action="store_true",
                        help="Ne pas écrire STATUS.md à la racine")
    args = parser.parse_args()

    data = collect_all()

    if args.output == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    status_content = format_status_md(data)

    if args.output == "md":
        print(status_content)
        return

    # Écrire STATUS.md
    if not args.no_status_md:
        STATUS_MD.write_text(status_content, encoding="utf-8")
        print(f"✅ STATUS.md mis à jour ({STATUS_MD})")

    # Rapport daté optionnel
    if args.report:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts    = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        rpath = REPORTS_DIR / f"status_{ts}.md"
        rpath.write_text(format_report_md(data), encoding="utf-8")
        print(f"✅ Rapport créé : {rpath}")

    # Résumé terminal
    meta     = data["meta"]
    services = data["services"]
    up_count = sum(1 for s in services if s["up"])
    print()
    print(f"TricorderKit {meta['version']} · commit {meta['commit']}")
    print(f"Services : {up_count}/{len(services)} actifs")
    print(f"Tests    : {meta['tests']}")
    hooks_runs = data["hooks"]["total_runs"]
    if hooks_runs:
        print(f"Hooks    : {hooks_runs} runs enregistrés")
    budget_alerts = data["budget"]["total_alerts"]
    if budget_alerts:
        print(f"Budget   : ⚠️  {budget_alerts} alerte(s)")
    else:
        print("Budget   : ✅ aucune alerte")
    print()


if __name__ == "__main__":
    main()
