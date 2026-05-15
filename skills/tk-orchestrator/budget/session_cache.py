"""
session_cache.py — Cache SQLite partagé avec tk-boot
TricorderKit v0.8 — tk-orchestrator v0.2.0

Lit le contexte de session chargé par tk-boot (STATE.md, DECISIONS.md, etc.)
pour éviter une double lecture des fichiers de planning.

Table partagée : session_context (même DB que tk-boot)
TTL : 300 secondes (configurable)
"""

from __future__ import annotations
import json
import sqlite3
import time
from pathlib import Path
from typing import Optional


# ── Constantes ────────────────────────────────────────────────────────────────

DEFAULT_CACHE_PATH = ".cache/orchestrator.db"
SESSION_TABLE = "session_context"
ORCHESTRATION_TABLE = "orchestration_log"
DEFAULT_TTL = 300  # secondes


# ── Initialisation ────────────────────────────────────────────────────────────

def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialise la base SQLite et crée les tables si nécessaire."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    conn.executescript(f"""
        CREATE TABLE IF NOT EXISTS {SESSION_TABLE} (
            key         TEXT PRIMARY KEY,
            value       TEXT NOT NULL,
            source      TEXT DEFAULT 'unknown',
            created_at  REAL NOT NULL,
            ttl         INTEGER DEFAULT {DEFAULT_TTL}
        );

        CREATE TABLE IF NOT EXISTS {ORCHESTRATION_TABLE} (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   REAL NOT NULL,
            intent_type TEXT,
            domain      TEXT,
            tool_used   TEXT,
            status      TEXT,
            tokens_used INTEGER,
            duration_ms INTEGER
        );

        CREATE INDEX IF NOT EXISTS idx_session_key
            ON {SESSION_TABLE}(key);
    """)
    conn.commit()
    return conn


def _get_conn(root: Path, cache_path: Optional[str] = None) -> sqlite3.Connection:
    db_path = root / (cache_path or DEFAULT_CACHE_PATH)
    return init_db(db_path)


# ── Lecture contexte tk-boot ──────────────────────────────────────────────────

def get_boot_context(
    root: Path,
    cache_path: Optional[str] = None,
    ttl: int = DEFAULT_TTL,
) -> Optional[dict]:
    """
    Lit le contexte chargé par tk-boot depuis le cache SQLite.
    Retourne None si absent ou expiré.

    Clés typiques stockées par tk-boot :
    - state_summary : résumé de STATE.md
    - active_tasks : tâches actives
    - open_risks : risques ouverts
    - recent_decisions : dernières décisions
    - token_budget_level : niveau de budget
    """
    try:
        conn = _get_conn(root, cache_path)
        cursor = conn.execute(
            f"""
            SELECT key, value, created_at, ttl
            FROM {SESSION_TABLE}
            WHERE source = 'tk-boot'
            ORDER BY created_at DESC
            """,
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        now = time.time()
        context = {}
        for row in rows:
            age = now - row["created_at"]
            effective_ttl = row["ttl"] if row["ttl"] else ttl
            if age <= effective_ttl:
                try:
                    context[row["key"]] = json.loads(row["value"])
                except (json.JSONDecodeError, TypeError):
                    context[row["key"]] = row["value"]

        return context if context else None

    except (sqlite3.Error, OSError):
        return None


def store_session_value(
    root: Path,
    key: str,
    value: object,
    source: str = "tk-orchestrator",
    ttl: int = DEFAULT_TTL,
    cache_path: Optional[str] = None,
) -> bool:
    """Stocke une valeur dans le cache de session."""
    try:
        conn = _get_conn(root, cache_path)
        conn.execute(
            f"""
            INSERT OR REPLACE INTO {SESSION_TABLE}
                (key, value, source, created_at, ttl)
            VALUES (?, ?, ?, ?, ?)
            """,
            (key, json.dumps(value, ensure_ascii=False), source, time.time(), ttl),
        )
        conn.commit()
        conn.close()
        return True
    except (sqlite3.Error, OSError, TypeError):
        return False


# ── Log d'orchestration ───────────────────────────────────────────────────────

def log_orchestration(
    root: Path,
    intent_type: str,
    domain: str,
    tool_used: str,
    status: str,
    tokens_used: int,
    duration_ms: int,
    cache_path: Optional[str] = None,
) -> bool:
    """Enregistre une exécution d'orchestration dans le log."""
    try:
        conn = _get_conn(root, cache_path)
        conn.execute(
            f"""
            INSERT INTO {ORCHESTRATION_TABLE}
                (timestamp, intent_type, domain, tool_used, status, tokens_used, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (time.time(), intent_type, domain, tool_used, status, tokens_used, duration_ms),
        )
        conn.commit()
        conn.close()
        return True
    except (sqlite3.Error, OSError):
        return False


def get_orchestration_stats(
    root: Path,
    limit: int = 10,
    cache_path: Optional[str] = None,
) -> list:
    """Retourne les dernières exécutions d'orchestration."""
    try:
        conn = _get_conn(root, cache_path)
        cursor = conn.execute(
            f"""
            SELECT * FROM {ORCHESTRATION_TABLE}
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
    except (sqlite3.Error, OSError):
        return []
