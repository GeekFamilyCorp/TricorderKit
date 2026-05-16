#!/usr/bin/env python3
"""
hook_types.py — Types partagés pour la Hook Layer TricorderKit.
Version : 0.2.0

Utilise TypedDict (stdlib) pour rester compatible sans dépendance externe.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict  # type: ignore[assignment]


class HookMetadata(TypedDict, total=False):
    """Métadonnées produites par le Pre-Intent Hook."""
    domain: str
    domain_scores: Dict[str, int]
    requires_deep_research: bool
    cli_hints: List[str]


class PreIntentOutput(TypedDict):
    raw_input: str
    hook_id: str        # UUID v4 — partageable avec Langfuse/Temporal
    timestamp: str      # ISO-8601 UTC
    metadata: HookMetadata


class HooksBlock(TypedDict, total=False):
    """Bloc injecté dans le plan par le Pre-Execution Hook."""
    hook_run_id: str
    hook_timestamp: str          # ISO-8601 UTC
    risk_hint: str               # LOW | MEDIUM | HIGH | CRITICAL
    estimated_tokens: int


class QualityBreakdown(TypedDict, total=False):
    has_status: bool
    has_output: bool
    has_sources: bool
    has_reliability: bool


class PostHooksBlock(TypedDict, total=False):
    hook_run_id: Optional[str]
    hook_timestamp: str
    quality_score: Optional[float]       # 0.0 – 1.0
    quality_breakdown: QualityBreakdown
    tokens_used: Optional[int]
    schema_valid: Optional[bool]
    schema_errors: List[str]
