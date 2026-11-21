"""Score frozen, independently labeled options against three baselines."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field, StrictBool, TypeAdapter, model_validator

from .errors import ReaderError
from .models import ImageType, Listing, ReadStatus, Review, Unit
from .paths import listing_filename, within_directory

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


class ReviewerDecision(BaseModel, extra="forbid"):
    decision: Literal["accepted", "dismissed", "needs_more_information"]
    reason: str
    at: AwareDatetime


class ReviewedOption(BaseModel, extra="forbid"):
    listing_id: str = Field(min_length=1)
    option_id: str = Field(min_length=1)
    verdict: Literal["mismatch", "no_mismatch", "unsure"]
    reviewer_decision: ReviewerDecision

    @property
    def key(self) -> tuple[str, str]:
        return self.listing_id, self.option_id

    @model_validator(mode="after")
    def check_verdict(self) -> ReviewedOption:
        expected = {
            "accepted": "mismatch",
            "dismissed": "no_mismatch",
            "needs_more_information": "unsure",
        }[self.reviewer_decision.decision]
        if self.verdict != expected:
            raise ValueError(f"Reviewer verdict and decision disagree for {self.key}.")
        return self


class Confidence(BaseModel):
    score: int = Field(ge=0, le=100, strict=True)


class Flag(BaseModel):
    listing_id: str
    option_id: str
    colour: str
    deciding: Literal["Q1", "Q2", "Q3", "Q4", "Q5", "grey"]
    confidence: Confidence


@dataclass(frozen=True)
class ScoredOption:
    label: OptionLabel
    flag: Flag
    low_stars: int
    matched_reviews: int
    predictions: tuple[bool, bool, bool, bool, bool]

    @property
    def truth(self) -> bool:
        return self.label.buyers_report_shortfall

    @property
    def primary_correct(self) -> bool:
        return self.predictions[0] == self.truth

    @property
    def option_key(self) -> str:
        listing_id, option_id = self.label.key
        return f"{_cell(listing_id)} / {_cell(option_id)}"

    @property
    def blind_label(self) -> str:
        return "Yes" if self.truth else "No"


def _read_json(path: str | Path, directory: Path):
    checked_path = within_directory(path, directory)
    return json.loads(checked_path.read_text(encoding="utf-8"))


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


def _validate_photo_label(label: PhotoLabel, listing: Listing | None) -> None:
    key = label.listing_id, label.review_id, label.image_ref
    if listing is None or not any(
        review.review_id == label.review_id and label.image_ref in review.images
        for review in listing.reviews
    ):
        raise ValueError(f"Photo label has no captured buyer image for {key}")
    if label.read_status == "ok" and label.image_type is None:
        raise ValueError(f"Readable photo label requires a type for {key}")
    if label.quantity is not None and label.unit in (None, "none"):
        raise ValueError(f"Photo label with a number requires a unit for {key}")


def _load_photo_findings(directory: Path, listing_id: str) -> list[dict]:
    try:
        raw = _read_json(listing_filename(listing_id), directory)
    except FileNotFoundError:
        return []
    return TypeAdapter(list[dict]).validate_python(raw)


def _photo_matches(reading: PhotoReading, label: PhotoLabel) -> bool:
    if reading.read_status != label.read_status:
        return False
    if label.read_status == "cannot_read":
        return True
    return (
        reading.image_type == label.image_type
        and reading.quantity == label.quantity
        and (label.quantity is None or reading.unit == label.unit)
    )


def _photo_summary(
    labels: list[PhotoLabel], listings: dict[str, Listing], findings_dir: Path,
) -> tuple[int, int]:
    keys = [(label.listing_id, label.review_id, label.image_ref) for label in labels]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate photo label.")
    # Check every human label against the captured images before loading model outputs.
    for label in labels:
        _validate_photo_label(label, listings.get(label.listing_id))
    findings = {
        listing_id: _load_photo_findings(findings_dir, listing_id)
        for listing_id in dict.fromkeys(label.listing_id for label in labels)
    }
    correct = missing = 0
    for label in labels:
        candidates = [
            PhotoReading.model_validate(item)
            for item in findings[label.listing_id]
            if item.get("review_id") == label.review_id and item.get("image_ref") == label.image_ref
        ]
        if candidates:
            correct += all(_photo_matches(item, label) for item in candidates)
        else:
            missing += 1
    return correct, missing


def _cell(text: str) -> str:
    return text.replace("|", r"\|").replace("\n", " ").replace("\r", " ")


def _validate_labels(labels: Labels) -> None:
    if not labels.options:
        raise ValueError("No blind-labeled options. Freeze real labels before scoring.")
    if not labels.labeled_by or not labels.labeled_by.strip() or not labels.frozen_at:
        raise ValueError("Record the independent labeler and freeze time before scoring.")
    if labels.frozen_at.utcoffset() is None:
        raise ValueError("Use a timezone-aware freeze time.")
    if len({label.key for label in labels.options}) != len(labels.options):
        raise ValueError("Duplicate option in blind labels.")


def _score_option(
    label: OptionLabel, listing: Listing, flags: list[Flag],
    chatgpt_by_option: dict[tuple[str, str], bool],
) -> ScoredOption:
    listing_id, option_id = label.key
    reviews = _matched_reviews(listing, option_id)
    matches = [flag for flag in flags if (flag.listing_id, flag.option_id) == label.key]
    if len(matches) != 1:
        raise ValueError(f"Expected one flag for {listing_id}/{option_id}")
    flag = matches[0]
    if flag.colour != COLOUR_BY_RULE[flag.deciding]:
        raise ValueError(f"Flag colour and deciding rule disagree for {listing_id}/{option_id}")
    if label.key not in chatgpt_by_option:
        raise ValueError(f"Missing ChatGPT prediction for {listing_id}/{option_id}")

    low_stars = sum(review.stars <= 2 for review in reviews)
    q3_red = flag.deciding == "Q3"
    predictions = (
        q3_red, q3_red or flag.colour == "YELLOW",
        low_stars * 100 >= LOW_STAR_PERCENT * len(reviews),
        any(review.tags for review in reviews), chatgpt_by_option[label.key],
    )
    return ScoredOption(label, flag, low_stars, len(reviews), predictions)


def _compare(primary_correct: bool, baseline_correct: bool) -> str:
    if primary_correct == baseline_correct:
        return "Tie"
    return "Win" if primary_correct else "Loss"


def _option_comparisons(options: list[ScoredOption]) -> tuple[list[str], list[str]]:
    comparisons = {method: Counter() for method in METHODS[2:]}
    option_rows = []
    for option in options:
        per_baseline = []
        for method, prediction in zip(METHODS[2:], option.predictions[2:], strict=True):
            comparison = _compare(option.primary_correct, prediction == option.truth)
            comparisons[method][comparison] += 1
            per_baseline.append(comparison)
        flag = option.flag
        option_rows.append(
            f"| {option.option_key} | {option.blind_label} | {flag.colour} ({flag.deciding}) | "
            f"{option.low_stars}/{option.matched_reviews} | {' | '.join(per_baseline)} |"
        )
    totals = [
        f"| {method} | {counts['Win']} | {counts['Tie']} | {counts['Loss']} |"
        for method, counts in comparisons.items()
    ]
    return option_rows, totals


def _render_report(
    labels: Labels, options: list[ScoredOption], listing_count: int, photo: tuple[int, int],
) -> str:
    outcomes = {
        method: Counter((option.truth, option.predictions[index]) for option in options)
        for index, method in enumerate(METHODS)
    }
    confidence = {band: Counter() for band in CONFIDENCE_BANDS}
    other_reds = []
    option_rows, comparison_rows = _option_comparisons(options)
    for option in options:
        flag = option.flag
        if flag.deciding in {"Q1", "Q2"}:
            other_reds.append((flag.deciding, option.option_key, option.blind_label))
        else:
            score = flag.confidence.score
            band = next(band for band in CONFIDENCE_BANDS if band[0] <= score <= band[1])
            confidence[band][option.primary_correct] += 1

    photo_correct, photo_missing = photo
    size = len(options)
    lines = [
        "# Buyer-evidence evaluation",
        "",
        f"**Sample:** {size} options across {listing_count} listings. "
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
        *comparison_rows,
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


def _render_reviewer_comparison(labels: Labels, decisions: list[ReviewedOption]) -> str:
    by_option = {decision.key: decision.verdict for decision in decisions}
    if len(by_option) != len(decisions):
        raise ValueError("Duplicate option in reviewer decisions.")

    outcomes = Counter(
        (by_option.get(label.key), label.buyers_report_shortfall)
        for label in labels.options
    )
    rows = (
        ("Shortfall confirmed", "mismatch"),
        ("Not confirmed", "no_mismatch"),
        ("Need more information", "unsure"),
        ("No decision exported", None),
    )
    outside_sample = len(by_option.keys() - {label.key for label in labels.options})
    return "\n".join([
        "",
        "## Reviewer decisions",
        "",
        "Reviewer decisions are shown alongside the frozen buyer labels. The baseline scores above use the frozen labels.",
        "",
        "| Reviewer decision | Blind label: Yes | Blind label: No |",
        "|---|---:|---:|",
        *(f"| {name} | {outcomes[verdict, True]} | {outcomes[verdict, False]} |" for name, verdict in rows),
        "",
        f"Decisions outside the blind sample: {outside_sample}.",
        "",
    ])


def evaluate(
    labels: Labels, chatgpt: list[OptionLabel], listings_dir: Path,
    flags_dir: Path, findings_dir: Path,
) -> str:
    _validate_labels(labels)
    chatgpt_by_option = {result.key: result.buyers_report_shortfall for result in chatgpt}
    if len(chatgpt_by_option) != len(chatgpt):
        raise ValueError("Duplicate option in ChatGPT predictions.")

    listings = {}
    flags = {}
    for listing_id in dict.fromkeys(label.listing_id for label in labels.options):
        filename = listing_filename(listing_id)
        listing = Listing.model_validate(_read_json(filename, listings_dir))
        if listing.listing_id != listing_id:
            raise ValueError(f"Captured listing ID differs from filename for {listing_id}")
        listings[listing_id] = listing
        flags[listing_id] = TypeAdapter(list[Flag]).validate_python(_read_json(filename, flags_dir))
    options = [
        _score_option(label, listings[label.listing_id], flags[label.listing_id], chatgpt_by_option)
        for label in labels.options
    ]
    photo = _photo_summary(labels.photos, listings, findings_dir)
    return _render_report(labels, options, len(listings), photo)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=Path("eval/labels.json"))
    parser.add_argument("--chatgpt", type=Path, default=Path("eval/chatgpt.json"))
    parser.add_argument("--listings-dir", type=Path, default=Path("data/listings"))
    parser.add_argument("--flags-dir", type=Path, default=Path("out/flags"))
    parser.add_argument("--findings-dir", type=Path, default=Path("out/findings"))
    parser.add_argument("--output", type=Path, default=Path("eval/results.md"))
    parser.add_argument(
        "--reviewer-decisions", type=Path,
        help="Optional Seller Guard JSON export to compare with the frozen buyer labels.",
    )
    args = parser.parse_args()
    root = Path.cwd()
    try:
        output = within_directory(args.output, root)
        listings_dir = within_directory(args.listings_dir, root)
        flags_dir = within_directory(args.flags_dir, root)
        findings_dir = within_directory(args.findings_dir, root)
        labels = Labels.model_validate(_read_json(args.labels, root))
        if not labels.options:
            raise ValueError("No blind-labeled options. Freeze real labels before scoring.")
        chatgpt = TypeAdapter(list[OptionLabel]).validate_python(_read_json(args.chatgpt, root))
        report = evaluate(labels, chatgpt, listings_dir, flags_dir, findings_dir)
        if args.reviewer_decisions is not None:
            decisions = TypeAdapter(list[ReviewedOption]).validate_python(
                _read_json(args.reviewer_decisions, root)
            )
            report += _render_reviewer_comparison(labels, decisions)
        output.write_text(report, encoding="utf-8")
    except (OSError, ValueError, ReaderError) as error:
        parser.exit(1, f"Evaluation stopped: {error}\n")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
