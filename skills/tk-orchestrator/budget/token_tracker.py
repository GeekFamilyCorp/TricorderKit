"""
token_tracker.py — Gestionnaire de budget token heuristique
TricorderKit v0.8 — tk-orchestrator v0.2.0

Heuristique : 1 token ≈ 4 caractères UTF-8 (texte latin/mixte).
Note pour le texte japonais : les kanji représentent ~1-2 chars/token,
ce qui donne une sur-estimation du budget consommé → marge de sécurité.

Référence : DEC-006 — Rate limiting token par workflow
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Constantes ────────────────────────────────────────────────────────────────

CHARS_PER_TOKEN = 4  # Heuristique standard UTF-8 latin
SAFETY_BUFFER_PCT = 0.20  # 20% de buffer de sécurité (DEC-006)
ORCHESTRATOR_BASE_BUDGET = 200  # Tokens réservés pour l'orchestration elle-même

# Budgets par type d'intention
INTENT_BUDGETS: Dict[str, int] = {
    "query": 300,
    "action": 500,
    "workflow": 1000,
    "research": 1500,
    "audit": 800,
    "unknown": 300,
}

# Seuils d'alerte (cohérent avec MainBrain v1.4 Token Hygiene Guard)
BUDGET_LEVELS = [
    (1.00, "CRITICAL"),
    (0.80, "ALERT"),
    (0.50, "WATCH"),
    (0.00, "SAFE"),
]


# ── Estimation tokens ─────────────────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    """
    Estime le nombre de tokens d'un texte.
    Heuristique : len(text) / 4, arrondi au supérieur, minimum 1.
    """
    if not text:
        return 0
    return max(1, (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


def estimate_tokens_dict(data: dict) -> int:
    """Estime les tokens d'un objet dict en le sérialisant en string."""
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
    """
    Gestionnaire de budget token pour un workflow orchestré.

    Attributes:
        total: Budget total alloué
        effective: Budget effectif (total - safety_buffer)
        used: Tokens consommés
        history: Historique des consommations
    """
    total: int
    effective: int
    used: int = 0
    history: List[TokenUsage] = field(default_factory=list)

    @classmethod
    def from_intent(cls, intent_type: str, input_text: str = "") -> "TokenBudget":
        """Crée un budget à partir du type d'intention et du texte d'entrée."""
        alloc = allocate_budget(intent_type, input_text)
        return cls(total=alloc.allocated, effective=alloc.effective_budget)

    def can_allocate(self, amount: int) -> bool:
        """Vérifie si on peut consommer `amount` tokens sans dépasser le budget effectif."""
        return (self.used + amount) <= self.effective

    def consume(self, amount: int, purpose: str, step: Optional[int] = None) -> bool:
        """
        Consomme `amount` tokens.
        Retourne True si OK, False si budget dépassé (ne bloque pas, juste flag).
        """
        self.used += amount
        self.history.append(TokenUsage(purpose=purpose, amount=amount, step=step))
        return self.used <= self.effective

    def remaining(self) -> int:
        """Tokens restants dans le budget effectif."""
        return max(0, self.effective - self.used)

    def used_pct(self) -> float:
        """Pourcentage du budget effectif consommé."""
        if self.effective == 0:
            return 1.0
        return min(1.0, self.used / self.effective)

    def level(self) -> str:
        """Niveau d'alerte : SAFE | WATCH | ALERT | CRITICAL."""
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
        """Format conforme skill_output.schema.json tokens_used."""
        # Approximation input/output : 70% input, 30% output
        input_tokens = int(self.used * 0.7)
        output_tokens = self.used - input_tokens
        return {
            "input": input_tokens,
            "output": output_tokens,
            "total": self.used,
        }


# ── Allocation ────────────────────────────────────────────────────────────────

def allocate_budget(intent_type: str, input_text: str = "") -> BudgetAllocation:
    """
    Calcule l'allocation de budget pour un type d'intention.

    Args:
        intent_type: Type classifié (query, action, workflow, research, audit)
        input_text: Texte de la requête (pour estimation input_tokens)

    Returns:
        BudgetAllocation avec allocated, safety_buffer, effective_budget, input_estimated
    """
    action_budget = INTENT_BUDGETS.get(intent_type, 300)
    allocated = ORCHESTRATOR_BASE_BUDGET + action_budget
    safety_buffer = int(allocated * SAFETY_BUFFER_PCT)
    effective = allocated - safety_buffer
    input_est = estimate_tokens(input_text)

    return BudgetAllocation(
        allocated=allocated,
        safety_buffer=safety_buffer,
        effective_budget=effective,
        input_estimated=input_est,
    )


def budget_report(intent_type: str, input_text: str = "") -> dict:
    """Rapport de budget pour /tk:budget-check."""
    alloc = allocate_budget(intent_type, input_text)
    return {
        "intent_type": intent_type,
        "allocated_tokens": alloc.allocated,
        "safety_buffer": alloc.safety_buffer,
        "effective_budget": alloc.effective_budget,
        "input_estimated": alloc.input_estimated,
        "breakdown": {
            "orchestration_base": ORCHESTRATOR_BASE_BUDGET,
            "action_budget": INTENT_BUDGETS.get(intent_type, 300),
            "safety_buffer_pct": f"{int(SAFETY_BUFFER_PCT * 100)}%",
        },
    }
