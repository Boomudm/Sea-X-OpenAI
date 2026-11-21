"""Match captured reviews to options and verify their measurement evidence."""

import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from functools import cache

from .profiles import CategoryProfile, UnitConversion, load_profile

_THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
_QUANTITY = r"(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?"
_OTHER_CAPACITY_BEFORE = re.compile(
    r"(?:\b(?:ordered|bought|promised|advertised|listed|rated|free space|os reports|"
    r"properties shows)\b|สั่ง(?:ซื้อ)?|โฆษณา|ระบุ|พื้นที่ว่าง)"
    r"[^,;.!?\n\d]{0,25}$",
    re.IGNORECASE,
)
_MEASUREMENT_BEFORE = re.compile(
    r"(?:\b(?:measured|verified|tested|actual|capacity is|corrupt after|"
    r"run|rerun|rechecked|retested|got only|got)\b|"
    r"วัดได้|ทดสอบได้|ความจุจริง|ได้แค่)[^,;.!?\n\d]{0,16}$",
    re.IGNORECASE,
)
_OTHER_CAPACITY_AFTER = re.compile(
    r"^\s*(?:/\s*s\b|per second\b|free\b|available space\b)",
    re.IGNORECASE,
)
_THAI_DISPLAY_BEFORE = re.compile(r"ขึ้นว่า\s*$")
_THAI_CAPACITY_LABEL_BEFORE = re.compile(r"ความจุ\s*[:：]?\s*$")
_THAI_ACTUAL_AFTER = re.compile(
    r"^\s*(?:แต่\s*(?:จุ\s*)?|จุ\s*)จร?ิง(?:\s*ๆ)?(?:\s*ได้)?\s*"
)
_THAI_TEST_BEFORE = re.compile(
    r"(?:วัด|ทดสอบ|\b(?:h2testw|f3)\b)[^,;.!?\n\d]{0,16}$", re.IGNORECASE,
)
_ITEM_COUNT_AFTER = re.compile(r"^\s*(?:drives?|pieces?)\b", re.IGNORECASE)
_RERUN_AFTER = re.compile(r"^\s*(?:on|in) (?:a |the )?(?:second run|rerun|retest)\b", re.IGNORECASE)
_ALTERNATIVE = re.compile(r"\s*(?:or|versus|vs\.?|หรือ(?:ว่า)?)\s*", re.IGNORECASE)
_COMPLETED_IMAGE_TYPES = {
    "completed_h2testw",
    "completed_f3",
    "completed_test",
    "h2testw_completed",
    "f3_completed",
    "h2testw_f3_completed",
    "completed_h2testw_f3",
}


def _decimal(value: object) -> Decimal | None:
    try:
        if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
            number = Decimal(str(value))
            return number if number.is_finite() and number >= 0 else None
        if isinstance(value, str):
            raw = value.strip().translate(_THAI_DIGITS)
            if re.fullmatch(_QUANTITY, raw):
                return Decimal(raw.replace(",", ""))
        return None
    except InvalidOperation:
        return None


@cache
def _storage_profile() -> CategoryProfile:
    return load_profile()


@cache
def _number_pattern(units: tuple[str, ...], *, optional: bool) -> re.Pattern[str]:
    alternatives = "|".join(re.escape(unit) for unit in sorted(units, key=len, reverse=True))
    suffix = rf"\s*({alternatives})(?![a-z])"
    if optional:
        return re.compile(
            rf"(?<![\d.\-−])({_QUANTITY})(?![0-9]|\.[0-9])(?:{suffix})?", re.IGNORECASE,
        )
    return re.compile(rf"{_QUANTITY}{suffix}", re.IGNORECASE)


def _review_pattern(profile: CategoryProfile) -> re.Pattern[str]:
    units = tuple(
        token for name, definition in profile.units.items() for token in (name, *definition.all_aliases)
    )
    return _number_pattern(units, optional=True)


