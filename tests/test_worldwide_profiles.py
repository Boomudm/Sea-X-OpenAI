import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from trongpok.profiles import CategoryProfile, load_profile


def test_categorical_profiles_have_no_required_numeric_promise():
    profile = CategoryProfile.model_validate({
        "category": "clothing",
        "attribute": "size",
        "measurement_mode": "categorical",
        "review_roles": ["other"],
        "normal_display_text": "Use the selected size and the buyer's account.",
        "mismatch_types": ["size_mismatch", "none"],
        "baseline_mismatch_rate": "0.1",
        "approved_by": "pending human review",
    })

    assert profile.promise_unit is None
    assert profile.units == {}
    assert profile.measured_roles == ()
    assert profile.baseline_mismatch_rate == Decimal("0.1")


@pytest.mark.parametrize("category", ["clothing", "cable_length", "aa_rechargeable_battery"])
def test_unapproved_samples_require_a_draft_opt_in(category):
    with pytest.raises(ValueError, match="--allow-draft"):
        load_profile(category)


def test_localized_spellings_cannot_mean_two_different_units():
    profile = load_profile().model_dump()
    profile["units"]["TB"]["aliases_by_language"] = {"en": ["GB"]}
    with pytest.raises(ValidationError, match="Duplicate unit token"):
        CategoryProfile.model_validate(profile)


def test_upper_bounds_require_unambiguous_measurement_conversions():
    profile = load_profile().model_dump()
    profile["maximum_ratio"] = "1.05"
    with pytest.raises(ValidationError, match="unambiguous measurement factors"):
        CategoryProfile.model_validate(profile)


def test_marketplace_fields_must_identify_distinct_inputs():
    profile = load_profile().model_dump()
    profile["marketplace_fields"].update(variation="variant", review_text="variant")
    with pytest.raises(ValidationError, match="Review field names must be distinct"):
        CategoryProfile.model_validate(profile)


@pytest.mark.parametrize(
    ("field", "conflicting_name"),
    [("variation", "text"), ("buyer", "variation_label"), ("now_price", "promise_value")],
)
def test_marketplace_aliases_cannot_claim_another_canonical_field(field, conflicting_name):
    profile = load_profile().model_dump()
    profile["marketplace_fields"][field] = conflicting_name
    with pytest.raises(ValidationError, match="reserved canonical field"):
        CategoryProfile.model_validate(profile)


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("clothing", ("RED", "Q3b")),
        ("cable_length", ("RED", "Q3")),
        ("aa_rechargeable_battery", ("GREEN", "Q5")),
    ],
)
def test_worldwide_samples_follow_the_code_rules(category, expected):
    from trongpok.capture import normalize_marketplace_fields
    from trongpok.rules import build_flags

    profile = load_profile(category, allow_draft=True)
    folder = Path(__file__).parent / "fixtures" / "worldwide" / category
    filename = f"sample-{category.replace('_', '-')}.json"
    listing = json.loads((folder / "listings" / filename).read_text(encoding="utf-8"))
    findings = json.loads((folder / "findings" / filename).read_text(encoding="utf-8"))

    assert profile.approved_by == "pending human review"
    assert listing["title"].startswith("Sample data")
    assert listing["url"].startswith("https://example.invalid/")

    listing = normalize_marketplace_fields(listing, profile)
    [flag] = build_flags(listing, findings=findings, profile=profile, allow_draft=True)

    assert (flag["colour"], flag["deciding"]) == expected
    assert flag["verdict"] == "unsure"
