#!/usr/bin/env python3
"""
test_source_watch_goat.py — TricorderKit v0.7
Contract tests pour source-watch-goat (dry-run uniquement, pas d'appels reseau).
Usage : python tests/cli_contracts/test_source_watch_goat.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT   = Path(__file__).parent.parent.parent
SCRIPT = ROOT / "plugins/cli-forge/generated/source-watch-goat/source_watch_goat.py"

PASS, FAIL = 0, 0


def run(cmd: list) -> dict:
    env = {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    import os; full_env = {**os.environ, **env}
    result = subprocess.run(
        [sys.executable] + cmd, capture_output=True, text=True,
        cwd=str(ROOT), env=full_env
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


def test_dry_run_returns_valid_structure(command: str):
    data = run([str(SCRIPT), "--dry-run", command])
    check(f"dry-run {command} — status=dry_run",
          data.get("status") == "dry_run", str(data.get("status")))
    check(f"dry-run {command} — has dry_run_report",
          "dry_run_report" in data, str(list(data.keys())))
    check(f"dry-run {command} — risk_level present",
          "risk_level" in data.get("dry_run_report", {}))
    check(f"dry-run {command} — estimated_tokens > 0",
          data.get("dry_run_report", {}).get("estimated_tokens", 0) > 0)
    check(f"dry-run {command} — actions not empty",
          len(data.get("dry_run_report", {}).get("actions_that_would_run", [])) > 0)


def test_output_fields():
    data = run([str(SCRIPT), "--dry-run", "trending-manga"])
    check("output — has skill_name",     "skill_name" in data)
    check("output — has skill_version",  "skill_version" in data)
    check("output — has timestamp",      "timestamp" in data)
    check("output — has output.summary", "summary" in data.get("output", {}))


def test_unknown_command():
    data = run([str(SCRIPT), "destroy-everything"])
    check("unknown command — status=error", data.get("status") == "error",
          str(data.get("status")))


def test_script_exists():
    check("script exists", SCRIPT.exists(), str(SCRIPT))


def main():
    print(f"\nContract tests — source-watch-goat\n{'='*40}")

    test_script_exists()
    test_dry_run_returns_valid_structure("trending-manga")
    test_dry_run_returns_valid_structure("search-manga")
    test_dry_run_returns_valid_structure("trending-anime")
    test_dry_run_returns_valid_structure("seasonal-anime")
    test_dry_run_returns_valid_structure("latest-manga")
    test_output_fields()
    test_unknown_command()

    total = PASS + FAIL
    print(f"\n{'='*40}")
    print(f"Resultat : {PASS}/{total} passes" + (" — OK" if FAIL == 0 else f" — {FAIL} echec(s)"))
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
