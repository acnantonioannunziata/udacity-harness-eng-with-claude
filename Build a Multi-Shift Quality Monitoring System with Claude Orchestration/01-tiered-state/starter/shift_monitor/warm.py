"""Warm tier: SQLite-backed defect store with indexed `defects_since` query."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS defects (
    id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    shift TEXT NOT NULL,
    component TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_defects_shift_ts
ON defects (shift, ts);

CREATE INDEX IF NOT EXISTS idx_defects_ts
ON defects (ts);
"""


class WarmStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)

    def insert_many(self, rows: Iterable[Mapping[str, Any]]) -> None:
        values = [
            (
                row["id"],
                row["ts"],
                row["shift"],
                row["component"],
                row["severity"],
                row["description"],
            )
            for row in rows
        ]
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO defects
                    (id, ts, shift, component, severity, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                values,
            )

    def count(self) -> int:
        with self._connect() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM defects")
            return int(cur.fetchone()[0])

    def fetch_by_id(self, defect_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM defects WHERE id = ?", (defect_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def column_names(self, table: str) -> list[str]:
        with self._connect() as conn:
            cur = conn.execute(f"PRAGMA table_info({table})")
            return [r["name"] for r in cur.fetchall()]

    def has_index_on(self, table: str, columns: tuple[str, ...]) -> bool:
        with self._connect() as conn:
            indexes = conn.execute(f"PRAGMA index_list({table})").fetchall()
            for idx in indexes:
                cols = conn.execute(f"PRAGMA index_info({idx['name']})").fetchall()
                if tuple(c["name"] for c in cols) == columns:
                    return True
            return False

    def defects_since(self, since_ts: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM defects
                WHERE ts > ?
                ORDER BY ts DESC
                LIMIT ?
                """,
                (since_ts, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def explain_defects_since(self, since_ts: str, limit: int = 50) -> list[tuple[Any, ...]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                EXPLAIN QUERY PLAN
                SELECT *
                FROM defects
                WHERE ts > ?
                ORDER BY ts DESC
                LIMIT ?
                """,
                (since_ts, limit),
            ).fetchall()
            return [tuple(row) for row in rows]

    def top_components_for_month(
        self, year: int, month: int, n: int = 3
    ) -> list[tuple[str, int]]:
        month_prefix = f"{year:04d}-{month:02d}-%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT component, COUNT(*) AS defect_count
                FROM defects
                WHERE ts LIKE ?
                GROUP BY component
                ORDER BY defect_count DESC, component ASC
                LIMIT ?
                """,
                (month_prefix, n),
            ).fetchall()
            return [(str(row["component"]), int(row["defect_count"])) for row in rows]

    def count_for_month(self, year: int, month: int) -> int:
        month_prefix = f"{year:04d}-{month:02d}-%"
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM defects WHERE ts LIKE ?",
                (month_prefix,),
            ).fetchone()
            return int(row[0])
