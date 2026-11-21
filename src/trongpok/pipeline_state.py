"""SQLite job leases, budget reservations and the pipeline's review queue."""

import json
import sqlite3
import time
from collections.abc import Iterator, Mapping
from contextlib import closing, contextmanager
from pathlib import Path

_LEASE_SECONDS = 180


class LostJobLease(RuntimeError):
    """Another worker may finish this job after its lease expires."""


class PipelineState:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS pipeline_jobs (
                    job_key TEXT PRIMARY KEY,
                    owner TEXT,
                    lease_until REAL,
                    reserved_microusd INTEGER NOT NULL DEFAULT 0,
                    had_ai_error INTEGER NOT NULL DEFAULT 0,
                    result TEXT
                );
                CREATE TABLE IF NOT EXISTS pipeline_queue (
                    listing_id TEXT NOT NULL,
                    option_id TEXT NOT NULL,
                    job_key TEXT NOT NULL REFERENCES pipeline_jobs(job_key),
                    PRIMARY KEY (listing_id, option_id)
                );
            """)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.path, timeout=10)) as connection, connection:
            yield connection

    def admit(self, listing_id: str, option_keys: Mapping[str, str]) -> None:
        """Switch the listing's active option set to this capture in one transaction."""
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM pipeline_queue WHERE listing_id = ?", (listing_id,))
            connection.executemany(
                "INSERT INTO pipeline_jobs (job_key) VALUES (?) ON CONFLICT DO NOTHING",
                ((key,) for key in option_keys.values()),
            )
            connection.executemany(
                "INSERT INTO pipeline_queue (listing_id, option_id, job_key) VALUES (?, ?, ?)",
                ((listing_id, option_id, key) for option_id, key in option_keys.items()),
            )

    def claim(self, job_key: str, owner: str) -> bool | None:
        now = time.time()
        with self._connect() as connection:
            row = connection.execute(
                """UPDATE pipeline_jobs
                   SET had_ai_error = MAX(had_ai_error, owner IS NOT NULL),
                       owner = ?, lease_until = ?
                   WHERE job_key = ? AND result IS NULL
                   AND (owner IS NULL OR lease_until <= ?)
                   RETURNING had_ai_error""",
                (owner, now + _LEASE_SECONDS, job_key, now),
            ).fetchone()
            return bool(row[0]) if row is not None else None

    def reserve(self, job_key: str, owner: str, amount: int, budget: int) -> bool:
        """Charge the upper-bound amount before attempting an external call."""
        now = time.time()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """SELECT reserved_microusd FROM pipeline_jobs
                   WHERE job_key = ? AND owner = ? AND lease_until > ?""",
                (job_key, owner, now),
            ).fetchone()
            if row is None:
                raise LostJobLease(job_key)
            if row[0] + amount > budget:
                return False
            connection.execute(
                """UPDATE pipeline_jobs
                   SET reserved_microusd = reserved_microusd + ?, lease_until = ?
                   WHERE job_key = ?""",
                (amount, now + _LEASE_SECONDS, job_key),
            )
            return True

    def record_error(self, job_key: str, owner: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE pipeline_jobs SET had_ai_error = 1
                   WHERE job_key = ? AND owner = ? AND lease_until > ?""",
                (job_key, owner, time.time()),
            )
            if cursor.rowcount != 1:
                raise LostJobLease(job_key)

    def finish(self, job_key: str, owner: str, result: dict) -> None:
        payload = json.dumps(result, ensure_ascii=False, allow_nan=False)
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE pipeline_jobs SET result = ?, owner = NULL, lease_until = NULL
                   WHERE job_key = ? AND owner = ? AND lease_until > ?""",
                (payload, job_key, owner, time.time()),
            )
            if cursor.rowcount != 1:
                raise LostJobLease(job_key)

    def results(self, listing_id: str | None = None) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT jobs.result FROM pipeline_queue AS queue
                   JOIN pipeline_jobs AS jobs ON jobs.job_key = queue.job_key
                   WHERE jobs.result IS NOT NULL AND (? IS NULL OR queue.listing_id = ?)""",
                (listing_id, listing_id),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]
