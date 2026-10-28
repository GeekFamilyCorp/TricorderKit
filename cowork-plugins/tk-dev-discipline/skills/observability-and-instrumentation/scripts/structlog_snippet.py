#!/usr/bin/env python3
"""Logger JSON structuré, stdlib seulement — à copier dans un script d'automatisation.

Usage dans un script :
    from structlog_snippet import get_logger
    log = get_logger("promote", logfile="promote.log")
    log.info("run_start", lot=25)
    log.error("fichier_illisible", path="x.md", exc=str(e))

Chaque ligne écrite est un objet JSON : {"ts": ISO8601 UTC, "level", "logger", "event", ...champs}.
Append-only, flush immédiat (survit au crash). Lancer `--demo` pour voir la sortie.
"""
import json
import logging
import sys
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    def format(self, record):
        doc = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        doc.update(getattr(record, "fields", {}))  # champs clé=valeur passés à l'appel
        return json.dumps(doc, ensure_ascii=False)


class _Log:
    """Façade minimale : log.info("event", cle=valeur, ...)."""

    def __init__(self, logger):
        self._l = logger

    def _emit(self, level, event, **fields):
        self._l.log(level, event, extra={"fields": fields})

    def info(self, event, **f):
        self._emit(logging.INFO, event, **f)

    def warning(self, event, **f):
        self._emit(logging.WARNING, event, **f)

    def error(self, event, **f):
        self._emit(logging.ERROR, event, **f)


def get_logger(name, logfile=None, level=logging.INFO):
    """Retourne une façade ; si `logfile` est donné, ajoute un fichier en append (UTF-8) + stderr."""
    logger = logging.getLogger(name)
    if not logger.handlers:  # idempotent
        handlers = [logging.StreamHandler(sys.stderr)]
        if logfile:
            handlers.append(logging.FileHandler(logfile, mode="a", encoding="utf-8"))
        for h in handlers:
            h.setFormatter(_JsonFormatter())
            logger.addHandler(h)
        logger.setLevel(level)
        logger.propagate = False
    return _Log(logger)


if __name__ == "__main__":
    if "--demo" in sys.argv:
        log = get_logger("demo")
        log.info("run_start", lot=3, source="démo")
        log.warning("skip", path="fiche_données_été.md", raison="doublon")
        log.info("run_end", promues=2, skip=1, duree_s=0.01)
        sys.exit(0)
    print(__doc__)
