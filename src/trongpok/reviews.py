"""Match captured reviews to options and verify their measurement evidence."""

import re
from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from functools import cache

from .profiles import CategoryProfile, Translations, UnitConversion, load_profile

_THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
_QUANTITY = r"(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?"
_COMMA_DECIMAL = frozenset({
    "bg", "ca", "cs", "da", "de", "el", "es", "et", "fi", "fr", "hr", "hu", "id", "is", "it",
    "lt", "lv", "nb", "nl", "nn", "pl", "pt", "ro", "ru", "sk", "sl", "sr", "sv", "tr", "uk", "vi",
})
_CONTEXT_BREAK = re.compile(
    r"(?<!\d)[,.]|[,.](?!\d)|[;!?。！？；，\n]"
    r"|\b(?:and|but|whereas|while(?!\s+charging))\b|(?:但是|然而|但|而)",
    re.IGNORECASE,
)
_SENTENCE_END = ".!?。！？"
_STATEMENT_BREAK = r"(?<![0-9])\.|\.(?![0-9])|[!?。！？\n]+"
_CONCESSIVE_BREAK = r",\s*(?=(?:although|though|even though|obwohl)\b)"
_SENTENCES = re.compile(_STATEMENT_BREAK)
_CATEGORICAL_CLAUSES = re.compile(rf"{_STATEMENT_BREAK}|{_CONCESSIVE_BREAK}", re.IGNORECASE)
_CONCESSIVE = re.compile(_CONCESSIVE_BREAK, re.IGNORECASE)
_GROUP_SPACE = " \u00a0\u202f"
_REMOVE_GROUP_SPACES = str.maketrans("", "", _GROUP_SPACE)
_SPACED_DIGITS_BEFORE = re.compile(r"[0-9][ \u00a0\u202f]+$")
_RANGE_JOINER = r"(?:[-‐‑‒–—−]|\bto\b)"
_RANGE_AFTER = re.compile(rf"\s*{_RANGE_JOINER}\s*[0-9]", re.IGNORECASE)
_RANGE_BEFORE = re.compile(rf"[0-9](?:\s*[^0-9\s,.;!?-]+)?\s*{_RANGE_JOINER}\s*$", re.IGNORECASE)
_BETWEEN_BEFORE = re.compile(
    r"\bbetween\s+[0-9][0-9,. \u00a0\u202f]*(?:\s*[a-z]+)?\s+and\s*$", re.IGNORECASE,
)
_BETWEEN_START = re.compile(r"\bbetween\s+$", re.IGNORECASE)
_AND_NUMBER = re.compile(r"\s+and\s+[0-9]", re.IGNORECASE)
_COMPLETION_DENIAL_BEFORE = re.compile(
    r"\b(?:no|without|never|not|didn't|didn’t|doesn't|hasn't)\b[\w \t’']{0,35}$"
    r"|(?:未|没有|并未)[^\s。！？]{0,8}$",
    re.IGNORECASE,
)
_COMPLETION_DENIAL_AFTER = re.compile(
    r"^\s*(?:(?:was|were|did|had|has)\s+(?:not|never)\b"
    r"|(?:wasn|weren|didn|hasn)['’]t\b|not\s+(?:completed|performed)|未|没有"
    r"|(?:should|would|could|might|may)\b|(?:is|was)\s+(?:expected|estimated|projected)\b)",
    re.IGNORECASE,
)
_MODEL_INSTRUCTION = re.compile(
    r"\b(?:ignore|disregard|override|forget)\b[^\n.!?]{0,45}\b(?:instructions?|rules?|prompts?|system)\b"
    r"|\b(?:system|developer|assistant|model)\s+(?:task|message|instructions?|prompt)\b"
    r"|\b(?:system|developer|assistant)\s*[:,]\s*(?:please\s+)?"
    r"(?:set|mark|report|classify|label|output|return)\b"
    r"|\b(?:tag|classify|label|mark)\s+(?:this|the|my)\s+review\s+(?:as|with)\b"
    r"|^\s*(?:please\s+)?(?:return|output|emit|respond with|reply with|report|tag|classify)\s+"
    r"(?:[0-9]|the\b|a\b|as\b|measured\b|delivered\b)",
    re.IGNORECASE,
)
_MISMATCH_WORD = r"(?:wrong|incorrect|mismatch|missing|falsch\w*|fehl\w*)"
_NEGATED_MISMATCH = re.compile(
    rf"\b(?:not|never|no|nicht|kein(?:e[nmrs]?)?)\s+"
    rf"(?:(?:a|an|the|any|actually|ein(?:e[nmrs]?)?|die|den|das)\s+){{0,4}}{_MISMATCH_WORD}\b"
    rf"|\b(?:not|never|don't|didn't|wouldn't|nicht)\s+"
    rf"(?:say|claim|think|believe|report|receive|sagen|behaupten|denken|glauben)\b"
    rf"[^.!?\n]{{0,60}}\b{_MISMATCH_WORD}\b",
    re.IGNORECASE,
)
_AFFIRMED_MATCH = re.compile(
    r"\b(?:matches (?:the listing|my order)|exactly what I ordered|same as (?:listed|ordered)"
    r"|nothing (?:was|is) missing|all (?:the )?parts (?:were|are) included|fits perfectly"
    r"|entspricht (?:der bestellung|dem angebot)|wie bestellt geliefert)\b",
    re.IGNORECASE,
)
_HYPOTHETICAL_MISMATCH = re.compile(
    r"\b(?:if|unless|falls|wenn|sofern|was worried|worried that|afraid that|assumed that"
    r"|reviews said|reviews say|other buyers say)\b",
    re.IGNORECASE,
)
_ORDERED = re.compile(
    r"\b(?:order\w*|option|bought|picked|requested|selected|bestellt\w*|bestellung|gekauft|gewählt)\b",
    re.IGNORECASE,
)
_DELIVERED = re.compile(
    r"\b(?:receiv\w*|got|arriv\w*|sent|contain\w*|deliver\w*|geliefert\w*|erhalten|bekommen|enthielt)\b",
    re.IGNORECASE,
)
_CONTRAST_TOKENS = {
    "size_mismatch": re.compile(
        r"\b(?:extra[- ](?:extra[- ])?(?:small|large)|XXXS|XXS|XS|S|M|L|XL|XXL|XXXL"
        r"|small|medium|large|[2-6][0-9])\b",
        re.IGNORECASE,
    ),
    "wrong_colour": re.compile(
        r"\b(?:black|blue|brown|grey|gray|green|orange|pink|purple|red|white|yellow"
        r"|blau|braun|gelb|grau|grün|rot|schwarz|weiß)\b",
        re.IGNORECASE,
    ),
    "wrong_model": re.compile(r"\b(?:Mini|Max|Pro|Plus|Ultra|[A-Z]{2,}-?[0-9]+[A-Z0-9]*)\b"),
}
_CONTRAST_NORMALIZATION = {
    "gray": "grey", "grau": "grey", "small": "s", "medium": "m", "large": "l",
    "extra small": "xs", "extra extra small": "xxs", "extra large": "xl", "extra extra large": "xxl",
}
_COMPONENT = (
    r"(?:brackets?|screws?|manuals?|cables?|chargers?|adapters?|parts?|pieces?|components?"
    r"|accessor(?:y|ies)|mounts?|batter(?:y|ies)|covers?|clips?)"
)
_MISSING_COMPONENT = re.compile(
    rf"\b(?:no|without|missing)\s+(?:the |a |an )?{_COMPONENT}\b"
    rf"|\b{_COMPONENT}\s+(?:(?:was|were|is|are)\s+)?(?:missing|not included)\b",
    re.IGNORECASE,
)
_OFFER_ONLY = re.compile(
    r"\b(?:listing|photo|description|advertis\w*|pictured|promis\w*|order\w*|bought|selected)\b",
    re.IGNORECASE,
)
_DEFAULT_MISMATCH_CUES = {
    "size_mismatch": ("wrong size", "different size", "smaller than advertised", "larger than advertised"),
    "wrong_model": ("wrong model", "different model", "wrong version", "different version"),
    "wrong_colour": ("wrong colour", "different colour", "wrong color", "different color"),
    "not_genuine_claim": ("not genuine", "not authentic", "not issued by", "not their product"),
    "wrong_item": ("wrong item", "different item", "not the item i ordered", "wrong product"),
}
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


