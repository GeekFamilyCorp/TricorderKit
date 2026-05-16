#!/usr/bin/env python3
"""
post_session_hook.py — Claude Code Stop hook
Déclenche usageObserverWorkflow via le client Temporal Python
au moment où Claude termine sa réponse (événement Stop).

Version : 0.1.0
Policy  : docs/05_hooks_policy.md — intercepteur léger, fail silently
Prérequis : pip install temporalio --break-system-packages
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

TEMPORAL_ADDRESS   = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TEMPORAL_TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "tricorderkit-hooks")
WORKFLOW_ID_PREFIX = "usage-observer-auto"


async def _trigger() -> None:
    try:
        from temporalio.client import Client  # type: ignore[import]
    except ImportError:
        print("[post_session] temporalio non installé — trigger ignoré", file=sys.stderr)
        return

    try:
        client = await Client.connect(TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE)
        wf_id = f"{WORKFLOW_ID_PREFIX}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
        await client.start_workflow(
            "usageObserverWorkflow",
            {"max_runs": 1, "token_budget": 2000},
            id=wf_id,
            task_queue=TEMPORAL_TASK_QUEUE,
        )
        print(f"[post_session] usageObserverWorkflow démarré : {wf_id}", file=sys.stderr)
    except Exception as exc:
        # Fail silently — hook_policy R4
        print(f"[post_session] Temporal indisponible — ignoré ({exc})", file=sys.stderr)


if __name__ == "__main__":
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except Exception:
        event = {}

    # Déclencher uniquement sur fin de session normale
    stop_reason = event.get("stop_reason", "end_turn")
    if stop_reason in ("end_turn", "tool_use", ""):
        asyncio.run(_trigger())

    sys.exit(0)
