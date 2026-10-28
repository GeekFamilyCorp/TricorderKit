"""
schema_validator.py — Validation JSON vs skill_output.schema.json
TricorderKit eval-lab v0.1.0

Valide qu'un output de skill respecte le contrat TricorderKit.
Utilisé par eval_runner.py et en standalone via stdin.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft7Validator, ValidationError

# -- Chemins ------------------------------------------------------------------
_HERE = Path(__file__).parent
_REPO_ROOT = _HERE.parent.parent
SCHEMA_PATH = _REPO_ROOT / "core" / "contracts" / "skill_output.schema.json"


# -- Résultats ----------------------------------------------------------------

@dataclass
class ViolationDetail:
    """Détail d'une violation de schéma."""
    path: str           # Chemin JSON (ex: "output.summary")
    message: str        # Message d'erreur jsonschema
    validator: str      # Nom du validateur (required, type, enum…)
    severity: str       # CRITICAL | HIGH | MEDIUM | LOW


@dataclass
class SchemaValidationResult:
    """Résultat de validation d'un output contre le schéma."""
    valid: bool
    violations: list[ViolationDetail] = field(default_factory=list)
    skill_name: str = ""
    skill_version: str = ""

    @property
    def has_critical(self) -> bool:
        return any(v.severity == "CRITICAL" for v in self.violations)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "skill_name": self.skill_name,
            "skill_version": self.skill_version,
            "violations": [
                {
                    "path": v.path,
                    "message": v.message,
                    "validator": v.validator,
                    "severity": v.severity,
                }
                for v in self.violations
            ],
        }


# -- Chargement schéma --------------------------------------------------------

_schema_cache: dict[str, Any] = {}


def load_schema(schema_path: Path | None = None) -> dict:
    """Charge le schéma JSON depuis le disque (cache mémoire)."""
    path = schema_path or SCHEMA_PATH
    key = str(path)
    if key not in _schema_cache:
        if not path.exists():
            raise FileNotFoundError(f"Schéma introuvable : {path}")
        with open(path, encoding="utf-8") as f:
            _schema_cache[key] = json.load(f)
    return _schema_cache[key]


# -- Classification sévérité --------------------------------------------------

# Champs obligatoires → CRITICAL si absents
_CRITICAL_REQUIRED = {"status", "skill_name", "skill_version", "timestamp", "output"}
_CRITICAL_TYPES = {"status", "skill_name", "skill_version"}

def _classify_severity(error: ValidationError) -> str:
    """Classifie la sévérité d'une erreur de validation."""
    # Champ obligatoire manquant
    if error.validator == "required":
        missing = set(error.validator_value) & _CRITICAL_REQUIRED
        return "CRITICAL" if missing else "HIGH"

    # Mauvais type sur un champ critique
    path_parts = list(error.absolute_path)
    if error.validator == "type" and path_parts and path_parts[0] in _CRITICAL_TYPES:
        return "CRITICAL"

    # Valeur enum invalide sur status
    if error.validator == "enum" and path_parts and path_parts[0] == "status":
        return "CRITICAL"

    # Longueur max dépassée (output.summary > 500 chars)
    if error.validator == "maxLength":
        return "MEDIUM"

    # Format date-time invalide
    if error.validator == "format":
        return "HIGH"

    return "MEDIUM"


# -- Validation principale ----------------------------------------------------

def validate_output(
    output: dict,
    schema_path: Path | None = None,
) -> SchemaValidationResult:
    """
    Valide un output de skill contre skill_output.schema.json.

    Args:
        output: dict Python représentant l'output du skill
        schema_path: chemin custom vers le schéma (défaut: SCHEMA_PATH)

    Returns:
        SchemaValidationResult avec violations détaillées
    """
    schema = load_schema(schema_path)
    validator = Draft7Validator(schema)

    violations: list[ViolationDetail] = []
    errors = list(validator.iter_errors(output))

    for error in errors:
        path = ".".join(str(p) for p in error.absolute_path) or "<root>"
        violations.append(
            ViolationDetail(
                path=path,
                message=error.message,
                validator=error.validator or "unknown",
                severity=_classify_severity(error),
            )
        )

    return SchemaValidationResult(
        valid=len(violations) == 0,
        violations=violations,
        skill_name=output.get("skill_name", ""),
        skill_version=output.get("skill_version", ""),
    )


def validate_json_string(json_str: str, schema_path: Path | None = None) -> SchemaValidationResult:
    """Valide un output au format JSON string."""
    try:
        output = json.loads(json_str)
    except json.JSONDecodeError as e:
        return SchemaValidationResult(
            valid=False,
            violations=[
                ViolationDetail(
                    path="<root>",
                    message=f"JSON invalide : {e}",
                    validator="json_parse",
                    severity="CRITICAL",
                )
            ],
        )
    return validate_output(output, schema_path)


# -- CLI standalone -----------------------------------------------------------

if __name__ == "__main__":
    import sys

    json_str = sys.stdin.read().strip()
    result = validate_json_string(json_str)

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    sys.exit(0 if result.valid else (2 if result.has_critical else 1))