def _separators(profile: CategoryProfile | None) -> tuple[str, str]:
    if profile is not None and profile.category != "storage":
        language = profile.locale.split("-", 1)[0].casefold()
        if language in _COMMA_DECIMAL:
            return ",", "."
    return ".", ","


@cache
def _quantity_pattern(decimal_separator: str, group_separator: str, *, space_groups: bool = False) -> str:
    if not space_groups and (decimal_separator, group_separator) == (".", ","):
        return _QUANTITY
    decimal = re.escape(decimal_separator)
    group = re.escape(group_separator)
    by_space = rf"|[0-9]{{1,3}}(?:[{_GROUP_SPACE}][0-9]{{3}})+" if space_groups else ""
    return rf"(?:[0-9]{{1,3}}(?:{group}[0-9]{{3}})+{by_space}|[0-9]+)(?:{decimal}[0-9]+)?"


def _decimal(value: object, *, profile: CategoryProfile | None = None) -> Decimal | None:
    try:
        if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
            number = Decimal(str(value))
            return number if number.is_finite() and number >= 0 else None
        if isinstance(value, str):
            raw = value.strip().translate(_THAI_DIGITS)
            decimal, group = _separators(profile)
            if re.fullmatch(_quantity_pattern(decimal, group, space_groups=True), raw):
                ungrouped = raw.translate(_REMOVE_GROUP_SPACES)
                return Decimal(ungrouped.replace(group, "").replace(decimal, "."))
        return None
    except InvalidOperation:
        return None


