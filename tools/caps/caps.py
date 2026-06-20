#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
caps.py — Capability-on-Demand orchestrator (Phase 1).

Garantit qu'une capacité (groupe d'outils) est PRÊTE au moment du besoin, et la
récupère quand elle est inactive. On ne gère plus des services, on garantit des capacités.

Commandes :
    caps.py status [--json]                 # état de toutes les capacités
    caps.py ensure <cap> [--dry-run]        # démarre + attend la santé (idempotent)
    caps.py touch  <cap>                     # marque la capacité comme utilisée (last_used)
    caps.py reap   [--idle N] [--dry-run]   # arrête les T1/T2 inactives > idle_timeout
    caps.py selftest                         # tests hors-ligne (parsing + logique)

Pilote : profiles docker-compose (graph/workflows/observability) + Ollama. T0 = noop (toujours là).
Générique/anonyme (R37) : chemins résolus en relatif (racine repo trouvée via docker-compose.yml).
Stdlib + pyyaml. Sûr : subprocess bornés, jamais d'écriture de données, ne touche pas aux secrets.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import yaml
except ImportError:
    sys.exit("pyyaml requis : pip install pyyaml")

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "capabilities.yaml"
STATE = Path(os.path.expanduser("~")) / ".tk-caps" / "state.json"
DOCKER_TIMEOUT = 20
HEALTH_POLL_TIMEOUT = 90      # secondes max d'attente de santé
HEALTH_POLL_INTERVAL = 3


# --------------------------------------------------------------------------- #
def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def repo_root() -> Path:
    """Racine repo = 1er parent contenant docker-compose.yml (en remontant depuis HERE)."""
    for d in [HERE, *HERE.parents]:
        if (d / "docker-compose.yml").exists():
            return d
    return HERE.parent.parent


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")


def touch(cap: str) -> None:
    st = load_state()
    st.setdefault(cap, {})["last_used"] = now_iso()
    save_state(st)


def minutes_since(iso: str) -> float:
    try:
        d = datetime.fromisoformat(iso)
    except Exception:
        return float("inf")
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc).astimezone() - d).total_seconds() / 60.0


