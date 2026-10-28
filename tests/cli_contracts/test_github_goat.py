#!/usr/bin/env python3
"""
test_github_goat.py — TricorderKit v0.7
Contract tests pour github-goat (dry-run uniquement, pas d'appels reseau).
Usage : python tests/cli_contracts/test_github_goat.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT   = Path(__file__).parent.parent.parent
SCRIPT = ROOT / "plugins/cli-forge/generated/github-goat/github_goat.py"

PASS, FAIL = 0, 0


def run(cmd: list) -> dict:
    import os
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [sys.executable] + cmd, capture_output=True, text=True,
        cwd=str(ROOT), env=env
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"_raw": result.stdout, "_err": result.stderr}


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))


def _dry_run(command: list, label: str):
    """Helper interne (non collecté par pytest — paramètres positionnels)."""
    data = run([str(SCRIPT), "--dry-run"] + command)
    check(f"dry-run {label} — status=dry_run",
          data.get("status") == "dry_run", str(data.get("status")))
    check(f"dry-run {label} — has dry_run_report",
          "dry_run_report" in data)
    check(f"dry-run {label} — risk_level=LOW",
          data.get("dry_run_report", {}).get("risk_level") == "LOW")
    check(f"dry-run {label} — estimated_tokens > 0",
          data.get("dry_run_report", {}).get("estimated_tokens", 0) > 0)


def test_script_exists():
    check("script exists", SCRIPT.exists(), str(SCRIPT))


def test_unknown_command():
    data = run([str(SCRIPT), "delete-everything"])
    check("unknown command — status=error", data.get("status") == "error")


def main():
    print(f"\nContract tests — github-goat\n{'='*40}")

    test_script_exists()
    _dry_run(["list-repos", "<owner>"], "list-repos")
    _dry_run(["get-repo", "<owner>", "<repo>"], "get-repo")
    _dry_run(["search-repos", "TricorderKit"], "search-repos")
    _dry_run(["list-issues", "<owner>", "<repo>"], "list-issues")
    test_unknown_command()

    total = PASS + FAIL
    print(f"\n{'='*40}")
    print(f"Resultat : {PASS}/{total} passes" + (" — OK" if FAIL == 0 else f" — {FAIL} echec(s)"))
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
