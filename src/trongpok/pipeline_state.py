"""SQLite job leases, budget reservations and the pipeline's review queue."""

import hashlib
import json
import sqlite3
import time
from collections.abc import Iterator, Mapping
from contextlib import closing, contextmanager
from dataclasses import dataclass
from pathlib import Path

from .errors import ReaderInputError
from .paths import within_directory

_LEASE_SECONDS = 180


class LostJobLease(RuntimeError):
    """Another worker may finish this job after its lease expires."""


@dataclass(frozen=True)
class _Admission:
    advance_revision: bool
    new_snapshot: bool
    changed: dict[str, str]
    removed: set[str]

    @property
    def needs_write(self) -> bool:
        return self.advance_revision or self.new_snapshot or bool(self.changed or self.removed)


def workspace_database_path(path: Path, workspace: Path) -> Path:
    """Recheck the canonical database path before reopening SQLite."""
    if not path.is_relative_to(workspace) or within_directory(path, workspace) != path:
        raise ReaderInputError("The selected workspace database path has changed")
    return path


class PipelineState:
    def __init__(self, path: str | Path, *, workspace_root: Path | None = None) -> None:
        self._path = Path(path).resolve()
        self._workspace_root = workspace_root
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
                CREATE TABLE IF NOT EXISTS pipeline_active_options (
                    profile_scope TEXT NOT NULL,
                    listing_id TEXT NOT NULL,
                    option_id TEXT NOT NULL,
                    job_key TEXT NOT NULL REFERENCES pipeline_jobs(job_key),
                    PRIMARY KEY (profile_scope, listing_id, option_id)
                );
                CREATE INDEX IF NOT EXISTS pipeline_active_job ON pipeline_active_options (job_key);
                CREATE TABLE IF NOT EXISTS pipeline_capture_revisions (
                    profile_scope TEXT NOT NULL,
                    listing_id TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    PRIMARY KEY (profile_scope, listing_id)
                );
                CREATE TABLE IF NOT EXISTS pipeline_capture_snapshots (
                    profile_scope TEXT NOT NULL,
                    listing_id TEXT NOT NULL,
                    snapshot_key TEXT NOT NULL,
                    PRIMARY KEY (profile_scope, listing_id, snapshot_key)
                );
            """)

    @property
    def path(self) -> Path:
        if self._workspace_root is None:
            return self._path
        return workspace_database_path(self._path, self._workspace_root)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.path, timeout=10)) as connection, connection:
            yield connection

    def admit(
        self,
        scope: str,
        listing_id: str,
        option_keys: Mapping[str, str],
        *,
        revision: str | None = None,
        from_message: bool = False,
    ) -> bool:
        """Admit the capture unless a broker delivery is older or has been superseded."""
        keys = (scope, listing_id)
        snapshot = hashlib.sha256(json.dumps((revision, dict(option_keys)), sort_keys=True).encode()).hexdigest()
        with self._connect() as connection:
            # Most watch scans see an unchanged capture. Read one consistent
            # snapshot without reserving the database's single writer slot.
            connection.execute("BEGIN")
            admission = self._plan_admission(connection, keys, option_keys, snapshot, revision, from_message)
            connection.rollback()
            if admission is None or not admission.needs_write:
                return admission is not None

            connection.execute("BEGIN IMMEDIATE")
            admission = self._plan_admission(connection, keys, option_keys, snapshot, revision, from_message)
            if admission is None:
                return False
            if not admission.needs_write:
                return True
            if admission.advance_revision:
                connection.execute(
                    """INSERT INTO pipeline_capture_revisions (profile_scope, listing_id, captured_at)
                       VALUES (?, ?, ?)
                       ON CONFLICT(profile_scope, listing_id) DO UPDATE SET captured_at = excluded.captured_at""",
                    (*keys, revision),
                )
            if admission.new_snapshot:
                connection.execute(
                    """INSERT INTO pipeline_capture_snapshots (profile_scope, listing_id, snapshot_key)
                       VALUES (?, ?, ?)""",
                    (*keys, snapshot),
                )
            connection.executemany(
                "INSERT INTO pipeline_jobs (job_key) VALUES (?) ON CONFLICT DO NOTHING",
                ((key,) for key in admission.changed.values()),
            )
            connection.executemany(
                """INSERT INTO pipeline_active_options (profile_scope, listing_id, option_id, job_key)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(profile_scope, listing_id, option_id) DO UPDATE SET job_key = excluded.job_key""",
                ((*keys, option, key) for option, key in admission.changed.items()),
            )
            connection.executemany(
                """DELETE FROM pipeline_active_options
                   WHERE profile_scope = ? AND listing_id = ? AND option_id = ?""",
                ((*keys, option) for option in admission.removed),
            )
            return True

    @staticmethod
    def _plan_admission(
        connection: sqlite3.Connection,
        keys: tuple[str, str],
        option_keys: Mapping[str, str],
        snapshot: str,
        revision: str | None,
        from_message: bool,
    ) -> _Admission | None:
        saved = connection.execute(
            """SELECT captured_at FROM pipeline_capture_revisions
               WHERE profile_scope = ? AND listing_id = ?""",
            keys,
        ).fetchone()
        newest = saved[0] if saved is not None else None
        if from_message and newest is not None and (revision is None or revision < newest):
            return None

        seen = connection.execute(
            """SELECT 1 FROM pipeline_capture_snapshots
               WHERE profile_scope = ? AND listing_id = ? AND snapshot_key = ?""",
            (*keys, snapshot),
        ).fetchone() is not None
        active = dict(connection.execute(
            """SELECT option_id, job_key FROM pipeline_active_options
               WHERE profile_scope = ? AND listing_id = ?""",
            keys,
        ))
        if from_message and seen and active != option_keys:
            return None
        return _Admission(
            advance_revision=revision is not None and (newest is None or revision > newest),
            new_snapshot=not seen,
            changed={option: key for option, key in option_keys.items() if active.get(option) != key},
            removed=active.keys() - option_keys.keys(),
        )

    def runnable_keys(self, scope: str, listing_id: str) -> set[str]:
        """Find active jobs eligible for an initial claim or expired-lease recovery."""
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT jobs.job_key FROM pipeline_active_options AS queue
                   JOIN pipeline_jobs AS jobs ON jobs.job_key = queue.job_key
                   WHERE queue.profile_scope = ? AND queue.listing_id = ? AND jobs.result IS NULL
                   AND (jobs.owner IS NULL OR jobs.lease_until <= ?)""",
                (scope, listing_id, time.time()),
            ).fetchall()
        return {row[0] for row in rows}

    def claim(self, job_key: str, owner: str) -> bool | None:
        now = time.time()
        with self._connect() as connection:
            row = connection.execute(
                """UPDATE pipeline_jobs
                   SET had_ai_error = MAX(had_ai_error, owner IS NOT NULL),
                       owner = ?, lease_until = ?
                   WHERE job_key = ? AND result IS NULL
                   AND (owner IS NULL OR lease_until <= ?)
                   AND EXISTS (SELECT 1 FROM pipeline_active_options WHERE job_key = pipeline_jobs.job_key)
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

    def results(self, scope: str, listing_id: str | None = None) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT jobs.result FROM pipeline_active_options AS queue
                   JOIN pipeline_jobs AS jobs ON jobs.job_key = queue.job_key
                   WHERE queue.profile_scope = ? AND jobs.result IS NOT NULL
                   AND (? IS NULL OR queue.listing_id = ?)""",
                (scope, listing_id, listing_id),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]
