from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from secsai_group_6.categories import Category


class StorageError(Exception):
    """Feedback could not be stored."""


_SCHEMA = """ 
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    shown_category TEXT NOT NULL,
    reported_category TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (url, shown_category, reported_category)
)
"""

_INSERT = """ 
INSERT INTO feedback (url, shown_category, reported_category, created_at)
VALUES (?, ?, ?, ?)
ON CONFLICT DO NOTHING
"""

_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS request_log (
    id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    status INTEGER NOT NULL,
    category TEXT,
    latency_ms INTEGER NOT NULL,
    worker_id TEXT
)
"""


def save_feedback(
    db_path: Path | str,
    url: str,
    shown_category: Category,
    reported_category: Category,
) -> bool:
    """Store a report. Returns True if new, False if it was already reported."""
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        with closing(sqlite3.connect(db_path)) as conn:
            with conn:
                conn.execute(_SCHEMA)
                cur = conn.execute(
                    _INSERT,
                    (url, shown_category.value, reported_category.value, created_at),
                )
                inserted = cur.rowcount == 1
    except sqlite3.Error as exc:
        raise StorageError("Could not save feedback") from exc
    return inserted


def log_request(
    db_path: Path | str,
    status: int,
    latency_ms: int,
    category: str | None = None,
    worker_id: str | None = None,
) -> None:
    """Record one /assess call. Stores no URL."""
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        with closing(sqlite3.connect(db_path)) as conn:
            with conn:
                conn.execute(_LOG_SCHEMA)
                conn.execute(
                    "INSERT INTO request_log (created_at, status, category, latency_ms, worker_id) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (created_at, status, category, latency_ms, worker_id),
                )
    except sqlite3.Error as exc:
        raise StorageError("Could not log request") from exc