# --------------------------------------------------------------------------- #
# Sondes de santé
# --------------------------------------------------------------------------- #
def probe_tcp(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


def probe_http(url: str, timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= r.status < 500
    except Exception:
        # un 4xx/redirect/refus applicatif = serveur joignable ; seul l'injoignable est False
        import urllib.error
        return False


def is_healthy(cap: dict) -> bool:
    kind = cap.get("kind")
    if kind == "always_on":
        return True
    if kind == "ollama":
        return probe_http(cap.get("endpoint", "http://127.0.0.1:11434") + "/api/tags")
    if kind == "docker_profile":
        checks = cap.get("health", [])
        if not checks:
            return False
        for c in checks:
            t = c.get("type")
            if t == "tcp" and not probe_tcp(c["host"], c["port"]):
                return False
            if t == "http" and not probe_http(c["url"]):
                return False
        return True
    return False


# --------------------------------------------------------------------------- #
# Docker
# --------------------------------------------------------------------------- #
def run(cmd: list, timeout: int = DOCKER_TIMEOUT, cwd: Path = None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=str(cwd) if cwd else None, encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except FileNotFoundError as e:
        return 127, f"introuvable: {e}"


def docker_daemon_up() -> bool:
    rc, _ = run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=8)
    return rc == 0


def compose_up(profile: str, cwd: Path):
    return run(["docker", "compose", "--profile", profile, "up", "-d"], timeout=DOCKER_TIMEOUT, cwd=cwd)


def compose_stop(profile: str, cwd: Path):
    return run(["docker", "compose", "--profile", profile, "stop"], timeout=DOCKER_TIMEOUT, cwd=cwd)


# --------------------------------------------------------------------------- #
# ensure / reap
# --------------------------------------------------------------------------- #
def cmd_ensure(caps: dict, name: str, dry: bool) -> int:
    cap = caps.get(name)
    if not cap:
        print(json.dumps({"ok": False, "error": f"capacité inconnue: {name}"}, ensure_ascii=False))
        return 1
    if cap.get("kind") == "always_on":
        print(json.dumps({"ok": True, "cap": name, "state": "always_on"}, ensure_ascii=False))
        return 0
    if is_healthy(cap):
        touch(name)
        print(json.dumps({"ok": True, "cap": name, "state": "already_healthy"}, ensure_ascii=False))
        return 0
    if dry:
        print(json.dumps({"ok": True, "dry_run": True, "cap": name, "would": "start+wait_health"},
                         ensure_ascii=False))
        return 0
    kind = cap.get("kind")
    if kind == "docker_profile":
        if not docker_daemon_up():
            print(json.dumps({"ok": False, "cap": name,
                              "error": "démon Docker indisponible — démarrer Docker Desktop"},
                             ensure_ascii=False))
            return 2
        rc, out = compose_up(cap["profile"], repo_root())
        if rc != 0:
            print(json.dumps({"ok": False, "cap": name, "error": "compose up échec", "detail": out[-400:]},
                             ensure_ascii=False))
            return 2
    elif kind == "ollama":
        print(json.dumps({"ok": False, "cap": name,
                          "error": "Ollama injoignable — démarrer `ollama serve` (Phase 1: pas d'auto-start)"},
                         ensure_ascii=False))
        return 2
    # attente de santé
    deadline = time.time() + HEALTH_POLL_TIMEOUT
    while time.time() < deadline:
        if is_healthy(cap):
            touch(name)
            print(json.dumps({"ok": True, "cap": name, "state": "started_healthy"}, ensure_ascii=False))
            return 0
        time.sleep(HEALTH_POLL_INTERVAL)
    print(json.dumps({"ok": False, "cap": name, "error": f"santé non atteinte en {HEALTH_POLL_TIMEOUT}s"},
                     ensure_ascii=False))
    return 3


def cmd_reap(caps: dict, idle_override, dry: bool) -> int:
    st = load_state()
    reaped, kept = [], []
    for name, cap in caps.items():
        if cap.get("tier") == "T0" or cap.get("kind") == "always_on":
            continue
        if not is_healthy(cap):
            continue  # déjà arrêté
        timeout = idle_override if idle_override is not None else cap.get("idle_timeout_min", 30)
        last = st.get(name, {}).get("last_used")
        idle = minutes_since(last) if last else float("inf")
        if idle >= timeout:
            if dry:
                reaped.append({"cap": name, "idle_min": round(idle, 1), "would_stop": True})
            else:
                if cap.get("kind") == "docker_profile":
                    compose_stop(cap["profile"], repo_root())
                reaped.append({"cap": name, "idle_min": round(idle, 1), "stopped": True})
        else:
            kept.append({"cap": name, "idle_min": round(idle, 1), "timeout": timeout})
    print(json.dumps({"ok": True, "dry_run": dry, "reaped": reaped, "kept": kept}, ensure_ascii=False, indent=2))
    return 0


def cmd_status(caps: dict, as_json: bool) -> int:
    st = load_state()
    rows = []
    for name, cap in caps.items():
        healthy = is_healthy(cap)
        last = st.get(name, {}).get("last_used")
        rows.append({"cap": name, "tier": cap.get("tier"), "kind": cap.get("kind"),
                     "healthy": healthy, "ram_mb": cap.get("ram_mb", 0),
                     "last_used": last, "idle_min": round(minutes_since(last), 1) if last else None})
    active_ram = sum(r["ram_mb"] for r in rows if r["healthy"])
    out = {"ok": True, "generated_at": now_iso(), "active_ram_mb": active_ram, "capabilities": rows}
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"Capacités ({now_iso()})  —  RAM active estimée: {active_ram} Mo")
        for r in rows:
            flag = "● UP " if r["healthy"] else "○ down"
            idle = f"idle {r['idle_min']}min" if r["idle_min"] is not None else ""
            print(f"  {flag} [{r['tier']}] {r['cap']:<14} {r['ram_mb']:>5} Mo  {idle}")
    return 0


# --------------------------------------------------------------------------- #
def selftest() -> int:
    cfg = load_config()
    caps = cfg["capabilities"]
    assert "graph" in caps and caps["graph"]["kind"] == "docker_profile"
    assert caps["memory"]["kind"] == "always_on"
    assert is_healthy(caps["memory"]) is True
    # repo root résolu
    assert (repo_root() / "docker-compose.yml").exists(), "repo root introuvable"
    # state round-trip
    touch("graph"); s = load_state()
    assert "last_used" in s.get("graph", {})
    # ensure always_on = ok sans docker
    rc = cmd_ensure(caps, "memory", dry=False)
    assert rc == 0
    # ensure dry-run sur docker cap = ok sans rien lancer
    rc = cmd_ensure(caps, "graph", dry=True)
    assert rc == 0
    print("[selftest] OK — config valide, repo root ok, health always_on, state, ensure dry-run.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="caps.py", description="Capability-on-Demand orchestrator")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("ensure"); e.add_argument("cap"); e.add_argument("--dry-run", action="store_true")
    sub.add_parser("touch").add_argument("cap")
    r = sub.add_parser("reap"); r.add_argument("--idle", type=int, default=None); r.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("status"); s.add_argument("--json", action="store_true")
    sub.add_parser("selftest")
    args = ap.parse_args()

    if args.cmd == "selftest":
        return selftest()
    cfg = load_config()
    caps = cfg["capabilities"]
    if args.cmd == "ensure":
        return cmd_ensure(caps, args.cap, args.dry_run)
    if args.cmd == "touch":
        touch(args.cap); print(json.dumps({"ok": True, "touched": args.cap}, ensure_ascii=False)); return 0
    if args.cmd == "reap":
        return cmd_reap(caps, args.idle, args.dry_run)
    if args.cmd == "status":
        return cmd_status(caps, args.json)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
