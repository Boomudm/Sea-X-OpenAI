"""Deterministic flags from captured listings, approved references and reader evidence."""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from .profiles import CategoryProfile, load_profile
from .reviews import measured_bytes as measured_bytes
from .reviews import review_evidence

QUESTION_ORDER = ("Q1", "Q2", "Q3", "Q4", "Q5")
COLOUR_ORDER = {"RED": 0, "YELLOW": 1, "GREY": 2, "GREEN": 3}


def _identity(value):
    return str(value or "").strip().casefold()


def _find_kb(claim, rows):
    brand = _identity(claim.get("brand"))
    product_line = _identity(claim.get("product_line"))
    storage_type = _identity(claim.get("type"))
    if not (brand and product_line and storage_type):
        return None

    matches = [
        row for row in rows
        if brand in {_identity(name) for name in [row["brand"], *row["aliases"]]}
        and product_line == _identity(row["product_line"])
        and storage_type == _identity(row["type"])
    ]
    return matches[0] if len(matches) == 1 else None


def _captured_kb(listing, rows):
    """Use a unique approved row named explicitly in the captured title and specs."""
    title = _identity(listing.get("title"))
    spec = _identity(listing.get("spec_text"))

    def mentions(value, text):
        name = _identity(value)
        return bool(name and re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text))

    matches = [
        row for row in rows
        if row.get("approved_by")
        and mentions(row["product_line"], title)
        and mentions(row["type"], spec)
        and any(mentions(name, title) for name in [row["brand"], *row["aliases"]])
    ]
    return matches[0] if len(matches) == 1 else None


def _number(value):
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _market_evidence(kb, promise, option):
    ranges = [
        band for band in kb["market_range"]
        if _number(band["capacity_gb"]) == promise
    ]
    if len(ranges) != 1:
        return None, False

    band = ranges[0]
    sources = [
        source for source in kb["mall_sources"]
        if _number(source["capacity_gb"]) == promise and source.get("url")
    ]
    source_count = len({source["url"] for source in sources})
    thin = min(band["offers_used"], source_count) < 3
    low_per_gb = _number(band["low_thb_per_gb"])
    high_per_gb = _number(band["high_thb_per_gb"])
    if thin or low_per_gb is None or high_per_gb is None or not 0 < low_per_gb <= high_per_gb:
        return None, thin

    return {
        "source": "market_range",
        "was_thb": option["was_thb"],
        "now_thb": option["now_thb"],
        "low_thb": float(low_per_gb * promise),
        "high_thb": float(high_per_gb * promise),
        "date": band["date"],
        "sources": sources,
    }, False


def _price_reasons(market):
    now = _number(market["now_thb"])
    was = _number(market["was_thb"])
    low = _number(market["low_thb"])
    high = _number(market["high_thb"])
    if now is None or now < 0:
        return {}
    result = {}
    if now < low / 2 or (
        was is not None and was > 0 and now < Decimal("0.75") * low
        and not low <= was <= high
    ):
        result["Q1"] = "Price is far below the market range"
    if low / 2 <= now < low:
        result["Q4"] = "Price is low"
    return result


def _challenge_sources(evidence):
    sources = set()
    for item in evidence:
        for key in ("review_id", "quote", "url", "image_ref"):
            value = item.get(key)
            if value:
                sources.add(value)
        sources.update(source["url"] for source in item.get("sources", []))
    return sources


