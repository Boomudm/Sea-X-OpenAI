"""Active queue admissions are isolated by profile and capture revision."""

import sqlite3
from contextlib import closing, contextmanager

import pytest

from trongpok.pipeline_state import PipelineState

OLDER = "2026-11-21T08:00:00.000000+00:00"
NEWER = "2026-11-21T08:01:00.000000+00:00"
LATEST = "2026-11-21T08:02:00.000000+00:00"


def _complete(state, job, colour):
    assert state.claim(job, "worker") is False
    state.finish(job, "worker", {"colour": colour})


def test_scoped_queue_excludes_other_profiles_and_approval_states(tmp_path):
    state = PipelineState(tmp_path / "queue.sqlite3")
    for scope, job, colour in [
        ("storage-approved", "storage-job", "GREEN"),
        ("clothing-draft", "draft-job", "RED"),
        ("clothing-approved", "approved-job", "YELLOW"),
    ]:
        assert state.admit(scope, "listing", {"option": job})
        _complete(state, job, colour)

    assert state.results("storage-approved") == [{"colour": "GREEN"}]
    assert state.results("clothing-draft", "listing") == [{"colour": "RED"}]
    assert state.results("clothing-approved", "listing") == [{"colour": "YELLOW"}]
    assert state.results("clothing-draft", "other-listing") == []
    assert state.results("different-configuration") == []


def test_delayed_queue_message_cannot_reactivate_an_older_job(tmp_path):
    state = PipelineState(tmp_path / "queue.sqlite3")
    assert state.admit("profile", "listing", {"option": "old"}, revision=OLDER, from_message=True)
    _complete(state, "old", "GREEN")
    assert state.admit("profile", "listing", {"option": "new"}, revision=NEWER, from_message=True)
    _complete(state, "new", "RED")

    assert not state.admit("profile", "listing", {"option": "old"}, revision=OLDER, from_message=True)
    assert not state.admit("profile", "listing", {"option": "old"}, from_message=True)
    assert state.results("profile") == [{"colour": "RED"}]

    assert state.admit("profile", "listing", {"option": "old"}, revision=OLDER)
    assert state.results("profile") == [{"colour": "GREEN"}]
    assert not state.admit("profile", "listing", {"option": "new"}, revision=OLDER, from_message=True)
    assert state.results("profile") == [{"colour": "GREEN"}]
    assert not state.admit("profile", "listing", {"option": "new"}, revision=NEWER, from_message=True)
    assert state.results("profile") == [{"colour": "GREEN"}]
    assert state.admit("profile", "listing", {"option": "new"}, revision=LATEST, from_message=True)
    assert state.results("profile") == [{"colour": "RED"}]


@pytest.mark.parametrize("revision", [None, OLDER])
def test_duplicate_snapshot_cannot_restore_previous_results_at_same_revision(tmp_path, revision):
    path = tmp_path / "queue.sqlite3"
    state = PipelineState(path)
    assert state.admit("profile", "listing", {"option": "old"}, revision=revision, from_message=True)
    _complete(state, "old", "GREEN")
    assert state.admit("profile", "listing", {"option": "new"}, revision=revision, from_message=True)
    _complete(state, "new", "RED")

    restarted = PipelineState(path)
    assert not restarted.admit("profile", "listing", {"option": "old"}, revision=revision, from_message=True)
    assert restarted.results("profile") == [{"colour": "RED"}]
    assert restarted.admit("profile", "listing", {"option": "old"}, revision=NEWER, from_message=True)
    assert restarted.results("profile") == [{"colour": "GREEN"}]


def test_identical_admission_does_not_write_and_later_timestamp_reuses_job(tmp_path):
    path = tmp_path / "queue.sqlite3"
    state = PipelineState(path)
    second_worker = PipelineState(path)
    options = {"option": "job"}
    assert state.admit("profile", "listing", options, revision=OLDER)
    _complete(state, "job", "GREEN")
    with closing(sqlite3.connect(path)) as observer:
        before = observer.execute("PRAGMA data_version").fetchone()
        assert second_worker.admit("profile", "listing", options, revision=OLDER, from_message=True)
        assert observer.execute("PRAGMA data_version").fetchone() == before
        assert second_worker.admit("profile", "listing", options, revision=NEWER, from_message=True)
        assert observer.execute("PRAGMA data_version").fetchone() != before
    assert state.claim("job", "worker") is None
    assert state.results("profile") == [{"colour": "GREEN"}]
    assert not state.admit("profile", "listing", options, revision=OLDER, from_message=True)


