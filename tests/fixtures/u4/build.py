"""Regenerate the explicitly labelled reviewer-queue samples with U3."""

import argparse
from pathlib import Path

from trongpok.paths import write_json
from trongpok.rules import build_flags


ROOT = Path(__file__).parent
DAY = "2026-11-21"
BASE_URL = "https://example.invalid/trongpok-sample"


def option(option_id, capacity, size_label, was, now, *, variation=None):
    return {
        "option_id": option_id,
        "variation_label": variation or size_label,
        "capacity_text": size_label,
        "promise_gb": capacity,
        "was_thb": was,
        "now_thb": now,
    }


def listing(listing_id, line, options, reviews=(), rating=None):
    return {
        "listing_id": listing_id,
        "url": f"{BASE_URL}/{listing_id}",
        "captured_at": f"{DAY}T10:00:00+07:00",
        "title": f"Sample · Fixture Brand {line}",
        "spec_text": f"USB flash drive{f' · {rating} stars' if rating else ''}",
        "description": "Synthetic demo fixture. No marketplace observations.",
        "listing_images": [],
        "options": options,
        "reviews": list(reviews),
    }


def review(listing_id, variation, number, text, stars=5):
    return {
        "review_id": f"{listing_id}-review-{number}",
        "variation_label": variation,
        "option_id": None,
        "buyer_masked": f"Bu***{number:02}",
        "date": f"2026-11-{21 - number:02}",
        "stars": stars,
        "text": text,
        "tags": [],
        "images": [],
    }


def finding(review, option_id, quantity=None, role="other", complaint="none"):
    return {
        "review_id": review["review_id"],
        "option_id": option_id,
        "complaint": complaint,
        "quantity": quantity,
        "unit": "GB" if quantity is not None else "none",
        "role": role,
        "bytes": None,
        "ratio": None,
        "quote": review["text"],
        "image_ref": None,
        "image_type": None,
        "read_status": "ok",
    }


def reference(line, capacity, prices):
    return {
        "brand": "Fixture Brand",
        "aliases": [],
        "product_line": line,
        "type": "USB flash drive",
        "mall_capacities_gb": [capacity],
        "brand_page": None,
        "market_range": [{
            "capacity_gb": capacity,
            "low_thb_per_gb": min(prices) / capacity,
            "high_thb_per_gb": max(prices) / capacity,
            "offers_used": len(prices),
            "date": DAY,
        }],
        "mall_sources": [
            {
                "url": f"{BASE_URL}/mall/{capacity}-{index}",
                "date": DAY,
                "capacity_gb": capacity,
                "now_thb": price,
            }
            for index, price in enumerate(prices, 1)
        ],
        "expected_display": "",
        "approved_by": "Synthetic fixture approver",
    }


def sample_inputs():
    hero_id = "sample-compact-64"
    standard_id = "sample-standard-64"
    drive_64 = option("64-gb", 64, "64 GB", 256, 224)
    hero_quotes = (
        ("Only 29 GB on mine.", 29, "delivered_capacity"),
        ("I received only 30.5 GB.", 30.5, "delivered_capacity"),
        ("My drive holds just 29 GB.", 29, "delivered_capacity"),
        ("Files corrupt after 30 GB.", 30, "fails_after"),
    )
    hero_reviews = [
        review(hero_id, "64 GB", index, quote, stars=4)
        for index, (quote, _, _) in enumerate(hero_quotes, 1)
    ]
    hero_findings = [
        finding(row, "64-gb", quantity, role, "capacity_short")
        for row, (_, quantity, role) in zip(hero_reviews, hero_quotes, strict=True)
    ]
    yield (
        listing(hero_id, "Compact", [drive_64], hero_reviews, rating="4.8"),
        reference("Compact", 64, [192, 224, 256]),
        hero_findings,
    )

    standard_quotes = (
        "Verified 58 GB on the drive.",
        "No errors after copying my files.",
        "Recognized immediately by my computer.",
        "Works with my school files.",
        "The advertised size matched my test.",
        "Read my backups without a problem.",
        "All copied files opened again.",
        "I am using it for documents.",
        "Easy to use for moving photos.",
        "Transfer finished without errors.",
    )
    standard_reviews = [
        review(standard_id, "64 GB", index, quote)
        for index, quote in enumerate(standard_quotes, 1)
    ]
    first, *other_reviews = standard_reviews
    yield (
        listing(standard_id, "Standard", [drive_64], standard_reviews),
        reference("Standard", 64, [192, 224, 256]),
        [finding(first, "64-gb", 58, "delivered_capacity")] +
        [finding(row, "64-gb") for row in other_reviews],
    )

    yield (
        listing("sample-discount-1tb", "Discount", [option("1-tb", 1000, "1 TB", 2990, 299)]),
        reference("Discount", 1000, [1800, 2100, 2400]),
        [],
    )
    yield (
        listing("sample-reference-1tb", "Reference", [
            option("1-tb", 1000, "1 TB", 6000, 2000, variation="1 TB · Black"),
            option("1-tb-blue", 1000, "1 TB", 2000, 1500, variation="1 TB · Blue"),
        ]),
        reference("Reference", 1000, [1800, 2100, 2400]),
        [],
    )


def generate(root):
    listings = root / "listings"
    flags = root / "flags"
    listings.mkdir(parents=True, exist_ok=True)
    flags.mkdir(parents=True, exist_ok=True)
    for captured, reference_row, findings in sample_inputs():
        filename = f"{captured['listing_id']}.json"
        write_json(listings / filename, captured)
        write_json(flags / filename, build_flags(captured, [reference_row], findings, as_of=DAY))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?", default=ROOT)
    generate(parser.parse_args().output)
