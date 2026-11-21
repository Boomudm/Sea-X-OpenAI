"""Pydantic models for the frozen contracts and internal structured reads."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Complaint = Literal[
    "capacity_short",
    "capacity_no_number",
    "wrong_item",
    "other",
    "none",
]
Unit = Literal["MB", "GB", "TB", "GiB", "TiB", "none"]
Role = Literal[
    "delivered capacity",
    "fails after",
    "OS-reported",
    "test result",
    "promise",
    "free space",
    "speed",
    "other",
]
ImageType = Literal[
    "OS Properties",
    "completed H2testw/F3",
    "speed test",
    "packaging/model code",
    "other",
]
ReadStatus = Literal["ok", "cannot_read"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Option(StrictModel):
    option_id: str
    variation_label: str
    capacity_text: str
    promise_gb: float | None = None
    was_thb: float | None = None
    now_thb: float


class Review(StrictModel):
    review_id: str
    variation_label: str
    option_id: str | None = None
    buyer_masked: str
    date: str
    stars: int = Field(ge=1, le=5)
    text: str
    tags: list[str]
    images: list[str]


class Listing(StrictModel):
    listing_id: str
    url: str
    captured_at: str
    title: str
    spec_text: str
    description: str
    listing_images: list[str]
    options: list[Option]
    reviews: list[Review]


class ClaimDraft(StrictModel):
    option_id: str
    promise_gb: float | None
    capacity_unclear: bool


class ClaimDraftBatch(StrictModel):
    options: list[ClaimDraft]


class ClaimOption(StrictModel):
    option_id: str
    promise_gb: float | None
    capacity_unclear: bool


class ClaimOutput(StrictModel):
    listing_id: str
    options: list[ClaimOption]


class ReviewDraft(StrictModel):
    review_id: str
    option_id: str
    complaint: Complaint
    quantity: float | None
    unit: Unit
    role: Role
    quote: str


class ReviewDraftBatch(StrictModel):
    findings: list[ReviewDraft]


class Finding(StrictModel):
    review_id: str
    option_id: str
    complaint: Complaint
    quantity: float | None
    unit: Unit
    role: Role
    bytes: int | None
    ratio: float | None
    quote: str
    image_ref: str | None
    image_type: ImageType | None
    read_status: ReadStatus


class ImageDraft(StrictModel):
    image_ref: str
    review_id: str | None
    option_id: str | None
    image_type: ImageType
    quantity: float | None
    unit: Unit
    role: Role
    visible_text: str | None
    read_status: ReadStatus


class ImageDraftBatch(StrictModel):
    images: list[ImageDraft]


class ImageReading(StrictModel):
    image_ref: str
    review_id: str | None
    option_id: str | None
    image_type: ImageType
    quantity: float | None
    unit: Unit
    role: Role
    bytes: int | None
    ratio: float | None
    visible_text: str | None
    read_status: ReadStatus


ChallengeKind = Literal[
    "gb_vs_gib",
    "wrong_option",
    "flash_sale",
    "duplicate_buyer",
    "other",
]


class Challenge(StrictModel):
    kind: ChallengeKind
    reason: str
    quote: str | None
    source: str | None


class ChallengeBatch(StrictModel):
    challenges: list[Challenge]


class ConfidenceAssessment(StrictModel):
    challenges: list[Challenge]
    rounds: Literal[1] = 1


JsonObject = dict[str, Any]