def _unit_key(unit: object, profile: CategoryProfile) -> str:
    key = str(unit or "").strip().casefold()
    for name, definition in profile.units.items():
        if key == name.casefold() or any(key == alias.casefold() for alias in definition.all_aliases):
            return name.casefold()
    return key


def _unit_definition(key: str, profile: CategoryProfile) -> UnitConversion | None:
    return next(
        (definition for name, definition in profile.units.items() if name.casefold() == key),
        None,
    )


def _measurement_unit(unit: object, measurement_text: str, profile: CategoryProfile) -> str:
    key = _unit_key(unit, profile)
    if key not in {"", "none"}:
        return key

    option_pattern = _number_pattern(tuple(profile.units), optional=False)
    matches = {name.casefold() for name in option_pattern.findall(measurement_text.translate(_THAI_DIGITS))}
    return matches.pop() if len(matches) == 1 else ""


def _measured_value(
    quantity: object, unit: object, measurement_text: str, profile: CategoryProfile,
) -> Decimal | None:
    number = _decimal(quantity)
    definition = _unit_definition(_measurement_unit(unit, measurement_text, profile), profile)
    if number is None or definition is None:
        return None
    return number * max(definition.measurement_factors)


def measured_bytes(quantity: object, unit: object, capacity_text: str) -> Decimal | None:
    """Convert a captured storage measurement using the storage profile."""
    return _measured_value(quantity, unit, capacity_text, _storage_profile())


def _non_measurement(
    mention: re.Match[str], previous_end: int, promised: Decimal | None,
    profile: CategoryProfile,
) -> bool:
    number, unit = mention.groups()
    before = mention.string[previous_end:mention.start()]
    after = mention.string[mention.end():]
    if _OTHER_CAPACITY_AFTER.match(after) or (unit is None and _ITEM_COUNT_AFTER.match(after)):
        return True
    if _MEASUREMENT_BEFORE.search(before):
        return False
    if _OTHER_CAPACITY_BEFORE.search(before):
        return True

    if profile.category != "storage":
        return False

    # A displayed or advertised capacity may be contrasted with what the drive actually holds.
    actual = _THAI_ACTUAL_AFTER.match(after)
    actual_number = _review_pattern(profile).match(after, actual.end()) if actual else None
    if not actual_number or not actual_number.group(2):
        return False
    # The preceding test name may itself contain a digit (H2testw or F3).
    if _THAI_TEST_BEFORE.search(mention.string, 0, mention.start()):
        return False
    if _THAI_DISPLAY_BEFORE.search(before):
        return True
    if not promised or not _THAI_CAPACITY_LABEL_BEFORE.search(before):
        return False
    definition = _unit_definition(_unit_key(unit, profile), profile)
    scale = definition.promise_factor if definition is not None else None
    quantity = _decimal(number)
    return scale is not None and quantity is not None and quantity * scale == promised


def review_number_units(
    text: str, quantity: object, *, measurements_only: bool = False,
    promised_bytes: Decimal | None = None, profile: CategoryProfile | None = None,
) -> set[str]:
    """Return the selected number's units, with an empty unit for a bare number."""
    selected = _decimal(quantity)
    if selected is None:
        return set()
    profile = profile or _storage_profile()
    normalized = text.translate(_THAI_DIGITS)
    previous_end = 0
    units = set()
    for mention in _review_pattern(profile).finditer(normalized):
        number, unit = mention.groups()
        if _decimal(number) == selected and (
            not measurements_only or not _non_measurement(mention, previous_end, promised_bytes, profile)
        ):
            units.add(_unit_key(unit, profile))
        previous_end = mention.end()
    return units


