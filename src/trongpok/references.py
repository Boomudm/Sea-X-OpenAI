"""Category-specific references supplied to the deterministic price and spec rules."""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

type Record = Mapping[str, Any]
type Promise = Decimal | str | None


@dataclass(frozen=True)
class MarketRange:
    low_per_unit: Decimal
    high_per_unit: Decimal
    currency: str
    unit: str
    date: str
    sources: tuple[Record, ...]

    def flag_evidence(self, promise: Decimal, option: Record) -> dict:
        """Show captured prices and the total prices for the promised quantity."""
        currency = self.currency.lower()
        was_key = f"was_{currency}"
        now_key = f"now_{currency}"
        was = _captured_price(option.get(was_key))
        now = _captured_price(option.get(now_key))
        return {
            "source": "market_range",
            was_key: was,
            now_key: now,
            f"low_{currency}": float(self.low_per_unit * promise),
            f"high_{currency}": float(self.high_per_unit * promise),
            "date": self.date,
            "sources": list(self.sources),
        }


@dataclass(frozen=True)
class OfficialSpec:
    values: tuple[Decimal | str, ...]
    evidence: Record
    promise_key: str | None = None

    def flag_evidence(self, promise: Decimal | str) -> dict:
        record = dict(self.evidence)
        if self.promise_key is not None:
            record[self.promise_key] = float(promise) if isinstance(promise, Decimal) else promise
        return record


@dataclass(frozen=True)
class ReferenceEvidence:
    matched: bool = False
    market: MarketRange | None = None
    thin: bool = False
    official: OfficialSpec | None = None
    mall: OfficialSpec | None = None


class ReferenceSource(Protocol):
    def resolve(self, listing: Record, claim: Record, promise: Promise) -> ReferenceEvidence:
        """Look up a captured market range and official variant list for the claim."""
        ...


class NoReferenceSource:
    """Leave market and manufacturer comparisons unavailable for unadapted categories."""

    def resolve(self, listing: Record, claim: Record, promise: Promise) -> ReferenceEvidence:
        return ReferenceEvidence()


def _identity(value: object) -> str:
    return str(value or "").strip().casefold()


def _claims_match(claim: Record, row: Record) -> bool:
    brand = _identity(claim.get("brand"))
    line = _identity(claim.get("product_line"))
    category = _identity(claim.get("type"))
    return (
        bool(brand and line and category)
        and brand in {_identity(name) for name in (row["brand"], *row["aliases"])}
        and line == _identity(row["product_line"])
        and category == _identity(row["type"])
    )


def _capture_matches(listing: Record, row: Record) -> bool:
    title = _identity(listing.get("title"))
    spec = _identity(listing.get("spec_text"))

    def mentions(value: object, text: str) -> bool:
        name = _identity(value)
        return bool(name and re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text))

    return (
        mentions(row["product_line"], title)
        and mentions(row["type"], spec)
        and any(mentions(name, title) for name in (row["brand"], *row["aliases"]))
    )


def reference_number(value: object) -> Decimal | None:
    """Parse a finite saved offer price or size without changing decimal boundaries."""
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _captured_price(value: object) -> int | float | str | None:
    if not isinstance(value, (int, float, str)):
        return None
    number = reference_number(value)
    return value if number is not None and number >= 0 else None


def _market_range(row: Record, promise: Decimal) -> tuple[MarketRange | None, bool]:
    ranges = [
        band for band in row["market_range"]
        if reference_number(band["capacity_gb"]) == promise
    ]
    if len(ranges) != 1:
        return None, False

    band = ranges[0]
    sources = tuple(
        source for source in row["mall_sources"]
        if reference_number(source["capacity_gb"]) == promise and source.get("url")
    )
    source_count = len({source["url"] for source in sources})
    thin = min(band["offers_used"], source_count) < 3
    low = reference_number(band["low_thb_per_gb"])
    high = reference_number(band["high_thb_per_gb"])
    if thin or low is None or high is None or not 0 < low <= high:
        return None, thin

    return MarketRange(low, high, "THB", "GB", band["date"], sources), False


def _spec_values(values: Iterable[object]) -> tuple[Decimal, ...]:
    return tuple(number for value in values if (number := reference_number(value)) is not None)


class StorageReferenceSource:
    """Adapt the approved storage knowledge base and preserve its evidence format."""

    def __init__(self, kb_rows: Iterable[Record]) -> None:
        self._rows = tuple(
            row for row in kb_rows
            if _identity(row.get("approved_by")) not in {"", "pending human review"}
        )

    def resolve(self, listing: Record, claim: Record, promise: Promise) -> ReferenceEvidence:
        has_claim_identity = any(claim.get(key) for key in ("brand", "product_line", "type"))
        if has_claim_identity:
            matches = [row for row in self._rows if _claims_match(claim, row)]
        else:
            matches = [row for row in self._rows if _capture_matches(listing, row)]
        if len(matches) != 1:
            return ReferenceEvidence()

        row = matches[0]
        market, thin = _market_range(row, promise) if isinstance(promise, Decimal) else (None, False)
        page = row["brand_page"]
        official = None
        if page and page["date"] and page["url"] and page["capacities_gb"]:
            values = _spec_values(page["capacities_gb"])
            if values:
                official = OfficialSpec(values, {**page, "source": "brand_page"}, "promise_gb")

        mall = None
        capacities = row["mall_capacities_gb"]
        if values := _spec_values(capacities):
            mall = OfficialSpec(values, {
                "source": "mall_capacities",
                "capacities_gb": capacities,
                "sources": row["mall_sources"],
            })
        return ReferenceEvidence(matched=True, market=market, thin=thin, official=official, mall=mall)


def reference_source_for(category: str, kb_rows: Iterable[Record] = ()) -> ReferenceSource:
    if category == "storage":
        return StorageReferenceSource(kb_rows)
    return NoReferenceSource()
