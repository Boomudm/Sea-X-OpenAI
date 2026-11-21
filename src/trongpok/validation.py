"""Deterministic evidence validation and storage-unit calculations."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from typing import Any

from .errors import InvalidReaderOutput
from .models import (
    Challenge,
    ClaimDraftBatch,
    ClaimOption,
    Finding,
    ImageDraft,
    ImageReading,
    Listing,
    Option,
    Review,
    ReviewDraft,
    Unit,
)
from .reviews import conflicting_review_measurements, measured_bytes, review_number_units

_THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
_NUMBER_RE = re.compile(r"(?<![\d.])([0-9]+(?:[,.][0-9]+)?)(?![\d.])")
_CAPACITY_RE = re.compile(
    r"(?<![\d.])([0-9]+(?:[,.][0-9]+)?)\s*(TB|GB)(?![A-Za-z])",
    re.IGNORECASE,
)
_UNIT_RE = re.compile(r"(?<![A-Za-z])(TiB|GiB|TB|GB|MB)(?![A-Za-z])", re.IGNORECASE)


def ascii_digits(value: str) -> str:
    return value.translate(_THAI_DIGITS)


def numbers_in_text(value: str) -> list[float]:
    normalized = ascii_digits(value)
    numbers: list[float] = []
    for match in _NUMBER_RE.finditer(normalized):
        try:
            numbers.append(_parse_number(match.group(1)))
        except ValueError:
            continue
    return numbers


def capacity_values_gb(value: str) -> list[float]:
    normalized = ascii_digits(value)
    result: list[float] = []
    for quantity, unit in _CAPACITY_RE.findall(normalized):
        number = _parse_number(quantity)
        result.append(number * 1000 if unit.upper() == "TB" else number)
    return result


def _parse_number(value: str) -> float:
    if "," in value and "." not in value:
        whole, fraction = value.split(",", 1)
        value = whole + fraction if len(fraction) == 3 else whole + "." + fraction
    return float(value.replace(",", ""))


def option_capacity_unit(option: Option) -> Unit:
    matches = _CAPACITY_RE.findall(ascii_digits(option.capacity_text))
    if len(matches) == 1:
        return "TB" if matches[0][1].upper() == "TB" else "GB"
    label_matches = _CAPACITY_RE.findall(ascii_digits(option.variation_label))
    if len(label_matches) == 1:
        return "TB" if label_matches[0][1].upper() == "TB" else "GB"
    return "none"


def units_in_text(value: str) -> set[Unit]:
    canonical: dict[str, Unit] = {
        "mb": "MB",
        "gb": "GB",
        "tb": "TB",
        "gib": "GiB",
        "tib": "TiB",
    }
    return {canonical[item.lower()] for item in _UNIT_RE.findall(value)}


def quantity_bytes(quantity: float | None, unit: Unit) -> int | None:
    if quantity is None or unit == "none":
        return None
    if not math.isfinite(quantity) or quantity < 0:
        raise InvalidReaderOutput("quantity must be a finite non-negative number")
    multipliers = {
        "MB": 1_000_000,
        "GB": 2**30,
        "TB": 2**40,
        "GiB": 2**30,
        "TiB": 2**40,
    }
    return round(quantity * multipliers[unit])


def normalize_claims(listing: Listing, drafts: ClaimDraftBatch) -> list[ClaimOption]:
    by_id = {draft.option_id: draft for draft in drafts.options}
    expected_ids = [option.option_id for option in listing.options]
    if len(by_id) != len(drafts.options) or set(by_id) != set(expected_ids):
        raise InvalidReaderOutput("claim output must contain every option exactly once")

    title_capacities = set(capacity_values_gb(listing.title))
    normalized: list[ClaimOption] = []
    for option in listing.options:
        draft = by_id[option.option_id]
        label_values = capacity_values_gb(option.variation_label)
        unique_values = set(label_values)
        parsed = next(iter(unique_values)) if len(unique_values) == 1 else None
        title_conflict = (
            parsed is not None
            and len(title_capacities) == 1
            and parsed not in title_capacities
        )
        unclear = parsed is None or title_conflict or draft.capacity_unclear
        if parsed is None:
            if draft.promise_gb is not None:
                raise InvalidReaderOutput(
                    f"option {option.option_id} has no checkable capacity label"
                )
            promise_gb = None
        else:
            if draft.promise_gb is None or not math.isclose(
                draft.promise_gb, parsed, rel_tol=0, abs_tol=1e-6
            ):
                raise InvalidReaderOutput(
                    f"option {option.option_id} promise does not match its label"
                )
            promise_gb = parsed
        normalized.append(
            ClaimOption(
                option_id=option.option_id,
                promise_gb=promise_gb,
                capacity_unclear=unclear,
            )
        )
    return normalized


def _quoted_review_unit(review: Review, option: Option, draft: ReviewDraft) -> Unit:
    written_units = review_number_units(draft.quote, draft.quantity)
    if not written_units:
        raise InvalidReaderOutput(
            f"quantity for review {review.review_id} is absent from its quote"
        )
    if draft.unit.casefold() in written_units:
        return draft.unit
    if "" in written_units:
        return option_capacity_unit(option)
    raise InvalidReaderOutput(f"unit for review {review.review_id} does not match its quote")


def normalize_review_draft(
    review: Review, option: Option, draft: ReviewDraft
) -> Finding:
    if draft.review_id != review.review_id or draft.option_id != option.option_id:
        raise InvalidReaderOutput("review or option ID changed in model output")
    if not draft.quote or draft.quote not in review.text:
        raise InvalidReaderOutput(
            f"quote for review {review.review_id} is not exact copied text"
        )
    quantity = draft.quantity
    unit: Unit = draft.unit
    role = draft.role
    measurable = role in {"delivered capacity", "fails after", "test result"}
    excluded = False
    if quantity is not None:
        unit = _quoted_review_unit(review, option, draft)
        excluded = measurable and not review_number_units(
            review.text, quantity, measurements_only=True,
        )
        if excluded:
            quantity = None
            unit = "none"
            role = "other"
        elif measurable and (
            unit == "none" or conflicting_review_measurements(
                review.text, measured_bytes(quantity, unit, option.capacity_text),
                option.capacity_text or option.variation_label,
            )
        ):
            quantity = None
            unit = "none"
        elif unit == "none":
            raise InvalidReaderOutput(
                f"bare quantity for review {review.review_id} has no option unit"
            )

    parsed_bytes = quantity_bytes(quantity, unit)
    promise_gb = option.promise_gb
    if promise_gb is None:
        values = capacity_values_gb(option.variation_label) or capacity_values_gb(
            option.capacity_text
        )
        promise_gb = values[0] if len(set(values)) == 1 else None
    ratio = (
        parsed_bytes / (promise_gb * 1_000_000_000)
        if parsed_bytes is not None and promise_gb
        else None
    )
    if excluded:
        complaint = "none"
    elif measurable and ratio is not None:
        complaint = "capacity_short" if ratio < 0.85 else "none"
    elif measurable or draft.complaint == "capacity_no_number":
        complaint = "capacity_no_number"
    elif draft.complaint == "capacity_short":
        raise InvalidReaderOutput("capacity_short requires a usable measured number")
    else:
        complaint = draft.complaint

    return Finding(
        review_id=review.review_id,
        option_id=option.option_id,
        complaint=complaint,
        quantity=quantity,
        unit=unit,
        role=role,
        bytes=parsed_bytes,
        ratio=ratio,
        quote=draft.quote,
        image_ref=None,
        image_type=None,
        read_status="ok",
    )


def normalize_image_draft(
    draft: ImageDraft,
    *,
    expected_ref: str,
    expected_review_id: str | None,
    expected_option: Option | None,
) -> ImageReading:
    if draft.image_ref != expected_ref:
        raise InvalidReaderOutput("image reference changed in model output")
    expected_option_id = expected_option.option_id if expected_option else None
    if draft.review_id != expected_review_id or draft.option_id != expected_option_id:
        raise InvalidReaderOutput("image association changed in model output")
    if draft.read_status == "cannot_read" and (
        draft.quantity is not None or draft.visible_text is not None
    ):
        raise InvalidReaderOutput("cannot_read image cannot contain extracted evidence")
    unit: Unit = draft.unit
    if draft.quantity is not None:
        visible_units = units_in_text(draft.visible_text or "")
        if len(visible_units) > 1:
            raise InvalidReaderOutput("image contains conflicting capacity units")
        if visible_units:
            visible_unit = next(iter(visible_units))
            if unit != visible_unit:
                raise InvalidReaderOutput("image unit does not match visible text")
        elif expected_option is not None:
            unit = option_capacity_unit(expected_option)
    parsed_bytes = quantity_bytes(draft.quantity, unit)
    promise_gb = expected_option.promise_gb if expected_option else None
    if promise_gb is None and expected_option is not None:
        values = capacity_values_gb(expected_option.variation_label)
        promise_gb = values[0] if len(set(values)) == 1 else None
    ratio = (
        parsed_bytes / (promise_gb * 1_000_000_000)
        if parsed_bytes is not None and promise_gb
        else None
    )
    return ImageReading(
        image_ref=draft.image_ref,
        review_id=draft.review_id,
        option_id=draft.option_id,
        image_type=draft.image_type,
        quantity=draft.quantity,
        unit=unit,
        role=draft.role,
        bytes=parsed_bytes,
        ratio=ratio,
        visible_text=draft.visible_text,
        read_status=draft.read_status,
    )


def image_reading_to_finding(reading: ImageReading) -> Finding | None:
    if reading.review_id is None or reading.option_id is None:
        return None
    measurable = reading.image_type == "completed H2testw/F3"
    complaint = (
        "capacity_short"
        if measurable and reading.ratio is not None and reading.ratio < 0.85
        else "none"
    )
    return Finding(
        review_id=reading.review_id,
        option_id=reading.option_id,
        complaint=complaint,
        quantity=reading.quantity,
        unit=reading.unit,
        role=reading.role,
        bytes=reading.bytes,
        ratio=reading.ratio,
        quote=reading.visible_text or "",
        image_ref=reading.image_ref,
        image_type=reading.image_type,
        read_status=reading.read_status,
    )


def merge_text_and_image_finding(text: Finding, image: Finding) -> Finding:
    """Keep one finding per buyer review while attaching its strongest image read."""
    if text.review_id != image.review_id or text.option_id != image.option_id:
        raise InvalidReaderOutput("cannot merge findings from different reviews")
    image_is_test = (
        image.image_type == "completed H2testw/F3" and image.read_status == "ok"
    )
    current_is_test = (
        text.image_type == "completed H2testw/F3" and text.read_status == "ok"
    )
    if current_is_test and not image_is_test:
        return text

    update: dict[str, Any] = {
        "image_ref": image.image_ref,
        "image_type": image.image_type,
        "read_status": image.read_status,
    }
    if image_is_test and image.quantity is not None:
        if text.quantity is not None and (
            text.unit != image.unit
            or not math.isclose(text.quantity, image.quantity, rel_tol=0, abs_tol=1e-6)
        ):
            update.update(
                complaint="capacity_no_number",
                quantity=None,
                unit="none",
                role="other",
                bytes=None,
                ratio=None,
            )
        elif text.quantity is None:
            update.update(
                complaint=image.complaint,
                quantity=image.quantity,
                unit=image.unit,
                role=image.role,
                bytes=image.bytes,
                ratio=image.ratio,
            )
    return text.model_copy(update=update)


def validate_challenges(
    challenges: Iterable[Challenge], evidence: Mapping[str, Any] | list[Any]
) -> list[Challenge]:
    strings = list(_evidence_quote_strings(evidence))
    sources = set(_source_values(evidence))
    validated: list[Challenge] = []
    for challenge in challenges:
        quote = challenge.quote.strip() if challenge.quote is not None else None
        source = challenge.source.strip() if challenge.source is not None else None
        if not quote and not source:
            raise InvalidReaderOutput(
                "each confidence challenge needs a quote or source"
            )
        if quote and not any(quote in text for text in strings):
            raise InvalidReaderOutput(
                "challenge quote is absent from supplied evidence"
            )
        if source and source not in sources:
            raise InvalidReaderOutput(
                "challenge source is absent from supplied evidence"
            )
        validated.append(challenge)
    return validated


def _evidence_quote_strings(value: Any) -> Iterable[str]:
    quote_keys = {"quote", "text", "excerpt", "visible_text"}
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in quote_keys and isinstance(item, str) and item.strip():
                yield item
            elif isinstance(item, (Mapping, list)):
                yield from _evidence_quote_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _evidence_quote_strings(item)


def _source_values(value: Any) -> Iterable[str]:
    source_keys = {"review_id", "image_ref", "url", "source", "id"}
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in source_keys and isinstance(item, str):
                yield item
            yield from _source_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _source_values(item)
