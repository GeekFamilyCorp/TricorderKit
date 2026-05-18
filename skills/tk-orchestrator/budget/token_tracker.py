"""
token_tracker.py — Gestionnaire de budget token heuristique
TricorderKit v0.9 — tk-orchestrator v0.3.0

Heuristique : 1 token ≈ 4 caractères UTF-8 (texte latin/mixte).
Note pour le texte japonais : les kanji représentent ~1-2 chars/token,
ce qui donne une sur-estimation du budget consommé → marge de sécurité.

Phase 2 (v0.3.0) :
  - Tiers T1/T2/T3 avec budgets et models cibles associés
  - tier_for_intent() : classification automatique T1→T3
  - guard_action() : décision proceed|pause|abort sur budget session
  - SESSION_BUDGET_DEFAULT : budget global par session (30 000 tokens)

Référence : DEC-006 — Rate limiting token par workflow
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Constantes ────────────────────────────────────────────────────────────────

CHARS_PER_TOKEN = 4
SAFETY_BUFFER_PCT = 0.20
ORCHESTRATOR_BASE_BUDGET = 200
SESSION_BUDGET_DEFAULT = 30_000
SESSION_ALERT_THRESHOLD = 0.80


# ── Tiers T1/T2/T3 ────────────────────────────────────────────────────────────

@dataclass
class TaskTier:
    level: str
    label: str
    model_target: str
    max_tokens: int
    intents: List[str]
    description: str


TASK_TIERS: Dict[str, TaskTier] = {
    "T1": TaskTier(
        level="T1", label="Simple",
        model_target="claude-haiku-4-5-20251001",
        max_tokens=500,
        intents=["query", "unknown"],
        description="FAQ, résumé court, reformulation, traduction, classification, extraction basique",
    ),
    "T2": TaskTier(
        level="T2", label="Standard",
        model_target="claude-sonnet-4-6",
        max_tokens=1500,
        intents=["action", "audit"],
        description="Rédaction, analyse documentaire, code non critique, refactor, recherche standard",
    ),
    "T3": TaskTier(
        level="T3", label="Complexe",
        model_target="claude-opus-4-6",
        max_tokens=5000,
        intents=["workflow", "research"],
        description="Architecture, code sécurité/prod, raisonnement multi-étapes, debug complexe",
    ),
}

_INTENT_TO_TIER: Dict[str, str] = {
    "query": "T1", "unknown": "T1",
    "action": "T2", "audit": "T2",
    "workflow": "T3", "research": "T3",
}

# Budgets par type d'intention
INTENT_BUDGETS: Dict[str, int] = {
    "query": 300, "action": 500, "workflow": 1000,
    "research": 1500, "audit": 800, "unknown": 300,
}

# Seuils d'alerte
BUDGET_LEVELS = [
    (1.00, "CRITICAL"),
    (0.80, "ALERT"),
    (0.50, "WATCH"),
    (0.00, "SAFE"),
]


# ── Estimation tokens ─────────────────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


def estimate_tokens_dict(data: dict) -> int:
    import json
    try:
        return estimate_tokens(json.dumps(data, ensure_ascii=False))
    except Exception:
        return estimate_tokens(str(data))


# ── Classe TokenBudget ────────────────────────────────────────────────────────

@dataclass
class BudgetAllocation:
    allocated: int
    safety_buffer: int
    effective_budget: int
    input_estimated: int


@dataclass
class TokenUsage:
    purpose: str
    amount: int
    step: Optional[int] = None


@dataclass
class TokenBudget:
    total: int
    effective: int
    used: int = 0
    history: List[TokenUsage] = field(default_factory=list)

    @classmethod
    def from_intent(cls, intent_type: str, input_text: str = "") -> "TokenBudget":
        alloc = allocate_budget(intent_type, input_text)
        return cls(total=alloc.allocated, effective=alloc.effective_budget)

    def can_allocate(self, amount: int) -> bool:
        return (self.used + amount) <= self.effective

    def consume(self, amount: int, purpose: str, step: Optional[int] = None) -> bool:
        self.used += amount
        self.history.append(TokenUsage(purpose=purpose, amount=amount, step=step))
        return self.used <= self.effective

    def remaining(self) -> int:
        return max(0, self.effective - self.used)

    def used_pct(self) -> float:
        if self.effective == 0:
            return 1.0
        return min(1.0, self.used / self.effective)

    def level(self) -> str:
        pct = self.used_pct()
        for threshold, label in BUDGET_LEVELS:
            if pct >= threshold:
                return label
        return "SAFE"

    def to_dict(self) -> dict:
        return {
            "allocated": self.total,
            "effective": self.effective,
            "safety_buffer": self.total - self.effective,
            "used": self.used,
            "remaining": self.remaining(),
            "used_pct": round(self.used_pct() * 100, 1),
            "level": self.level(),
        }

    def to_schema_dict(self) -> dict:
        input_tokens = int(self.used * 0.7)
        output_tokens = self.used - input_tokens
        return {"input": input_tokens, "output": output_tokens, "total": self.used}


# ── Allocation ────────────────────────────────────────────────────────────────

def allocate_budget(intent_type: str, input_text: str = "") -> BudgetAllocation:
    action_budget = INTENT_BUDGETS.get(intent_type, 300)
    allocated = ORCHESTRATOR_BASE_BUDGET + action_budget
    safety_buffer = int(allocated * SAFETY_BUFFER_PCT)
    effective = allocated - safety_buffer
    input_est = estimate_tokens(input_text)
    return BudgetAllocation(
        allocated=allocated, safety_buffer=safety_buffer,
        effective_budget=effective, input_estimated=input_est,
    )


def budget_report(intent_type: str, input_text: str = "") -> dict:
    alloc = allocate_budget(intent_type, input_text)
    tier = tier_for_intent(intent_type)
    return {
        "intent_type": intent_type,
        "allocated_tokens": alloc.allocated,
        "safety_buffer": alloc.safety_buffer,
        "effective_budget": alloc.effective_budget,
        "input_estimated": alloc.input_estimated,
        "tier": tier.level,
        "model_target": tier.model_target,
        "breakdown": {
            "orchestration_base": ORCHESTRATOR_BASE_BUDGET,
            "action_budget": INTENT_BUDGETS.get(intent_type, 300),
            "safety_buffer_pct": f"{int(SAFETY_BUFFER_PCT * 100)}%",
        },
    }


# ── Tier classification ───────────────────────────────────────────────────────

def tier_for_intent(intent_type: str) -> TaskTier:
    """Retourne le tier T1/T2/T3 pour un type d'intention."""
    tier_key = _INTENT_TO_TIER.get(intent_type, "T2")
    return TASK_TIERS[tier_key]


