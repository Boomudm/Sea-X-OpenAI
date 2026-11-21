"""Plain U2 reader functions for claims, reviews, images, and confidence."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .cache import ReviewCache
from .client import OpenAIReaderClient, StructuredReader
from .errors import InvalidReaderOutput, ReaderInputError, ReaderUnavailableError
from .models import (
    ChallengeBatch,
    ClaimDraftBatch,
    ClaimOutput,
    ConfidenceAssessment,
    Finding,
    ImageDraftBatch,
    ImageReading,
    Listing,
    Option,
    Review,
    ReviewDraft,
    ReviewDraftBatch,
)
from .prompts import (
    CLAIMS_DEVELOPER,
    CONFIDENCE_DEVELOPER,
    IMAGES_DEVELOPER,
    REVIEWS_DEVELOPER,
    REVIEWS_PROMPT_VERSION,
)
from .validation import (
    image_reading_to_finding,
    merge_text_and_image_finding,
    normalize_claims,
    normalize_image_draft,
    normalize_review_draft,
    validate_challenges,
)


def extract_claims(
    listing: Listing | Mapping[str, Any],
    *,
    client: StructuredReader | None = None,
) -> ClaimOutput:
    parsed = _listing(listing)
    reader = client or OpenAIReaderClient()
    payload = {
        "listing_id": parsed.listing_id,
        "title": parsed.title,
        "options": [
            {
                "option_id": option.option_id,
                "variation_label": option.variation_label,
                "capacity_text": option.capacity_text,
            }
            for option in parsed.options
        ],
    }
    drafts = reader.generate(
        ClaimDraftBatch,
        developer=CLAIMS_DEVELOPER,
        user_text=json.dumps(payload, ensure_ascii=False),
    )
    return ClaimOutput(
        listing_id=parsed.listing_id,
        options=normalize_claims(parsed, drafts),
    )


def read_reviews(
    listing: Listing | Mapping[str, Any],
    *,
    client: StructuredReader | None = None,
    cache: ReviewCache | None = None,
) -> list[Finding]:
    parsed = _listing(listing)
    reader = client or OpenAIReaderClient()
    own_cache = cache is None
    review_cache = cache or ReviewCache()
    matched = _matched_reviews(parsed)
    findings: dict[str, Finding] = {}
    missing_by_option: dict[str, list[Review]] = defaultdict(list)
    options = {option.option_id: option for option in parsed.options}

    try:
        for review, option in matched:
            cached = review_cache.get(review.review_id, REVIEWS_PROMPT_VERSION)
            if cached is not None:
                try:
                    cached_finding = Finding.model_validate(cached)
                    finding = normalize_review_draft(
                        review,
                        option,
                        ReviewDraft(
                            review_id=cached_finding.review_id,
                            option_id=cached_finding.option_id,
                            complaint=cached_finding.complaint,
                            quantity=cached_finding.quantity,
                            unit=cached_finding.unit,
                            role=cached_finding.role,
                            quote=cached_finding.quote,
                        ),
                    )
                except (ValidationError, InvalidReaderOutput):
                    missing_by_option[option.option_id].append(review)
                else:
                    if finding.option_id == option.option_id:
                        findings[review.review_id] = finding
                    else:
                        missing_by_option[option.option_id].append(review)
            else:
                missing_by_option[option.option_id].append(review)

        for option_id, reviews in missing_by_option.items():
            option = options[option_id]
            payload = {
                "option": option.model_dump(mode="json"),
                "reviews": [review.model_dump(mode="json") for review in reviews],
            }
            try:
                batch = reader.generate(
                    ReviewDraftBatch,
                    developer=REVIEWS_DEVELOPER,
                    user_text=json.dumps(payload, ensure_ascii=False),
                )
            except InvalidReaderOutput:
                raise
            except Exception as exc:
                raise ReaderUnavailableError(
                    f"reader unavailable and {len(reviews)} review(s) were not cached"
                ) from exc
            by_review = {draft.review_id: draft for draft in batch.findings}
            expected = {review.review_id for review in reviews}
            if len(by_review) != len(batch.findings) or set(by_review) != expected:
                raise InvalidReaderOutput(
                    "review output must contain every requested review exactly once"
                )
            for review in reviews:
                finding = normalize_review_draft(
                    review, option, by_review[review.review_id]
                )
                review_cache.put(
                    review.review_id,
                    REVIEWS_PROMPT_VERSION,
                    finding.model_dump(mode="json"),
                )
                findings[review.review_id] = finding

        return [
            findings[review.review_id]
            for review, _ in matched
            if review.review_id in findings
        ]
    finally:
        if own_cache:
            review_cache.close()


def read_images(
    listing: Listing | Mapping[str, Any],
    *,
    client: StructuredReader | None = None,
    reread_image_refs: Sequence[str] = (),
) -> list[ImageReading]:
    parsed = _listing(listing)
    reader = client or OpenAIReaderClient()
    reread = set(reread_image_refs)
    inputs = _image_inputs(parsed)
    known_refs = {item[0] for item in inputs}
    unknown = reread - known_refs
    if unknown:
        raise ReaderInputError("reread requested for an image outside the listing")

    results: list[ImageReading] = []
    for image_ref, review_id, option in inputs:
        reading = _read_one_image(reader, image_ref, review_id, option, reread=False)
        if image_ref in reread:
            reading = _read_one_image(reader, image_ref, review_id, option, reread=True)
        results.append(reading)
    return results


def assess_confidence(
    flag: Mapping[str, Any],
    evidence: Mapping[str, Any] | list[Any],
    *,
    client: StructuredReader | None = None,
) -> ConfidenceAssessment:
    reader = client or OpenAIReaderClient()
    payload = {"flag": dict(flag), "evidence": evidence, "round": 1, "tools": []}
    batch = reader.generate(
        ChallengeBatch,
        developer=CONFIDENCE_DEVELOPER,
        user_text=json.dumps(payload, ensure_ascii=False),
    )
    return ConfidenceAssessment(
        challenges=validate_challenges(batch.challenges, evidence), rounds=1
    )


def process_listing_file(
    listing_path: str | Path,
    *,
    output_root: str | Path = "out",
    client: StructuredReader | None = None,
    cache: ReviewCache | None = None,
    reread_image_refs: Sequence[str] = (),
) -> tuple[Path, Path]:
    path = Path(listing_path)
    listing = _listing(json.loads(path.read_text(encoding="utf-8")))
    reader = client or OpenAIReaderClient(project_root=Path.cwd())
    claims = extract_claims(listing, client=reader)
    text_findings = read_reviews(listing, client=reader, cache=cache)
    image_readings = read_images(
        listing, client=reader, reread_image_refs=reread_image_refs
    )
    image_findings = [
        finding
        for reading in image_readings
        if (finding := image_reading_to_finding(reading)) is not None
    ]

    merged_findings = {finding.review_id: finding for finding in text_findings}
    for image_finding in image_findings:
        current = merged_findings.get(image_finding.review_id)
        merged_findings[image_finding.review_id] = (
            image_finding
            if current is None
            else merge_text_and_image_finding(current, image_finding)
        )

    root = Path(output_root)
    claims_path = root / "claims" / f"{listing.listing_id}.json"
    findings_path = root / "findings" / f"{listing.listing_id}.json"
    claims_path.parent.mkdir(parents=True, exist_ok=True)
    findings_path.parent.mkdir(parents=True, exist_ok=True)
    claims_path.write_text(
        json.dumps(claims.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    findings_path.write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in merged_findings.values()],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return claims_path, findings_path


def _read_one_image(
    reader: StructuredReader,
    image_ref: str,
    review_id: str | None,
    option: Option | None,
    *,
    reread: bool,
) -> ImageReading:
    payload = {
        "image_ref": image_ref,
        "review_id": review_id,
        "option_id": option.option_id if option else None,
        "option": option.model_dump(mode="json") if option else None,
        "attempt": 2 if reread else 1,
        "instruction": "independent re-read of original image"
        if reread
        else "first read",
    }
    batch = reader.generate(
        ImageDraftBatch,
        developer=IMAGES_DEVELOPER,
        user_text=json.dumps(payload, ensure_ascii=False),
        image_refs=[image_ref],
    )
    if len(batch.images) != 1:
        raise InvalidReaderOutput("image call must return exactly one image reading")
    return normalize_image_draft(
        batch.images[0],
        expected_ref=image_ref,
        expected_review_id=review_id,
        expected_option=option,
    )


def _listing(value: Listing | Mapping[str, Any]) -> Listing:
    if isinstance(value, Listing):
        return value
    try:
        return Listing.model_validate(value)
    except ValidationError as exc:
        raise ReaderInputError("listing does not match the shared contract") from exc


def _matched_reviews(listing: Listing) -> list[tuple[Review, Option]]:
    by_id = {option.option_id: option for option in listing.options}
    by_label: dict[str, list[Option]] = defaultdict(list)
    for option in listing.options:
        by_label[option.variation_label.strip()].append(option)
    result: list[tuple[Review, Option]] = []
    for review in listing.reviews:
        if review.option_id is not None:
            option = by_id.get(review.option_id)
            if (
                option is None
                or review.variation_label.strip() != option.variation_label.strip()
            ):
                continue
        else:
            candidates = by_label.get(review.variation_label.strip(), [])
            option = candidates[0] if len(candidates) == 1 else None
        if option is not None:
            result.append((review, option))
    return result


def _image_inputs(listing: Listing) -> list[tuple[str, str | None, Option | None]]:
    inputs: list[tuple[str, str | None, Option | None]] = [
        (image_ref, None, None) for image_ref in listing.listing_images
    ]
    matched = {review.review_id: option for review, option in _matched_reviews(listing)}
    for review in listing.reviews:
        option = matched.get(review.review_id)
        for image_ref in review.images:
            inputs.append((image_ref, review.review_id, option))
    return inputs