@cache
def _storage_profile() -> CategoryProfile:
    return load_profile()


@cache
def _number_pattern(
    units: tuple[str, ...], *, optional: bool, separators: tuple[str, str], legacy: bool,
) -> re.Pattern[str]:
    alternatives = "|".join(re.escape(unit) for unit in sorted(units, key=len, reverse=True))
    unit_end = r"(?![a-z])" if legacy else r"(?![a-z0-9_²³])"
    whitespace = r"\s*" if legacy else rf"[{_GROUP_SPACE}\t]*"
    suffix = rf"{whitespace}({alternatives}){unit_end}"
    quantity = _quantity_pattern(*separators, space_groups=not legacy)
    if legacy:
        if optional:
            return re.compile(
                rf"(?<![\d.\-−])({quantity})(?![0-9]|\.[0-9])(?:{suffix})?", re.IGNORECASE,
            )
        return re.compile(rf"{quantity}{suffix}", re.IGNORECASE)

    # Consume or reject a number together, so a separator cannot expose a
    # prefix or suffix as another measurement in a different locale.
    pattern = rf"(?<![\d.\-−])(?<!\d[,.])({quantity})(?![0-9]|[,.][0-9])"
    return re.compile(pattern + (rf"(?:{suffix})?" if optional else suffix), re.IGNORECASE)


def _review_pattern(profile: CategoryProfile, *, strict: bool = False) -> re.Pattern[str]:
    units = tuple(
        token for name, definition in profile.units.items() for token in (name, *definition.all_aliases)
    )
    return _number_pattern(
        units, optional=True, separators=_separators(profile),
        legacy=profile.category == "storage" and not strict,
    )


def _statement_spans(text: str, *, split_concessions: bool = False) -> Iterable[tuple[int, int]]:
    start = 0
    boundaries = _CATEGORICAL_CLAUSES if split_concessions else _SENTENCES
    for ending in boundaries.finditer(text):
        yield start, ending.end()
        start = ending.end()
    if start < len(text):
        yield start, len(text)


def _source_mentions(
    text: str, profile: CategoryProfile, *, strict: bool = False, for_measurement: bool = False,
) -> Iterable[re.Match[str]]:
    pattern = _review_pattern(profile, strict=strict)
    ranges = _statement_spans(text) if for_measurement else ((0, len(text)),)
    for start, end in ranges:
        if for_measurement and _MODEL_INSTRUCTION.search(text[start:end]):
            continue
        for mention in pattern.finditer(text, start, end):
            if strict or profile.category != "storage":
                before = text[max(0, mention.start() - 64):mention.start()]
                if (
                    _SPACED_DIGITS_BEFORE.search(before) or _RANGE_BEFORE.search(before)
                    or _BETWEEN_BEFORE.search(before) or _RANGE_AFTER.match(text, mention.end())
                    or (_BETWEEN_START.search(before) and _AND_NUMBER.match(text, mention.end()))
                ):
                    continue
            yield mention