def conflicting_review_measurements(
    text: str, selected: Decimal | None, capacity_text: str,
    *, promised_bytes: Decimal | None = None, profile: CategoryProfile | None = None,
) -> bool:
    """Check the whole review for competing capacity readings missing from a short quote."""
    profile = profile or _storage_profile()
    normalized = text.translate(_THAI_DIGITS)
    mentions = list(_review_pattern(profile).finditer(normalized))
    measurements = {selected} if selected is not None else set()
    previous_end = 0
    for index, mention in enumerate(mentions):
        non_measurement = _non_measurement(mention, previous_end, promised_bytes, profile)
        before = normalized[previous_end:mention.start()]
        previous_end = mention.end()
        if non_measurement:
            continue
        quantity, unit = mention.groups()
        if unit is None:
            if profile.category != "storage":
                continue
            after = normalized[previous_end:]
            unit = _alternative_unit(mentions, index, before, after)
            if unit is None and not (
                _MEASUREMENT_BEFORE.search(before) or _RERUN_AFTER.match(after)
            ):
                continue
        number = _measured_value(quantity, unit, capacity_text, profile)
        if number is not None:
            measurements.add(number)
        if len(measurements) > 1:
            return True
    return False


def _alternative_unit(mentions, index: int, before: str, after: str) -> str | None:
    if index > 0 and _ALTERNATIVE.fullmatch(before):
        return mentions[index - 1].group(2) or ""
    if index + 1 < len(mentions):
        gap = mentions[index + 1].start() - mentions[index].end()
        if _ALTERNATIVE.fullmatch(after[:gap]):
            return mentions[index + 1].group(2) or ""
    return None


def _quote_supports_number(
    quote: str, finding: dict, measurement_text: str, profile: CategoryProfile,
) -> bool:
    unit = _measurement_unit(finding.get("unit"), measurement_text, profile)
    written_units = review_number_units(quote, finding.get("quantity"), profile=profile)
    # Legacy storage captures allow bare quantities. Other profiles require a
    # written unit so an unsupported unit cannot be read as the advertised one.
    return any(
        (written_unit or profile.category == "storage")
        and _measurement_unit(written_unit, measurement_text, profile) == unit
        for written_unit in written_units
    )


def _label(value: object) -> str:
    return re.sub(r"[\s/-]+", "_", str(value or "").strip().casefold())


def _role(finding: dict) -> str:
    label = _label(finding.get("role"))
    return {
        "completed_test_result": "test_result",
        "completed_test": "test_result",
        "os_reported_capacity": "os_reported",
    }.get(label, label)


def _mismatch_type(finding: dict, profile: CategoryProfile) -> str | None:
    if profile.category == "storage":
        return None
    kind = finding.get("mismatch_type") or finding.get("complaint")
    if isinstance(kind, str) and kind in profile.mismatch_types and kind not in {
        "capacity_short", "capacity_no_number", "none", "other",
    }:
        return kind
    return None


def _outside_tolerance(number: Decimal, promise: Decimal, profile: CategoryProfile) -> bool:
    return number < promise * profile.tolerance or (
        profile.maximum_ratio is not None and number > promise * profile.maximum_ratio
    )


