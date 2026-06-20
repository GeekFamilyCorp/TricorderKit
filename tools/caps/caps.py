#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
caps.py — Capability-on-Demand orchestrator (Phases 1-4).

Garantit qu'une capacité (groupe d'outils) est PRÊTE au moment du besoin, et la
récupère quand elle est inactive. On ne gère plus des services, on garantit des capacités.

Commandes :
    caps.py status [--json]                 # état de toutes les capacités
    caps.py ensure <cap> [--dry-run] [--force]   # gouverneur RAM + start + attente santé (idempotent)
    caps.py resolve <intent> [--json]       # intent -> capacités (via triggers)
    caps.py ensure-for <intent> [--dry-run] [--force]   # résout puis ensure chaque capacité
    caps.py touch  <cap>                     # marque comme utilisée (last_used)
    caps.py reap   [--idle N] [--dry-run]   # arrête les T1/T2 inactives > idle_timeout
    caps.py selftest                         # tests hors-ligne

Phase 2 = gouverneur RAM (préemption des inactives de priorité inférieure avant de dépasser le budget).
Phase 4 = résolveur d'intention (situations -> capacités).
Générique/anonyme (R37). Stdlib + pyyaml. Sûr : subprocess bornés, ne touche pas aux secrets/données.
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
HEALTH_POLL_TIMEOUT = 90
HEALTH_POLL_INTERVAL = 3
PREEMPT_GRACE_MIN = 2.0       # une capacité utilisée il y a < 2 min n'est jamais préemptée


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def repo_root() -> Path:
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


def set_pin(cap: str, val: bool) -> None:
    """Épingle une capacité : le reaper ne l'arrête pas tant qu'elle est pinned
    (ex. un worker long-running garde Temporal up)."""
    st = load_state()
    st.setdefault(cap, {})["pinned"] = bool(val)
    save_state(st)


def minutes_since(iso) -> float:
    if not iso:
        return float("inf")
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


def stop_cap(cap: dict):
    if cap.get("kind") == "docker_profile":
        return compose_stop(cap["profile"], repo_root())
    return 0, "noop"


# --------------------------------------------------------------------------- #
# Gouverneur RAM (Phase 2)
# --------------------------------------------------------------------------- #
def active_ram(caps: dict, exclude: str = None) -> int:
    total = 0
    for n, c in caps.items():
        if n == exclude or c.get("tier") == "T0" or c.get("kind") == "always_on":
            continue
        if is_healthy(c):
            total += int(c.get("ram_mb", 0))
    return total


def governor_make_room(caps: dict, target_name: str, budget: int, dry: bool) -> dict:
    """Préempte des capacités INACTIVES de priorité inférieure pour faire de la place au target.
    Garde-fou : ne stoppe jamais une capacité utilisée il y a < PREEMPT_GRACE_MIN, ni les T0."""
    target = caps[target_name]
    need = int(target.get("ram_mb", 0))
    projected = active_ram(caps, exclude=target_name) + need
    if projected <= budget:
        return {"action": "none", "projected_mb": projected, "budget_mb": budget}
    st = load_state()
    # candidats : healthy, non-T0, priorité < target, inactifs (idle >= grace)
    cands = []
    tprio = int(target.get("priority", 0))
    for n, c in caps.items():
        if c.get("tier") == "T0" or c.get("kind") == "always_on" or n == target_name:
            continue
        if not is_healthy(c):
            continue
        if int(c.get("priority", 0)) >= tprio:
            continue
        idle = minutes_since(st.get(n, {}).get("last_used"))
        if idle < PREEMPT_GRACE_MIN:
            continue
        cands.append((n, c, idle))
    # ordre : priorité asc (basses d'abord) puis idle desc (les plus oubliées d'abord)
    cands.sort(key=lambda x: (int(x[1].get("priority", 0)), -x[2]))
    freed = []
    for n, c, idle in cands:
        if projected <= budget:
            break
        if not dry:
            stop_cap(c)
        freed.append({"cap": n, "ram_mb": c.get("ram_mb", 0), "idle_min": round(idle, 1)})
        projected -= int(c.get("ram_mb", 0))
    return {"action": "preempt", "freed": freed, "projected_mb": projected, "budget_mb": budget,
            "fits": projected <= budget}