def _quote_spans(text: str, quote: str) -> Iterable[tuple[int, int]]:
    if not quote.strip():
        return
    start = text.find(quote)
    while start >= 0:
        yield start, start + len(quote)
        start = text.find(quote, start + 1)


def plain_quote_supported(text: str, quote: str) -> bool:
    """Verify a verbatim quote outside a model-directed source sentence."""
    directed_spans = (
        (start, end) for start, end in _statement_spans(text)
        if _MODEL_INSTRUCTION.search(text[start:end])
    )
    directed = next(directed_spans, None)
    for start, end in _quote_spans(text, quote):
        while directed is not None and directed[1] <= start:
            directed = next(directed_spans, None)
        if directed is None or end <= directed[0]:
            return True
    return False


def advertised_amounts(text: str, profile: CategoryProfile) -> set[Decimal]:
    """Find complete advertised numbers with explicit units, in the profile's promise unit."""
    if profile.promise_unit is None:
        return set()
    promise_factor = profile.units[profile.promise_unit].promise_factor
    assert promise_factor is not None
    amounts = set()
    normalized = text.translate(_THAI_DIGITS)
    for mention in _source_mentions(normalized, profile, strict=True):
        quantity, unit = mention.groups()
        if unit is None or _OTHER_CAPACITY_AFTER.match(normalized[mention.end():]):
            continue
        definition = _unit_definition(_unit_key(unit, profile), profile)
        value = _decimal(quantity, profile=profile)
        if definition is not None and definition.promise_factor is not None and value is not None:
            amounts.add(value * definition.promise_factor / promise_factor)
    return amounts


def quoted_number_units(
    text: str, quote: str, quantity: object, *, profile: CategoryProfile, for_measurement: bool = True,
) -> set[str]:
    """Find original number-plus-unit tokens wholly inside an exact evidence quote."""
    selected = _decimal(quantity, profile=profile)
    spans = list(_quote_spans(text, quote))
    if selected is None or not spans:
        return set()
    units = set()
    next_span = iter(spans)
    span = next(next_span)
    normalized = text.translate(_THAI_DIGITS)
    for mention in _source_mentions(normalized, profile, strict=True, for_measurement=for_measurement):
        while span[1] < mention.end():
            span = next(next_span, None)
            if span is None:
                return units
        number, unit = mention.groups()
        if (
            span[0] <= mention.start()
            and _decimal(number, profile=profile) == selected
            and (not for_measurement or _measurement_context_supported(mention, profile))
            and not (unit and _OTHER_CAPACITY_AFTER.match(mention.string[mention.end():]))
        ):
            units.add(_unit_key(unit, profile))
    return units


def _contrasting_values(quote: str, tokens: re.Pattern[str]) -> bool:
    order = _ORDERED.search(quote)
    delivery = _DELIVERED.search(quote)
    if delivery is None:
        return False
    contrast = re.search(r"\binstead of\b", quote, flags=re.IGNORECASE)
    if contrast:
        actual = tokens.findall(quote[:contrast.start()])
        expected = tokens.findall(quote[contrast.end():])
    elif order is None:
        return False
    elif order.start() < delivery.start():
        expected = tokens.findall(quote[order.end():delivery.start()])
        if not expected:
            expected = tokens.findall(quote[:order.start()])[-1:]
        actual = tokens.findall(quote[delivery.end():])
    else:
        expected = tokens.findall(quote[order.end():])
        actual = tokens.findall(quote[delivery.end():order.start()])
        if not actual:
            actual = tokens.findall(quote[:delivery.start()])[-1:]
    if not expected or not actual:
        return False
    expected_value = expected[0].casefold().replace("-", " ")
    actual_value = actual[0].casefold().replace("-", " ")
    return _CONTRAST_NORMALIZATION.get(expected_value, expected_value) != _CONTRAST_NORMALIZATION.get(
        actual_value, actual_value,
    )


