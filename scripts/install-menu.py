#!/usr/bin/env python3
"""
TricorderKit — Guided Install Script
Usage: python scripts/install-menu.py

Interactive menu to configure, install and verify TricorderKit.
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent


def title(text: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)


def step(n: int, text: str) -> None:
    print(f"\n[{n}] {text}")


def ok(text: str) -> None:
    print(f"  [OK]   {text}")


def warn(text: str) -> None:
    print(f"  [WARN] {text}")


def fail(text: str) -> None:
    print(f"  [FAIL] {text}")


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"  → {prompt}{suffix}: ").strip()
        return val if val else default
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        sys.exit(0)


def check_prerequisites() -> bool:
    title("Step 1 — Prerequisites check")
    checks = [
        ("python", ["python", "--version"]),
        ("docker",  ["docker", "--version"]),
        ("git",     ["git", "--version"]),
    ]
    all_ok = True
    for name, cmd in checks:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            ver = (result.stdout or result.stderr).strip().split("\n")[0]
            ok(f"{name}: {ver}")
        except FileNotFoundError:
            fail(f"{name}: not found — install before continuing")
            all_ok = False
        except Exception as e:
            warn(f"{name}: {e}")
    return all_ok


def setup_env() -> None:
    title("Step 2 — Environment setup")
    env_example = ROOT / ".env.example"
    env_file = ROOT / ".env"

    if env_file.exists():
        warn(".env already exists — skipping copy")
        choice = ask("Edit .env now? (y/n)", "n")
        if choice.lower() == "y":
            editor = os.environ.get("EDITOR", "notepad" if sys.platform == "win32" else "nano")
            subprocess.run([editor, str(env_file)])
        return

    if not env_example.exists():
        fail(".env.example not found — cannot continue")
        sys.exit(1)

    shutil.copy(env_example, env_file)
    ok(".env created from .env.example")
    print("\n  Required variables to fill in .env:")
    print("    ANTHROPIC_API_KEY       — your Anthropic API key")
    print("    NEO4J_PASSWORD          — choose a strong password")
    print("    LANGFUSE_NEXTAUTH_SECRET — random 32-char string")
    print("    LANGFUSE_SALT           — random 32-char string")
    print("    OBSIDIAN_VAULT_PATH     — absolute path to your Obsidian vault")

    choice = ask("Open .env in editor now? (y/n)", "y")
    if choice.lower() == "y":
        editor = os.environ.get("EDITOR", "notepad" if sys.platform == "win32" else "nano")
        subprocess.run([editor, str(env_file)])


def start_docker() -> None:
    title("Step 3 — Docker infrastructure")
    compose_file = ROOT / "docker-compose.yml"
    if not compose_file.exists():
        fail("docker-compose.yml not found")
        return

    choice = ask("Start Docker services? (y/n)", "y")
    if choice.lower() != "y":
        warn("Skipping Docker start")
        return

    print("  Starting services (Neo4j · Qdrant · Langfuse · Temporal)...")
    try:
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        if result.returncode == 0:
            ok("Docker services started")
            print("  Waiting 15s for services to initialize...")
            import time
            time.sleep(15)
        else:
            fail("docker compose failed:")
            print(result.stderr[:500])
    except Exception as e:
        fail(f"Docker error: {e}")


def run_doctor() -> None:
    title("Step 4 — System health check (tk doctor)")
    tk = ROOT / "cli" / "tk.py"
    if not tk.exists():
        fail("cli/tk.py not found")
        return

    try:
        result = subprocess.run(
            [sys.executable, str(tk), "doctor"],
            cwd=ROOT,
            capture_output=False,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
    except Exception as e:
        fail(f"tk doctor failed: {e}")


def install_deps() -> None:
    title("Step 2b — Python dependencies (optional)")
    req_file = ROOT / "requirements.txt"
    if not req_file.exists():
        warn("No requirements.txt found — skipping")
        return
    choice = ask("Install Python dependencies? (y/n)", "y")
    if choice.lower() != "y":
        warn("Skipping pip install")
        return
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            check=True,
        )
        ok("Dependencies installed")
    except subprocess.CalledProcessError as e:
        fail(f"pip install failed: {e}")


def main() -> None:
    title("TricorderKit v0.9 — Guided Install")
    print("""
  This script will:
    1. Check prerequisites (python, docker, git)
    2. Set up your .env file
    3. Start Docker services
    4. Run tk doctor to verify the installation

  Press Ctrl+C at any time to abort.
""")
    input("  Press Enter to start...")

    if not check_prerequisites():
        print("\n  Fix missing prerequisites and re-run this script.")
        sys.exit(1)

    setup_env()
    install_deps()
    start_docker()
    run_doctor()

    title("Installation complete")
    print("""
  Next steps:
    → Open a new session in Claude Code
    → Run /tk:boot to initialize the agent session
    → Run: python cli/tk.py doctor   (verify any time)
    → See INSTALL.md for advanced options
""")


if __name__ == "__main__":
    main()