def _confidence(deciding_evidence, all_evidence, market, thin, kb, uncertain, as_of, challenges, missing,
                extra_sources=frozenset(), *, profile: CategoryProfile):
    reviews = [item for item in deciding_evidence if item["source"] == "review"]
    storage = profile.category == "storage"
    measurement_key = "bytes" if storage else "ratio"
    test_reason = "Completed write-and-verify result" if storage else "Completed measurement result"
    factors = (
        (len({item["buyer_masked"] for item in reviews if item["buyer_masked"]}) >= 2,
         15, "2 or more separate buyers"),
        (any(item.get(measurement_key) is not None for item in reviews),
         10, "Deciding buyer evidence quotes a clear number"),
        (bool(reviews), 10, "Deciding reviews match the option exactly"),
        (market and market["date"][:10] == as_of and len({
            source["url"] for source in market["sources"] if source["date"][:10] == as_of
        }) >= 3, 10, "Market range and at least 3 offers captured today"),
        (any(item.get("role") == "test_result" and item.get(measurement_key) is not None
             for item in reviews), 10, test_reason),
        (uncertain, -10, "An option match is uncertain"),
        (any(item.get("image_type") == "os_properties" for item in reviews)
         and all(not item.get("image_ref") or item.get("image_type") == "os_properties"
                 for item in reviews), -10, "Image evidence is OS-screen only"),
        (thin or kb is None, -10, "Market range is thin or the KB row is missing"),
    )
    adjustments = [
        {"points": points, "reason": reason} for applies, points, reason in factors if applies
    ]
    base = max(0, min(100, 50 + sum(item["points"] for item in adjustments)))
    change = 0
    sources = _challenge_sources(all_evidence) | set(extra_sources)
    price_decided = any(item.get("source") == "market_range" for item in deciding_evidence)
    seen = set()
    for challenge in challenges:
        points = challenge.get("points")
        source = challenge.get("source")
        reason = challenge.get("reason")
        kind = challenge.get("kind")
        if (
            not isinstance(points, int) or points not in (-10, -5, 5, 10)
            or not isinstance(source, str) or source not in sources
            or not isinstance(reason, str) or not reason.strip() or source in seen
            or not -20 <= change + points <= 20
            # Code already reads every GB/TB number both ways (§4.4), so the AI
            # cannot lower confidence on GB vs GiB grounds.
            or (storage and kind == "gb_vs_gib" and points < 0)
            # Sale or promotion pricing only bears on a flag decided by price.
            or (kind == "flash_sale" and not price_decided)
        ):
            continue
        change += points
        seen.add(source)
        adjustments.append({"points": points, "reason": reason})

    return {
        "score": max(0, min(100, base + change)),
        "base": base,
        "adjustments": adjustments,
        "missing_evidence": missing,
        "rounds": int(bool(challenges)),
    }


def _checked_review_ids(listing, option, findings):
    """IDs of clean checked reviews of this option, which a GREEN challenge may cite."""
    reviews = {
        review["review_id"]: review for review in listing.get("reviews", ())
        if review.get("variation_label") == option.get("variation_label")
    }
    return {
        finding["review_id"] for finding in findings
        if finding.get("review_id") in reviews and finding.get("complaint") == "none"
        and finding.get("read_status") == "ok" and not finding.get("image_ref")
    }


