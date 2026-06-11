#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_common.py — Helpers partagés des scripts learning-engine (DEC-046, Phase 3, Lot A).

Conventions repo :
  - CLI argparse (pas typer) : zéro dépendance pip hors `jsonschema`, sûr sous Windows
    (cf. mémoire feedback_typer_windows_cli, et cli/tk.py qui est lui-même en argparse).
  - Sortie structurée conforme à core/contracts/skill_output.schema.json.
  - PATTERN-WIN-ENCODING : stdout/stderr forcés en UTF-8.
  - Dry-run par défaut sur toute écriture externe (Règle 4 TricorderKit).
"""
from __future__ import annotations

import datetime as _dt
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

# ── Racines ────────────────────────────────────────────────────────────────────
# scripts/ -> learning-engine/ -> plugins/ -> REPO_ROOT
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PLUGIN_ROOT.parent.parent
SCHEMA_DIR = PLUGIN_ROOT / "schemas"
SKILL_OUTPUT_CONTRACT = REPO_ROOT / "core" / "contracts" / "skill_output.schema.json"

SKILL_VERSION = "0.1.0"  # aligné sur plugins/learning-engine/manifest.yml


# ── Encodage (PATTERN-WIN-ENCODING) ─────────────────────────────────────────────
def setup_utf8() -> None:
    """Force UTF-8 sur stdout/stderr (Windows console = cp1252 par défaut).

    N'altère pas un flux déjà UTF-8 (ex. capture pytest) : on préserve l'objet
    en place via reconfigure() quand c'est possible, et on ne re-wrappe le buffer
    qu'en dernier recours (console Windows cp1252).
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        enc = (getattr(stream, "encoding", "") or "").lower()
        if enc.startswith("utf"):
            continue  # déjà OK (capsys, terminaux UTF-8) — ne pas toucher
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
                continue
            except Exception:
                pass
        buffer = getattr(stream, "buffer", None)
        if buffer is not None:
            try:
                setattr(
                    sys, stream_name,
                    io.TextIOWrapper(buffer, encoding="utf-8", errors="replace"),
                )
            except Exception:
                pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


# ── Temps ───────────────────────────────────────────────────────────────────────
def now_iso() -> str:
    """Timestamp ISO-8601 UTC (suffixe Z), conforme `format: date-time`."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return _dt.date.today().isoformat()


# ── jsonschema (Draft 2020-12) ──────────────────────────────────────────────────
def _load_validator(schema: dict):
    """Retourne un validateur Draft 2020-12 si dispo, sinon le meilleur disponible."""
    import jsonschema  # import paresseux : seul script à dépendre de la lib

    validator_cls = getattr(jsonschema, "Draft202012Validator", None)
    if validator_cls is None:  # vieille lib (sandbox jsonschema 3.x)
        validator_cls = jsonschema.validators.validator_for(schema)
    return validator_cls(schema)


def load_schema(name: str) -> dict:
    """Charge un schéma learning-engine par nom court (sans extension)."""
    path = SCHEMA_DIR / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def validate(obj: dict, schema_name: str) -> list[str]:
    """Valide `obj` contre un schéma learning-engine.

    Retourne la liste des messages d'erreur (vide = valide).
    """
    schema = load_schema(schema_name)
    validator = _load_validator(schema)
    errors = sorted(validator.iter_errors(obj), key=lambda e: list(e.path))
    return [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors]


# ── IO JSON ──────────────────────────────────────────────────────────────────────
def read_json(path: str | Path) -> Any:
    # utf-8-sig : tolère un BOM UTF-8 (fréquent sur fichiers produits sous Windows /
    # PowerShell Out-File / autres agents) — cf. PATTERN-WIN-ENCODING.
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_json_stdin_or_path(path: str | None) -> Any:
    if path in (None, "-", ""):
        return json.loads(sys.stdin.read().lstrip("﻿"))
    return read_json(path)


def write_json(path: str | Path, obj: Any) -> Path:
    """Écriture atomique UTF-8 (tmp + replace)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)
    return p


def iter_json_files(directory: str | Path, prefix: str = "") -> list[Path]:
    d = Path(directory)
    if not d.exists():
        return []
    return sorted(p for p in d.glob("*.json") if p.name.startswith(prefix))


# ── Contrat de sortie skill_output ────────────────────────────────────────────────
def skill_output(
    *,
    skill_name: str,
    status: str,
    summary: str,
    data: Any | None = None,
    files_created: Iterable[str] | None = None,
    decisions_logged: Iterable[str] | None = None,
    next_steps: Iterable[str] | None = None,
    error: dict | None = None,
    dry_run_report: dict | None = None,
    duration_ms: int | None = None,
) -> dict:
    """Construit un objet conforme à core/contracts/skill_output.schema.json."""
    if status not in ("success", "partial", "error", "dry_run"):
        raise ValueError(f"status invalide: {status}")
    output: dict[str, Any] = {"summary": summary[:500]}
    if data is not None:
        output["data"] = data
    if files_created is not None:
        output["files_created"] = list(files_created)
    if decisions_logged is not None:
        output["decisions_logged"] = list(decisions_logged)
    if next_steps is not None:
        output["next_steps"] = list(next_steps)[:5]

    env: dict[str, Any] = {
        "status": status,
        "skill_name": skill_name,
        "skill_version": SKILL_VERSION,
        "timestamp": now_iso(),
        "output": output,
    }
    if duration_ms is not None:
        env["duration_ms"] = int(duration_ms)
    if error is not None:
        env["error"] = error
    if dry_run_report is not None:
        env["dry_run_report"] = dry_run_report
    return env


def emit(envelope: dict, fmt: str = "json") -> None:
    """Imprime l'enveloppe. `json` (défaut) ou `md` (résumé lisible)."""
    if fmt == "md":
        o = envelope.get("output", {})
        print(f"# {envelope['skill_name']} — {envelope['status']}")
        print(f"\n{o.get('summary', '')}\n")
        for label, key in (("Fichiers", "files_created"),
                           ("Décisions", "decisions_logged"),
                           ("Prochaines étapes", "next_steps")):
            vals = o.get(key)
            if vals:
                print(f"## {label}")
                for v in vals:
                    print(f"- {v}")
                print()
    else:
        print(json.dumps(envelope, ensure_ascii=False, indent=2))


def add_format_arg(parser) -> None:
    parser.add_argument(
        "--format", choices=["json", "md"], default="json",
        help="Format de sortie (défaut: json, conforme skill_output)",
    )


def fail(skill_name: str, code: str, message: str, *, recoverable: bool = True,
         rollback_available: bool = False, fmt: str = "json") -> int:
    """Émet une enveloppe d'erreur et retourne un code de sortie non nul."""
    emit(
        skill_output(
            skill_name=skill_name, status="error",
            summary=f"{code}: {message}",
            error={
                "code": code, "message": message,
                "recoverable": recoverable,
                "rollback_available": rollback_available,
            },
        ),
        fmt,
    )
    return 1


# learning-engine Lot A — DEC-046

