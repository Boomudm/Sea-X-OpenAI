"""Shared JSON record shapes from AGENTS.md §4.10."""
from typing import Literal, NotRequired, TypedDict

type Number = int | float
type Question = Literal["Q1", "Q2", "Q3", "Q4", "Q5", "grey"]
type Colour = Literal["RED", "YELLOW", "GREEN", "GREY"]


class Option(TypedDict):
    option_id: str
    variation_label: str
    capacity_text: str
    promise_gb: Number | None
    was_thb: Number | None
    now_thb: Number


class Review(TypedDict):
    review_id: str
    variation_label: str
    option_id: str | None
    buyer_masked: str
    date: str
    stars: int
    text: str
    tags: list[str]
    images: list[str]


class Listing(TypedDict):
    listing_id: str
    url: str
    captured_at: str
    title: str
    spec_text: str
    description: str
    listing_images: list[str]
    options: list[Option]
    reviews: list[Review]


class BrandPage(TypedDict):
    url: str
    date: str
    capacities_gb: list[Number]


class MarketRange(TypedDict):
    capacity_gb: Number
    low_thb_per_gb: Number
    high_thb_per_gb: Number
    offers_used: int
    date: str


class MallSource(TypedDict):
    url: str
    date: str
    capacity_gb: Number
    now_thb: Number


class KBRow(TypedDict):
    brand: str
    aliases: list[str]
    product_line: str
    type: str
    mall_capacities_gb: list[Number]
    brand_page: BrandPage | None
    market_range: list[MarketRange]
    mall_sources: list[MallSource]
    expected_display: str
    approved_by: str


class Finding(TypedDict):
    review_id: str
    option_id: str
    complaint: Literal["capacity_short", "capacity_no_number", "wrong_item", "other", "none"]
    quantity: Number | None
    unit: Literal["MB", "GB", "TB", "GiB", "TiB", "none"]
    role: str
    bytes: Number | None
    ratio: Number | None
    quote: str
    image_ref: str | None
    image_type: str | None
    read_status: Literal["ok", "cannot_read"]


class Adjustment(TypedDict):
    points: int
    reason: str


class Confidence(TypedDict):
    score: int
    base: int
    adjustments: list[Adjustment]
    missing_evidence: list[str]
    rounds: int


class ReviewerDecision(TypedDict):
    decision: Literal["accepted", "dismissed"]
    reason: str
    at: str


class Flag(TypedDict):
    listing_id: str
    option_id: str
    colour: Colour
    deciding: Question
    path: list[str]
    reasons: list[str]
    evidence: list[dict]
    verdict: Literal["unsure", "mismatch", "no_mismatch"]
    confidence: Confidence
    reviewer_decision: ReviewerDecision | None


class Claim(TypedDict):
    option_id: str
    promise_gb: Number | None
    capacity_unclear: bool
    brand: NotRequired[str]
    product_line: NotRequired[str]
    type: NotRequired[str]
