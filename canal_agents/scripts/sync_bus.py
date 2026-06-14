#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_bus.py v2 - Bus multi-agents TricorderKit (canal_agents)
=============================================================

Canal unique et generique : claude, antigravity, codex.
Transport append-only (events.jsonl), lecture par curseur (anti-staleness),
ZERO token LLM. Deterministe, stdlib uniquement (Python 3.11+).

v2 ajoute :
- Cycle de vie des taches : claim / done / task-status / tasks
  (statuts assigned -> in_progress -> done | failed). Anti-doublon : claim
  refuse si la tache est deja in_progress (claim frais).
- Verrous a TTL : lock / unlock (locks/<resource>.json, expiration auto).
- Validation de schema des evenements a l'ecriture (events.schema.json).
- health --alert : detecteur de staleness (taches non reclamees / bloquees,
  heartbeats perimes, verrous expires) -> events 'alert' + ALERTS.md.

Conventions projet : CLI avant LLM ; --dry-run avant ecriture ; output JSON.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import uuid
from pathlib import Path

AGENTS = ("claude", "antigravity", "codex", "qwen")
DESTINATIONS = AGENTS + ("all",)
VALID_STATES = ("idle", "working", "blocked", "offline", "error")
TASK_STATES = ("assigned", "in_progress", "done", "failed")
EVENT_TYPES = (
    "announce", "heartbeat", "message",
    "task_assign", "task_accept", "task_progress", "task_done", "task_failed",
    "deliverable_ready", "question", "answer", "gap", "lock", "unlock", "alert",
)

# Seuils d'alerte (minutes)
ASSIGN_TIMEOUT_MIN = 15      # tache 'assigned' jamais reclamee
INPROGRESS_TIMEOUT_MIN = 30  # tache 'in_progress' bloquee
HEARTBEAT_STALE_MIN = 15     # agent 'working' sans heartbeat recent
CLAIM_STALE_MIN = 30         # un claim plus vieux est considere perime (re-claim ok)

CANAL_ROOT = Path(__file__).resolve().parent.parent
BUS_DIR = CANAL_ROOT / "bus"
EVENTS = BUS_DIR / "events.jsonl"
INBOX = CANAL_ROOT / "inbox"
OUTBOX = CANAL_ROOT / "outbox"
ARCHIVE = CANAL_ROOT / "archive"
LOCKS = CANAL_ROOT / "locks"
STATUS = CANAL_ROOT / "STATUS.json"
ALERTS_MD = CANAL_ROOT / "ALERTS.md"


# --------------------------------------------------------------------------- #
# Utilitaires temps / FS
# --------------------------------------------------------------------------- #
def now_dt() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc).astimezone()


def now_iso() -> str:
    return now_dt().isoformat(timespec="seconds")


def parse_iso(s):
    if not s:
        return None
    try:
        return _dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def minutes_since(iso) -> float:
    d = parse_iso(iso)
    if d is None:
        return float("inf")
    if d.tzinfo is None:
        d = d.replace(tzinfo=_dt.timezone.utc)
    return (now_dt() - d).total_seconds() / 60.0


def ensure_tree() -> None:
    for d in (BUS_DIR, ARCHIVE, LOCKS):
        d.mkdir(parents=True, exist_ok=True)
    for a in AGENTS:
        (INBOX / a).mkdir(parents=True, exist_ok=True)
        (OUTBOX / a).mkdir(parents=True, exist_ok=True)
    if not EVENTS.exists():
        EVENTS.touch()