def _finding_evidence(
    finding: dict, review: dict, measurement_text: str, promised: Decimal | None,
    profile: CategoryProfile, *, mismatch_type: str | None = None,
) -> tuple[dict, Decimal | None, bool, bool] | None:
    """Verify the finding and identify unresolvable text contradictions."""
    storage = profile.category == "storage"
    if not storage and finding.get("read_status") != "ok":
        return None
    image_ref = finding.get("image_ref")
    quote = finding.get("quote") or ""
    if image_ref:
        if mismatch_type or image_ref not in review.get("images", ()):
            return None
    elif not quote.strip() or quote not in review.get("text", ""):
        return None

    role = _role(finding)
    complaint_kind = finding.get("complaint")
    reported = complaint_kind in profile.mismatch_types
    complaint = bool(mismatch_type) or (
        reported and (
            complaint_kind == "capacity_no_number" or (
                complaint_kind == "capacity_short" and role not in {"free_space", "promise", "speed"}
            )
        )
    )
    quantity = None if mismatch_type else _decimal(finding.get("quantity"))
    image_type = _label(finding.get("image_type"))
    number = None
    measurable = role in profile.measured_roles and not mismatch_type
    if finding.get("read_status", "ok") == "ok" and measurable:
        if image_ref:
            supported = storage and role == "test_result" and image_type in _COMPLETED_IMAGE_TYPES
        else:
            supported = _quote_supports_number(quote, finding, measurement_text, profile)
        if supported:
            number = _measured_value(quantity, finding.get("unit"), measurement_text, profile)
            complaint = complaint or (
                number is not None
                and promised is not None
                and _outside_tolerance(number, promised, profile)
            )

    measured_text = not image_ref and measurable
    excluded = measured_text and quantity is not None and not review_number_units(
        review["text"], quantity, measurements_only=True, promised_bytes=promised, profile=profile,
    )
    if excluded:
        number = quantity = None
        complaint = False
    ambiguous = measured_text and conflicting_review_measurements(
        review["text"], number, measurement_text, promised_bytes=promised, profile=profile,
    )
    if ambiguous:
        number = quantity = None
        complaint = True

    evidence = {
        "source": "review",
        "review_id": review["review_id"],
        "buyer_masked": review.get("buyer_masked"),
        "date": review.get("date"),
        "quote": quote,
        "quantity": float(quantity) if quantity is not None else None,
        "unit": "none" if ambiguous or excluded else finding.get("unit"),
        "role": role,
        "bytes": float(number) if number is not None and storage else None,
        "ratio": float(number / promised) if number is not None and promised else None,
        "image_ref": image_ref,
        "image_type": finding.get("image_type"),
    }
    if mismatch_type:
        evidence["mismatch_type"] = mismatch_type
    return evidence, number, complaint, ambiguous


def _review_signal(
    review: dict, findings: Iterable[dict], measurement_text: str, promised: Decimal | None,
    profile: CategoryProfile,
) -> tuple[dict | None, bool]:
    measurements = []
    complaints = []
    images = defaultdict(list)
    for finding in findings:
        result = _finding_evidence(finding, review, measurement_text, promised, profile)
        if result is None:
            continue
        evidence, number, complaint, ambiguous = result
        if ambiguous:
            return evidence, False
        if complaint:
            complaints.append(evidence)
        if number is None:
            continue
        if evidence["image_ref"]:
            images[evidence["image_ref"]].append((number, evidence))
        else:
            measurements.append((number, evidence))

    # An image can drive RED only after two successful reads agree.
    for readings in images.values():
        if len(readings) >= 2 and len({number for number, _ in readings}) == 1:
            measurements.append(readings[0])

    if not measurements:
        return (complaints[0], False) if complaints else (None, False)
    number, evidence = measurements[0]
    if len({value for value, _ in measurements}) > 1 or not promised:
        return {**evidence, "quantity": None, "unit": "none", "bytes": None, "ratio": None}, False
    if _outside_tolerance(number, promised, profile):
        return evidence, bool((review.get("buyer_masked") or "").strip())
    return next((complaint for complaint in complaints if complaint["ratio"] is None), None), False


