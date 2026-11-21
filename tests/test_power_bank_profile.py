"""Exercise the profile-driven decision tree with labelled sample data."""

import json
from pathlib import Path

import pytest

from trongpok.rules import build_flags

FIXTURES = Path(__file__).parent / "fixtures" / "power_bank"


def load_sample(name):
    listing = json.loads((FIXTURES / "listings" / f"{name}.json").read_text(encoding="utf-8"))
    findings = json.loads((FIXTURES / "findings" / f"{name}.json").read_text(encoding="utf-8"))
    assert listing["title"].startswith("Sample data")
    return listing, findings


@pytest.fixture
def power_bank():
    from trongpok.profiles import load_profile

    profile = load_profile("power_bank", allow_draft=True)
    assert profile.approved_by == "pending human review"
    return profile


def test_two_independent_low_at_port_readings_trigger_q3(power_bank):
    listing, findings = load_sample("sample-power-bank-low")
    [flag] = build_flags(listing, findings=findings, profile=power_bank, allow_draft=True)

    assert (flag["colour"], flag["deciding"], flag["verdict"]) == ("RED", "Q3", "unsure")
    reviews = [item for item in flag["evidence"] if item["source"] == "review"]
    assert [item["ratio"] for item in reviews] == pytest.approx([0.2, 0.25])
    assert {item["quote"] for item in reviews} == {review["text"] for review in listing["reviews"]}
    assert [item["unit"] for item in reviews] == ["mAh", "Ah"]
    assert all(item["bytes"] is None for item in reviews)


def test_normal_65_percent_reading_with_ten_checked_reviews_is_green(power_bank):
    listing, findings = load_sample("sample-power-bank-normal")
    [flag] = build_flags(listing, findings=findings, profile=power_bank, allow_draft=True)

    assert (flag["colour"], flag["deciding"]) == ("GREEN", "Q5")
    assert flag["evidence"] == [{
        "source": "review_count",
        "matched_text_reviews": 10,
        "checked_text_reviews": 10,
    }]


def test_unmeasured_complaint_goes_to_a_person(power_bank):
    listing, findings = load_sample("sample-power-bank-complaint")
    [flag] = build_flags(listing, findings=findings, profile=power_bank, allow_draft=True)

    assert (flag["colour"], flag["deciding"], flag["verdict"]) == ("YELLOW", "Q4", "unsure")
    [review] = [item for item in flag["evidence"] if item["source"] == "review"]
    assert review["quote"] == listing["reviews"][0]["text"]
    assert review["quantity"] is None and review["ratio"] is None


@pytest.mark.parametrize(
    ("reading", "expected"),
    [(9_999, ("YELLOW", "Q4")), (10_000, ("GREEN", "Q5")), (11_800, ("GREEN", "Q5"))],
)
def test_tolerance_is_a_strict_lower_bound(power_bank, reading, expected):
    listing, findings = load_sample("sample-power-bank-normal")
    review = listing["reviews"][0]
    review["text"] = review["text"].replace("13,000", f"{reading:,}")
    findings[0].update(quantity=reading, quote=review["text"])

    [flag] = build_flags(listing, findings=findings, profile=power_bank, allow_draft=True)

    assert (flag["colour"], flag["deciding"]) == expected