def _categorical_assertion(quote: str, mismatch_type: str, profile: CategoryProfile | None) -> bool:
    if mismatch_type == "missing_parts" and _OFFER_ONLY.search(quote) and not _DELIVERED.search(quote):
        return False
    candidate = quote.casefold()
    configured = profile.mismatch_cues.get(mismatch_type, {}) if profile is not None else {}
    cues = (*_DEFAULT_MISMATCH_CUES.get(mismatch_type, ()), *(
        cue for phrases in configured.values() for cue in phrases
    ))
    if any(cue.casefold() in candidate for cue in cues):
        return True
    if mismatch_type == "missing_parts":
        return bool(_MISSING_COMPONENT.search(quote))
    tokens = _CONTRAST_TOKENS.get(mismatch_type)
    return tokens is not None and _contrasting_values(quote, tokens)


def _supporting_statement_block(quote: str, mismatch_type: str, profile: CategoryProfile | None) -> bool:
    supported: list[str] = []
    for start, end in _statement_spans(quote, split_concessions=True):
        statement = quote[start:end]
        if (
            statement.rstrip().endswith(("?", "？")) or _NEGATED_MISMATCH.search(statement)
            or _AFFIRMED_MATCH.search(statement) or _HYPOTHETICAL_MISMATCH.search(statement)
        ):
            if supported and _categorical_assertion(" ".join(supported), mismatch_type, profile):
                return True
            supported.clear()
        else:
            supported.append(statement)
    return bool(supported and _categorical_assertion(" ".join(supported), mismatch_type, profile))


def categorical_quote_supported(
    text: str, quote: str, *, mismatch_type: str, profile: CategoryProfile | None = None,
) -> bool:
    """Require recognizable affirmative evidence in a complete copied statement."""
    folded = text.casefold()
    if _MODEL_INSTRUCTION.search(text) or ("_" in mismatch_type and mismatch_type.casefold() in folded):
        return False
    if not _supporting_statement_block(quote, mismatch_type, profile):
        return False
    for start, end in _quote_spans(text, quote):
        before = text[:start].rstrip(" \t\r")
        after = text[end:].lstrip(" \t\r")
        if before and before[-1] not in _SENTENCE_END + "\n":
            continue
        if after.startswith(("?", "？")):
            continue
        if (
            not after or after[0] in _SENTENCE_END + "\n" or quote.rstrip()[-1] in _SENTENCE_END
            or _CONCESSIVE.match(("," if quote.rstrip().endswith(",") else "") + after)
        ):
            return True
    return False


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

    if profile.category == "storage":
        option_pattern = _number_pattern(
            tuple(profile.units), optional=False, separators=(".", ","), legacy=True,
        )
        matches = {name.casefold() for name in option_pattern.findall(measurement_text.translate(_THAI_DIGITS))}
    else:
        matches = {
            _unit_key(unit, profile)
            for _, unit in _review_pattern(profile).findall(measurement_text.translate(_THAI_DIGITS))
            if unit
        }
    return matches.pop() if len(matches) == 1 else ""


def _measured_value(
    quantity: object, unit: object, measurement_text: str, profile: CategoryProfile,
) -> Decimal | None:
    number = _decimal(quantity, profile=profile)
    definition = _unit_definition(_measurement_unit(unit, measurement_text, profile), profile)
    if number is None or definition is None:
        return None
    return number * max(definition.measurement_factors)


def measured_bytes(quantity: object, unit: object, capacity_text: str) -> Decimal | None:
    """Convert a captured storage measurement using the storage profile."""
    return _measured_value(quantity, unit, capacity_text, _storage_profile())


