"""
baseline_store.py — Persistance SQLite des baselines de référence
TricorderKit eval-lab v0.1.0

Stocke et récupère les outputs de référence pour la détection de régression.
Pattern identique à QualityGuard error_memory.sqlite (SHA-256 + timestamps).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

# -- Chemins ------------------------------------------------------------------
_HERE = Path(__file__).parent
_REPO_ROOT = _HERE.parent.parent
DEFAULT_DB_PATH = _REPO_ROOT / "data" / "eval-lab" / "baselines.sqlite"

# -- DDL ----------------------------------------------------------------------
_DDL = """
CREATE TABLE IF NOT EXISTS baselines (
    skill_name      TEXT NOT NULL,
    skill_version   TEXT NOT NULL,
    output_hash     TEXT NOT NULL,
    output_json     TEXT NOT NULL,
    recorded_at     TEXT NOT NULL,
    PRIMARY KEY (skill_name, skill_version)
);

CREATE TABLE IF NOT EXISTS eval_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name      TEXT NOT NULL,
    skill_version   TEXT NOT NULL,
    status          TEXT NOT NULL,          -- pass | fail | schema_error
    violations_json TEXT NOT NULL DEFAULT '[]',
    regressions_json TEXT NOT NULL DEFAULT '[]',
    output_hash     TEXT NOT NULL,
    evaluated_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_eval_history_skill ON eval_history(skill_name, evaluated_at);
"""


# -- Dataclasses --------------------------------------------------------------

@dataclass
class BaselineRecord:
    skill_name: str
    skill_version: str
    output_hash: str
    output: dict
    recorded_at: str


@dataclass
class EvalHistoryEntry:
    skill_name: str
    skill_version: str
    status: str             # pass | fail | schema_error
    violations: list
    regressions: list
    output_hash: str
    evaluated_at: str


# -- BaselineStore ------------------------------------------------------------

class BaselineStore:
    """Store SQLite pour les baselines et l'historique d'évaluation."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    # -- Connexion ------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        conn = self._connect()
        conn.executescript(_DDL)
        conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # -- Baselines ------------------------------------------------------------

    @staticmethod
    def _hash_output(output: dict) -> str:
        """Hash SHA-256 déterministe de l'output (clés triées)."""
        canonical = json.dumps(output, sort_keys=True, ensure_ascii=False)
        return sha256(canonical.encode()).hexdigest()

    def get_baseline(self, skill_name: str) -> BaselineRecord | None:
        """Récupère la baseline la plus récente pour un skill."""
        conn = self._connect()
        row = conn.execute(
            "SELECT * FROM baselines WHERE skill_name = ? ORDER BY recorded_at DESC LIMIT 1",
            (skill_name,),
        ).fetchone()
        if row is None:
            return None
        return BaselineRecord(
            skill_name=row["skill_name"],
            skill_version=row["skill_version"],
            output_hash=row["output_hash"],
            output=json.loads(row["output_json"]),
            recorded_at=row["recorded_at"],
        )

    def save_baseline(self, skill_name: str, output: dict) -> BaselineRecord:
        """Sauvegarde ou met à jour la baseline d'un skill."""
        now = datetime.now(timezone.utc).isoformat()
        output_hash = self._hash_output(output)
        skill_version = output.get("skill_version", "0.0.0")

        conn = self._connect()
        conn.execute(
            """
            INSERT INTO baselines (skill_name, skill_version, output_hash, output_json, recorded_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(skill_name, skill_version) DO UPDATE SET
                output_hash = excluded.output_hash,
                output_json = excluded.output_json,
                recorded_at = excluded.recorded_at
            """,
            (skill_name, skill_version, output_hash, json.dumps(output), now),
        )
        conn.commit()
        return BaselineRecord(
            skill_name=skill_name,
            skill_version=skill_version,
            output_hash=output_hash,
            output=output,
            recorded_at=now,
        )

    def baseline_exists(self, skill_name: str) -> bool:
        """Vérifie si une baseline existe pour un skill."""
        conn = self._connect()
        row = conn.execute(
            "SELECT 1 FROM baselines WHERE skill_name = ? LIMIT 1",
            (skill_name,),
        ).fetchone()
        return row is not None

    # -- Historique -----------------------------------------------------------

    def log_eval(
        self,
        skill_name: str,
        skill_version: str,
        status: str,
        violations: list,
        regressions: list,
        output_hash: str,
    ) -> None:
        """Log un résultat d'évaluation dans l'historique."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        conn.execute(
            """
            INSERT INTO eval_history
                (skill_name, skill_version, status, violations_json, regressions_json, output_hash, evaluated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                skill_name,
                skill_version,
                status,
                json.dumps(violations),
                json.dumps(regressions),
                output_hash,
                now,
            ),
        )
        conn.commit()

    def get_history(self, skill_name: str, limit: int = 10) -> list[EvalHistoryEntry]:
        """Récupère l'historique d'évaluation d'un skill."""
        conn = self._connect()
        rows = conn.execute(
            """
            SELECT * FROM eval_history
            WHERE skill_name = ?
            ORDER BY evaluated_at DESC
            LIMIT ?
            """,
            (skill_name, limit),
        ).fetchall()
        return [
            EvalHistoryEntry(
                skill_name=row["skill_name"],
                skill_version=row["skill_version"],
                status=row["status"],
                violations=json.loads(row["violations_json"]),
                regressions=json.loads(row["regressions_json"]),
                output_hash=row["output_hash"],
                evaluated_at=row["evaluated_at"],
            )
            for row in rows
        ]

    def list_skills(self) -> list[str]:
        """Liste les skills ayant une baseline."""
        conn = self._connect()
        rows = conn.execute("SELECT DISTINCT skill_name FROM baselines ORDER BY skill_name").fetchall()
        return [row["skill_name"] for row in rows]
