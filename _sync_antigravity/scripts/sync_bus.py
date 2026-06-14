#!/usr/bin/env python3
"""TricorderKit — sync_bus : transport de communication Claude <-> Antigravity <-> Hermes.

PHILOSOPHIE (DEC-032 / tk-realtime/1 — clarif. Sebastien 2026-06-04) :
  La communication est du PYTHON DETERMINISTE, ZERO TOKEN LLM. Le scheduler (ou un run
  Haiku leger) appelle ce script ; aucun modele cher ne poll. Haiku ne fait que LIRE le
  digest produit ici et decider quoi ordonner. Opus reste hors de la boucle routiniere.

Corrige par construction le bug de troncature de STATUS.json : l'ecriture passe TOUJOURS
par json.dump (JSON valide garanti), les narratifs sont bornes, les cles _legacy purgees.

Bus = bus/events.jsonl (append-only, jamais reecrit). Curseur par agent (anti-staleness mtime).

Usage :
  python3 sync_bus.py heartbeat <agent> [--state idle|working] [--note "..."]
  python3 sync_bus.py emit <type> --from <agent> [--ref R] [--payload '{...}']
  python3 sync_bus.py read --agent <agent>                # consomme le bus au-dela du curseur
  python3 sync_bus.py health [--write-status]             # verdict + compteurs disque
  python3 sync_bus.py dispatch                            # offloads ouverts (pour decision Haiku)
  python3 sync_bus.py sense                               # deduit la presence d'Antigravity (sans qu'il lance rien)
  python3 sync_bus.py repair-status                       # reconstruit un STATUS.json valide
"""
import json, os, sys, glob, datetime, argparse, re, time

# Forcer la sortie en UTF-8 : evite UnicodeEncodeError sur console Windows cp1252
# (signale par Codex 2026-06-05 sur `read`). N'affecte pas les donnees du bus.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUS_DIR = os.path.join(BASE, "bus")
EVENTS = os.path.join(BUS_DIR, "events.jsonl")
WAKE = os.path.join(BUS_DIR, ".wake")
STATUS = os.path.join(BASE, "STATUS.json")
RAPPORTS = os.path.join(BASE, "rapports")
AG_INBOX = os.path.join(BASE, "commands", "antigravity_inbox")
CL_INBOX = os.path.join(BASE, "commands", "claude_inbox")
ETAT = os.path.join(BASE, "ETAT_PARTAGE.md")

STALE_MIN = 90          # agent silencieux > 90 min = stale
NOTE_CAP = 280          # borne anti-troncature pour last_action

TZ = datetime.timezone(datetime.timedelta(hours=2))
def now_iso(): return datetime.datetime.now(TZ).isoformat(timespec="seconds")

def minutes_since(iso):
    if not iso: return None
    try:
        t = datetime.datetime.fromisoformat(iso)
        return round((datetime.datetime.now(t.tzinfo) - t).total_seconds() / 60, 1)
    except Exception:
        return None

# ---------- STATUS (toujours valide, borne) ----------
def _skeleton():
    return {
        "schema": "tk-sync-status/1",
        "updated_by": "sync_bus",
        "updated_at": now_iso(),
        "cadence": {"mode": "realtime-poll", "transport": "python:sync_bus",
                    "poll_seconds": 60, "lock_for": "vault_writes_only",
                    "deprecated": "battement horaire XX:01/XX:10"},
        "agents": {},
    }

