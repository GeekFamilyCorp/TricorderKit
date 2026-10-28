#!/usr/bin/env python3
"""health_heartbeat.py - Check horaire Ollama + Qdrant, LOG ONLY (supervision sante / DEC-025).

Aucune action intrusive : ecrit une ligne d'etat dans health_heartbeat.log.
Le fait que ce script s'execute prouve que l'hote est allume (host=UP).
A planifier par l'agent de scheduling (cron/Task Scheduler) ; supervision passive.

Usage : python health_heartbeat.py
"""
import os, urllib.request, datetime

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "health_heartbeat.log")


def _up(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return getattr(r, "status", 200) == 200
    except Exception:
        return False


def main():
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    ollama = "UP" if _up("http://localhost:11434/api/tags") else "DOWN"
    qdrant = "UP" if _up("http://localhost:6333/collections") else "DOWN"
    line = "%s | host=UP | ollama=%s | qdrant=%s\n" % (ts, ollama, qdrant)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
