"""Score frozen, independently labeled options against three baselines."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, StrictBool, TypeAdapter

from .models import ImageType, Listing, ReadStatus, Review, Unit

LOW_STAR_PERCENT = 20
CONFIDENCE_BANDS = [(0, 49), (50, 69), (70, 84), (85, 100)]
METHODS = [
    "Q3 RED", "Q3 RED + YELLOW", "1–2-star share (≥20%)",
    "Shopee complaint tag", "ChatGPT",
]
COLOUR_BY_RULE = {
    "Q1": "RED", "Q2": "RED", "Q3": "RED", "Q4": "YELLOW",
    "Q5": "GREEN", "grey": "GREY",
}


class OptionLabel(BaseModel, extra="forbid"):
    listing_id: str = Field(min_length=1)
    option_id: str = Field(min_length=1)
    buyers_report_shortfall: StrictBool

    @property
    def key(self) -> tuple[str, str]:
        return self.listing_id, self.option_id


class PhotoReading(BaseModel):
    review_id: str
    image_ref: str
    read_status: ReadStatus
    image_type: ImageType | None
    quantity: float | None = Field(ge=0, allow_inf_nan=False)
    unit: Unit | None


class PhotoLabel(PhotoReading, extra="forbid"):
    listing_id: str


class Labels(BaseModel, extra="forbid"):
    labeled_by: str | None
    frozen_at: datetime | None
    options: list[OptionLabel]
    photos: list[PhotoLabel]


class Confidence(BaseModel):
    score: int = Field(ge=0, le=100, strict=True)


class Flag(BaseModel):
    listing_id: str
    option_id: str
    colour: str
    deciding: Literal["Q1", "Q2", "Q3", "Q4", "Q5", "grey"]
    confidence: Confidence


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _listing_file(directory: Path, listing_id: str) -> Path:
    filename = f'{listing_id}.json'
    if Path(filename).name != filename:
        raise ValueError(f"Invalid listing ID {listing_id!r}")
    return directory / filename


def _matched_reviews(listing: Listing, option_id: str) -> list[Review]:
    options = [option for option in listing.options if option.option_id == option_id]
    if len(options) != 1:
        raise ValueError(f"Expected one captured option {listing.listing_id}/{option_id}")
    variation = options[0].variation_label
    if not variation or sum(opt.variation_label == variation for opt in listing.options) != 1:
        raise ValueError(f"Ambiguous Variation for {listing.listing_id}/{option_id}")
    reviews = [review for review in listing.reviews if review.variation_label == variation]
    if not reviews:
        raise ValueError(f"No matched buyer reviews for {listing.listing_id}/{option_id}")
    return reviews


def _photo_summary(
    labels: list[PhotoLabel], listings: dict[str, Listing], findings_dir: Path
) -> tuple[int, int]:
    seen = set()
    findings_by_listing = {}
    correct = missing = 0
    for label in labels:
        key = label.listing_id, label.review_id, label.image_ref
        if key in seen:
            raise ValueError(f"Duplicate photo label for {key}")
        seen.add(key)
        listing = listings.get(label.listing_id)
        if listing is None or not any(
            review.review_id == label.review_id and label.image_ref in review.images
            for review in listing.reviews
        ):
            raise ValueError(f"Photo label has no captured buyer image for {key}")
        if label.read_status == "ok" and label.image_type is None:
            raise ValueError(f"Readable photo label requires a type for {key}")
        if label.quantity is not None and label.unit in (None, "none"):
            raise ValueError(f"Photo label with a number requires a unit for {key}")
        if label.listing_id not in findings_by_listing:
            path = _listing_file(findings_dir, label.listing_id)
            findings_by_listing[label.listing_id] = _read_json(path) if path.is_file() else []
        candidates = [
            PhotoReading.model_validate(item)
            for item in findings_by_listing[label.listing_id]
            if item.get("review_id") == label.review_id and item.get("image_ref") == label.image_ref
        ]
        if not candidates:
            missing += 1
            continue
        correct += all(
            item.read_status == label.read_status and (
                label.read_status == "cannot_read" or (
                    item.image_type == label.image_type
                    and item.quantity == label.quantity
                    and (label.quantity is None or item.unit == label.unit)
                )
            )
            for item in candidates
        )
    return correct, missing


def _cell(text: str) -> str:
    return text.replace("|", r"\|").replace("\n", " ").replace("\r", " ")


def evaluate(
    labels: Labels, chatgpt: list[OptionLabel], listings_dir: Path,
    flags_dir: Path, findings_dir: Path,
) -> str:
    if not labels.options:
        raise ValueError("No blind-labeled options. Freeze real labels before scoring.")
    if not labels.labeled_by or not labels.labeled_by.strip() or not labels.frozen_at:
        raise ValueError("Record the independent labeler and freeze time before scoring.")
    if labels.frozen_at.utcoffset() is None:
        raise ValueError("Use a timezone-aware freeze time.")
    if len({label.key for label in labels.options}) != len(labels.options):
        raise ValueError("Duplicate option in blind labels.")
    chatgpt_by_option = {result.key: result.buyers_report_shortfall for result in chatgpt}
    if len(chatgpt_by_option) != len(chatgpt):
        raise ValueError("Duplicate option in ChatGPT predictions.")

    listings = {}
    flags = {}
    outcomes = {method: Counter() for method in METHODS}
    comparisons = {method: Counter() for method in METHODS[2:]}
    confidence = {band: Counter() for band in CONFIDENCE_BANDS}
    other_reds = []
    option_rows = []
    for label in labels.options:
        listing_id, option_id = label.key
        if listing_id not in listings:
            listing = Listing.model_validate(_read_json(_listing_file(listings_dir, listing_id)))
            if listing.listing_id != listing_id:
                raise ValueError(f"Captured listing ID differs from filename for {listing_id}")
            listings[listing_id] = listing
            flags[listing_id] = TypeAdapter(list[Flag]).validate_python(
                _read_json(_listing_file(flags_dir, listing_id))
            )
        reviews = _matched_reviews(listings[listing_id], option_id)
        matches = [
            flag for flag in flags[listing_id]
            if flag.listing_id == listing_id and flag.option_id == option_id
        ]
        if len(matches) != 1:
            raise ValueError(f"Expected one flag for {listing_id}/{option_id}")
        flag = matches[0]
        if flag.colour != COLOUR_BY_RULE[flag.deciding]:
            raise ValueError(f"Flag colour and deciding rule disagree for {listing_id}/{option_id}")
        if label.key not in chatgpt_by_option:
            raise ValueError(f"Missing ChatGPT prediction for {listing_id}/{option_id}")

        low_stars = sum(review.stars <= 2 for review in reviews)
        q3_red = flag.deciding == "Q3"
        predictions = [
            q3_red, q3_red or flag.colour == "YELLOW",
            low_stars * 100 >= LOW_STAR_PERCENT * len(reviews),
            any(review.tags for review in reviews), chatgpt_by_option[label.key],
        ]
        truth = label.buyers_report_shortfall
        for method, prediction in zip(METHODS, predictions, strict=True):
            outcomes[method][truth, prediction] += 1
        primary_correct = q3_red == truth
        per_baseline = []
        for method, prediction in zip(METHODS[2:], predictions[2:], strict=True):
            baseline_correct = prediction == truth
            comparison = "Tie" if primary_correct == baseline_correct else (
                "Win" if primary_correct else "Loss"
            )
            comparisons[method][comparison] += 1
            per_baseline.append(comparison)

        option_key = f"{_cell(listing_id)} / {_cell(option_id)}"
        blind_label = "Yes" if truth else "No"
        option_rows.append(
            f"| {option_key} | {blind_label} | {flag.colour} ({flag.deciding}) | "
            f"{low_stars}/{len(reviews)} | {' | '.join(per_baseline)} |"
        )
        if flag.deciding in {"Q1", "Q2"}:
            other_reds.append((flag.deciding, option_key, blind_label))
        else:
            score = flag.confidence.score
            band = next(band for band in CONFIDENCE_BANDS if band[0] <= score <= band[1])
            confidence[band][primary_correct] += 1

    photo_correct, photo_missing = _photo_summary(labels.photos, listings, findings_dir)
    size = len(labels.options)
    lines = [
        "# Buyer-evidence evaluation",
        "",
        f"**Sample:** {size} options across {len(listings)} listings. "
        f"Blind labels frozen by {_cell(labels.labeled_by)} at {labels.frozen_at.isoformat()}.",
        "",
        "## Buyer shortfall detection",
        "",
        "| Method | N | True positives | Misses | False alarms | True negatives |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, count in outcomes.items():
        lines.append(
            f"| {method} | {size} | {count[True, True]} | {count[True, False]} | "
            f"{count[False, True]} | {count[False, False]} |"
        )
    lines += [
        "", "## Price and brand REDs", "",
        f"**Q1 price:** {sum(rule == 'Q1' for rule, _, _ in other_reds)}. "
        f"**Q2 brand:** {sum(rule == 'Q2' for rule, _, _ in other_reds)}.",
        "",
        "| Deciding rule | Listing / option | Blind buyer label |",
        "|---|---|---|",
        *(f"| {rule} | {key} | {label} |" for rule, key, label in other_reds),
        "", "## Option-level comparisons", "",
        "A win means Q3 RED mode predicted the blind label correctly and the baseline missed it.",
        "",
        "| Option | Blind buyer label | Flag | Low stars / matched | vs stars | vs tag | vs ChatGPT |",
        "|---|---|---|---:|---|---|---|",
        *option_rows,
        "",
        "| Baseline | Wins | Ties | Losses |",
        "|---|---:|---:|---:|",
        *(
            f"| {method} | {counts['Win']} | {counts['Tie']} | {counts['Loss']} |"
            for method, counts in comparisons.items()
        ),
        "", "## Confidence by score band", "",
        "Correctness uses the Q3 RED buyer prediction. Q1/Q2 REDs are excluded here.",
        "",
        "| Confidence | N | Correct | Accuracy |",
        "|---|---:|---:|---:|",
    ]
    for (low, high), counts in confidence.items():
        total = counts.total()
        accuracy = f"{counts[True] / total:.0%}" if total else "—"
        lines.append(f"| {low}–{high} | {total} | {counts[True]} | {accuracy} |")
    lines += ["", "## Photo-reading accuracy", ""]
    if labels.photos:
        photo_count = len(labels.photos)
        lines.append(
            f"{photo_correct}/{photo_count} correct ({photo_correct / photo_count:.0%}). "
            f"Missing readings: {photo_missing}."
        )
    else:
        lines.append("No independently labeled buyer photos in this sample.")
    lines += ["", "These results describe this sample.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=Path("eval/labels.json"))
    parser.add_argument("--chatgpt", type=Path, default=Path("eval/chatgpt.json"))
    parser.add_argument("--listings-dir", type=Path, default=Path("data/listings"))
    parser.add_argument("--flags-dir", type=Path, default=Path("out/flags"))
    parser.add_argument("--findings-dir", type=Path, default=Path("out/findings"))
    parser.add_argument("--output", type=Path, default=Path("eval/results.md"))
    args = parser.parse_args()
    try:
        labels = Labels.model_validate(_read_json(args.labels))
        if not labels.options:
            raise ValueError("No blind-labeled options. Freeze real labels before scoring.")
        chatgpt = TypeAdapter(list[OptionLabel]).validate_python(_read_json(args.chatgpt))
        report = evaluate(labels, chatgpt, args.listings_dir, args.flags_dir, args.findings_dir)
        args.output.write_text(report, encoding="utf-8")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Evaluation stopped: {error}\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
