#!/usr/bin/env python3
"""
test_observability.py — Tests observabilité Langfuse (M4)
TricorderKit v0.9

Teste que :
  1. LangfuseObserver s'initialise correctement (enabled/disabled)
  2. Les 3 hooks s'exécutent et retournent les bons champs
  3. Les événements sont émis sans erreur (mock HTTP en CI)
  4. Le mode no-op fonctionne quand les clés sont absentes
  5. observe_hook_cycle retourne un résultat enrichi complet
  6. send_event fonctionne (mock + live optionnel)

Usage:
  pytest tests/test_observability.py -v
  pytest tests/test_observability.py -v --live   # test avec vraie connexion Langfuse
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_plan() -> Dict[str, Any]:
    return {
        "skill": "rtk-pipeline",
        "action_type": "research",
        "query": "Chainsaw Man",
    }


@pytest.fixture
def sample_result() -> Dict[str, Any]:
    return {
        "status": "success",
        "output": {
            "data": {"title": "Chainsaw Man", "author": "Fujimoto, Tatsuki"},
        },
        "source": "mangadex+jikan",
    }


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset LangfuseObserver singleton avant chaque test."""
    import importlib
    import core.hooks.langfuse_observer as mod
    mod.LangfuseObserver._instance = None
    yield
    mod.LangfuseObserver._instance = None


# ── Tests : initialisation ────────────────────────────────────────────────────

class TestLangfuseObserverInit:
    def test_disabled_without_keys(self, monkeypatch):
        """Sans clés env → observer disabled (no-op)."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        assert obs.enabled is False

    def test_disabled_with_placeholder_keys(self, monkeypatch):
        """Clés placeholder 'your_...' → disabled."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "your_langfuse_public_key_here")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "your_langfuse_secret_key_here")
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        assert obs.enabled is False

    def test_enabled_with_real_keys(self, monkeypatch):
        """Clés réelles → observer enabled."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test-1234")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test-5678")
        monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:3001")
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        assert obs.enabled is True

    def test_singleton_returns_same_instance(self, monkeypatch):
        """LangfuseObserver est un singleton."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test-1234")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test-5678")
        from core.hooks.langfuse_observer import LangfuseObserver
        obs1 = LangfuseObserver()
        obs2 = LangfuseObserver()
        assert obs1 is obs2


# ── Tests : hooks purs ────────────────────────────────────────────────────────

class TestHookOutputs:
    def test_pre_intent_hook_output_structure(self, monkeypatch, sample_plan):
        """pre_intent hook retourne les champs attendus."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        out = obs.observe_pre_intent("Chainsaw Man manga pipeline")
        assert "hook_id" in out
        assert "timestamp" in out
        assert "metadata" in out
        assert "domain" in out["metadata"]

    def test_pre_intent_detects_manga_domain(self, monkeypatch):
        """pre_intent détecte le domaine manga_anime pour une requête manga."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        out = obs.observe_pre_intent("Chainsaw Man manga latest volume")
        assert out["metadata"]["domain"] == "manga_anime"

    def test_pre_execution_enriches_plan(self, monkeypatch, sample_plan):
        """pre_execution ajoute hook_run_id et risk_hint au plan."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        enriched = obs.observe_pre_execution(sample_plan)
        assert "hooks" in enriched
        assert "hook_run_id" in enriched["hooks"]
        assert "risk_hint" in enriched["hooks"]
        assert enriched["hooks"]["risk_hint"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_pre_execution_risk_research_is_low(self, monkeypatch):
        """action_type=research → risk_hint=LOW."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        enriched = obs.observe_pre_execution({"action_type": "research"})
        assert enriched["hooks"]["risk_hint"] == "LOW"

    def test_post_execution_quality_score_range(self, monkeypatch, sample_plan, sample_result):
        """post_execution retourne quality_score entre 0.0 et 1.0."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        enriched_plan = obs.observe_pre_execution(sample_plan)
        enriched = obs.observe_post_execution(enriched_plan, sample_result)
        hooks = enriched["hooks"]
        assert "quality_score" in hooks
        assert 0.0 <= hooks["quality_score"] <= 1.0

    def test_post_execution_propagates_run_id(self, monkeypatch, sample_plan, sample_result):
        """hook_run_id est propagé de pre_execution → post_execution."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        enriched_plan = obs.observe_pre_execution(sample_plan)
        run_id = enriched_plan["hooks"]["hook_run_id"]
        enriched = obs.observe_post_execution(enriched_plan, sample_result)
        # hook_run_id est visible dans post_execution
        assert enriched["hooks"]["hook_run_id"] == run_id


# ── Tests : mode no-op (disabled) ────────────────────────────────────────────

