"""Match captured reviews to options and verify their capacity evidence."""

import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation

_THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
_UNIT_BYTES = {
    "mb": 10**6,
    "gb": 2**30,
    "tb": 2**40,
    "gib": 2**30,
    "tib": 2**40,
}
_QUANTITY = r"(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?"
_REVIEW_NUMBER = re.compile(
    rf"(?<![\d.\-−])({_QUANTITY})(?![0-9]|\.[0-9])"
    r"(?:\s*(GiB|TiB|MB|GB|TB|กิกะไบต์|เทราไบต์|เมกะไบต์|จีบี|ทีบี|เอ็มบี)(?![a-z]))?",
    re.IGNORECASE,
)
_OPTION_UNIT = re.compile(rf"{_QUANTITY}\s*(GiB|TiB|MB|GB|TB)(?![a-z])", re.IGNORECASE)
_THAI_UNITS = {
    "กิกะไบต์": "gb",
    "จีบี": "gb",
    "เทราไบต์": "tb",
    "ทีบี": "tb",
    "เมกะไบต์": "mb",
    "เอ็มบี": "mb",
}
_OTHER_CAPACITY_BEFORE = re.compile(
    r"(?:\b(?:ordered|bought|promised|advertised|listed|rated|free space|os reports|"
    r"properties shows)\b|สั่ง(?:ซื้อ)?|โฆษณา|ระบุ|พื้นที่ว่าง)"
    r"[^,;.!?\n\d]{0,25}$",
    re.IGNORECASE,
)
_MEASUREMENT_BEFORE = re.compile(
    r"(?:\b(?:measured|verified|tested|actual|capacity is|corrupt after)\b|"
    r"วัดได้|ทดสอบได้|ความจุจริง)[^,;.!?\n\d]{0,16}$",
    re.IGNORECASE,
)
_OTHER_CAPACITY_AFTER = re.compile(r"^\s*(?:/\s*s\b|per second\b|free\b)", re.IGNORECASE)
_ALTERNATIVE = re.compile(r"\s*(?:or|versus|vs\.?|หรือ(?:ว่า)?)\s*", re.IGNORECASE)
_MEASURED_ROLES = {"delivered_capacity", "fails_after", "test_result"}
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


def _unit_key(unit: object) -> str:
    key = str(unit or "").strip().casefold()
    return _THAI_UNITS.get(key, key)


def _capacity_unit(unit: object, capacity_text: str) -> str:
    key = _unit_key(unit)
    if key not in {"", "none"}:
        return key
    matches = {name.casefold() for name in _OPTION_UNIT.findall(capacity_text.translate(_THAI_DIGITS))}
    return matches.pop() if len(matches) == 1 else ""


def measured_bytes(quantity: object, unit: object, capacity_text: str) -> Decimal | None:
    """Convert a captured measurement with the conservative GB/TB interpretation."""
    number = _decimal(quantity)
    scale = _UNIT_BYTES.get(_capacity_unit(unit, capacity_text))
    if number is None or scale is None:
        return None
    return number * scale


def review_number_units(text: str, quantity: object) -> set[str]:
    """Return units attached to the selected number. A bare number has an empty unit."""
    selected = _decimal(quantity)
    if selected is None:
        return set()
    return {
        _unit_key(unit)
        for number, unit in _REVIEW_NUMBER.findall(text.translate(_THAI_DIGITS))
        if _decimal(number) == selected
    }


def conflicting_review_measurements(
    text: str, selected: Decimal | None, capacity_text: str
) -> bool:
    """Check the whole review for competing capacity readings missing from a short quote."""
    normalized = text.translate(_THAI_DIGITS)
    mentions = list(_REVIEW_NUMBER.finditer(normalized))
    measurements = {selected} if selected is not None else set()
    previous_end = 0
    for index, mention in enumerate(mentions):
        before = normalized[previous_end:mention.start()]
        previous_end = mention.end()
        after = normalized[previous_end:]
        other_capacity = _OTHER_CAPACITY_BEFORE.search(before)
        measured_context = _MEASUREMENT_BEFORE.search(before)
        if (other_capacity and not measured_context) or _OTHER_CAPACITY_AFTER.match(after):
            continue
        quantity, unit = mention.groups()
        if unit is None:
            unit = _alternative_unit(mentions, index, before, after)
            if unit is None and not measured_context:
                continue
        number = measured_bytes(quantity, unit, capacity_text)
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