# --------------------------------------------------------------------------- #
# Evenements + validation de schema
# --------------------------------------------------------------------------- #
def validate_event(ev: dict):
    """Retourne (True, '') si valide, sinon (False, raison). Reflet de
    events.schema.json (validation stdlib, pas de dependance jsonschema)."""
    for k in ("seq", "id", "ts", "from", "to", "type"):
        if k not in ev:
            return False, f"champ requis manquant: {k}"
    if not isinstance(ev["seq"], int) or ev["seq"] < 1:
        return False, "seq doit etre un entier >= 1"
    if ev["from"] not in AGENTS:
        return False, f"from invalide: {ev['from']}"
    if ev["to"] not in DESTINATIONS:
        return False, f"to invalide: {ev['to']}"
    if ev["type"] not in EVENT_TYPES:
        return False, f"type invalide: {ev['type']}"
    if "payload" in ev and not isinstance(ev["payload"], dict):
        return False, "payload doit etre un objet"
    return True, ""


def read_events() -> list:
    if not EVENTS.exists():
        return []
    out = []
    with EVENTS.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                out.append({"_corrupt": True, "raw": line})
    return out


def next_seq() -> int:
    mx = 0
    for e in read_events():
        if isinstance(e, dict) and isinstance(e.get("seq"), int):
            mx = max(mx, e["seq"])
    return mx + 1


def make_event(sender, to, etype, task=None, msg="", payload=None) -> dict:
    return {
        "seq": next_seq(), "id": uuid.uuid4().hex[:12], "ts": now_iso(),
        "from": sender, "to": to, "type": etype,
        "task": task, "msg": msg or "", "payload": payload or {},
    }


def append_event(ev: dict, validate: bool = True) -> dict:
    if validate:
        ok, why = validate_event(ev)
        if not ok:
            raise ValueError(f"event invalide ({why})")
    ensure_tree()
    with EVENTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


# --------------------------------------------------------------------------- #
# Curseurs
# --------------------------------------------------------------------------- #
def cursor_path(agent: str) -> Path:
    return BUS_DIR / ("cursor." + agent)


def get_cursor(agent: str) -> int:
    p = cursor_path(agent)
    if not p.exists():
        return 0
    try:
        return int(p.read_text(encoding="utf-8").strip() or "0")
    except ValueError:
        return 0


