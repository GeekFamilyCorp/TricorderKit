#!/usr/bin/env python3
"""
langfuse_observer.py — Observabilité hook layer → Langfuse
TricorderKit v0.9 — M4

Envoie les événements des 3 hooks vers Langfuse via REST API directe.
Compatible Python 3.11+ sans dépendance au SDK langfuse (Python 3.14 incompatible).

Protocole : POST /api/public/ingestion — format batch
  • pre_intent    → trace-create  : intent.{domain}
  • pre_execution → span-create   : plan enrichi, risk_hint, estimated_tokens
  • post_execution → span-create  : quality_score, tokens_used, schema_valid

Architecture :
  - `LangfuseObserver` : singleton lazy — ne se connecte que si des clés existent
  - Fallback silencieux (no-op) si Langfuse indisponible ou clés absentes
  - `observe_pre_intent(raw_input)` — wraps pre_intent_hook
  - `observe_hook_cycle(raw_input, plan, result)` — appel groupé
  - Envoie un seul batch HTTP par cycle (3 events)

Usage:
  from core.hooks.langfuse_observer import LangfuseObserver
  obs = LangfuseObserver()
  obs.observe_hook_cycle("Chainsaw Man", plan_dict, result_dict)
"""

from __future__ import annotations

import base64
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Imports hooks purs ────────────────────────────────────────────────────────

_HOOKS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _HOOKS_DIR.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from core.hooks.pre_intent_hook import run_pre_intent_hook
from core.hooks.pre_execution_hook import run_pre_execution_hook
from core.hooks.post_execution_hook import run_post_execution_hook


# ── Chargement .env ───────────────────────────────────────────────────────────

def _load_env() -> None:
    env_path = _REPO_ROOT / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore[import]
        load_dotenv(env_path, override=False)
    except ImportError:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


_load_env()


# ── Helpers REST ──────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_event(event_type: str, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "timestamp": _now_iso(),
        "body": body,
    }


