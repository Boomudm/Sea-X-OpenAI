"""Validated category knowledge for deterministic review rules."""

import re
from decimal import Decimal
from importlib.resources import files
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

_CATEGORY_PATTERN = r"[a-z][a-z0-9_-]*"
PENDING_APPROVAL = "pending human review"
CategoryId = Annotated[str, StringConstraints(pattern=rf"^{_CATEGORY_PATTERN}$")]
Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*$")]
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
LanguageTag = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8})*$")]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
Factor = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]
Translations = dict[LanguageTag, tuple[NonEmptyText, ...]]


class UnitConversion(BaseModel):
    """Factors convert the stated unit to the profile's common comparison unit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Interpret an ambiguous reading conservatively by using the largest factor.
    measurement_factors: tuple[Factor, ...] = Field(min_length=1)
    promise_factor: Factor | None = None
    aliases: tuple[NonEmptyText, ...] = ()
    aliases_by_language: Translations = Field(default_factory=dict)

    @property
    def all_aliases(self) -> tuple[str, ...]:
        aliases: dict[str, str] = {}
        for spellings in (self.aliases, *self.aliases_by_language.values()):
            for spelling in spellings:
                aliases.setdefault(spelling.casefold(), spelling)
        return tuple(aliases.values())


class MarketplaceFields(BaseModel):
    """Input field names to map into the review and option records."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    variation: NonEmptyText = "variation_label"
    was_price: NonEmptyText = "was_thb"
    now_price: NonEmptyText = "now_thb"
    buyer: NonEmptyText = "buyer_masked"
    review_text: NonEmptyText = "text"

    @model_validator(mode="after")
    def validate_mappings(self) -> Self:
        option_fields = {
            "variation_label": self.variation,
            "was_thb": self.was_price,
            "now_thb": self.now_price,
        }
        review_fields = {
            "variation_label": self.variation,
            "buyer_masked": self.buyer,
            "text": self.review_text,
        }
        option_keys = set(option_fields) | {
            "option_id", "promise_value", "promise_gb", "measurement_text",
            "capacity_text", "measurement_unclear", "capacity_unclear",
        }
        review_keys = set(review_fields) | {"review_id", "option_id", "date", "stars", "tags", "images"}
        for mappings, keys in ((option_fields, option_keys), (review_fields, review_keys)):
            for canonical, source in mappings.items():
                if source != canonical and source in keys:
                    raise ValueError(f"{source!r} is a reserved canonical field")
        if len({self.variation, self.was_price, self.now_price}) != 3:
            raise ValueError("Option field names must be distinct")
        if len({self.variation, self.buyer, self.review_text}) != 3:
            raise ValueError("Review field names must be distinct")
        return self


class CategoryProfile(BaseModel):
    """A category's units, measurement rules, and reader guidance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    category: CategoryId
    version: NonEmptyText = "1"
    attribute: NonEmptyText
    measurement_mode: Literal["numeric", "categorical"] = "numeric"
    promise_unit: NonEmptyText | None = None
    units: dict[NonEmptyText, UnitConversion] = Field(default_factory=dict)
    tolerance: Decimal = Field(default=Decimal(1), gt=0, le=1, allow_inf_nan=False)
    maximum_ratio: Decimal | None = Field(default=None, ge=1, allow_inf_nan=False)
    baseline_mismatch_rate: Decimal | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    review_roles: tuple[Identifier, ...] = Field(min_length=1)
    measured_roles: tuple[Identifier, ...] = ()
    normal_display_text: NonEmptyText
    mismatch_types: tuple[Identifier, ...] = Field(min_length=1)
    prompt_traps: tuple[NonEmptyText, ...] = ()
    currency: Currency = "THB"
    price_per_unit: NonEmptyText | None = None
    locale: LanguageTag = "th-TH"
    languages: tuple[LanguageTag, ...] = Field(default=("th", "en"), min_length=1)
    prompt_traps_by_language: Translations = Field(default_factory=dict)
    measurement_exclusions: Translations = Field(default_factory=dict)
    completed_measurement_cues: Translations = Field(default_factory=dict)
    mismatch_cues: dict[Identifier, Translations] = Field(default_factory=dict)
    marketplace_fields: MarketplaceFields = Field(default_factory=MarketplaceFields)
    official_spec_urls: tuple[NonEmptyText, ...] = ()
    approved_by: NonEmptyText

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        if self.measurement_mode == "numeric":
            promise = self.units.get(self.promise_unit) if self.promise_unit else None
            if promise is None or promise.promise_factor is None:
                raise ValueError("promise_unit must refer to a unit with a promise_factor")
            if "tolerance" not in self.model_fields_set:
                raise ValueError("tolerance is required for numeric profiles")
            if not self.measured_roles:
                raise ValueError("measured_roles is required for numeric profiles")
        elif (
            self.promise_unit is not None or self.units or self.measured_roles
            or self.maximum_ratio is not None or self.measurement_exclusions
            or self.completed_measurement_cues
        ):
            raise ValueError("Categorical profiles cannot declare numeric measurement rules")

        if not set(self.measured_roles).issubset(self.review_roles):
            raise ValueError("measured_roles must be listed in review_roles")

        if self.maximum_ratio is not None and any(
            len(set(conversion.measurement_factors)) > 1 for conversion in self.units.values()
        ):
            raise ValueError("maximum_ratio requires unambiguous measurement factors")

        if not set(self.mismatch_cues).issubset(self.mismatch_types):
            raise ValueError("Mismatch cues must belong to a configured mismatch type")

        languages = {language.casefold() for language in self.languages}
        localized = (
            *self.prompt_traps_by_language,
            *self.measurement_exclusions,
            *self.completed_measurement_cues,
            *(tag for cues in self.mismatch_cues.values() for tag in cues),
            *(tag for unit in self.units.values() for tag in unit.aliases_by_language),
        )
        if any(language.casefold() not in languages for language in localized):
            raise ValueError("Localized aliases and traps must use a declared language")

        seen = {"none"}
        for unit, conversion in self.units.items():
            for token in (unit, *conversion.all_aliases):
                key = token.casefold()
                if key in seen:
                    raise ValueError(f"Duplicate unit token or reserved name: {token!r}")
                seen.add(key)
        return self


class ProfileApprovalError(ValueError):
    """A draft needs an explicit opt-in before analysis."""


def require_profile_approval(profile: CategoryProfile, *, allow_draft: bool = False) -> CategoryProfile:
    if profile.approved_by.casefold() == PENDING_APPROVAL and not allow_draft:
        raise ProfileApprovalError(f"Profile {profile.category!r} is pending human review. Use --allow-draft to try it.")
    return profile


def load_profile(category: str = "storage", *, allow_draft: bool = False) -> CategoryProfile:
    """Load a built-in category by ID from a checkout or an installed wheel."""
    if re.fullmatch(_CATEGORY_PATTERN, category) is None:
        raise ValueError(f"Invalid category profile name: {category!r}")

    filename = f"{category}.json"
    package_dir = Path(__file__).resolve().parent
    if package_dir.parent.name == "src":
        source = package_dir.parent.parent / "profiles" / filename
    else:
        source = files(__package__).joinpath("profile_data", filename)

    if not source.is_file():
        raise FileNotFoundError(f"No category profile named {category!r}")
    profile = CategoryProfile.model_validate_json(source.read_bytes())
    if profile.category != category:
        raise ValueError(f"Profile category {profile.category!r} does not match {category!r}")
    return require_profile_approval(profile, allow_draft=allow_draft)
