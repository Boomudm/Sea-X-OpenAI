"""Durable validated review cache keyed by (review_id, prompt_version)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Self


class ReviewCache:
    def __init__(self, path: str | Path = "out/cache/readers.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS review_cache (
                review_id TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (review_id, prompt_version)
            )
            """
        )
        self._connection.commit()

    def get(self, review_id: str, prompt_version: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT payload FROM review_cache WHERE review_id = ? AND prompt_version = ?",
            (review_id, prompt_version),
        ).fetchone()
        return None if row is None else json.loads(row[0])

    def put(self, review_id: str, prompt_version: str, payload: dict[str, Any]) -> None:
        self._connection.execute(
            """
            INSERT INTO review_cache (review_id, prompt_version, payload)
            VALUES (?, ?, ?)
            ON CONFLICT(review_id, prompt_version) DO UPDATE SET payload = excluded.payload,
                created_at = CURRENT_TIMESTAMP
            """,
            (review_id, prompt_version, json.dumps(payload, ensure_ascii=False)),
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
