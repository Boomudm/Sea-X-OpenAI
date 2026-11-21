"""Replay the submission's saved evidence through the storage profile."""

import json
from pathlib import Path

from trongpok.paths import write_json
from trongpok.profiles import load_profile
from trongpok.rules import build_flags

_ROOT = Path(__file__).resolve().parents[1]


def _read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def test_storage_profile_replays_the_ten_submission_flags_byte_for_byte(tmp_path):
    profile = load_profile("storage")
    kb = _read_json(_ROOT / "data/kb/kb.json")
    listings = sorted((_ROOT / "data/listings").glob("*.json"))
    expected_reports = sorted((_ROOT / "out/flags").glob("*.json"))
    assert [path.name for path in listings] == [path.name for path in expected_reports]

    count = 0
    for listing_path, expected_path in zip(listings, expected_reports, strict=True):
        filename = listing_path.name
        claims = _read_json(_ROOT / "out/claims" / filename, [])
        if isinstance(claims, dict):
            claims = claims["options"]
        challenge_path = _ROOT / "out/challenges" / filename
        assert challenge_path.is_file(), filename
        flags = build_flags(
            _read_json(listing_path),
            kb,
            _read_json(_ROOT / "out/findings" / filename, []),
            claims,
            as_of="2026-11-21",
            challenges=_read_json(challenge_path),
            profile=profile,
        )
        count += len(flags)
        generated = tmp_path / filename
        write_json(generated, flags)
        assert generated.read_bytes() == expected_path.read_bytes(), filename

    assert count == 10
