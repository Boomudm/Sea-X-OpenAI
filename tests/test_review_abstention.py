"""A short quote cannot turn contradictory buyer text into a measurement."""

import json
from pathlib import Path

import pytest

from trongpok.models import Finding, Listing, ReviewDraft
from trongpok.rules import build_flags
from trongpok.validation import normalize_review_draft


FIXTURE = Path(__file__).parent / "fixtures" / "listing.json"


def listing_with_reviews(*texts, capacity_text="64 GB", promise_gb=64):
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw["options"][0].update(
        variation_label=capacity_text, capacity_text=capacity_text, promise_gb=promise_gb,
    )
    raw["reviews"] = [
        {**review, "variation_label": capacity_text, "text": text}
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
            "First run: 29. Second run: 58.",
            "First run: 29",
            id="bare-test-run-results",
        ),
        pytest.param(
            "วัดได้แค่ ๒๙ GB แต่วัดอีกครั้งได้ ๕๘ GiB",
            "วัดได้แค่ ๒๙ GB",
            id="thai-digits",
        ),
        pytest.param(
            "ขึ้นว่า 64 GB แต่จุจิงๆได้ 29 GB แต่วัดอีกครั้งได้ 58 GB",
            "จุจิงๆได้ 29 GB",
            id="displayed-capacity-with-two-disagreeing-delivered-readings",
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


@pytest.mark.parametrize("read_path", ["reader-draft", "saved-finding"])
@pytest.mark.parametrize(
    ("text", "quote", "quantity"),
    [
        # 8082164236-r01 reports a little over 10 GB. The test draft uses the
        # written number and retains the hedge in its quote.
        pytest.param(
            "ความคุ้มค่า :  ของปลอม ของปลอมครับ ขึ้นว่า 1.90 TB แต่จริง ๆ 10 GB กว่า ๆ "
            "อารมณ์เสียเลย ตอนแรกนึกว่าโดนไวรัส เสียเงินค่าซื้อ Avast ไปอีก 600 กว่าบาท "
            "สรุป ไม่มีไวรัส แต่เป็นของปลอม -*-",
            "แต่จริง ๆ 10 GB กว่า ๆ",
            10,
            id="os-display-before-approximate-delivery",
        ),
        pytest.param(
            "คุณภาพแย่มากๆ ความจุ 2TB จุจิงๆได้ 20GB ข้อมูลก็หายอีก",
            "จุจิงๆได้ 20GB ข้อมูลก็หายอีก",
            20,
            id="promise-before-delivered-capacity",
        ),
    ],
)
def test_antecedent_capacity_does_not_suppress_delivered_reading(text, quote, quantity, read_path):
    listing = listing_with_reviews(text, capacity_text="2TB", promise_gb=2000)
    [review] = listing.reviews
    [option] = listing.options
    draft = draft_for(listing, 0, quote, quantity)

    if read_path == "reader-draft":
        finding = normalize_review_draft(review, option, draft)
        assert finding.complaint == "capacity_short"
    else:
        finding = Finding(
            **draft.model_dump(), bytes=quantity * 2**30, ratio=quantity * 2**30 / 2e12,
            image_ref=None, image_type=None, read_status="ok",
        )

    flag = build_single_flag(listing, [finding])
    assert (flag["colour"], flag["deciding"], flag["verdict"]) == ("YELLOW", "Q4", "unsure")
    [evidence] = [item for item in flag["evidence"] if item["source"] == "review"]
    assert (evidence["quote"], evidence["quantity"], evidence["unit"]) == (quote, quantity, "GB")
    assert 0 < evidence["ratio"] < 0.85


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


@pytest.mark.parametrize("suffix", [" free", "/s"], ids=["free-space", "speed"])
def test_non_measurement_cannot_supply_second_buyer(suffix):
    listing = listing_with_reviews("Measured 30.5 GB.", f"29 GB{suffix}.")
    [option] = listing.options
    clear_draft = draft_for(listing, 0, "Measured 30.5 GB", 30.5)
    misread = draft_for(listing, 1, "29 GB", 29)

    clear = normalize_review_draft(listing.reviews[0], option, clear_draft)
    finding = normalize_review_draft(listing.reviews[1], option, misread)
    assert finding.complaint == "none"
    assert finding.quantity is finding.bytes is finding.ratio is None

    legacy = Finding(
        **misread.model_dump(), bytes=29 * 2**30, ratio=0.486,
        image_ref=None, image_type=None, read_status="ok",
    )
    flag = build_single_flag(listing, [clear, legacy])
    assert (flag["colour"], flag["deciding"]) == ("YELLOW", "Q4")
    evidence = [item for item in flag["evidence"] if item["source"] == "review"]
    assert [item["quote"] for item in evidence] == [clear.quote]