def load_status():
    if os.path.exists(STATUS):
        for attempt in range(5):
            try:
                with open(STATUS, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content.strip():
                        raise ValueError("STATUS.json is empty")
                    return json.loads(content)
            except Exception as e:
                if attempt == 4:
                    if isinstance(e, PermissionError) or "sharing violation" in str(e).lower():
                        print(f"Error: STATUS.json is locked: {e}", file=sys.stderr)
                        sys.exit(1)
                time.sleep(0.1)
    return _skeleton()

def save_status(st):
    import uuid
    st["updated_at"] = now_iso()
    for name, a in list(st.get("agents", {}).items()):
        for k in list(a.keys()):
            if k.startswith("_legacy"):
                del a[k]
        if isinstance(a.get("last_action"), str) and len(a["last_action"]) > NOTE_CAP:
            a["last_action"] = a["last_action"][:NOTE_CAP - 1] + "..."
    tmp = STATUS + f".{uuid.uuid4().hex}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
        for attempt in range(5):
            try:
                os.replace(tmp, STATUS)
                break
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(0.1)
    except Exception as e:
        print(f"Error saving STATUS.json: {e}", file=sys.stderr)
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except Exception: pass
        raise

# ---------- BUS (append-only) ----------
def append_event(ev):
    os.makedirs(BUS_DIR, exist_ok=True)
    with open(EVENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    try:
        open(WAKE, "w").write(now_iso())
    except Exception:
        pass

def read_events():
    if not os.path.exists(EVENTS): return []
    out = []
    for line in open(EVENTS, encoding="utf-8"):
        line = line.strip()
        if line:
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def cursor_path(agent): return os.path.join(BUS_DIR, "cursor." + agent)
def get_cursor(agent):
    try: return int(open(cursor_path(agent)).read().strip())
    except Exception: return 0
def set_cursor(agent, n): open(cursor_path(agent), "w").write(str(n))

def _evid():
    return "EVT-" + datetime.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%f")[:-3]

def _read_frontmatter_field(path, field):
    try:
        txt = open(path, encoding="utf-8").read(4000)
        m = re.search(r'^' + field + r'\s*:\s*"?([0-9T:\-+]+)"?\s*$', txt, re.M)
        return m.group(1) if m else None
    except Exception:
        return None

# ---------- Commandes ----------
def cmd_heartbeat(args):
    ev = {"id": _evid(), "ts": now_iso(), "from": args.agent, "type": "heartbeat",
          "ref": None, "payload": {"state": args.state}}
    append_event(ev)
    st = load_status()
    st.setdefault("agents", {})[args.agent] = {
        "heartbeat": ev["ts"], "state": args.state, "last_action": (args.note or "")[:NOTE_CAP]}
    save_status(st)
    print(json.dumps({"ok": True, "heartbeat": ev["ts"], "agent": args.agent}, ensure_ascii=False))

def cmd_emit(args):
    payload = {}
    if args.payload:
        try: payload = json.loads(args.payload)
        except Exception: payload = {"raw": args.payload}
    ev = {"id": _evid(), "ts": now_iso(), "from": getattr(args, "from"),
          "type": args.type, "ref": args.ref, "payload": payload}
    append_event(ev)
    print(json.dumps({"ok": True, "event": ev["id"], "type": args.type}, ensure_ascii=False))

def cmd_read(args):
    evs = read_events()
    cur = get_cursor(args.agent)
    new = [e for e in evs[cur:] if e.get("from") != args.agent]
    set_cursor(args.agent, len(evs))
    print(json.dumps({"agent": args.agent, "from_cursor": cur, "to_cursor": len(evs),
                      "new_events": new}, ensure_ascii=False, indent=2))

def cmd_health(args):
    so = len(glob.glob(os.path.join(RAPPORTS, "SO*.md")))
    st_ = len(glob.glob(os.path.join(RAPPORTS, "ST*.md")))
    total = len(glob.glob(os.path.join(RAPPORTS, "*.md")))
    st = load_status()
    agents = st.get("agents", {})
    health = {"verdict": "green", "checks": {"rapports_present": so > 0}}
    if so == 0:
        health["verdict"] = "red"; health["checks"]["reason"] = "aucun rapport SO"
    for name, a in agents.items():
        m = minutes_since(a.get("heartbeat"))
        stale = (m is None) or (m > STALE_MIN)
        health["checks"][name + "_heartbeat_min"] = m
        health["checks"][name + "_stale"] = stale
        if stale and health["verdict"] == "green":
            health["verdict"] = "yellow"
    out = {"ts": now_iso(),
           "counters_disk": {"rapports_total": total, "so_rapports": so, "st_rapports": st_,
                             "queue_antigravity_inbox": len(glob.glob(os.path.join(AG_INBOX, "2*.md"))),
                             "queue_claude_inbox": len(glob.glob(os.path.join(CL_INBOX, "2*.md")))},
           "agents": agents, "health": health}
    if args.write_status:
        st["counters_disk"] = out["counters_disk"]; st["health"] = health
        st["updated_by"] = "sync_bus:health"
        save_status(st)
    print(json.dumps(out, ensure_ascii=False, indent=2))

def cmd_dispatch(args):
    open_offloads = []
    for f in sorted(glob.glob(os.path.join(AG_INBOX, "2*.md"))):
        head = open(f, encoding="utf-8").read(600)
        open_offloads.append({"file": os.path.basename(f),
                              "queued": ("status: queued" in head or "status: in_progress" in head)})
    results_waiting = [os.path.basename(f) for f in sorted(glob.glob(os.path.join(CL_INBOX, "2*.md")))]
    print(json.dumps({"ts": now_iso(), "antigravity_inbox_open": open_offloads,
                      "claude_inbox_results_waiting": results_waiting}, ensure_ascii=False, indent=2))

def cmd_sense(args):
    """Deduit le heartbeat d'Antigravity de signaux QU'IL ECRIT LUI-MEME (sans qu'il lance rien) :
    maj_antigravity dans ETAT_PARTAGE.md + frontmatter date/traite_le des derniers task_result."""
    candidates = []
    maj = _read_frontmatter_field(ETAT, "maj_antigravity")
    if maj: candidates.append(maj)
    for f in sorted(glob.glob(os.path.join(CL_INBOX, "2*.md")))[-3:]:
        for fld in ("traite_le", "date"):
            d = _read_frontmatter_field(f, fld)
            if d: candidates.append(d if "T" in d else d + "T00:00:00+02:00")
    best = None
    for c in candidates:
        try:
            t = datetime.datetime.fromisoformat(c)
            if best is None or t > best: best = t
        except Exception:
            pass
    st = load_status()
    if best:
        ag = st.setdefault("agents", {}).setdefault("antigravity", {})
        ag["heartbeat"] = best.isoformat(timespec="seconds")
        ag.setdefault("state", "idle")
        ag["last_action"] = "presence deduite (sense): maj_antigravity + dernier task_result"
        save_status(st)
    hb = best.isoformat(timespec="seconds") if best else None
    print(json.dumps({"ts": now_iso(), "antigravity_present": best is not None,
                      "deduced_heartbeat": hb, "minutes_since": minutes_since(hb)},
                     ensure_ascii=False, indent=2))

def cmd_repair_status(args):
    # load_status() retombe sur un squelette valide si STATUS.json est corrompu/tronque
    st = load_status()
    st["updated_by"] = "sync_bus:repair"
    save_status(st)
    print(json.dumps({"ok": True, "repaired": True, "path": STATUS}, ensure_ascii=False))

# ---------- CLI ----------
def main():
    p = argparse.ArgumentParser(prog="sync_bus")
    sub = p.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("heartbeat"); h.add_argument("agent")
    h.add_argument("--state", default="idle", choices=["idle", "working"])
    h.add_argument("--note", default="")
    h.set_defaults(func=cmd_heartbeat)

    e = sub.add_parser("emit"); e.add_argument("type")
    e.add_argument("--from", required=True)
    e.add_argument("--ref", default=None)
    e.add_argument("--payload", default=None)
    e.set_defaults(func=cmd_emit)

    r = sub.add_parser("read"); r.add_argument("--agent", required=True)
    r.set_defaults(func=cmd_read)

    he = sub.add_parser("health"); he.add_argument("--write-status", action="store_true")
    he.set_defaults(func=cmd_health)

    sub.add_parser("dispatch").set_defaults(func=cmd_dispatch)
    sub.add_parser("sense").set_defaults(func=cmd_sense)
    sub.add_parser("repair-status").set_defaults(func=cmd_repair_status)

    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
