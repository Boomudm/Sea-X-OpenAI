"""Exercise categorical and numeric decisions through the option rule engine."""

from decimal import Decimal

import pytest

from trongpok.profiles import CategoryProfile
from trongpok.rules import build_flags

MISMATCH_REPORTS = {
    "wrong_model": ("I ordered the Mini but received the Max.", "A Max arrived instead of the Mini."),
    "wrong_colour": ("The blue option arrived in red.", "My blue order contained a red item."),
    "missing_parts": ("The mounting bracket was missing.", "There was no bracket in my box."),
    "not_genuine_claim": (
        "The manufacturer told me the label was not issued by them.",
        "The brand service centre told me this unit was not their product.",
    ),
    "size_mismatch": ("The medium order contained a small.", "I ordered medium and received small."),
}


def option_flag(profile_fields, reports, *, promise=None):
    """Build one sample option from (masked buyer, text, findings) records."""
    profile = CategoryProfile.model_validate({
        "category": "sample",
        "attribute": "size",
        "promise_unit": None,
        "units": {},
        "tolerance": Decimal("0.95"),
        "review_roles": ["other"],
        "measured_roles": [],
        "normal_display_text": "Use the advertised option.",
        "mismatch_types": ["none", *MISMATCH_REPORTS],
        "approved_by": "Test reviewer",
        "measurement_mode": "categorical",
        "baseline_mismatch_rate": Decimal("0.2"),
        **profile_fields,
    })
    options = [{"option_id": "opt", "variation_label": "Blue large", **(promise or {})}]
    reviews = []
    findings = []
    for index, (buyer, text, observations) in enumerate(reports):
        review_id = f"review-{index}"
        reviews.append({
            "review_id": review_id,
            "variation_label": "Blue large",
            "buyer_masked": buyer,
            "text": text,
        })
        findings.extend({
            "review_id": review_id,
            "option_id": "opt",
            "role": "other",
            "read_status": "ok",
            "complaint": complaint,
            "quote": text,
            **overrides,
        } for complaint, overrides in observations)
    [flag] = build_flags(
        {"listing_id": "sample-rules", "options": options, "reviews": reviews},
        findings=findings,
        profile=profile,
    )
    return flag


@pytest.mark.parametrize("kind", MISMATCH_REPORTS)
def test_independent_quoted_reports_for_same_mismatch_above_baseline_are_red(kind):
    first, second = MISMATCH_REPORTS[kind]
    flag = option_flag({}, [("a***", first, [(kind, {})]), ("b***", second, [(kind, {})])])

    assert (flag["colour"], flag["deciding"], flag["verdict"]) == ("RED", "Q3b", "unsure")
    assert "Q3b: decided" in flag["path"]
    assert [item["mismatch_type"] for item in flag["evidence"] if item["source"] == "review"] == [
        kind, kind,
    ]


@pytest.mark.parametrize(("reports", "expected"), [
    (
        [("a***", MISMATCH_REPORTS["wrong_model"][0], [("wrong_model", {})])],
        ("YELLOW", "Q4"),
    ),
    (
        [
            ("a***", MISMATCH_REPORTS["wrong_model"][0], [("wrong_model", {})]),
            ("a***", MISMATCH_REPORTS["wrong_model"][1], [("wrong_model", {})]),
            ("b***", MISMATCH_REPORTS["wrong_model"][0], [("wrong_model", {})]),
        ],
        ("YELLOW", "Q4"),
    ),
    (
        [
            ("a***", MISMATCH_REPORTS["wrong_model"][0], [("wrong_model", {})]),
            ("b***", MISMATCH_REPORTS["wrong_colour"][1], [("wrong_colour", {})]),
        ],
        ("YELLOW", "Q4"),
    ),
    (
        [
            ("a***", MISMATCH_REPORTS["wrong_model"][0], [("wrong_model", {})]),
            ("b***", "A clean review", [("wrong_model", {"quote": "fabricated quote"})]),
        ],
        ("YELLOW", "Q4"),
    ),
    (
        [
            ("a***", MISMATCH_REPORTS["wrong_model"][0], [("wrong_model", {})]),
            ("b***", MISMATCH_REPORTS["wrong_model"][1], [("wrong_model", {"read_status": "cannot_read"})]),
        ],
        ("YELLOW", "Q4"),
    ),
    (
        [
            ("a***", MISMATCH_REPORTS["wrong_model"][0], [("wrong_model", {})]),
            ("b***", MISMATCH_REPORTS["wrong_model"][1], [("wrong_model", {"option_id": "different-option"})]),
        ],
        ("YELLOW", "Q4"),
    ),
])
def test_category_reports_need_independence_same_type_and_exact_successful_quotes(reports, expected):
    flag = option_flag({}, reports)

    assert (flag["colour"], flag["deciding"]) == expected


