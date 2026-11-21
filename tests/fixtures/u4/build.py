"""Regenerate the explicitly labelled reviewer-queue samples with U3."""

import argparse
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory

from trongpok.export_web import build_cases
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


def reference(line, capacity, prices, date=DAY):
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
            "date": date,
        }],
        "mall_sources": [
            {
                "url": f"{BASE_URL}/mall/{capacity}-{index}",
                "date": date,
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


DEMO_GROUPS = {
    "multiple shortfalls": 12,
    "very low price": 11,
    "unsupported capacity": 7,
    "one shortfall": 9,
    "low price": 9,
    "unmeasured complaint": 9,
    "checked reviews": 24,
    "too few reviews": 14,
}
DRIVE_SIZES = (
    (32, "32 GB"), (64, "64 GB"), (128, "128 GB"),
    (256, "256 GB"), (512, "512 GB"), (1000, "1 TB"),
)
DRIVE_LINES = ("Pocket", "Slider", "Attach", "Keyring", "Swivel", "Mini")
NEUTRAL_REVIEWS = (
    "Recognized immediately by my laptop.",
    "I used it to transfer a folder.",
    "Reopened the copied files successfully.",
    "Works with the USB port on my computer.",
    "Used it for school documents.",
    "It mounted and ejected normally.",
    "Transferred the photos I needed.",
    "Backed up a folder and opened it again.",
    "It works for moving files between computers.",
)


def volume_sample_inputs():
    """Produce synthetic inputs for the larger web queue."""
    serial = 0
    for scenario, count in DEMO_GROUPS.items():
        for index in range(count):
            serial += 1
            listing_id = f"sample-usb-{serial:03}"
            line = f"{DRIVE_LINES[index % len(DRIVE_LINES)]} {serial:03}"
            size, label = DRIVE_SIZES[index % len(DRIVE_SIZES)]
            market_low = round(80 + size * 1.7) + (index % 5) * 15
            prices = [market_low, market_low + 35, market_low + 70]
            dated = "2026-11-20" if index % 3 == 1 else DAY
            kb = reference(line, size, prices, dated)

            current = prices[1]
            if scenario == "very low price":
                current = round(market_low * (0.21 + index % 4 * 0.06))
            elif scenario == "low price":
                current = round(market_low * (0.78 + index % 4 * 0.04))
            elif scenario == "unsupported capacity":
                kb["brand_page"] = {
                    "url": f"{BASE_URL}/brand/{listing_id}",
                    "date": DAY,
                    "capacities_gb": [capacity for capacity, _ in DRIVE_SIZES if capacity != size],
                }

            drive = option("usb", size, label, prices[-1], current)
            reviews, findings = volume_sample_reviews(scenario, listing_id, drive, index)
            yield listing(listing_id, line, [drive], reviews), kb, findings


def volume_sample_reviews(scenario, listing_id, drive, index):
    option_id = drive["option_id"]
    variation = drive["variation_label"]
    size = drive["promise_gb"]
    if scenario in {"one shortfall", "multiple shortfalls"}:
        measured = round(size * (0.29 + index % 7 * 0.06))
        completed = scenario == "one shortfall" and index % 3 == 0
        quote = (
            f"Completed a write and verify test and measured {measured} GB."
            if completed else f"I measured only {measured} GB."
        )
        first = review(listing_id, variation, 1, quote, stars=3)
        role = "test_result" if completed else "delivered_capacity"
        first_finding = finding(first, option_id, measured, role, "capacity_short")
        if scenario == "one shortfall":
            return [first], [first_finding]
        second = review(listing_id, variation, 2, f"Files corrupt after {measured + 1} GB.", stars=2)
        second_finding = finding(second, option_id, measured + 1, "fails_after", "capacity_short")
        return [first, second], [first_finding, second_finding]
    if scenario == "unmeasured complaint":
        row = review(listing_id, variation, 1, "The capacity seems much smaller than the advertised size.", stars=3)
        return [row], [finding(row, option_id, complaint="capacity_no_number")]
    if scenario == "checked reviews":
        measured = round(size * 0.93)
        first = review(listing_id, variation, 1, f"Verified {measured} GB on the drive.")
        other = [review(listing_id, variation, number, text) for number, text in enumerate(NEUTRAL_REVIEWS, 2)]
        findings = [finding(first, option_id, measured, "delivered_capacity")]
        findings.extend(finding(row, option_id) for row in other)
        return [first, *other], findings
    if scenario == "too few reviews":
        excerpts = NEUTRAL_REVIEWS[:index % 4]
        rows = [review(listing_id, variation, number, text) for number, text in enumerate(excerpts, 1)]
        return rows, [finding(row, option_id) for row in rows[:1]]
    return [], []


def generate(root, inputs):
    listings = root / "listings"
    flags = root / "flags"
    listings.mkdir(parents=True, exist_ok=True)
    flags.mkdir(parents=True, exist_ok=True)
    for captured, reference_row, findings in inputs:
        filename = f"{captured['listing_id']}.json"
        write_json(listings / filename, captured)
        write_json(flags / filename, build_flags(captured, [reference_row], findings, as_of=DAY))


def generate_web(output):
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        generate(root, chain(sample_inputs(), volume_sample_inputs()))
        write_json(output, build_cases(root / "flags", root / "listings"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?", default=ROOT)
    parser.add_argument("--web-output", type=Path, help="Write the larger bundled sample queue")
    args = parser.parse_args()
    if args.web_output:
        generate_web(args.web_output)
    else:
        generate(args.output, sample_inputs())