def tier_from_complexity(
    intent_type: str,
    request_length: int = 0,
    has_code: bool = False,
    has_multifile: bool = False,
    is_destructive: bool = False,
) -> TaskTier:
    """Tier avec escalade contextuelle."""
    base_tier_key = _INTENT_TO_TIER.get(intent_type, "T2")
    if has_code and has_multifile:
        base_tier_key = "T3"
    elif has_code or is_destructive:
        if base_tier_key == "T1":
            base_tier_key = "T2"
    elif request_length > 500 and base_tier_key == "T1":
        base_tier_key = "T2"
    return TASK_TIERS[base_tier_key]


# ── Guard action ──────────────────────────────────────────────────────────────

@dataclass
class GuardResult:
    action: str       # "proceed" | "pause" | "abort"
    reason: str
    session_used: int
    session_budget: int
    session_pct: float
    tier: str
    model_target: str
    alert_level: str

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "reason": self.reason,
            "session_used": self.session_used,
            "session_budget": self.session_budget,
            "session_pct": round(self.session_pct * 100, 1),
            "tier": self.tier,
            "model_target": self.model_target,
            "alert_level": self.alert_level,
        }


def guard_action(
    intent_type: str,
    session_used: int,
    session_budget: int = SESSION_BUDGET_DEFAULT,
    alert_threshold: float = SESSION_ALERT_THRESHOLD,
    on_budget_exceeded: str = "pause_and_notify",
) -> GuardResult:
    """
    Décide de l'action pour une tâche selon l'état du budget session.

    Returns:
        GuardResult avec action: proceed | pause | abort
    """
    tier = tier_for_intent(intent_type)
    task_cost = INTENT_BUDGETS.get(intent_type, 300) + ORCHESTRATOR_BASE_BUDGET
    projected_used = session_used + task_cost

    session_pct = session_used / session_budget if session_budget > 0 else 1.0
    projected_pct = projected_used / session_budget if session_budget > 0 else 1.0

    alert_level = "SAFE"
    for threshold, label in BUDGET_LEVELS:
        if session_pct >= threshold:
            alert_level = label
            break

    if session_used >= session_budget:
        action = "abort" if on_budget_exceeded == "abort" else "pause"
        reason = (
            f"Budget session épuisé ({session_used}/{session_budget} tokens). "
            f"Action: {on_budget_exceeded}."
        )
    elif projected_pct > 1.0:
        action = "pause"
        reason = (
            f"La tâche {intent_type} ({task_cost} tokens estimés) dépasserait "
            f"le budget session ({projected_used}/{session_budget} projetés). "
            "Vérifier ou augmenter le budget."
        )
    elif session_pct >= alert_threshold:
        action = "abort" if on_budget_exceeded == "abort" else "proceed"
        reason = (
            f"Seuil d'alerte atteint ({session_pct*100:.0f}% du budget session). "
            f"Budget restant: {session_budget - session_used} tokens."
        )
    else:
        action = "proceed"
        reason = (
            f"Budget OK ({session_pct*100:.0f}% utilisé). "
            f"Tâche {tier.level} ({tier.label}) → {tier.model_target}."
        )

    return GuardResult(
        action=action, reason=reason,
        session_used=session_used, session_budget=session_budget,
        session_pct=session_pct, tier=tier.level,
        model_target=tier.model_target, alert_level=alert_level,
    )