def test_unchanged_capture_can_read_while_another_worker_holds_the_writer_slot(tmp_path, monkeypatch):
    path = tmp_path / "queue.sqlite3"
    state = PipelineState(path)
    assert state.admit("profile", "listing", {"a": "old-a", "b": "old-b"}, from_message=True)
    assert state.admit("profile", "listing", {"a": "new-a", "b": "new-b"}, from_message=True)
    connect = state._connect

    @contextmanager
    def no_writer_wait():
        with connect() as connection:
            connection.execute("PRAGMA busy_timeout = 0")
            yield connection

    monkeypatch.setattr(state, "_connect", no_writer_wait)
    with closing(sqlite3.connect(path)) as writer, writer:
        writer.execute("BEGIN IMMEDIATE")
        assert state.admit("profile", "listing", {"b": "new-b", "a": "new-a"}, from_message=True)
        assert not state.admit("profile", "listing", {"b": "old-b", "a": "old-a"}, from_message=True)


def test_admission_rechecks_identities_after_another_worker_changes_the_active_snapshot(tmp_path, monkeypatch):
    path = tmp_path / "queue.sqlite3"
    state = PipelineState(path)
    competitor = PipelineState(path)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
    plan = state._plan_admission
    plans = []

    def interleave(*args):
        result = plan(*args)
        plans.append(result)
        if len(plans) == 1:
            assert competitor.admit("profile", "listing", {"option": "old"}, from_message=True)
            assert competitor.admit("profile", "listing", {"option": "new"}, from_message=True)
        return result

    monkeypatch.setattr(state, "_plan_admission", interleave)
    assert not state.admit("profile", "listing", {"option": "old"}, from_message=True)
    assert len(plans) == 2 and plans[0] is not None and plans[1] is None
    assert state.runnable_keys("profile", "listing") == {"new"}
    assert state.claim("old", "late-worker") is None


def test_runnable_keys_exclude_completed_and_live_leases_but_recover_expired_ones(tmp_path, monkeypatch):
    now = [100.0]
    monkeypatch.setattr("trongpok.pipeline_state.time.time", lambda: now[0])
    state = PipelineState(tmp_path / "queue.sqlite3")
    options = {"done": "done", "busy": "busy", "new": "new"}
    assert state.admit("profile", "listing", options, from_message=True)
    assert state.admit("other-profile", "listing", {"other": "other"}, from_message=True)
    _complete(state, "done", "RED")
    assert state.claim("busy", "crashed-worker") is False
    assert state.runnable_keys("profile", "listing") == {"new"}

    now[0] += 181
    assert state.admit("profile", "listing", options, from_message=True)
    assert state.runnable_keys("profile", "listing") == {"new", "busy"}
    assert state.claim("busy", "second-worker") is True


def test_unscoped_pre_audit_queue_does_not_leak_into_scoped_results(tmp_path):
    path = tmp_path / "queue.sqlite3"
    state = PipelineState(path)
    state.admit("known-profile", "active-listing", {"option": "existing-job"})
    _complete(state, "existing-job", "RED")
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript("""
            CREATE TABLE pipeline_queue (listing_id TEXT, option_id TEXT, job_key TEXT);
            INSERT INTO pipeline_queue VALUES ('legacy-listing', 'option', 'existing-job');
        """)

    restarted = PipelineState(path)
    assert restarted.results("unknown-profile") == []
    assert restarted.results("known-profile", "legacy-listing") == []
    assert restarted.results("known-profile", "active-listing") == [{"colour": "RED"}]
    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("SELECT listing_id FROM pipeline_queue").fetchall() == [("legacy-listing",)]