def review_evidence(
    listing: dict, option: dict, promise_gb: object, findings: Iterable[dict],
    *, profile: CategoryProfile | None = None,
) -> tuple[list[dict], list[dict], dict[str, list[dict]], int, int, bool]:
    """Return review signals for a promise given in the active profile's promise unit."""
    profile = profile or _storage_profile()
    storage = profile.category == "storage"
    variation = option.get("variation_label")
    unique_variation = bool(variation) and sum(
        candidate.get("variation_label") == variation
        for candidate in listing.get("options", (option,))
    ) == 1
    reviews_by_id = {review["review_id"]: review for review in listing.get("reviews", ())}
    matched = {
        review_id: review
        for review_id, review in reviews_by_id.items()
        if unique_variation and review.get("variation_label") == variation
    }
    text_count = sum(bool(review.get("text", "").strip()) for review in matched.values())
    option_id = option["option_id"]
    by_review = defaultdict(list)
    uncertain = not unique_variation
    for finding in findings:
        review_id = finding.get("review_id")
        if review_id in matched:
            by_review[review_id].append(finding)
            if not storage and finding.get("option_id") != option_id:
                uncertain = True
        elif finding.get("option_id") == option_id:
            uncertain = True

    checked_count = sum(
        _checked_text_review(review, by_review[review_id], profile, option_id)
        for review_id, review in matched.items()
    )

    promise = _decimal(promise_gb)
    promised = promise * profile.units[profile.promise_unit].promise_factor if (
        promise and profile.promise_unit is not None
    ) else None
    text_key = "capacity_text" if storage else "measurement_text"
    measurement_text = option.get(text_key) or variation
    measured = []
    unverified = []
    mismatches = defaultdict(list)
    for review_id, review in matched.items():
        review_text = review.get("text", "").strip()
        measurement_findings = []
        for finding in by_review[review_id]:
            if not storage and finding.get("option_id") != option_id:
                continue
            mismatch_type = _mismatch_type(finding, profile)
            if mismatch_type is None:
                measurement_findings.append(finding)
                continue
            result = _finding_evidence(
                finding, review, measurement_text, promised, profile, mismatch_type=mismatch_type,
            )
            if result is not None:
                evidence, _, _, _ = result
                mismatches[mismatch_type].append((evidence, review_text))
        evidence, outside_tolerance = _review_signal(
            review, measurement_findings, measurement_text, promised, profile,
        )
        if evidence is not None:
            (measured if outside_tolerance else unverified).append((evidence, review_text))

    # Numeric signals share a deduplication pool. Categorical reports count
    # independently for each mismatch, even when the same buyer reports two kinds.
    seen_buyers: set[str] = set()
    seen_texts: set[str] = set()
    measured = _independent(measured, seen_buyers, seen_texts)
    unverified = _independent(unverified, seen_buyers, seen_texts)
    categorical = {
        kind: _independent(sorted(signals, key=_without_buyer), set(), set())
        for kind, signals in mismatches.items()
    }
    return measured, unverified, categorical, text_count, checked_count, uncertain


def _checked_text_review(
    review: dict, findings: list[dict], profile: CategoryProfile, option_id: str,
) -> bool:
    text = review.get("text", "")
    if not text.strip():
        return False

    def checked(finding: dict) -> bool:
        quote = finding.get("quote") or ""
        return (
            finding.get("read_status") == "ok"
            and (quote or finding.get("complaint") == "none")
            and quote in text
        )

    def valid_type(finding: dict) -> bool:
        complaint = finding.get("mismatch_type") or finding.get("complaint")
        return complaint == "none" or (
            complaint in profile.mismatch_types and bool((finding.get("quote") or "").strip())
        )

    text_findings = [finding for finding in findings if not finding.get("image_ref")]
    if profile.category == "storage":
        return any(map(checked, text_findings))
    return bool(text_findings) and all(
        checked(finding)
        and finding.get("option_id") == option_id
        and valid_type(finding)
        for finding in findings
    )


def _without_buyer(signal: tuple[dict, str]) -> bool:
    return not (signal[0].get("buyer_masked") or "").strip()


def _independent(
    signals: list[tuple[dict, str]], seen_buyers: set[str], seen_texts: set[str],
) -> list[dict]:
    result = []
    for evidence, text in signals:
        buyer = (evidence.get("buyer_masked") or "").strip()
        if buyer in seen_buyers or (text and text in seen_texts):
            continue
        seen_buyers.add(buyer)
        if text:
            seen_texts.add(text)
        result.append(evidence)
    return result