def test_mismatch_rate_equal_to_baseline_is_yellow_even_with_many_clean_reviews():
    flag = option_flag({}, [
        ("a***", MISMATCH_REPORTS["missing_parts"][0], [("missing_parts", {})]),
        ("b***", MISMATCH_REPORTS["missing_parts"][1], [("missing_parts", {})]),
        *[(f"{index}***", f"Clean review {index}", [("none", {})]) for index in range(8)],
    ])

    assert (flag["colour"], flag["deciding"]) == ("YELLOW", "Q4")
    assert sum(item.get("mismatch_type") == "missing_parts" for item in flag["evidence"]) == 2


def test_each_type_has_its_own_rate_and_a_review_can_report_two_types():
    flag = option_flag({}, [
        ("a***", "Wrong colour and parts missing.", [("wrong_colour", {}), ("missing_parts", {})]),
        ("b***", "Was sent a different colour.", [("wrong_colour", {})]),
    ])

    assert (flag["colour"], flag["deciding"]) == ("RED", "Q3b")
    assert "Q4: triggered" in flag["path"]
    assert [item["mismatch_type"] for item in flag["evidence"] if item["source"] == "review"] == [
        "wrong_colour", "wrong_colour", "missing_parts",
    ]


@pytest.mark.parametrize("invalid_finding", [
    {"read_status": "cannot_read"},
    {"quote": "fabricated quote"},
    {"mismatch_type": "size_mismatch", "quote": ""},
])
def test_invalid_finding_cannot_be_covered_by_another_finding_of_the_same_review(invalid_finding):
    reports = [(f"{index}***", f"Clean review {index}", [("none", {})]) for index in range(9)]
    flag = option_flag({}, [
        *reports,
        ("a***", "Unreadable review", [("none", {}), ("none", invalid_finding)]),
    ])

    assert (flag["colour"], flag["deciding"]) == ("GREY", "grey")
    assert "Matched text reviews are still unchecked" in flag["reasons"]


@pytest.mark.parametrize(
    ("quantities", "expected"),
    [
        ((940, 1060), ("RED", "Q3")),
        ((950, 1050), ("GREY", "grey")),
        ((1060, 1050), ("YELLOW", "Q4")),
    ],
)
def test_two_sided_tolerance_is_inclusive_and_localized_units_are_supported(quantities, expected):
    reports = [
        (f"{index}***", f"Measured {quantity} milímetros", [
            ("none", {"role": "test_result", "quantity": quantity, "unit": "mm"}),
        ]) for index, quantity in enumerate(quantities)
    ]
    flag = option_flag({
        "measurement_mode": "numeric",
        "attribute": "length",
        "promise_unit": "mm",
        "maximum_ratio": Decimal("1.05"),
        "review_roles": ["test_result", "other"],
        "measured_roles": ["test_result"],
        "languages": ["es"],
        "units": {
            "mm": {
                "measurement_factors": [1],
                "promise_factor": 1,
                "aliases_by_language": {"es": ["milímetros"]},
            },
        },
    }, reports, promise={"promise_value": 1000, "measurement_text": "1000 mm"})

    assert (flag["colour"], flag["deciding"]) == expected
