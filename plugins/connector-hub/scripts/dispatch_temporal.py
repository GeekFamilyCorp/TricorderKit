#!/usr/bin/env python3
"""
dispatch_temporal.py — Déclencheur Temporal pour TricorderKit connector_hub

Déclenche le workflow sourceWatch via le SDK Python Temporal.
Fallback automatique vers temporalio si absent → npx ts-node trigger.

Usage :
  python dispatch_temporal.py --workflow source-watch --source mangadex anilist
  python dispatch_temporal.py --workflow source-watch --all --dry-run
  python dispatch_temporal.py --status <workflow_id>

Version : 0.1.0 — 2026-05-18
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────────
VERSION             = "0.1.0"
REPO_ROOT           = Path(__file__).resolve().parent.parent.parent.parent
TEMPORAL_ADDRESS    = os.environ.get("TEMPORAL_ADDRESS",    "localhost:7233")
TEMPORAL_NAMESPACE  = os.environ.get("TEMPORAL_NAMESPACE",  "default")
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "tricorderkit-hooks")
OBSIDIAN_VAULT      = os.environ.get("OBSIDIAN_VAULT_PATH", r"%USERPROFILE%\Documents\Claude\claude-vault")

# Workflow IDs déterministes (idempotence Temporal)
WORKFLOW_IDS = {
    "source-watch": "tricorderkit-source-watch-{date}",
    "usage-observer": "tricorderkit-usage-observer",
    "skill-eval": "tricorderkit-skill-eval-{date}",
}

# TypeScript trigger (fallback si temporalio Python SDK absent)
TS_TRIGGER = REPO_ROOT / "plugins" / "connector-hub" / "scripts" / "trigger_workflow.ts"
WORKFLOW_ENGINE = REPO_ROOT / "plugins" / "workflow-engine"


def build_output(status: str, data: dict) -> dict:
    return {
        "status": status,
        "skill_name": "dispatch-temporal",
        "skill_version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output": {**data, "next_steps": []},
    }


def dispatch_via_python_sdk(workflow: str, sources: list[str],
                             dry_run: bool, interval_minutes: int = 60) -> dict:
    """Déclenche via temporalio Python SDK."""
    try:
        import asyncio
        from temporalio.client import Client

        workflow_id = WORKFLOW_IDS.get(workflow, workflow).format(
            date=datetime.now().strftime("%Y%m%d")
        )

        input_payload = {
            "interval_minutes": interval_minutes,
            "sources": sources,
            "filters": {"min_score": 70, "languages": ["fr", "en"]},
            "obsidian_vault_path": OBSIDIAN_VAULT,
            "token_budget": {"max_tokens": 30000, "on_budget_exceeded": "pause_and_notify"},
        }

        if dry_run:
            return build_output("dry_run", {
                "workflow": workflow,
                "workflow_id": workflow_id,
                "task_queue": TEMPORAL_TASK_QUEUE,
                "address": TEMPORAL_ADDRESS,
                "input": input_payload,
                "message": "Dry-run: aucun workflow déclenché",
            })

        async def _start():
            client = await Client.connect(TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE)
            handle = await client.start_workflow(
                "sourceWatch",
                input_payload,
                id=workflow_id,
                task_queue=TEMPORAL_TASK_QUEUE,
            )
            return handle.id, handle.run_id

        wf_id, run_id = asyncio.run(_start())
        return build_output("success", {
            "workflow": workflow,
            "workflow_id": wf_id,
            "run_id": run_id,
            "task_queue": TEMPORAL_TASK_QUEUE,
            "address": TEMPORAL_ADDRESS,
            "sources": sources,
            "ui_url": f"http://localhost:8080/namespaces/{TEMPORAL_NAMESPACE}/workflows/{wf_id}",
        })

    except ImportError:
        return None  # SDK absent → fallback TS


def dispatch_via_typescript(workflow: str, sources: list[str],
                             dry_run: bool) -> dict:
    """Fallback : déclenche via npx ts-node trigger_workflow.ts."""
    trigger_script = WORKFLOW_ENGINE / "scripts" / "trigger_workflow.ts"

    if not trigger_script.exists():
        return build_output("error", {
            "message": f"Trigger TypeScript introuvable: {trigger_script}",
            "suggestion": "pip install temporalio pour utiliser le SDK Python",
        })

    env = {
        **os.environ,
        "TEMPORAL_ADDRESS":    TEMPORAL_ADDRESS,
        "TEMPORAL_NAMESPACE":  TEMPORAL_NAMESPACE,
        "TEMPORAL_TASK_QUEUE": TEMPORAL_TASK_QUEUE,
        "WORKFLOW_NAME":       workflow,
        "WORKFLOW_SOURCES":    ",".join(sources),
        "DRY_RUN":             "1" if dry_run else "0",
    }

    workflow_id = WORKFLOW_IDS.get(workflow, workflow).format(
        date=datetime.now().strftime("%Y%m%d")
    )
    env["WORKFLOW_ID"] = workflow_id

    if dry_run:
        return build_output("dry_run", {
            "workflow": workflow,
            "workflow_id": workflow_id,
            "mode": "typescript-trigger",
            "script": str(trigger_script),
            "message": "Dry-run: aucun workflow déclenché",
        })

    try:
        r = subprocess.run(
            ["npx", "ts-node", str(trigger_script)],
            capture_output=True, text=True, timeout=30,
            cwd=str(WORKFLOW_ENGINE), env=env,
        )
        if r.returncode == 0:
            return build_output("success", {
                "workflow": workflow,
                "workflow_id": workflow_id,
                "mode": "typescript-trigger",
                "stdout": r.stdout.strip()[:500],
            })
        return build_output("error", {
            "workflow": workflow,
            "returncode": r.returncode,
            "stderr": r.stderr.strip()[:500],
        })
    except FileNotFoundError:
        return build_output("error", {
            "message": "npx introuvable. Installer Node.js ou pip install temporalio.",
        })
    except subprocess.TimeoutExpired:
        return build_output("error", {
            "message": "Timeout npx ts-node (30s). Vérifier que Temporal est démarré.",
            "suggestion": "docker compose ps — vérifier service temporal",
        })


def cmd_dispatch(workflow: str, sources: list[str],
                 dry_run: bool, interval: int) -> dict:
    """Dispatch principal avec fallback automatique Python SDK → TypeScript."""
    # Tentative SDK Python
    result = dispatch_via_python_sdk(workflow, sources, dry_run, interval)
    if result is not None:
        return result

    # Fallback TypeScript
    return dispatch_via_typescript(workflow, sources, dry_run)


def cmd_status(workflow_id: str) -> dict:
    """Vérifie le statut d'un workflow Temporal via l'API REST."""
    url = (f"http://{TEMPORAL_ADDRESS.replace('7233', '8080')}"
           f"/api/v1/namespaces/{TEMPORAL_NAMESPACE}/workflows/{workflow_id}")
    try:
        import urllib.request
        req = urllib.request.urlopen(url, timeout=5)
        data = json.loads(req.read())
        status = data.get("workflowExecutionInfo", {}).get("status", "UNKNOWN")
        return build_output("success", {
            "workflow_id": workflow_id,
            "status": status,
            "ui_url": f"http://localhost:8080/namespaces/{TEMPORAL_NAMESPACE}/workflows/{workflow_id}",
        })
    except Exception as e:
        return build_output("error", {
            "workflow_id": workflow_id,
            "message": str(e),
            "suggestion": "Vérifier que Temporal UI tourne sur port 8080",
        })


def main():
    parser = argparse.ArgumentParser(
        description=f"dispatch_temporal v{VERSION} — Déclencheur Temporal TricorderKit"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--format", choices=["json", "table"], default="json")
    parser.add_argument("--version", action="version", version=f"dispatch-temporal {VERSION}")

    sub = parser.add_subparsers(dest="command")

    # dispatch
    p = sub.add_parser("dispatch", help="Déclenche un workflow Temporal")
    p.add_argument("--workflow", default="source-watch",
                   choices=list(WORKFLOW_IDS.keys()),
                   help="Nom du workflow à déclencher")
    p.add_argument("--source", nargs="+", dest="sources",
                   default=["mangadex", "anilist"],
                   help="Sources à surveiller")
    p.add_argument("--all", action="store_true", dest="all_sources",
                   help="Toutes les sources disponibles")
    p.add_argument("--interval", type=int, default=60,
                   help="Intervalle en minutes entre cycles (défaut: 60)")

    # status
    p = sub.add_parser("status", help="Vérifie le statut d'un workflow")
    p.add_argument("workflow_id", help="ID du workflow Temporal")

    args = parser.parse_args()

    if not args.command:
        sys.stdout.write(json.dumps({
            "status": "error",
            "message": "Commande requise: dispatch | status"
        }) + "\n")
        sys.stdout.flush()
        sys.exit(1)

    if args.command == "dispatch":
        sources = ["mangadex", "anilist", "jikan"] if args.all_sources else args.sources
        result = cmd_dispatch(args.workflow, sources, args.dry_run, args.interval)
    elif args.command == "status":
        result = cmd_status(args.workflow_id)
    else:
        result = {"status": "error", "message": f"Commande inconnue: {args.command}"}

    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