def _quote_supports_number(quote: str, finding: dict, capacity_text: str) -> bool:
    unit = _capacity_unit(finding.get("unit"), capacity_text)
    return any(
        _capacity_unit(written_unit, capacity_text) == unit
        for written_unit in review_number_units(quote, finding.get("quantity"))
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


def _finding_evidence(
    finding: dict, review: dict, capacity_text: str, promised_bytes: Decimal | None
) -> tuple[dict, Decimal | None, bool, bool] | None:
    """Verify the finding and identify unresolvable text contradictions."""
    image_ref = finding.get("image_ref")
    quote = finding.get("quote") or ""
    if image_ref:
        if image_ref not in review.get("images", ()):
            return None
    elif not quote.strip() or quote not in review.get("text", ""):
        return None

    role = _role(finding)
    complaint_kind = finding.get("complaint")
    complaint = complaint_kind == "capacity_no_number" or (
        complaint_kind == "capacity_short" and role not in {"free_space", "promise", "speed"}
    )
    quantity = _decimal(finding.get("quantity"))
    image_type = _label(finding.get("image_type"))
    number = None
    if finding.get("read_status", "ok") == "ok" and role in _MEASURED_ROLES:
        if image_ref:
            supported = role == "test_result" and image_type in _COMPLETED_IMAGE_TYPES
        else:
            supported = _quote_supports_number(quote, finding, capacity_text)
        if supported:
            number = measured_bytes(quantity, finding.get("unit"), capacity_text)
            complaint = complaint or (
                number is not None
                and promised_bytes is not None
                and number < promised_bytes * Decimal("0.85")
            )

    ambiguous = (
        not image_ref and role in _MEASURED_ROLES
        and conflicting_review_measurements(review["text"], number, capacity_text)
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
        "unit": "none" if ambiguous else finding.get("unit"),
        "role": role,
        "bytes": float(number) if number is not None else None,
        "ratio": float(number / promised_bytes) if number is not None and promised_bytes else None,
        "image_ref": image_ref,
        "image_type": finding.get("image_type"),
    }
    return evidence, number, complaint, ambiguous


def _review_signal(
    review: dict, findings: Iterable[dict], capacity_text: str, promised_bytes: Decimal | None
) -> tuple[dict | None, bool]:
    measurements = []
    complaints = []
    images = defaultdict(list)
    for finding in findings:
        result = _finding_evidence(finding, review, capacity_text, promised_bytes)
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
    if len({value for value, _ in measurements}) > 1 or not promised_bytes:
        return {**evidence, "quantity": None, "unit": "none", "bytes": None, "ratio": None}, False
    if number < Decimal("0.85") * promised_bytes:
        return evidence, bool((review.get("buyer_masked") or "").strip())
    if any(complaint["bytes"] is None for complaint in complaints):
        return next(complaint for complaint in complaints if complaint["bytes"] is None), False
    return None, False


def review_evidence(
    listing: dict, option: dict, promise_gb: object, findings: Iterable[dict]
) -> tuple[list[dict], list[dict], int, int, bool]:
    """Return shortfalls, complaints, matched and checked text counts, and ambiguity."""
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
    by_review = defaultdict(list)
    uncertain = not unique_variation
    for finding in findings:
        review_id = finding.get("review_id")
        if review_id in matched:
            by_review[review_id].append(finding)
        elif finding.get("option_id") == option["option_id"]:
            uncertain = True

    checked_count = sum(
        bool(review.get("text", "").strip()) and any(
            finding.get("read_status") == "ok"
            and not finding.get("image_ref")
            and (finding.get("quote") or finding.get("complaint") == "none")
            and (finding.get("quote") or "") in review["text"]
            for finding in by_review[review_id]
        )
        for review_id, review in matched.items()
    )

    promise = _decimal(promise_gb)
    promised_bytes = promise * 10**9 if promise else None
    measured = []
    unverified = []
    for review_id, review in matched.items():
        evidence, shortfall = _review_signal(
            review, by_review[review_id], option.get("capacity_text") or variation, promised_bytes
        )
        if evidence is not None:
            text = review.get("text", "").strip()
            (measured if shortfall else unverified).append((evidence, text))

    seen_buyers: set[str] = set()
    seen_texts: set[str] = set()

    def independent(signals: list[tuple[dict, str]]) -> list[dict]:
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

    return independent(measured), independent(unverified), text_count, checked_count, uncertain