class TestNoOpMode:
    def setup_method(self):
        """Disable observer for no-op tests."""
        import core.hooks.langfuse_observer as mod
        mod.LangfuseObserver._instance = None

    def test_observe_hook_cycle_noop(self, monkeypatch, sample_plan, sample_result):
        """observe_hook_cycle sans clés retourne le résultat enrichi sans erreur."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        result = obs.observe_hook_cycle("test query", sample_plan, sample_result)
        assert "hooks" in result
        assert result["hooks"]["quality_score"] is not None

    def test_flush_noop_returns_false(self, monkeypatch):
        """flush sans clés retourne False sans erreur."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        assert obs.flush() is False

    def test_send_event_noop_returns_false(self, monkeypatch):
        """send_event sans clés retourne False sans erreur."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
        from core.hooks.langfuse_observer import LangfuseObserver
        obs = LangfuseObserver()
        assert obs.send_event("test.event", input_data="hello") is False


# ── Tests : émission mock HTTP ────────────────────────────────────────────────

class TestMockHTTP:
    """Tests avec mock HTTP — vérifient que le payload est bien formé."""

    def _make_obs(self, monkeypatch):
        import core.hooks.langfuse_observer as mod
        mod.LangfuseObserver._instance = None
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test-mock")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test-mock")
        monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:3001")
        from core.hooks.langfuse_observer import LangfuseObserver
        return LangfuseObserver()

    def test_batch_sent_on_flush(self, monkeypatch, sample_plan, sample_result):
        """flush envoie un batch HTTP avec les événements queués."""
        import core.hooks.langfuse_observer as mod

        sent_batches = []

        def fake_send(events, host, pub, sec):
            sent_batches.append(events)
            return True

        monkeypatch.setattr(mod, "_send_batch", fake_send)
        obs = self._make_obs(monkeypatch)

        obs.observe_hook_cycle("test query", sample_plan, sample_result)

        assert len(sent_batches) == 1
        batch = sent_batches[0]
        # 3 events : trace-create + 2 span-create
        assert len(batch) == 3

    def test_batch_event_types(self, monkeypatch, sample_plan, sample_result):
        """Le batch contient 1 trace-create et 2 span-create."""
        import core.hooks.langfuse_observer as mod

        sent_batches = []
        monkeypatch.setattr(mod, "_send_batch", lambda e, h, p, s: sent_batches.append(e) or True)

        obs = self._make_obs(monkeypatch)
        obs.observe_hook_cycle("test query", sample_plan, sample_result)

        types = [e["type"] for e in sent_batches[0]]
        assert "trace-create" in types
        assert types.count("span-create") == 2

    def test_trace_id_shared_across_batch(self, monkeypatch, sample_plan, sample_result):
        """Les spans partagent le même traceId que la trace."""
        import core.hooks.langfuse_observer as mod

        sent_batches = []
        monkeypatch.setattr(mod, "_send_batch", lambda e, h, p, s: sent_batches.append(e) or True)

        obs = self._make_obs(monkeypatch)
        obs.observe_hook_cycle("test query", sample_plan, sample_result)

        batch = sent_batches[0]
        trace = next(e for e in batch if e["type"] == "trace-create")
        trace_id = trace["body"]["id"]
        spans = [e for e in batch if e["type"] == "span-create"]
        for span in spans:
            assert span["body"].get("traceId") == trace_id

    def test_send_event_http_called(self, monkeypatch):
        """send_event émet un HTTP call."""
        import core.hooks.langfuse_observer as mod

        calls = []
        monkeypatch.setattr(mod, "_send_batch", lambda e, h, p, s: calls.append(e) or True)

        obs = self._make_obs(monkeypatch)
        ok = obs.send_event("tk.test_event", input_data={"test": True}, tags=["unit"])
        assert ok is True
        assert len(calls) == 1
        assert calls[0][0]["type"] == "trace-create"
        assert calls[0][0]["body"]["name"] == "tk.test_event"

    def test_metadata_contains_quality_score(self, monkeypatch, sample_plan, sample_result):
        """Le span post_execution contient quality_score dans les metadata."""
        import core.hooks.langfuse_observer as mod

        sent_batches = []
        monkeypatch.setattr(mod, "_send_batch", lambda e, h, p, s: sent_batches.append(e) or True)

        obs = self._make_obs(monkeypatch)
        obs.observe_hook_cycle("test query", sample_plan, sample_result)

        post_spans = [
            e for e in sent_batches[0]
            if e["type"] == "span-create" and "post_execution" in e["body"]["name"]
        ]
        assert len(post_spans) == 1
        meta = post_spans[0]["body"].get("metadata", {})
        assert "quality_score" in meta
        assert meta["quality_score"] is not None


# ── Tests live (optionnels) ───────────────────────────────────────────────────

@pytest.mark.live
class TestLangfuseLive:
    """Tests avec vraie connexion Langfuse. Nécessite --live et .env configuré."""

    def test_langfuse_reachable(self):
        """Langfuse répond sur /api/public/health."""
        import urllib.request
        try:
            with urllib.request.urlopen("http://localhost:3001/api/public/health", timeout=5) as r:
                body = json.loads(r.read())
            assert body.get("status") == "OK"
        except Exception as e:
            pytest.skip(f"Langfuse unreachable: {e}")

    def test_trace_ingested_in_langfuse(self):
        """Envoie une trace réelle et vérifie qu'elle apparaît dans l'API."""
        import time, urllib.request, base64
        import core.hooks.langfuse_observer as mod
        mod.LangfuseObserver._instance = None
        from core.hooks.langfuse_observer import LangfuseObserver

        obs = LangfuseObserver()
        if not obs.enabled:
            pytest.skip("LANGFUSE_PUBLIC_KEY/SECRET_KEY non configurées")

        test_name = f"tk.test.live.{uuid.uuid4().hex[:8]}"
        ok = obs.send_event(test_name, input_data="pytest live test", tags=["test"])
        assert ok is True

        # Attendre l'ingestion (max 5s)
        time.sleep(3)

        creds = base64.b64encode(
            f"{obs._public_key}:{obs._secret_key}".encode()
        ).decode()
        req = urllib.request.Request(
            f"{obs._host}/api/public/traces?limit=20",
            headers={"Authorization": f"Basic {creds}"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())

        names = [t["name"] for t in data.get("data", [])]
        assert test_name in names, f"Trace '{test_name}' non trouvée dans {names}"
