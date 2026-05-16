"""
regression_checker.py — Comparaison output courant vs baseline
TricorderKit eval-lab v0.1.0

Détecte les régressions structurelles entre un output courant et sa baseline.
Compare la structure (clés, types) — pas le contenu (qui peut légitimement changer).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# -- Résultats ----------------------------------------------------------------

@dataclass
class RegressionDetail:
    """Détail d'une régression détectée."""
    path: str           # Chemin JSON impacté (ex: "output.data.total_items")
    kind: str           # field_missing | type_changed | value_aberrant | enum_invalid
    expected: Any       # Valeur / type attendu (baseline)
    got: Any            # Valeur / type observé (courant)
    severity: str       # CRITICAL | HIGH | MEDIUM | LOW


@dataclass
class RegressionResult:
    """Résultat de la comparaison baseline vs output courant."""
    has_regressions: bool
    regressions: list[RegressionDetail] = field(default_factory=list)
    baseline_version: str = ""
    current_version: str = ""

    @property
    def has_critical(self) -> bool:
        return any(r.severity == "CRITICAL" for r in self.regressions)

    def to_dict(self) -> dict:
        return {
            "has_regressions": self.has_regressions,
            "baseline_version": self.baseline_version,
            "current_version": self.current_version,
            "regressions": [
                {
                    "path": r.path,
                    "kind": r.kind,
                    "expected": str(r.expected),
                    "got": str(r.got),
                    "severity": r.severity,
                }
                for r in self.regressions
            ],
        }


# -- Champs critiques ---------------------------------------------------------

# Ces champs, s'ils disparaissent ou changent de type, = CRITICAL
_CRITICAL_FIELDS = {
    "status", "skill_name", "skill_version", "timestamp", "output", "output.summary"
}

# Valeurs enum valides pour status
_VALID_STATUSES = {"success", "partial", "error", "dry_run"}

# Bornes plausibles pour tokens
_MAX_TOKENS_TOTAL = 200_000   # 200K — fenêtre max Claude
_MIN_DURATION_MS = 0
_MAX_DURATION_MS = 300_000    # 5 minutes max raisonnable


# -- Comparaison structurelle -------------------------------------------------

def _type_name(val: Any) -> str:
    """Retourne un nom de type lisible."""
    if val is None:
        return "null"
    return type(val).__name__


def _check_field(
    path: str,
    baseline_val: Any,
    current_val: Any,
    regressions: list[RegressionDetail],
) -> None:
    """Compare un champ entre baseline et courant."""
    is_critical = path in _CRITICAL_FIELDS

    # Champ disparu
    if current_val is None and baseline_val is not None:
        regressions.append(RegressionDetail(
            path=path,
            kind="field_missing",
            expected=_type_name(baseline_val),
            got="null",
            severity="CRITICAL" if is_critical else "HIGH",
        ))
        return

    # Type changé
    if type(baseline_val) is not type(current_val):
        regressions.append(RegressionDetail(
            path=path,
            kind="type_changed",
            expected=_type_name(baseline_val),
            got=_type_name(current_val),
            severity="CRITICAL" if is_critical else "HIGH",
        ))


def _check_status(output: dict, regressions: list[RegressionDetail]) -> None:
    """Valide que le status est une valeur connue."""
    status = output.get("status")
    if status and status not in _VALID_STATUSES:
        regressions.append(RegressionDetail(
            path="status",
            kind="enum_invalid",
            expected=str(_VALID_STATUSES),
            got=str(status),
            severity="CRITICAL",
        ))


def _check_tokens(output: dict, regressions: list[RegressionDetail]) -> None:
    """Valide les valeurs de tokens_used."""
    tokens = output.get("tokens_used")
    if not isinstance(tokens, dict):
        return
    total = tokens.get("total")
    if isinstance(total, int) and total > _MAX_TOKENS_TOTAL:
        regressions.append(RegressionDetail(
            path="tokens_used.total",
            kind="value_aberrant",
            expected=f"<= {_MAX_TOKENS_TOTAL}",
            got=str(total),
            severity="HIGH",
        ))
    inp = tokens.get("input", 0)
    out = tokens.get("output", 0)
    if isinstance(inp, int) and isinstance(out, int) and isinstance(total, int):
        if inp + out != total:
            regressions.append(RegressionDetail(
                path="tokens_used",
                kind="value_aberrant",
                expected=f"input+output == total ({inp}+{out}={inp+out})",
                got=f"total={total}",
                severity="MEDIUM",
            ))


def _check_duration(output: dict, regressions: list[RegressionDetail]) -> None:
    """Valide duration_ms."""
    duration = output.get("duration_ms")
    if duration is None:
        return
    if not isinstance(duration, int):
        regressions.append(RegressionDetail(
            path="duration_ms",
            kind="type_changed",
            expected="int",
            got=_type_name(duration),
            severity="MEDIUM",
        ))
        return
    if duration < _MIN_DURATION_MS or duration > _MAX_DURATION_MS:
        regressions.append(RegressionDetail(
            path="duration_ms",
            kind="value_aberrant",
            expected=f"{_MIN_DURATION_MS}–{_MAX_DURATION_MS}",
            got=str(duration),
            severity="MEDIUM",
        ))


def _compare_structure(
    baseline: dict,
    current: dict,
    path: str,
    regressions: list[RegressionDetail],
    depth: int = 0,
) -> None:
    """Compare récursivement la structure de deux dicts (max depth 3)."""
    if depth > 3:
        return
    for key, bval in baseline.items():
        cval = current.get(key)
        full_path = f"{path}.{key}" if path else key
        _check_field(full_path, bval, cval, regressions)
        # Récursion sur les sous-dicts
        if isinstance(bval, dict) and isinstance(cval, dict):
            _compare_structure(bval, cval, full_path, regressions, depth + 1)


# -- Entrée publique ----------------------------------------------------------

def check_regression(
    baseline_output: dict,
    current_output: dict,
) -> RegressionResult:
    """
    Compare l'output courant d'un skill avec sa baseline.

    Args:
        baseline_output: output de référence (chargé depuis BaselineStore)
        current_output: output fraîchement produit

    Returns:
        RegressionResult avec la liste des régressions détectées
    """
    regressions: list[RegressionDetail] = []

    # 1. Comparaison structurelle récursive
    _compare_structure(baseline_output, current_output, "", regressions)

    # 2. Invariants métier
    _check_status(current_output, regressions)
    _check_tokens(current_output, regressions)
    _check_duration(current_output, regressions)

    return RegressionResult(
        has_regressions=len(regressions) > 0,
        regressions=regressions,
        baseline_version=baseline_output.get("skill_version", ""),
        current_version=current_output.get("skill_version", ""),
    )
