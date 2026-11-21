"""Regression check for the visibly labelled U4 demo scenarios."""

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from trongpok.rules import queue_key


SAMPLE_ROOT = Path(__file__).parent / "fixtures" / "u4"
BUNDLED_SAMPLES = SAMPLE_ROOT.parents[2] / "web/seller-guard/src/data/sampleCases.json"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_saved_demo_files_match_current_rules(tmp_path):
    subprocess.run([sys.executable, SAMPLE_ROOT / "build.py", tmp_path], check=True)
    for directory in ("flags", "listings"):
        names = sorted(path.name for path in (SAMPLE_ROOT / directory).glob("*.json"))
        assert names == sorted(path.name for path in (tmp_path / directory).glob("*.json"))
        for name in names:
            assert read_json(SAMPLE_ROOT / directory / name) == read_json(tmp_path / directory / name)


def test_bundled_sample_queue_matches_generator(tmp_path):
    output = tmp_path / "sampleCases.json"
    subprocess.run([sys.executable, SAMPLE_ROOT / "build.py", "--web-output", output], check=True)
    cases = read_json(output)
    assert cases == read_json(BUNDLED_SAMPLES)
    assert len({(case["listing_id"], case["option_id"]) for case in cases}) == len(cases) == 100
    assert Counter(case["priority"] for case in cases) == {"red": 32, "yellow": 28, "green": 25, "unknown": 15}
    assert {urlsplit(case["capture"]["listing_url"]).hostname for case in cases} == {"example.invalid"}
    assert {finding for case in cases for finding in case["findings"]} == {
        "unsupported", "capacity", "price", "reports", "clear",
    }


def test_demo_pairs_show_the_claimed_evidence():
    report = [
        flag for path in (SAMPLE_ROOT / "flags").glob("*.json")
        for flag in read_json(path)
    ]
    hero, low_price, sale, inflated, standard = sorted(report, key=queue_key)
    assert [(flag["listing_id"], flag["option_id"], flag["colour"], flag["deciding"])
            for flag in (hero, low_price, sale, inflated, standard)] == [
        ("sample-compact-64", "64-gb", "RED", "Q3"),
        ("sample-discount-1tb", "1-tb", "RED", "Q1"),
        ("sample-reference-1tb", "1-tb-blue", "YELLOW", "Q4"),
        ("sample-reference-1tb", "1-tb", "GREY", "grey"),
        ("sample-standard-64", "64-gb", "GREEN", "Q5"),
    ]
    hero_listing = read_json(SAMPLE_ROOT / "listings" / "sample-compact-64.json")
    quotes = [item for item in hero["evidence"] if item["source"] == "review"]
    assert len({item["buyer_masked"] for item in quotes}) == 4
    assert {item["quote"] for item in quotes} == {review["text"] for review in hero_listing["reviews"]}
    assert hero_listing["options"][0]["now_thb"] == 224
    assert "4.8 stars" in hero_listing["spec_text"]
    assert hero["path"][0] == "Q1: clear"

    market = next(item for item in low_price["evidence"] if item["source"] == "market_range")
    assert (market["was_thb"], market["now_thb"], market["low_thb"], market["high_thb"]) == (
        2990, 299, 1800, 2400,
    )
    assert len({source["url"] for source in market["sources"]}) == 3
    reference_listing = read_json(SAMPLE_ROOT / "listings" / "sample-reference-1tb.json")
    assert reference_listing["options"][0]["was_thb"] == 6000
    assert market["low_thb"] <= reference_listing["options"][0]["now_thb"] <= market["high_thb"]
    assert inflated["path"][0] == "Q1: clear"
    assert inflated["confidence"]["missing_evidence"]

    standard_listing = read_json(SAMPLE_ROOT / "listings" / "sample-standard-64.json")
    assert standard_listing["reviews"][0]["text"] == "Verified 58 GB on the drive."
    assert standard["evidence"] == [{
        "source": "review_count",
        "matched_text_reviews": 10,
        "checked_text_reviews": 10,
    }]