# --------------------------------------------------------------------------- #
# ensure / reap / resolve
# --------------------------------------------------------------------------- #
def ensure(caps: dict, name: str, budget: int, dry: bool, force: bool) -> dict:
    cap = caps.get(name)
    if not cap:
        return {"ok": False, "error": f"capacité inconnue: {name}"}
    if cap.get("kind") == "always_on":
        return {"ok": True, "cap": name, "state": "always_on"}
    if is_healthy(cap):
        touch(name)
        return {"ok": True, "cap": name, "state": "already_healthy"}
    # Gouverneur RAM
    gov = governor_make_room(caps, name, budget, dry)
    if gov.get("action") == "preempt" and not gov.get("fits") and not force:
        return {"ok": False, "cap": name, "error": "budget RAM insuffisant (préemption partielle)",
                "governor": gov, "hint": "--force pour passer outre"}
    if dry:
        return {"ok": True, "dry_run": True, "cap": name, "would": "start+wait_health", "governor": gov}
    kind = cap.get("kind")
    if kind == "docker_profile":
        if not docker_daemon_up():
            return {"ok": False, "cap": name, "error": "démon Docker indisponible — démarrer Docker Desktop"}
        rc, out = compose_up(cap["profile"], repo_root())
        if rc != 0:
            return {"ok": False, "cap": name, "error": "compose up échec", "detail": out[-400:]}
    elif kind == "ollama":
        return {"ok": False, "cap": name,
                "error": "Ollama injoignable — démarrer `ollama serve` (Phase 1: pas d'auto-start)"}
    deadline = time.time() + HEALTH_POLL_TIMEOUT
    while time.time() < deadline:
        if is_healthy(cap):
            touch(name)
            return {"ok": True, "cap": name, "state": "started_healthy", "governor": gov}
        time.sleep(HEALTH_POLL_INTERVAL)
    return {"ok": False, "cap": name, "error": f"santé non atteinte en {HEALTH_POLL_TIMEOUT}s"}


def resolve(caps: dict, intent: str) -> list:
    return [n for n, c in caps.items() if intent in (c.get("triggers") or [])]


def cmd_ensure(caps, name, budget, dry, force):
    res = ensure(caps, name, budget, dry, force)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("ok") else 2


def cmd_resolve(caps, intent, as_json):
    names = resolve(caps, intent)
    if as_json:
        print(json.dumps({"ok": True, "intent": intent, "capabilities": names}, ensure_ascii=False))
    else:
        print(f"intent '{intent}' -> {', '.join(names) if names else '(aucune)'}")
    return 0


def cmd_ensure_for(caps, intent, budget, dry, force):
    names = resolve(caps, intent)
    if not names:
        print(json.dumps({"ok": False, "intent": intent, "error": "aucune capacité pour cet intent"},
                         ensure_ascii=False))
        return 1
    results = [ensure(caps, n, budget, dry, force) for n in names]
    ok = all(r.get("ok") for r in results)
    print(json.dumps({"ok": ok, "intent": intent, "results": results}, ensure_ascii=False, indent=2))
    return 0 if ok else 2


def cmd_reap(caps: dict, idle_override, dry: bool) -> int:
    st = load_state()
    reaped, kept = [], []
    for name, cap in caps.items():
        if cap.get("tier") == "T0" or cap.get("kind") == "always_on":
            continue
        if not is_healthy(cap):
            continue
        if st.get(name, {}).get("pinned"):
            kept.append({"cap": name, "pinned": True})
            continue
        timeout = idle_override if idle_override is not None else cap.get("idle_timeout_min", 30)
        idle = minutes_since(st.get(name, {}).get("last_used"))
        if idle >= timeout:
            if not dry:
                stop_cap(cap)
            reaped.append({"cap": name, "idle_min": round(idle, 1), "stopped": not dry})
        else:
            kept.append({"cap": name, "idle_min": round(idle, 1), "timeout": timeout})
    print(json.dumps({"ok": True, "dry_run": dry, "reaped": reaped, "kept": kept}, ensure_ascii=False, indent=2))
    return 0


