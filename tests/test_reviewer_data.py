import json
from pathlib import Path

from trongpok.decisions import save_decision
from trongpok.reviewer_data import (
    DECISION_READ_ERROR,
    load_listings,
    load_queue,
    resolve_thumbnail,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _flag(listing_id, option_id, colour, score):
    flag = json.loads((FIXTURES / "flags.json").read_text())[0]
    flag.update(listing_id=listing_id, option_id=option_id, colour=colour)
    flag["confidence"]["score"] = score
    return flag


def _write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_queue_sorts_across_files_deduplicates_and_keeps_valid_rows(tmp_path):
    red = _flag("listing-a", "64", "RED", 82)
    rows = [
        _flag("listing-a", "2000", "GREEN", 96),
        _flag("listing-a", "128", "GREEN", 21),
        _flag("listing-a", "32", "GREY", 33),
        _flag("listing-b", "64", "RED", 82),
        _flag("listing-b", "128", "RED", 69),
        {"listing_id": "incomplete"},
    ]
    _write(tmp_path / "a-backup.json", [red | {"reasons": ["Old evidence"]}])
    _write(tmp_path / "listing-a.json", [red, _flag("listing-a", "256", "YELLOW", 97)])
    _write(tmp_path / "listing-b.json", rows)
    (tmp_path / "malformed.json").write_text("{")

    flags, issues = load_queue(tmp_path, tmp_path / "not-created.sqlite3")

    assert [(flag["listing_id"], flag["option_id"]) for flag in flags] == [
        ("listing-a", "64"),
        ("listing-b", "64"),
        ("listing-b", "128"),
        ("listing-a", "256"),
        ("listing-a", "32"),
        ("listing-a", "128"),
        ("listing-a", "2000"),
    ]
    assert flags[0] == red
    assert len(issues) == 3
    assert not (tmp_path / "not-created.sqlite3").exists()


def test_sqlite_is_authoritative_per_option_after_reopening_queue(tmp_path):
    database = tmp_path / "review.sqlite3"
    stored = {"decision": "accepted", "reason": "Stale snapshot", "at": "2026-11-20"}
    flags = [_flag("listing", size, "RED", 80) for size in ("128", "64")]
    flags[0].update(reviewer_decision=stored, verdict="mismatch")
    _write(tmp_path / "listing.json", flags)

    reopened, _ = load_queue(tmp_path, database)
    assert reopened[0]["reviewer_decision"] is None
    assert reopened[0]["verdict"] == "unsure"

    decision = save_decision(database, "listing", "64", "dismissed", "Verified the 64 GB option")
    reopened, issues = load_queue(tmp_path, database)
    assert not issues
    assert reopened[0]["reviewer_decision"] is None
    assert reopened[1]["reviewer_decision"] == decision
    assert reopened[1]["verdict"] == "no_mismatch"

    accepted = save_decision(database, "listing", "128", "accepted", "Verified the 128 GB option")
    reopened, issues = load_queue(tmp_path, database)
    assert not issues
    assert reopened[0]["reviewer_decision"] == accepted
    assert reopened[0]["verdict"] == "mismatch"
    assert reopened[1]["reviewer_decision"] == decision


def test_unreadable_database_keeps_evidence_visible_with_warning(tmp_path):
    _write(tmp_path / "listing.json", [_flag("listing", "1", "RED", 75)])
    database = tmp_path / "bad.sqlite3"
    database.write_text("not a database")

    flags, issues = load_queue(tmp_path, database)

    assert len(flags) == 1
    assert issues == [DECISION_READ_ERROR]


def test_rejects_reports_whose_confidence_or_evidence_cannot_be_rendered(tmp_path):
    report = _flag("listing", "1", "RED", 75)
    invalid = [
        _flag("listing", "2", "RED", 101),
        _flag("listing", "3", "RED", 50) | {"reasons": []},
        _flag("listing", "4", "RED", 60) | {"evidence": [{"source": "market_range", "sources": None}]},
    ]
    _write(tmp_path / "listing.json", [report, *invalid])

    flags, issues = load_queue(tmp_path, tmp_path / "review.sqlite3")

    assert flags == [report]
    assert issues == ["Could not load 3 option record(s) in listing.json."]


def test_capture_is_optional_and_partial_files_do_not_hide_valid_details(tmp_path):
    capture = json.loads((FIXTURES / "listing.json").read_text())
    capture["displayed_rating"] = 4.8
    _write(tmp_path / "fixture-listing.json", capture)
    _write(tmp_path / "bad.json", {"listing_id": "bad"})

    listings, issues = load_listings(tmp_path)

    assert listings == {"fixture-listing": capture}
    assert len(issues) == 1
    assert load_listings(tmp_path / "missing") == ({}, [])


def test_thumbnail_resolves_only_inside_configured_capture_root(tmp_path):
    captures = tmp_path / "separate-checkout" / "data" / "listings"
    folder = captures / "listing" / "images"
    folder.mkdir(parents=True)
    photo = folder / "photo.jpg"
    photo.touch()
    outside = tmp_path / "private.jpg"
    outside.touch()
    (folder / "linked.jpg").symlink_to(outside)
    (folder / "vector.svg").touch()

    assert resolve_thumbnail("data/listings/listing/images/photo.jpg", captures, tmp_path) == photo.resolve()
    assert resolve_thumbnail("listing/images/photo.jpg", captures, tmp_path) == photo.resolve()
    assert resolve_thumbnail(str(outside), captures, tmp_path) is None
    assert resolve_thumbnail("listing/images/linked.jpg", captures, tmp_path) is None
    assert resolve_thumbnail("listing/images/vector.svg", captures, tmp_path) is None
    assert resolve_thumbnail("https://example.invalid/photo.jpg", captures, tmp_path) is None
