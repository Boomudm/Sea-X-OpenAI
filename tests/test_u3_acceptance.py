"""The 12 rules-engine acceptance cases agreed in AGENTS.md §4.11."""

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from trongpok.decisions import load_decision, save_decision


FIXTURE_DIR = Path(__file__).parent / "fixtures"
CAPTURE_DATE = "2026-11-21"


@pytest.fixture
def sample():
    listing = json.loads((FIXTURE_DIR / "listing.json").read_text(encoding="utf-8"))
    findings = json.loads((FIXTURE_DIR / "findings.json").read_text(encoding="utf-8"))
    return listing, findings


@pytest.fixture
def measured_bytes():
    from trongpok.rules import measured_bytes as convert

    return convert


def _evaluate(listing, findings=(), kb_rows=(), claims=()):
    from trongpok.rules import build_flags

    return build_flags(
        listing, kb_rows=kb_rows, findings=findings, claims=claims, as_of=CAPTURE_DATE
    )


def _price_inputs(listing, was, now, *, capacity=1000):
    option = listing["options"][0]
    option.update(was_thb=was, now_thb=now)
    if capacity == 1000:
        option.update(capacity_text="1 TB", variation_label="1 TB", promise_gb=1000)
    price_range = {
        "capacity_gb": capacity,
        "low_thb_per_gb": 1800 / capacity,
        "high_thb_per_gb": 2400 / capacity,
        "offers_used": 3,
        "date": CAPTURE_DATE,
    }
    row = {
        "brand": "Fixture Brand",
        "aliases": [],
        "product_line": "Fixture Line",
        "type": "USB flash drive",
        "mall_capacities_gb": [capacity],
        "brand_page": None,
        "market_range": [price_range],
        "mall_sources": [
            {
                "url": f"https://example.invalid/fixture/mall-{index}",
                "date": CAPTURE_DATE,
                "capacity_gb": capacity,
                "now_thb": price,
            }
            for index, price in enumerate([1800, 2100, 2400], start=1)
        ],
        "expected_display": "",
        "approved_by": "Fixture approver",
    }
    claim = {
        "option_id": option["option_id"],
        "brand": row["brand"],
        "product_line": row["product_line"],
        "type": row["type"],
        "promise_gb": capacity,
        "capacity_unclear": False,
    }
    return [row], [claim]


def _single_review(sample, text, quantity, unit, *, role="delivered_capacity"):
    listing, findings = sample
    review = listing["reviews"][0]
    review["text"] = text
    listing["reviews"] = [review]
    finding = findings[0]
    finding.update(quote=text, quantity=quantity, unit=unit, role=role)
    return listing, [finding]


def test_01_four_independent_buyer_measurements_are_red_and_show_every_quote(sample):
    listing, findings = sample
    [flag] = _evaluate(listing, findings)
    assert (flag["colour"], flag["deciding"], flag["verdict"]) == ("RED", "Q3", "unsure")
    assert {item["quote"] for item in flag["evidence"] if "quote" in item} == {
        review["text"] for review in listing["reviews"]
    }