def cmd_status(caps: dict, as_json: bool, budget: int) -> int:
    st = load_state()
    rows = []
    for name, cap in caps.items():
        healthy = is_healthy(cap)
        last = st.get(name, {}).get("last_used")
        rows.append({"cap": name, "tier": cap.get("tier"), "kind": cap.get("kind"),
                     "healthy": healthy, "ram_mb": cap.get("ram_mb", 0),
                     "priority": cap.get("priority"), "last_used": last,
                     "idle_min": round(minutes_since(last), 1) if last else None})
    aram = sum(r["ram_mb"] for r in rows if r["healthy"])
    out = {"ok": True, "generated_at": now_iso(), "active_ram_mb": aram, "budget_mb": budget,
           "capabilities": rows}
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"Capacités ({now_iso()})  —  RAM active ~{aram}/{budget} Mo")
        for r in rows:
            flag = "● UP " if r["healthy"] else "○ down"
            idle = f"idle {r['idle_min']}min" if r["idle_min"] is not None else ""
            print(f"  {flag} [{r['tier']}] {r['cap']:<14} {r['ram_mb']:>5} Mo  {idle}")
    return 0


# --------------------------------------------------------------------------- #
def selftest() -> int:
    cfg = load_config()
    caps = cfg["capabilities"]
    budget = int(cfg.get("budget_mb", 3000))
    assert caps["memory"]["kind"] == "always_on" and is_healthy(caps["memory"])
    assert (repo_root() / "docker-compose.yml").exists()
    # resolve via triggers
    assert "graph" in resolve(caps, "semantic_search"), resolve(caps, "semantic_search")
    assert "local-llm" in resolve(caps, "embeddings")
    # ensure always_on
    assert ensure(caps, "memory", budget, dry=False, force=False)["ok"]
    # ensure dry-run docker cap -> ok, gouverneur calculé
    r = ensure(caps, "graph", budget, dry=True, force=False)
    assert r["ok"] and "governor" in r, r
    # gouverneur : budget minuscule -> préemption tentée (rien d'actif ici -> action none/preempt sans fits)
    gov = governor_make_room(caps, "graph", budget=10, dry=True)
    assert gov["budget_mb"] == 10
    # state round-trip
    touch("graph"); assert "last_used" in load_state().get("graph", {})
    print("[selftest] OK — config, repo, resolve(triggers), ensure(always_on+dry), gouverneur, state.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="caps.py", description="Capability-on-Demand orchestrator")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("ensure"); e.add_argument("cap"); e.add_argument("--dry-run", action="store_true"); e.add_argument("--force", action="store_true")
    ef = sub.add_parser("ensure-for"); ef.add_argument("intent"); ef.add_argument("--dry-run", action="store_true"); ef.add_argument("--force", action="store_true")
    rs = sub.add_parser("resolve"); rs.add_argument("intent"); rs.add_argument("--json", action="store_true")
    sub.add_parser("touch").add_argument("cap")
    sub.add_parser("pin").add_argument("cap")
    sub.add_parser("unpin").add_argument("cap")
    r = sub.add_parser("reap"); r.add_argument("--idle", type=int, default=None); r.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("status"); s.add_argument("--json", action="store_true")
    sub.add_parser("selftest")
    args = ap.parse_args()

    if args.cmd == "selftest":
        return selftest()
    cfg = load_config()
    caps = cfg["capabilities"]
    budget = int(cfg.get("budget_mb", 3000))
    if args.cmd == "ensure":
        return cmd_ensure(caps, args.cap, budget, args.dry_run, args.force)
    if args.cmd == "ensure-for":
        return cmd_ensure_for(caps, args.intent, budget, args.dry_run, args.force)
    if args.cmd == "resolve":
        return cmd_resolve(caps, args.intent, args.json)
    if args.cmd == "touch":
        touch(args.cap); print(json.dumps({"ok": True, "touched": args.cap}, ensure_ascii=False)); return 0
    if args.cmd == "pin":
        set_pin(args.cap, True); print(json.dumps({"ok": True, "pinned": args.cap}, ensure_ascii=False)); return 0
    if args.cmd == "unpin":
        set_pin(args.cap, False); print(json.dumps({"ok": True, "unpinned": args.cap}, ensure_ascii=False)); return 0
    if args.cmd == "reap":
        return cmd_reap(caps, args.idle, args.dry_run)
    if args.cmd == "status":
        return cmd_status(caps, args.json, budget)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
