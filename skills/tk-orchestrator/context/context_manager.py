"""
context_manager.py - Gestionnaire d isolation de contexte
TricorderKit v0.8 - tk-orchestrator v0.2.0
"""

from __future__ import annotations
import gc
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from router.skill_registry import CLIEntry, SkillEntry

CLI_TIMEOUT_SECONDS = 30
MAX_OUTPUT_SIZE = 50_000


def run_cli_tool(cli: CLIEntry, command: str, args: Dict[str, Any],
                 dry_run: bool = False, timeout: int = CLI_TIMEOUT_SECONDS) -> Dict:
    if not Path(cli.path).exists():
        return _error_result("CLI introuvable : {}".format(cli.path), recoverable=True)

    cmd = _build_cli_command(cli.path, command, args, dry_run)
    t_start = time.time()
    raw_output = None

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        raw_output = proc.stdout
        duration_ms = int((time.time() - t_start) * 1000)

        if proc.returncode != 0:
            return _error_result(
                "CLI exit {}: {}".format(proc.returncode, proc.stderr[:500]),
                recoverable=True, duration_ms=duration_ms)

        if not raw_output or not raw_output.strip():
            return _error_result("CLI output vide", recoverable=True, duration_ms=duration_ms)

        if len(raw_output) > MAX_OUTPUT_SIZE:
            raw_output = raw_output[:MAX_OUTPUT_SIZE] + "\n[OUTPUT TRUNCATED]"

        output_data = json.loads(raw_output)
        tokens = _estimate_tokens(raw_output)
        return {"status": "success", "output": output_data, "tokens": tokens,
                "duration_ms": duration_ms, "error": None}

    except subprocess.TimeoutExpired:
        return _error_result("Timeout CLI apres {}s".format(timeout), recoverable=False)
    except json.JSONDecodeError as e:
        return _error_result("Output CLI non-JSON : {}".format(str(e)[:200]), recoverable=True)
    except Exception as e:
        return _error_result(str(e), recoverable=False)
    finally:
        del raw_output
        gc.collect()


def _build_cli_command(cli_path: str, command: str, args: Dict[str, Any], dry_run: bool) -> List[str]:
    cmd = [sys.executable, cli_path, command]
    if dry_run:
        cmd.append("--dry-run")
    for key, value in args.items():
        if key.startswith("_"):
            continue
        if isinstance(value, bool):
            if value:
                cmd.append("--{}".format(key))
        elif value is not None:
            cmd.extend(["--{}".format(key), str(value)])
    cmd.extend(["--output", "json"])
    return cmd


def load_skill_minimal(skill: SkillEntry, args: Dict[str, Any], dry_run: bool = False) -> Dict:
    skill_md_path = Path(skill.path)
    if not skill_md_path.exists():
        return _error_result("SKILL.md introuvable : {}".format(skill.path), recoverable=True)
    t_start = time.time()
    try:
        content = skill_md_path.read_text(encoding="utf-8")
        tokens = _estimate_tokens(content)
        duration_ms = int((time.time() - t_start) * 1000)
        preview = content[:300] + "..." if len(content) > 300 else content
        return {
            "status": "dry_run" if dry_run else "success",
            "output": {"skill_name": skill.name, "skill_path": str(skill.path),
                       "invocation_mode": "cowork_scope", "args": args,
                       "dry_run": dry_run, "instructions_preview": preview},
            "tokens": tokens, "duration_ms": duration_ms, "error": None,
        }
    except Exception as e:
        return _error_result(str(e), recoverable=True)
    finally:
        gc.collect()


def dry_run_preview(tool_name: str, tool_type: str, command: str,
                    args: Dict[str, Any], risk_level: str = "LOW") -> Dict:
    estimated_tokens = _estimate_tokens(str(args)) + 50
    duration_map = {"LOW": 200, "MEDIUM": 500, "HIGH": 1000}
    return {
        "status": "dry_run",
        "output": {"would_execute": True, "tool": tool_name, "tool_type": tool_type,
                   "command": command, "args": args},
        "tokens": 0, "duration_ms": 0,
        "dry_run_report": {
            "actions_that_would_run": [
                "{} {}:{} {}".format(tool_type.upper(), tool_name, command, args)],
            "estimated_tokens": estimated_tokens,
            "estimated_duration_ms": duration_map.get(risk_level, 300),
            "risk_level": risk_level,
        },
        "error": None,
    }


def _error_result(message: str, recoverable: bool = True,
                  duration_ms: int = 0, raw=None) -> Dict:
    return {"status": "error", "output": None, "tokens": 0,
            "duration_ms": duration_ms, "error": message,
            "recoverable": recoverable, "raw": raw}


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4) if text else 0
