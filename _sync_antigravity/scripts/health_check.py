#!/usr/bin/env python3
"""TricorderKit — capteur sync Antigravity (remplace la sonde mtime defaillante).
Compte les fichiers REELS et lit les heartbeats de STATUS.json. Sortie JSON.
Usage: python3 health_check.py [--write-status]"""
import json, os, sys, glob, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAPPORTS = os.path.join(BASE, "rapports")
STATUS = os.path.join(BASE, "STATUS.json")
HEARTBEAT_STALE_MIN = 90   # un agent silencieux > 90 min = stale

def now_iso():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2))).isoformat(timespec="seconds")

def count(pattern):
    return len(glob.glob(os.path.join(RAPPORTS, pattern)))

def minutes_since(iso):
    if not iso: return None
    try:
        t = datetime.datetime.fromisoformat(iso)
        d = datetime.datetime.now(t.tzinfo) - t
        return round(d.total_seconds()/60, 1)
    except Exception:
        return None

def main():
    so = count("SO*.md")
    st = count("ST*.md")
    total = len([f for f in glob.glob(os.path.join(RAPPORTS,"*.md"))])
    status = {}
    if os.path.exists(STATUS):
        try: status = json.load(open(STATUS, encoding="utf-8"))
        except Exception: status = {}
    agents = status.get("agents", {})
    health = {"verdict": "green", "checks": {}}
    # Regle d'or : NE JAMAIS conclure "muet" sur l'absence du dossier de rapports si des fichiers existent.
    health["checks"]["rapports_present"] = so > 0
    if so == 0:
        health["verdict"] = "red"; health["checks"]["reason"] = "aucun rapport SO sur disque"
    for name, a in agents.items():
        m = minutes_since(a.get("heartbeat"))
        a_stale = (m is None) or (m > HEARTBEAT_STALE_MIN)
        health["checks"][f"{name}_heartbeat_min"] = m
        health["checks"][f"{name}_stale"] = a_stale
        if a_stale and health["verdict"] == "green":
            health["verdict"] = "yellow"
    out = {
        "ts": now_iso(),
        "counters_disk": {
            "rapports_total": total, "so_rapports": so, "st_rapports": st,
            "queue_antigravity_inbox": len(glob.glob(os.path.join(BASE,"commands","antigravity_inbox","2*.md"))),
            "queue_claude_inbox": len(glob.glob(os.path.join(BASE,"commands","claude_inbox","2*.md"))),
        },
        "agents": agents,
        "health": health,
    }
    if "--write-status" in sys.argv:
        status["updated_by"] = "health_check"; status["updated_at"] = out["ts"]
        status["counters_disk"] = out["counters_disk"]; status["health"] = health
        json.dump(status, open(STATUS,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
