"""Persist reviewer decisions independently of the generated flag reports."""

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path


def save_decision(
    db_path: str | Path,
    listing_id: str,
    option_id: str,
    decision: str,
    reason: str,
    *,
    at: str | None = None,
) -> dict[str, str]:
    """Save or replace the decision for one listing option."""
    if decision not in ("accepted", "dismissed"):
        raise ValueError("Decision must be 'accepted' or 'dismissed'.")

    timestamp = datetime.now(UTC).isoformat() if at is None else at
    path = Path(db_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, uri=False)) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reviewer_decisions (
                listing_id TEXT NOT NULL,
                option_id TEXT NOT NULL,
                decision TEXT NOT NULL CHECK (decision IN ('accepted', 'dismissed')),
                reason TEXT NOT NULL,
                at TEXT NOT NULL,
                PRIMARY KEY (listing_id, option_id)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO reviewer_decisions (listing_id, option_id, decision, reason, at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (listing_id, option_id) DO UPDATE SET
                decision = excluded.decision,
                reason = excluded.reason,
                at = excluded.at
            """,
            (listing_id, option_id, decision, reason, timestamp),
        )
    return {"decision": decision, "reason": reason, "at": timestamp}


def load_decision(
    db_path: str | Path,
    listing_id: str,
    option_id: str,
) -> dict[str, str] | None:
    """Return the saved decision for one option, if there is one."""
    path = Path(db_path).resolve()
    if not path.exists():
        return None

    # Encode the filename before adding the fixed read-only SQLite URI option.
    database_uri = path.as_uri() + "?mode=ro"
    with closing(sqlite3.connect(database_uri, uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        initialized = connection.execute(
            "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = 'reviewer_decisions'"
        ).fetchone()
        if initialized is None:
            return None

        record = connection.execute(
            """
            SELECT decision, reason, at
            FROM reviewer_decisions
            WHERE listing_id = ? AND option_id = ?
            """,
            (listing_id, option_id),
        ).fetchone()
    return dict(record) if record is not None else None
