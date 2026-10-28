#!/usr/bin/env python3
"""
hook_log_to_obsidian.py — Pipeline observabilité hook logs → Obsidian ERRORS.md
TricorderKit v0.9 — B2

Lit .cache/hooks/pre_execution.log et post_execution.log (JSON-lines),
agrège les événements d'erreur et les notes de qualité basse,
puis écrit une note Obsidian ERRORS.md dans le vault TricorderKit.

Usage:
  python3 tools/observability/hook_log_to_obsidian.py [--dry-run] [--since HOURS] [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent

HOOK_LOGS_DIR = ROOT_DIR / ".cache" / "hooks"
PRE_EXEC_LOG = HOOK_LOGS_DIR / "pre_execution.log"
POST_EXEC_LOG = HOOK_LOGS_DIR / "post_execution.log"

DEFAULT_VAULT_PATH = os.environ.get(
    "OBSIDIAN_VAULT_PATH",
    str(Path.home() / "Documents" / "obsidian" / "TricorderKit")
)
DEFAULT_NOTE_PATH = "ERRORS.md"

QUALITY_SCORE_THRESHOLD = 0.6
RISK_LEVEL_HIGH = {"HIGH", "CRITICAL"}


def parse_jsonlines(log_path: Path) -> List[Dict[str, Any]]:
    if not log_path.exists():
        return []
    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                events.append({
                    "_parse_error": str(e),
                    "_raw_line": line[:200],
                    "_line_no": line_no,
                })
    return events


def filter_since(events: List[Dict], hours: float) -> List[Dict]:
    if hours <= 0:
        return events
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    filtered = []
    for ev in events:
        ts_str = ev.get("timestamp") or ev.get("created_at") or ev.get("ts", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts >= cutoff:
                filtered.append(ev)
        except (ValueError, AttributeError):
            filtered.append(ev)
    return filtered


def extract_errors_from_pre_exec(events: List[Dict]) -> List[Dict]:
    errors = []
    for ev in events:
        if "_parse_error" in ev:
            errors.append({"type": "parse_error", "detail": ev})
            continue
        risk = (ev.get("risk_hint") or ev.get("risk_level") or "").upper()
        if risk in RISK_LEVEL_HIGH:
            errors.append({
                "type": "high_risk",
                "hook_id": ev.get("hook_id", ""),
                "timestamp": ev.get("timestamp", ""),
                "intent": ev.get("intent_type", "unknown"),
                "risk": risk,
                "estimated_tokens": ev.get("estimated_tokens", 0),
                "reason": ev.get("risk_reason") or ev.get("reason") or "",
            })
    return errors


def extract_errors_from_post_exec(events: List[Dict]) -> List[Dict]:
    errors = []
    for ev in events:
        if "_parse_error" in ev:
            errors.append({"type": "parse_error", "detail": ev})
            continue
        quality = ev.get("quality_score")
        if quality is not None and quality < QUALITY_SCORE_THRESHOLD:
            errors.append({
                "type": "low_quality",
                "hook_id": ev.get("hook_id", ""),
                "timestamp": ev.get("timestamp", ""),
                "intent": ev.get("intent_type", "unknown"),
                "quality_score": quality,
                "skill_name": ev.get("skill_name") or ev.get("skill", ""),
                "failure_reasons": ev.get("failure_reasons") or ev.get("quality_issues") or [],
            })
        if ev.get("status") == "error" or ev.get("error"):
            errors.append({
                "type": "execution_error",
                "hook_id": ev.get("hook_id", ""),
                "timestamp": ev.get("timestamp", ""),
                "intent": ev.get("intent_type", "unknown"),
                "error": ev.get("error") or ev.get("error_message", ""),
                "skill_name": ev.get("skill_name") or ev.get("skill", ""),
            })
    return errors


def render_obsidian_note(
    pre_errors: List[Dict],
    post_errors: List[Dict],
    since_hours: float,
    stats: Dict[str, Any],
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    since_label = f"dernières {since_hours:.0f}h" if since_hours > 0 else "toute la session"
    total_errors = len(pre_errors) + len(post_errors)
    status_icon = "🔴" if total_errors > 0 else "✅"

    lines = [
        "---",
        "tags: [tricorderkit, observabilite, errors, hooks]",
        f'generated_at: "{now}"',
        f"error_count: {total_errors}",
        "source: hook_log_to_obsidian",
        "---",
        "",
        f"# {status_icon} ERRORS — Hook Logs ({since_label})",
        "",
        f"> Généré le {now} | Période : {since_label}",
        "",
        "## Résumé",
        "",
        "| Métrique | Valeur |",
        "|---|---|",
        f"| Événements pre_exec analysés | {stats.get('pre_total', 0)} |",
        f"| Événements post_exec analysés | {stats.get('post_total', 0)} |",
        f"| Erreurs HIGH/CRITICAL (pre_exec) | {len(pre_errors)} |",
        f"| Qualité basse ou erreurs (post_exec) | {len(post_errors)} |",
        f"| **Total erreurs** | **{total_errors}** |",
        "",
    ]

    if not pre_errors and not post_errors:
        lines += [
            "## ✅ Aucune erreur détectée",
            "",
            "Tous les hooks ont fonctionné dans les seuils acceptables.",
            "",
        ]
        return "\n".join(lines)

    if pre_errors:
        lines += ["## ⚠️ Risques élevés (pre_execution_hook)", ""]
        for i, err in enumerate(pre_errors, 1):
            if err["type"] == "parse_error":
                lines.append(f"### [{i}] Erreur de parsing log")
                lines.append("")
                continue
            ts = err.get("timestamp", "")[:19].replace("T", " ")
            lines += [
                f"### [{i}] `{err.get('risk', 'HIGH')}` — {err.get('intent', '?')} @ {ts}",
                f"- **hook_id** : `{err.get('hook_id', 'n/a')}`",
                f"- **Tokens estimés** : {err.get('estimated_tokens', 0)}",
            ]
            if err.get("reason"):
                lines.append(f"- **Raison** : {err['reason']}")
            lines.append("")

    if post_errors:
        lines += ["## 🔴 Qualité basse / Erreurs d'exécution (post_execution_hook)", ""]
        for i, err in enumerate(post_errors, 1):
            if err["type"] == "parse_error":
                lines.append(f"### [{i}] Erreur de parsing log")
                lines.append("")
                continue
            ts = err.get("timestamp", "")[:19].replace("T", " ")
            etype = err["type"]
            if etype == "execution_error":
                label = "⚡ Erreur exec"
            else:
                qs = err.get("quality_score", 0)
                label = f"📉 Qualité {qs:.0%}"
            lines += [
                f"### [{i}] {label} — {err.get('skill_name', '?')} @ {ts}",
                f"- **hook_id** : `{err.get('hook_id', 'n/a')}`",
                f"- **Intent** : {err.get('intent', '?')}",
            ]
            if etype == "execution_error" and err.get("error"):
                lines.append(f"- **Erreur** : {err['error']}")
            elif etype == "low_quality" and err.get("failure_reasons"):
                reasons = err["failure_reasons"]
                if isinstance(reasons, list):
                    for r in reasons:
                        lines.append(f"  - {r}")
                else:
                    lines.append(f"- **Raisons** : {reasons}")
            lines.append("")

    lines += [
        "---",
        "*Auto-généré par `hook_log_to_obsidian.py` — TricorderKit v0.9*",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Exporte les erreurs hook logs vers une note Obsidian ERRORS.md"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--since", type=float, default=24.0)
    parser.add_argument("--output", default=DEFAULT_NOTE_PATH)
    parser.add_argument("--vault", default=DEFAULT_VAULT_PATH)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    pre_events = parse_jsonlines(PRE_EXEC_LOG)
    post_events = parse_jsonlines(POST_EXEC_LOG)

    if args.since > 0:
        pre_events = filter_since(pre_events, args.since)
        post_events = filter_since(post_events, args.since)

    stats = {"pre_total": len(pre_events), "post_total": len(post_events)}

    pre_errors = extract_errors_from_pre_exec(pre_events)
    post_errors = extract_errors_from_post_exec(post_events)
    total_errors = len(pre_errors) + len(post_errors)

    note_content = render_obsidian_note(pre_errors, post_errors, args.since, stats)
    output_path = Path(args.vault) / args.output

    if args.dry_run:
        print(f"[DRY-RUN] Cible : {output_path}")
        print(f"[DRY-RUN] Erreurs détectées : {total_errors}")
        print("─" * 60)
        print(note_content)
        result = {
            "status": "dry_run",
            "target": str(output_path),
            "errors_found": total_errors,
            "pre_errors": len(pre_errors),
            "post_errors": len(post_errors),
        }
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(note_content)
        result = {
            "status": "success",
            "written_to": str(output_path),
            "errors_found": total_errors,
        }
        print(f"✅ Note écrite : {output_path}")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