def test_02_normal_display_with_ten_matched_reviews_is_green(sample, measured_bytes):
    listing, findings = _single_review(sample, "My computer shows 58", 58, "none")
    findings[0]["complaint"] = "none"
    first_review = listing["reviews"][0]
    for index in range(2, 11):
        review = dict(
            first_review,
            review_id=f"clean-{index}",
            buyer_masked=f"clean-{index}***",
            text=f"Review {index}: drive works as expected",
        )
        listing["reviews"].append(review)
        findings.append(dict(findings[0], review_id=review["review_id"], quote=review["text"],
                             quantity=None, role="other"))

    assert measured_bytes(58, "none", "64 GB") == Decimal(58) * 2**30
    [flag] = _evaluate(listing, findings)
    assert (flag["colour"], flag["deciding"]) == ("GREEN", "Q5")
    assert flag["confidence"]["score"] == flag["confidence"]["base"]

    from trongpok.rules import build_flags

    challenge = {"points": -5, "reason": "A clean review is vague", "source": "clean-2"}
    [challenged] = build_flags(listing, findings=findings, as_of=CAPTURE_DATE,
                               challenges={flag["option_id"]: [challenge]})
    assert challenged["colour"] == "GREEN"
    assert challenged["confidence"]["score"] == flag["confidence"]["base"] - 5
    challenge["source"] = "not-a-review"
    [rejected] = build_flags(listing, findings=findings, as_of=CAPTURE_DATE,
                             challenges={flag["option_id"]: [challenge]})
    assert rejected["confidence"]["score"] == flag["confidence"]["base"]

    off_topic = [
        {"kind": "gb_vs_gib", "points": -5, "reason": "Unit unclear", "source": "clean-2"},
        {"kind": "flash_sale", "points": -5, "reason": "Bought on a sale", "source": "clean-3"},
        {"kind": "gb_vs_gib", "points": 5, "reason": "Normal display", "source": "clean-4"},
    ]
    [filtered] = build_flags(listing, findings=findings, as_of=CAPTURE_DATE,
                             challenges={flag["option_id"]: off_topic})
    assert filtered["confidence"]["score"] == flag["confidence"]["base"] + 5

    [unchecked_flag] = _evaluate(listing, [])
    assert (unchecked_flag["colour"], unchecked_flag["deciding"]) == ("GREY", "grey")
    assert "Matched text reviews are still unchecked" in unchecked_flag["reasons"]


@pytest.mark.parametrize(
    ("was", "now", "expected"),
    [
        (2990, 299, ("RED", "Q1")),
        (6000, 2000, ("GREY", "grey")),
        (2000, 1500, ("YELLOW", "Q4")),
        (2000, 299, ("RED", "Q1")),
        (3500, 3000, ("GREY", "grey")),
    ],
)
def test_03_two_price_cases(sample, was, now, expected):
    listing, _ = sample
    kb_rows, claims = _price_inputs(listing, was, now)
    [flag] = _evaluate(listing, kb_rows=kb_rows, claims=claims)
    assert (flag["colour"], flag["deciding"]) == expected


def test_04_duplicate_review_text_counts_once_across_buyers(sample):
    listing, findings = sample
    listing["reviews"] = listing["reviews"][:2]
    first_review, second_review = listing["reviews"]
    second_review["text"] = first_review["text"]
    findings[1].update(quote=findings[0]["quote"], quantity=findings[0]["quantity"])

    [flag] = _evaluate(listing, findings[:2])
    assert (flag["colour"], flag["deciding"]) == ("YELLOW", "Q4")
    assert len([item for item in flag["evidence"] if item.get("quote")]) == 1


def test_05_reviews_are_assigned_using_exact_variation(sample):
    listing, findings = sample
    listing["reviews"] = listing["reviews"][:2]
    listing["options"].append(
        dict(
            listing["options"][0],
            option_id="fixture-128",
            variation_label="128 GB",
            capacity_text="128 GB",
            promise_gb=128,
        )
    )
    other_review = listing["reviews"][1]
    other_review["variation_label"] = "128 GB"
    # A reader may send the wrong option ID; the captured Variation is authoritative.
    first, second = findings[:2]
    assert second["option_id"] == listing["options"][0]["option_id"]

    flags = {flag["option_id"]: flag for flag in _evaluate(listing, [first, second])}
    first_flag = flags[first["option_id"]]
    assert first_flag["colour"] == "YELLOW"
    assert other_review["text"] not in {item.get("quote") for item in first_flag["evidence"]}