def _measurement_context_supported(mention: re.Match[str], profile: CategoryProfile) -> bool:
    if not profile.measurement_exclusions and not profile.completed_measurement_cues:
        return True
    # Keep the phrase attached to its original reading. A separate partial
    # reading in the same review does not invalidate a completed measurement.
    window_before = mention.string[max(0, mention.start() - 180):mention.start()]
    window_after = mention.string[mention.end():mention.end() + 180]
    preceding = _CONTEXT_BREAK.split(window_before)[-1].casefold()
    following = _CONTEXT_BREAK.split(window_after, maxsplit=1)[0].casefold()
    pattern = _review_pattern(profile, strict=True)

    def nearby(cues: Translations, before: str, after: str, *, affirmative: bool = False) -> bool:
        for phrases in cues.values():
            for phrase in phrases:
                marker = phrase.casefold()
                prefix, delimiter, tail = before.rpartition(marker)
                if (
                    delimiter and not any(unit for _, unit in pattern.findall(tail))
                    and (not affirmative or not denied(prefix, tail))
                ):
                    return True
                head, delimiter, suffix = after.partition(marker)
                if (
                    delimiter and not any(unit for _, unit in pattern.findall(head))
                    and (not affirmative or not denied(head, suffix))
                ):
                    return True
        return False

    def denied(before: str, after: str) -> bool:
        return bool(_COMPLETION_DENIAL_BEFORE.search(before) or _COMPLETION_DENIAL_AFTER.match(after))

    if nearby(profile.measurement_exclusions, preceding, following):
        return False
    if not profile.completed_measurement_cues:
        return True
    # A comma can separate a completion phrase from its result, but other
    # conjunctions and sentence boundaries keep separate tests apart.
    earlier = _CONTEXT_BREAK.split(window_before.rstrip(" ,，"))[-1].casefold()
    later = _CONTEXT_BREAK.split(window_after.lstrip(" ,，"), maxsplit=1)[0].casefold()
    return nearby(profile.completed_measurement_cues, earlier, later, affirmative=True)


def _non_measurement(
    mention: re.Match[str], previous_end: int, promised: Decimal | None,
    profile: CategoryProfile,
) -> bool:
    number, unit = mention.groups()
    before = mention.string[previous_end:mention.start()]
    after = mention.string[mention.end():]
    if not _measurement_context_supported(mention, profile):
        return True
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
    actual_number = _review_pattern(profile, strict=True).match(after, actual.end()) if actual else None
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
    profile = profile or _storage_profile()
    selected = _decimal(quantity, profile=profile)
    if selected is None:
        return set()
    normalized = text.translate(_THAI_DIGITS)
    previous_end = 0
    units = set()
    for mention in _source_mentions(
        normalized, profile, strict=measurements_only, for_measurement=measurements_only,
    ):
        number, unit = mention.groups()
        if _decimal(number, profile=profile) == selected and (
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
    mentions = list(_source_mentions(normalized, profile, strict=True, for_measurement=True))
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
    text: str, quote: str, finding: dict, measurement_text: str, profile: CategoryProfile,
) -> bool:
    unit = _measurement_unit(finding.get("unit"), measurement_text, profile)
    written_units = quoted_number_units(text, quote, finding.get("quantity"), profile=profile)
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
    else:
        review_text = review.get("text", "")
        supported_quote = (
            categorical_quote_supported(review_text, quote, mismatch_type=mismatch_type, profile=profile)
            if mismatch_type else plain_quote_supported(review_text, quote)
        )
        if not supported_quote:
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
    quantity = None if mismatch_type else _decimal(finding.get("quantity"), profile=profile)
    image_type = _label(finding.get("image_type"))
    number = None
    measurable = role in profile.measured_roles and not mismatch_type
    if finding.get("read_status", "ok") == "ok" and measurable:
        if image_ref:
            supported = storage and role == "test_result" and image_type in _COMPLETED_IMAGE_TYPES
        else:
            supported = _quote_supports_number(
                review["text"], quote, finding, measurement_text, profile,
            )
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
            and (
                plain_quote_supported(text, quote)
                if quote else finding.get("complaint") == "none"
            )
        )

    def valid_observation(finding: dict) -> bool:
        complaint = finding.get("mismatch_type") or finding.get("complaint")
        quote = finding.get("quote") or ""
        if complaint != "none" and (complaint not in profile.mismatch_types or not quote.strip()):
            return False
        mismatch_type = _mismatch_type(finding, profile)
        if mismatch_type:
            return categorical_quote_supported(text, quote, mismatch_type=mismatch_type, profile=profile)
        quantity = finding.get("quantity")
        if _role(finding) in profile.measured_roles and quantity is not None:
            unit = _unit_key(finding.get("unit"), profile)
            return bool(unit) and unit in quoted_number_units(text, quote, quantity, profile=profile)
        return True

    text_findings = [finding for finding in findings if not finding.get("image_ref")]
    if profile.category == "storage":
        return any(map(checked, text_findings))
    return bool(text_findings) and all(
        checked(finding)
        and finding.get("option_id") == option_id
        and valid_observation(finding)
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