def _send_batch(
    events: List[Dict[str, Any]],
    host: str,
    public_key: str,
    secret_key: str,
) -> bool:
    """POST /api/public/ingestion avec basic auth. Retourne True si 2xx."""
    try:
        import urllib.request
        payload = json.dumps({"batch": events}, ensure_ascii=False).encode("utf-8")
        creds = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        req = urllib.request.Request(
            url=f"{host.rstrip('/')}/api/public/ingestion",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Basic {creds}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status < 300
    except Exception:
        return False


# ── LangfuseObserver ──────────────────────────────────────────────────────────

class LangfuseObserver:
    """
    Singleton lazy qui envoie les événements hook vers Langfuse via REST.

    - Pas de dépendance au SDK langfuse (incompatible Python 3.14).
    - Se connecte uniquement si LANGFUSE_PUBLIC_KEY/SECRET_KEY sont définis.
    - Toutes les méthodes sont des no-ops si non configuré ou si réseau KO.
    """

    _instance: Optional["LangfuseObserver"] = None

    def __new__(cls) -> "LangfuseObserver":
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
            inst._secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
            inst._host = os.environ.get("LANGFUSE_HOST", "http://localhost:3001")
            inst._enabled = (
                bool(inst._public_key)
                and bool(inst._secret_key)
                and not inst._public_key.startswith("your_")
            )
            cls._instance = inst
        return cls._instance

    # ── API publique ──────────────────────────────────────────────────────────

    def observe_pre_intent(self, raw_input: str) -> Dict[str, Any]:
        """Run pre_intent hook et émet un trace-create Langfuse."""
        output = run_pre_intent_hook(raw_input)
        if not self._enabled:
            return output

        meta = output.get("metadata", {})
        hook_id = output.get("hook_id", str(uuid.uuid4()))

        event = _make_event("trace-create", {
            "id": hook_id,
            "name": "tk.pre_intent",
            "input": raw_input,
            "metadata": {
                "domain": meta.get("domain", "other"),
                "domain_scores": meta.get("domain_scores", {}),
                "requires_deep_research": meta.get("requires_deep_research", False),
                "cli_hints": meta.get("cli_hints", []),
            },
            "tags": ["pre_intent", meta.get("domain", "other")],
            "timestamp": output.get("timestamp", _now_iso()),
        })
        self._queue = getattr(self, "_queue", [])
        self._queue.append(event)

        return output

    def observe_pre_execution(
        self,
        plan: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run pre_execution hook et émet un span-create Langfuse."""
        enriched = run_pre_execution_hook(plan)
        if not self._enabled:
            return enriched

        hooks = enriched.get("hooks", {})
        span_id = hooks.get("hook_run_id", str(uuid.uuid4()))
        skill = plan.get("skill") or plan.get("action_type") or "unknown"

        body: Dict[str, Any] = {
            "id": span_id,
            "name": f"tk.pre_execution.{skill}",
            "input": plan,
            "metadata": {
                "risk_hint": hooks.get("risk_hint"),
                "estimated_tokens": hooks.get("estimated_tokens"),
                "action_type": plan.get("action_type"),
                "skill": plan.get("skill"),
            },
            "startTime": hooks.get("hook_timestamp", _now_iso()),
        }
        if trace_id:
            body["traceId"] = trace_id

        event = _make_event("span-create", body)
        self._queue = getattr(self, "_queue", [])
        self._queue.append(event)

        return enriched

    def observe_post_execution(
        self,
        plan: Dict[str, Any],
        result: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run post_execution hook et émet un span-create Langfuse."""
        enriched = run_post_execution_hook(plan, result)
        if not self._enabled:
            return enriched

        hooks = enriched.get("hooks", {})
        hooks_plan = plan.get("hooks", {})
        span_id = hooks.get("hook_run_id") or hooks_plan.get("hook_run_id") or str(uuid.uuid4())
        # Créer un span distinct du pre_execution
        post_span_id = "post-" + span_id[:28]
        skill = (
            plan.get("skill") or plan.get("goat")
            or plan.get("name") or "unknown"
        )

        body: Dict[str, Any] = {
            "id": post_span_id,
            "name": f"tk.post_execution.{skill}",
            "output": result,
            "metadata": {
                "quality_score": hooks.get("quality_score"),
                "quality_breakdown": hooks.get("quality_breakdown", {}),
                "tokens_used": hooks.get("tokens_used"),
                "schema_valid": hooks.get("schema_valid"),
                "schema_errors": hooks.get("schema_errors", []),
                "risk_hint": hooks_plan.get("risk_hint"),
            },
            "endTime": hooks.get("hook_timestamp", _now_iso()),
        }
        if trace_id:
            body["traceId"] = trace_id

        event = _make_event("span-create", body)
        self._queue = getattr(self, "_queue", [])
        self._queue.append(event)

        return enriched

    def observe_hook_cycle(
        self,
        raw_input: str,
        plan: Dict[str, Any],
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Appel groupé : pre_intent → pre_execution → post_execution.

        Retourne le résultat enrichi (post_execution output).
        Envoie un seul batch HTTP avec les 3 événements liés par trace_id.
        """
        self._queue: List[Dict] = []

        pre_intent = self.observe_pre_intent(raw_input)
        trace_id = pre_intent.get("hook_id") if self._enabled else None

        enriched_plan = self.observe_pre_execution(plan, trace_id=trace_id)
        enriched_result = self.observe_post_execution(
            enriched_plan, result, trace_id=trace_id
        )

        if self._enabled and self._queue:
            self.flush()

        return enriched_result

    def flush(self) -> bool:
        """Envoie le batch en attente vers Langfuse. Retourne True si succès."""
        queue = getattr(self, "_queue", [])
        if not self._enabled or not queue:
            return False
        ok = _send_batch(queue, self._host, self._public_key, self._secret_key)
        self._queue = []
        return ok

    def send_event(
        self,
        name: str,
        input_data: Any = None,
        output_data: Any = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Émet un événement ponctuel (trace-create) et l'envoie immédiatement."""
        if not self._enabled:
            return False
        trace_id = str(uuid.uuid4())
        body: Dict[str, Any] = {
            "id": trace_id,
            "name": name,
            "timestamp": _now_iso(),
        }
        if input_data is not None:
            body["input"] = input_data
        if output_data is not None:
            body["output"] = output_data
        if metadata:
            body["metadata"] = metadata
        if tags:
            body["tags"] = tags
        event = _make_event("trace-create", body)
        return _send_batch([event], self._host, self._public_key, self._secret_key)

    @property
    def enabled(self) -> bool:
        return self._enabled