def set_cursor(agent: str, seq: int) -> None:
    cursor_path(agent).write_text(str(seq), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Taches (fichiers inbox)
# --------------------------------------------------------------------------- #
def task_file(agent: str, task: str) -> Path:
    return INBOX / agent / (task + ".json")


def load_task(agent: str, task: str):
    f = task_file(agent, task)
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def save_task(agent: str, task: str, rec: dict) -> None:
    task_file(agent, task).write_text(json.dumps(rec, ensure_ascii=False, indent=2),
                                      encoding="utf-8")


# --------------------------------------------------------------------------- #
# Verrous a TTL
# --------------------------------------------------------------------------- #
def lock_file(resource: str) -> Path:
    safe = resource.replace("/", "_").replace("\\", "_")
    return LOCKS / (safe + ".json")


def lock_is_expired(rec: dict) -> bool:
    return minutes_since(rec.get("expires_at")) >= 0  # expires_at deja passe


# --------------------------------------------------------------------------- #
# Commandes
# --------------------------------------------------------------------------- #
def cmd_init(args) -> dict:
    ensure_tree()
    if not STATUS.exists():
        write_status()
    return {"ok": True, "action": "init", "canal_root": str(CANAL_ROOT),
            "agents": list(AGENTS)}


def cmd_heartbeat(args) -> dict:
    if args.agent not in AGENTS:
        return {"ok": False, "error": "agent inconnu: " + args.agent}
    if args.state not in VALID_STATES:
        return {"ok": False, "error": "state invalide: " + args.state}
    ev = make_event(args.agent, "all", "heartbeat", msg=args.note or "",
                    payload={"state": args.state})
    if args.dry_run:
        return {"ok": True, "dry_run": True, "would_append": ev}
    append_event(ev)
    write_status()
    return {"ok": True, "action": "heartbeat", "event": ev}


def cmd_post(args) -> dict:
    if args.sender not in AGENTS:
        return {"ok": False, "error": "emetteur inconnu: " + args.sender}
    if args.to not in DESTINATIONS:
        return {"ok": False, "error": "destinataire inconnu: " + args.to}
    if args.type not in EVENT_TYPES:
        return {"ok": False, "error": "type inconnu: " + args.type, "valides": list(EVENT_TYPES)}
    payload = {}
    if args.payload:
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as exc:
            return {"ok": False, "error": "payload JSON invalide: " + str(exc)}
    ev = make_event(args.sender, args.to, args.type, task=args.task,
                    msg=args.msg or "", payload=payload)
    if args.dry_run:
        return {"ok": True, "dry_run": True, "would_append": ev}
    append_event(ev)
    return {"ok": True, "action": "post", "event": ev}


def cmd_dispatch(args) -> dict:
    if args.sender not in AGENTS:
        return {"ok": False, "error": "emetteur inconnu: " + args.sender}
    if args.to not in AGENTS:
        return {"ok": False, "error": "destinataire inconnu: " + args.to}
    task_id = args.task or ("T-" + _dt.date.today().isoformat() + "-" + uuid.uuid4().hex[:6].upper())
    ev = make_event(args.sender, args.to, "task_assign", task=task_id, msg=args.msg or "",
                    payload={"lane": args.lane or "", "priority": args.priority,
                             "deliverable": args.deliverable or ""})
    record = dict(ev)
    record["status"] = "assigned"
    record["attempts"] = 0
    if args.dry_run:
        return {"ok": True, "dry_run": True, "would_append": ev,
                "would_write": str(task_file(args.to, task_id))}
    append_event(ev)
    save_task(args.to, task_id, record)
    return {"ok": True, "action": "dispatch", "task": task_id, "to": args.to,
            "inbox_file": str(task_file(args.to, task_id)), "event": ev}


def cmd_claim(args) -> dict:
    """Reclame une tache. Anti-doublon : echoue si deja in_progress (frais) ou done."""
    rec = load_task(args.agent, args.task)
    if not rec:
        return {"ok": False, "error": "tache absente", "task": args.task, "agent": args.agent}
    st = rec.get("status", "assigned")
    if st == "done":
        return {"ok": False, "reason": "deja done", "task": args.task, "status": st}
    if st == "in_progress":
        age = minutes_since(rec.get("claimed_at"))
        if age < CLAIM_STALE_MIN:
            return {"ok": False, "reason": "deja in_progress",
                    "claimed_by": rec.get("claimed_by"), "claimed_at": rec.get("claimed_at"),
                    "age_min": round(age, 1)}
        # claim perime -> takeover autorise
    rec["status"] = "in_progress"
    rec["claimed_by"] = args.agent
    rec["claimed_at"] = now_iso()
    rec["attempts"] = int(rec.get("attempts", 0)) + 1
    if args.dry_run:
        return {"ok": True, "dry_run": True, "would_claim": rec}
    save_task(args.agent, args.task, rec)
    append_event(make_event(args.agent, "claude", "task_accept", task=args.task,
                            payload={"attempt": rec["attempts"]}))
    return {"ok": True, "action": "claim", "task": args.task, "attempts": rec["attempts"],
            "status": "in_progress"}


def cmd_done(args) -> dict:
    rec = load_task(args.agent, args.task)
    if not rec:
        return {"ok": False, "error": "tache absente", "task": args.task}
    status = args.status
    rec["status"] = status
    rec["done_at"] = now_iso()
    if args.deliverable:
        rec["deliverable"] = args.deliverable
    if args.dry_run:
        return {"ok": True, "dry_run": True, "would_finalize": rec}
    save_task(args.agent, args.task, rec)
    etype = "task_done" if status == "done" else "task_failed"
    append_event(make_event(args.agent, "claude", etype, task=args.task,
                            msg=args.msg or "", payload={"deliverable": args.deliverable or ""}))
    if args.archive:
        dest = ARCHIVE / (args.agent + "_" + args.task + ".json")
        task_file(args.agent, args.task).replace(dest)
        rec["_archived_to"] = str(dest)
    return {"ok": True, "action": "done", "task": args.task, "status": status}


def cmd_task_status(args) -> dict:
    rec = load_task(args.agent, args.task)
    if not rec:
        return {"ok": False, "error": "tache absente", "task": args.task}
    return {"ok": True, "action": "task-status", "task": args.task,
            "status": rec.get("status"), "attempts": rec.get("attempts", 0),
            "claimed_by": rec.get("claimed_by"), "claimed_at": rec.get("claimed_at"),
            "record": rec}


def cmd_tasks(args) -> dict:
    agents = [args.agent] if args.agent else list(AGENTS)
    out = []
    for a in agents:
        d = INBOX / a
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                r = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            out.append({"agent": a, "task": r.get("task"), "status": r.get("status"),
                        "attempts": r.get("attempts", 0), "priority": r.get("payload", {}).get("priority"),
                        "claimed_at": r.get("claimed_at")})
    return {"ok": True, "action": "tasks", "count": len(out), "tasks": out}


def cmd_lock(args) -> dict:
    ensure_tree()
    lf = lock_file(args.resource)
    if lf.exists():
        try:
            cur = json.loads(lf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cur = {}
        if cur and not lock_is_expired(cur) and cur.get("holder") != args.agent:
            return {"ok": False, "reason": "verrou tenu", "holder": cur.get("holder"),
                    "expires_at": cur.get("expires_at")}
    expires = (now_dt() + _dt.timedelta(minutes=args.ttl_min)).isoformat(timespec="seconds")
    rec = {"resource": args.resource, "holder": args.agent, "pid": args.pid,
           "acquired_at": now_iso(), "expires_at": expires}
    if args.dry_run:
        return {"ok": True, "dry_run": True, "would_lock": rec}
    lf.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    append_event(make_event(args.agent, "all", "lock", payload={"resource": args.resource,
                            "expires_at": expires}))
    return {"ok": True, "action": "lock", "resource": args.resource, "expires_at": expires}


def cmd_unlock(args) -> dict:
    lf = lock_file(args.resource)
    if not lf.exists():
        return {"ok": True, "action": "unlock", "note": "deja libre", "resource": args.resource}
    try:
        cur = json.loads(lf.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        cur = {}
    if cur.get("holder") not in (args.agent, None) and not args.force:
        return {"ok": False, "reason": "verrou tenu par un autre", "holder": cur.get("holder")}
    lf.unlink()
    append_event(make_event(args.agent, "all", "unlock", payload={"resource": args.resource}))
    return {"ok": True, "action": "unlock", "resource": args.resource}


def cmd_read(args) -> dict:
    if args.agent not in AGENTS:
        return {"ok": False, "error": "agent inconnu: " + args.agent}
    cur = get_cursor(args.agent)
    evs = [e for e in read_events() if isinstance(e, dict) and not e.get("_corrupt")]
    unread = [e for e in evs
              if e.get("seq", 0) > cur
              and e.get("from") != args.agent
              and e.get("to") in (args.agent, "all")]
    last = max((e.get("seq", 0) for e in evs), default=cur)
    if args.advance and unread and not args.dry_run:
        set_cursor(args.agent, last)
    return {"ok": True, "action": "read", "agent": args.agent,
            "cursor_before": cur, "cursor_after": (last if args.advance else cur),
            "count": len(unread), "events": unread}


def cmd_inbox(args) -> dict:
    if args.agent not in AGENTS:
        return {"ok": False, "error": "agent inconnu: " + args.agent}
    d = INBOX / args.agent
    items = []
    if d.exists():
        for f in sorted(d.glob("*.json")):
            try:
                items.append(json.loads(f.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                items.append({"_file": f.name, "_corrupt": True})
    return {"ok": True, "action": "inbox", "agent": args.agent,
            "count": len(items), "items": items}


# --------------------------------------------------------------------------- #
# Statut + alertes
# --------------------------------------------------------------------------- #
def collect_status() -> dict:
    evs = [e for e in read_events() if isinstance(e, dict)]
    corrupt = sum(1 for e in evs if e.get("_corrupt"))
    clean = [e for e in evs if not e.get("_corrupt")]
    last_hb = {}
    for e in clean:
        if e.get("type") == "heartbeat":
            last_hb[e["from"]] = {"state": e.get("payload", {}).get("state"),
                                  "ts": e.get("ts"), "seq": e.get("seq")}
    agents = {}
    for a in AGENTS:
        inbox_n = len(list((INBOX / a).glob("*.json"))) if (INBOX / a).exists() else 0
        agents[a] = {"last_heartbeat": last_hb.get(a), "cursor": get_cursor(a),
                     "inbox_pending": inbox_n}
    return {
        "generated_at": now_iso(), "canal_root": str(CANAL_ROOT),
        "events_total": len(clean), "events_corrupt": corrupt,
        "last_seq": max((e.get("seq", 0) for e in clean), default=0),
        "agents": agents, "health": "ok" if corrupt == 0 else "degraded",
    }


def compute_alerts() -> list:
    alerts = []
    # Taches
    for a in AGENTS:
        d = INBOX / a
        if not d.exists():
            continue
        for f in d.glob("*.json"):
            try:
                r = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            st = r.get("status", "assigned")
            task = r.get("task")
            if st == "assigned" and minutes_since(r.get("ts")) > ASSIGN_TIMEOUT_MIN:
                alerts.append({"level": "warn", "kind": "task_unclaimed", "agent": a,
                               "task": task, "age_min": round(minutes_since(r.get("ts")), 1)})
            elif st == "in_progress" and minutes_since(r.get("claimed_at")) > INPROGRESS_TIMEOUT_MIN:
                alerts.append({"level": "warn", "kind": "task_stuck", "agent": a,
                               "task": task, "attempts": r.get("attempts", 0),
                               "age_min": round(minutes_since(r.get("claimed_at")), 1)})
    # Verrous expires non liberes
    if LOCKS.exists():
        for lf in LOCKS.glob("*.json"):
            try:
                rec = json.loads(lf.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if lock_is_expired(rec):
                alerts.append({"level": "info", "kind": "lock_expired",
                               "resource": rec.get("resource"), "holder": rec.get("holder")})
    return alerts


def write_alerts_md(alerts: list) -> None:
    lines = ["# ALERTES canal_agents", "", "_Genere : " + now_iso() + "_", ""]
    if not alerts:
        lines.append("Aucune alerte. Systeme nominal.")
    else:
        lines.append("| Niveau | Type | Detail |")
        lines.append("|---|---|---|")
        for al in alerts:
            detail = ", ".join(f"{k}={v}" for k, v in al.items() if k not in ("level", "kind"))
            lines.append(f"| {al.get('level')} | {al.get('kind')} | {detail} |")
    ALERTS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_status() -> dict:
    ensure_tree()
    st = collect_status()
    import time
    for i in range(5):
        try:
            STATUS.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
            break
        except OSError as exc:
            if i == 4:
                print(f"Warning: failed to write STATUS.json: {exc}", file=sys.stderr)
            else:
                time.sleep(0.1)
    return st



# --------------------------------------------------------------------------- #
# Rotation / compaction de events.jsonl
# --------------------------------------------------------------------------- #
AUTO_ROTATE_AT = 2000  # au-dela : compaction automatique


def rotate_events(threshold: int = AUTO_ROTATE_AT, force: bool = False) -> dict:
    """Archive les events consommes par TOUS les agents (seq <= min des curseurs),
    en conservant le dernier heartbeat de chaque agent. Sans perte de livraison :
    un event non encore lu par un agent (seq > son curseur) n'est jamais archive.
    Ecriture atomique (tmp + replace)."""
    import os as _os
    raw = read_events()
    clean = [e for e in raw if isinstance(e, dict) and not e.get("_corrupt")
             and isinstance(e.get("seq"), int)]
    if not force and len(clean) <= threshold:
        return {"rotated": 0, "kept": len(clean)}
    cursors = [get_cursor(a) for a in AGENTS]
    safe = min(cursors) if cursors else 0
    latest_hb = {}
    for e in clean:
        if e.get("type") == "heartbeat":
            a = e.get("from")
            if a not in latest_hb or e["seq"] > latest_hb[a]:
                latest_hb[a] = e["seq"]
    keep_seqs = set(latest_hb.values())
    # TOUJOURS conserver le seq maximal (la queue) sinon next_seq() reculerait
    # apres compaction -> risque de collision de seq.
    keep_seqs.add(max(e["seq"] for e in clean))
    keep, arch = [], []
    for e in clean:
        if e["seq"] > safe or e["seq"] in keep_seqs:
            keep.append(e)
        else:
            arch.append(e)
    if not arch:
        return {"rotated": 0, "kept": len(keep)}
    keep.sort(key=lambda x: x["seq"])
    arch.sort(key=lambda x: x["seq"])
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    afile = ARCHIVE / ("events-" + _dt.date.today().isoformat() + ".jsonl")
    with afile.open("a", encoding="utf-8") as fh:
        for e in arch:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    tmp = EVENTS.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for e in keep:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    _os.replace(tmp, EVENTS)
    return {"rotated": len(arch), "kept": len(keep), "safe_seq": safe,
            "archive_file": str(afile)}


def maybe_auto_rotate() -> dict:
    try:
        return rotate_events()
    except Exception as exc:  # rotation best-effort, ne casse jamais health
        return {"rotated": 0, "error": str(exc)}


def cmd_rotate(args) -> dict:
    info = rotate_events(force=args.force)
    info["ok"] = True
    info["action"] = "rotate"
    return info


def cmd_health(args) -> dict:
    ensure_tree()
    rot = maybe_auto_rotate()
    st = collect_status()
    if args.write_status:
        STATUS.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
        st["status_written"] = str(STATUS)
    result = {"action": "health"}
    result.update(st)
    if args.alert:
        alerts = compute_alerts()
        result["alerts"] = alerts
        result["alert_count"] = len(alerts)
        write_alerts_md(alerts)
        if args.emit and alerts:
            for al in alerts:
                append_event(make_event("claude", "claude", "alert",
                                        msg=al.get("kind", "alert"), payload=al))
    if rot.get("rotated"):
        result["rotated"] = rot
    # ok reflete l'execution + l'integrite du bus, PAS la presence d'alertes
    # (les alertes sont des donnees rapportees dans le payload / ALERTS.md).
    result["ok"] = (st["health"] == "ok")
    return result


def cmd_status(args) -> dict:
    base = {"ok": True, "action": "status"}
    if STATUS.exists():
        base.update(json.loads(STATUS.read_text(encoding="utf-8")))
    else:
        base.update(collect_status())
    return base


# --------------------------------------------------------------------------- #
# Parseur
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sync_bus.py", description="Bus multi-agents TricorderKit v2")
    p.add_argument("--json", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    hb = sub.add_parser("heartbeat")
    hb.add_argument("agent", choices=AGENTS)
    hb.add_argument("--state", default="idle", choices=VALID_STATES)
    hb.add_argument("--note", default="")
    hb.add_argument("--dry-run", action="store_true")

    po = sub.add_parser("post")
    po.add_argument("--from", dest="sender", required=True, choices=AGENTS)
    po.add_argument("--to", required=True)
    po.add_argument("--type", default="message")
    po.add_argument("--task", default=None)
    po.add_argument("--msg", default="")
    po.add_argument("--payload", default=None)
    po.add_argument("--dry-run", action="store_true")

    di = sub.add_parser("dispatch")
    di.add_argument("--from", dest="sender", required=True, choices=AGENTS)
    di.add_argument("--to", required=True, choices=AGENTS)
    di.add_argument("--task", default=None)
    di.add_argument("--lane", default=None)
    di.add_argument("--priority", default="normal", choices=["low", "normal", "high", "critical"])
    di.add_argument("--deliverable", default=None)
    di.add_argument("--msg", default="")
    di.add_argument("--dry-run", action="store_true")

    cl = sub.add_parser("claim")
    cl.add_argument("--agent", required=True, choices=AGENTS)
    cl.add_argument("--task", required=True)
    cl.add_argument("--dry-run", action="store_true")

    dn = sub.add_parser("done")
    dn.add_argument("--agent", required=True, choices=AGENTS)
    dn.add_argument("--task", required=True)
    dn.add_argument("--status", default="done", choices=["done", "failed"])
    dn.add_argument("--deliverable", default=None)
    dn.add_argument("--msg", default="")
    dn.add_argument("--archive", action="store_true")
    dn.add_argument("--dry-run", action="store_true")

    ts = sub.add_parser("task-status")
    ts.add_argument("--agent", required=True, choices=AGENTS)
    ts.add_argument("--task", required=True)

    tk = sub.add_parser("tasks")
    tk.add_argument("--agent", default=None, choices=AGENTS)

    lk = sub.add_parser("lock")
    lk.add_argument("--resource", required=True)
    lk.add_argument("--agent", required=True, choices=AGENTS)
    lk.add_argument("--ttl-min", type=int, default=30)
    lk.add_argument("--pid", default=None)
    lk.add_argument("--dry-run", action="store_true")

    ul = sub.add_parser("unlock")
    ul.add_argument("--resource", required=True)
    ul.add_argument("--agent", required=True, choices=AGENTS)
    ul.add_argument("--force", action="store_true")

    rd = sub.add_parser("read")
    rd.add_argument("--agent", required=True, choices=AGENTS)
    rd.add_argument("--advance", action="store_true")
    rd.add_argument("--dry-run", action="store_true")

    ib = sub.add_parser("inbox")
    ib.add_argument("--agent", required=True, choices=AGENTS)

    he = sub.add_parser("health")
    he.add_argument("--write-status", action="store_true")
    he.add_argument("--alert", action="store_true")
    he.add_argument("--emit", action="store_true", help="poster les alertes sur le bus")

    ro = sub.add_parser("rotate")
    ro.add_argument("--force", action="store_true", help="compacter meme sous le seuil")

    sub.add_parser("status")
    return p


DISPATCH = {
    "init": cmd_init, "heartbeat": cmd_heartbeat, "post": cmd_post, "dispatch": cmd_dispatch,
    "claim": cmd_claim, "done": cmd_done, "task-status": cmd_task_status, "tasks": cmd_tasks,
    "lock": cmd_lock, "unlock": cmd_unlock, "read": cmd_read, "inbox": cmd_inbox,
    "health": cmd_health, "status": cmd_status, "rotate": cmd_rotate,
}


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = DISPATCH[args.cmd](args)
    except ValueError as exc:
        result = {"ok": False, "error": str(exc)}
    rc = 0 if result.get("ok") else 1
    stream = sys.stdout
    if stream is None:
        return rc
    try:
        is_tty = bool(stream.isatty())
    except Exception:
        is_tty = False
    if args.json or not is_tty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        head = "OK" if result.get("ok") else "ERREUR"
        print("[" + head + "] " + str(result.get("action", args.cmd)))
        for k, v in result.items():
            if k in ("ok", "action"):
                continue
            if isinstance(v, (dict, list)):
                print("  " + k + ": " + json.dumps(v, ensure_ascii=False))
            else:
                print("  " + k + ": " + str(v))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
