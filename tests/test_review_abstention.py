"""A short quote cannot turn contradictory buyer text into a measurement."""

import json
from pathlib import Path

import pytest

from trongpok.models import Finding, Listing, ReviewDraft
from trongpok.rules import build_flags
from trongpok.validation import normalize_review_draft


FIXTURE = Path(__file__).parent / "fixtures" / "listing.json"


def listing_with_reviews(*texts):
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw["reviews"] = [
        {**review, "text": text}
        for review, text in zip(raw["reviews"][:len(texts)], texts, strict=True)
    ]
    return Listing.model_validate(raw)


def draft_for(listing, index, quote, quantity):
    return ReviewDraft(
        review_id=listing.reviews[index].review_id,
        option_id=listing.options[0].option_id,
        complaint="capacity_short",
        quantity=quantity,
        unit="GB",
        role="delivered capacity",
        quote=quote,
    )


def build_single_flag(listing, findings):
    [flag] = build_flags(
        listing.model_dump(mode="json"),
        findings=[finding.model_dump(mode="json") for finding in findings],
        as_of="2026-11-21",
    )
    return flag


def assert_unmeasured_flag(flag, quotes):
    assert (flag["colour"], flag["deciding"]) == ("YELLOW", "Q4")
    evidence = [item for item in flag["evidence"] if item["source"] == "review"]
    assert [item["quote"] for item in evidence] == quotes
    assert all(
        item["quantity"] is item["bytes"] is item["ratio"] is None
        for item in evidence
    )


@pytest.mark.parametrize(
    ("text", "quote"),
    [
        pytest.param(
            "Measured 29 GB. Measured 58 GB on a second run.",
            "Measured 29 GB",
            id="short-quote-hides-second-reading",
        ),
        pytest.param(
            "Measured 29 GB or 58 GiB.",
            "Measured 29 GB or 58 GiB.",
            id="full-quote-with-gb-and-gib",
        ),
        pytest.param(
            "Measured 29 or 58 GB.",
            "Measured 29 or 58 GB.",
            id="alternative-with-one-written-unit",
        ),
        pytest.param(
            "Measured 29, then measured 58.",
            "Measured 29",
            id="two-bare-measurements-inherit-option-unit",
        ),
        pytest.param(
            "วัดได้แค่ ๒๙ GB แต่วัดอีกครั้งได้ ๕๘ GiB",
            "วัดได้แค่ ๒๙ GB",
            id="thai-digits",
        ),
    ],
)
def test_conflicting_capacity_becomes_unmeasured_complaint(text, quote):
    listing = listing_with_reviews(text)
    [review] = listing.reviews
    [option] = listing.options

    finding = normalize_review_draft(review, option, draft_for(listing, 0, quote, 29))

    assert finding.complaint == "capacity_no_number"
    assert finding.quote == quote
    assert finding.unit == "none"
    assert finding.quantity is finding.bytes is finding.ratio is None
    assert_unmeasured_flag(build_single_flag(listing, [finding]), [quote])


def test_promised_capacity_and_one_measured_capacity_per_buyer_make_q3_red():
    quotes = (
        "Ordered 64 GB, got only 29 GB.",
        "สั่ง ๖๔ GB แต่ได้แค่ ๓๐.๕ GB",
    )
    listing = listing_with_reviews(*quotes)
    [option] = listing.options

    findings = [
        normalize_review_draft(review, option, draft_for(listing, index, quote, quantity))
        for index, (review, quote, quantity) in enumerate(
            zip(listing.reviews, quotes, (29, 30.5), strict=True)
        )
    ]

    assert [finding.quantity for finding in findings] == [29, 30.5]
    assert all(finding.complaint == "capacity_short" for finding in findings)
    flag = build_single_flag(listing, findings)
    assert (flag["colour"], flag["deciding"]) == ("RED", "Q3")
    evidence = [item for item in flag["evidence"] if item["source"] == "review"]
    assert [item["quote"] for item in evidence] == list(quotes)


def test_legacy_saved_short_finding_cannot_hide_conflicting_review_text():
    quotes = ("Measured 29 GB", "Got 30.5 GB")
    listing = listing_with_reviews(
        "Measured 29 GB. Measured 58 GB later.",
        "Got 30.5 GB, then measured 57 GiB.",
    )
    findings = [
        Finding(
            **draft_for(listing, index, quote, quantity).model_dump(),
            bytes=int(quantity * 2**30),
            ratio=quantity * 2**30 / 64_000_000_000,
            image_ref=None,
            image_type=None,
            read_status="ok",
        )
        for index, (quote, quantity) in enumerate(zip(quotes, (29, 30.5), strict=True))
    ]

    assert_unmeasured_flag(build_single_flag(listing, findings), list(quotes))
