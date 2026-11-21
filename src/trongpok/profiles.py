"""Validated category knowledge for deterministic review rules."""

import re
from decimal import Decimal
from importlib.resources import files
from pathlib import Path
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

_CATEGORY_PATTERN = r"[a-z][a-z0-9_-]*"
CategoryId = Annotated[str, StringConstraints(pattern=rf"^{_CATEGORY_PATTERN}$")]
Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*$")]
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Factor = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]


class UnitConversion(BaseModel):
    """Factors convert the stated unit to the profile's common comparison unit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Interpret an ambiguous reading conservatively by using the largest factor.
    measurement_factors: tuple[Factor, ...] = Field(min_length=1)
    promise_factor: Factor | None = None
    aliases: tuple[NonEmptyText, ...] = ()


class CategoryProfile(BaseModel):
    """A category's units, measurement rules, and reader guidance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    category: CategoryId
    attribute: NonEmptyText
    promise_unit: NonEmptyText
    units: dict[NonEmptyText, UnitConversion] = Field(min_length=1)
    tolerance: Decimal = Field(gt=0, le=1, allow_inf_nan=False)
    review_roles: tuple[Identifier, ...] = Field(min_length=1)
    measured_roles: tuple[Identifier, ...] = Field(min_length=1)
    normal_display_text: NonEmptyText
    mismatch_types: tuple[Identifier, ...] = Field(min_length=1)
    prompt_traps: tuple[NonEmptyText, ...] = ()
    approved_by: NonEmptyText

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        promise = self.units.get(self.promise_unit)
        if promise is None or promise.promise_factor is None:
            raise ValueError("promise_unit must refer to a unit with a promise_factor")

        if not set(self.measured_roles).issubset(self.review_roles):
            raise ValueError("measured_roles must be listed in review_roles")

        seen = {"none"}
        for unit, conversion in self.units.items():
            for token in (unit, *conversion.aliases):
                key = token.casefold()
                if key in seen:
                    raise ValueError(f"Duplicate unit token or reserved name: {token!r}")
                seen.add(key)
        return self


def load_profile(category: str = "storage") -> CategoryProfile:
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
    return profile