def _build_flag(listing, option, claim, rows, findings, as_of, challenges, profile):
    storage = profile.category == "storage"
    promise_key = "promise_gb" if storage else "promise_value"
    text_key = "capacity_text" if storage else "measurement_text"
    unclear_key = "capacity_unclear" if storage else "measurement_unclear"
    promise = _number(claim.get(promise_key, option.get(promise_key)))
    unclear = claim.get(unclear_key, False) or promise is None or promise <= 0
    if not storage:
        unclear = unclear or option.get(unclear_key, False)
    kb = None
    if storage:
        has_claim_identity = any(claim.get(field) for field in ("brand", "product_line", "type"))
        kb = _find_kb(claim, rows) if has_claim_identity else _captured_kb(listing, rows)
    attribute = profile.attribute
    tolerance = format((profile.tolerance * 100).normalize(), "f")
    reasons = {}
    evidence = {}
    missing = []
    market = None
    thin = False

    def add(question, reason, items):
        reasons.setdefault(question, []).append(reason)
        evidence.setdefault(question, []).extend(items)

    if unclear:
        add("Q4", f"{attribute.capitalize()} is unclear", [{
            "source": "option", text_key: option.get(text_key, option["variation_label"]),
        }])
        missing.append(f"Confirm the {attribute} advertised for this option")
        promise = None
    if kb is None:
        missing.append("Find an approved reference for this brand, product line and type")
    elif promise is not None:
        market, thin = _market_evidence(kb, promise, option)
        if market:
            for question, reason in _price_reasons(market).items():
                add(question, reason, [market])
        else:
            missing.append("Capture at least 3 comparable official Mall offers for this capacity")

        brand_page = kb["brand_page"]
        if brand_page and brand_page["date"] and brand_page["url"] and brand_page["capacities_gb"]:
            if promise not in map(_number, brand_page["capacities_gb"]):
                add("Q2", "The brand page does not list this capacity", [
                    {**brand_page, "source": "brand_page", "promise_gb": float(promise)},
                ])
        elif kb["mall_capacities_gb"] and promise not in map(_number, kb["mall_capacities_gb"]):
            add("Q4", "This capacity was not observed in official Mall offers", [{
                "source": "mall_capacities", "capacities_gb": kb["mall_capacities_gb"],
                "sources": kb["mall_sources"],
            }])
            missing.append("Check the manufacturer's dated capacity list for this line")

    shortfalls, unverified, matched_count, checked_count, uncertain = review_evidence(
        listing, option, promise, findings, profile=profile,
    )
    if len(shortfalls) >= 2:
        add("Q3", f"Buyers measured below {tolerance}% of the advertised {attribute}", shortfalls)
    elif shortfalls:
        add("Q4", f"One buyer measured below {tolerance}% of the advertised {attribute}", shortfalls)
        missing.append("Look for an independent measured report for this variation")
    unmeasured = [item for item in unverified if not item.get("mismatch_type")]
    if unmeasured:
        add("Q4", f"{attribute.capitalize()} complaint needs a usable measurement", unmeasured)
        missing.append(f"Verify the reported {attribute} against the original review or completed test")
    categorical = [item for item in unverified if item.get("mismatch_type")]
    if categorical:
        add("Q4", "Reported mismatch needs a manual check", categorical)
        missing.append("Verify the reported mismatch against the original review and advertised option")

    deciding = next((question for question in ("Q3", "Q2", "Q1", "Q4") if question in reasons), None)
    count_evidence = {
        "source": "review_count",
        "matched_text_reviews": matched_count,
        "checked_text_reviews": checked_count,
    }
    if deciding is None:
        deciding = "Q5" if matched_count >= 10 and checked_count == matched_count else "grey"
        if deciding == "Q5":
            add("Q5", "No flags found in the matched reviews", [count_evidence])
        else:
            if matched_count < 10:
                add("grey", "Not enough matched text reviews", [count_evidence])
                missing.append(f"Collect {10 - matched_count} more matched text reviews")
            if checked_count < matched_count:
                add("grey", "Matched text reviews are still unchecked", [count_evidence])
                missing.append(f"Read {matched_count - checked_count} more matched text reviews")

    colours = {"Q1": "RED", "Q2": "RED", "Q3": "RED", "Q4": "YELLOW",
               "Q5": "GREEN", "grey": "GREY"}
    all_evidence = []
    for question in (deciding, *(item for item in QUESTION_ORDER if item != deciding)):
        for item in evidence.get(question, []):
            if item not in all_evidence:
                all_evidence.append(item)
    if count_evidence not in all_evidence:
        all_evidence.append(count_evidence)
    path = [
        f"{question}: {'decided' if question == deciding else 'triggered' if question in reasons else 'clear'}"
        for question in QUESTION_ORDER
    ]
    if deciding == "grey":
        path.append("grey: decided")
    return {
        "listing_id": listing["listing_id"],
        "option_id": option["option_id"],
        "colour": colours[deciding],
        "deciding": deciding,
        "path": path,
        "reasons": [
            *reasons[deciding],
            *(reason for question in QUESTION_ORDER if question != deciding
              for reason in reasons.get(question, [])),
        ],
        "evidence": all_evidence,
        "verdict": "unsure",
        "confidence": _confidence(
            evidence[deciding], all_evidence, market, thin, kb, uncertain, as_of, challenges, missing,
            _checked_review_ids(listing, option, findings) if deciding == "Q5" else frozenset(),
            profile=profile,
        ),
        "reviewer_decision": None,
    }


def queue_key(flag):
    score = flag["confidence"]["score"]
    return (COLOUR_ORDER[flag["colour"]], score if flag["colour"] == "GREEN" else -score,
            flag["listing_id"], flag["option_id"])


def build_flags(
    listing, kb_rows=(), findings=(), claims=(), *, as_of=None, challenges=None,
    profile: CategoryProfile | None = None,
):
    """Evaluate every option using the active profile, defaulting to storage."""
    profile = profile or load_profile()
    as_of = str(as_of or datetime.now(ZoneInfo("Asia/Bangkok")).date())[:10]
    claims_by_option = {claim["option_id"]: claim for claim in claims}
    challenges_by_option = challenges or {}
    kb_rows = tuple(kb_rows)
    findings = tuple(findings)
    return sorted((
        _build_flag(
            listing, option, claims_by_option.get(option["option_id"], {}), kb_rows,
            findings, as_of, challenges_by_option.get(option["option_id"], ()), profile,
        )
        for option in listing["options"]
    ), key=queue_key)