def test_06_unknown_brand_skips_market_and_brand_rules(sample):
    listing, _ = sample
    kb_rows, claims = _price_inputs(listing, 2990, 299)
    claims[0]["brand"] = "Unlisted Fixture Brand"
    kb_rows[0]["brand_page"] = {
        "url": "https://example.invalid/fixture/brand",
        "date": CAPTURE_DATE,
        "capacities_gb": [64],
    }
    [flag] = _evaluate(listing, kb_rows=kb_rows, claims=claims)
    assert (flag["colour"], flag["deciding"]) == ("GREY", "grey")
    assert not any(
        item.get("source") in {"market_range", "brand_page"} for item in flag["evidence"]
    )


def test_07_files_corrupt_after_30_gb_is_a_measured_shortfall(sample):
    listing, findings = _single_review(
        sample, "Files corrupt after 30 GB", 30, "GB", role="fails_after"
    )
    [flag] = _evaluate(listing, findings)
    assert (flag["colour"], flag["deciding"]) == ("YELLOW", "Q4")
    [measurement] = [item for item in flag["evidence"] if item.get("source") == "review"]
    assert measurement["quote"] == "Files corrupt after 30 GB"
    assert measurement["ratio"] == pytest.approx(30 * 2**30 / 64_000_000_000)


def test_08_normal_2_tb_binary_display_is_not_a_shortfall(sample, measured_bytes):
    listing, findings = _single_review(sample, "Size shows 1.81 TB", 1.81, "TB")
    listing["options"][0].update(capacity_text="2 TB", variation_label="2 TB", promise_gb=2000)
    listing["reviews"][0]["variation_label"] = "2 TB"
    findings[0]["complaint"] = "none"

    assert measured_bytes(Decimal("1.81"), "TB", "2 TB") == Decimal("1.81") * 2**40
    [flag] = _evaluate(listing, findings)
    assert (flag["colour"], flag["deciding"]) == ("GREY", "grey")


def test_09_exactly_85_percent_is_not_a_shortfall(sample, measured_bytes):
    quantity = Decimal(64_000_000_000) * Decimal("0.85") / 2**30
    listing, findings = _single_review(
        sample, f"Capacity is {quantity} GiB", quantity, "GiB"
    )
    assert measured_bytes(quantity, "GiB", "64 GB") == Decimal(54_400_000_000)
    [flag] = _evaluate(listing, findings)
    assert (flag["colour"], flag["deciding"]) == ("GREY", "grey")


def test_10_review_decision_survives_a_new_process(tmp_path):
    database = tmp_path / "decisions.sqlite"
    at = "2026-11-21T03:00:00+00:00"
    reason = "Compared the captured review text with the option"
    assert load_decision(database, "listing-1", "option-1") is None

    saved = save_decision(database, "listing-1", "option-1", "accepted", reason, at=at)

    expected = {"decision": "accepted", "reason": reason, "at": at}
    assert saved == expected
    restarted = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, sys; from trongpok.decisions import load_decision; "
            "print(json.dumps(load_decision(sys.argv[1], 'listing-1', 'option-1')))",
            str(database),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(restarted.stdout) == expected
    assert load_decision(database, "listing-1", "option-2") is None


@pytest.mark.parametrize(
    ("now", "expected"),
    [(1500, ("YELLOW", "Q4")), (1200, ("RED", "Q1"))],
)
def test_11_crossed_out_price_outside_range_requires_below_75_percent(sample, now, expected):
    listing, _ = sample
    kb_rows, claims = _price_inputs(listing, 2990, now)
    [flag] = _evaluate(listing, kb_rows=kb_rows, claims=claims)
    assert (flag["colour"], flag["deciding"]) == expected


def test_12_buyer_evidence_decides_red_when_price_also_fires(sample):
    listing, findings = sample
    kb_rows, claims = _price_inputs(listing, 2990, 299, capacity=64)
    [flag] = _evaluate(listing, findings, kb_rows, claims)

    assert (flag["colour"], flag["deciding"]) == ("RED", "Q3")
    assert "Price is far below the market range" in flag["reasons"]
    assert {"points": 15, "reason": "2 or more separate buyers"} in flag["confidence"][
        "adjustments"
    ]
