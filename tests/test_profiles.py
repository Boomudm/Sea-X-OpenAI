from decimal import Decimal

import pytest
from pydantic import ValidationError

from trongpok.profiles import CategoryProfile, load_profile


def test_storage_is_the_default_profile_outside_the_checkout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    profile = load_profile()

    assert profile.category == "storage"
    assert profile.attribute == "capacity"
    assert profile.tolerance == Decimal("0.85")
    assert profile.promise_unit == "GB"
    assert profile.units["TB"].promise_factor / profile.units["GB"].promise_factor == 1000
    assert set(profile.units["GB"].measurement_factors) == {10**9, 2**30}
    assert set(profile.units["TB"].measurement_factors) == {10**12, 2**40}
    assert profile.measured_roles == ("delivered_capacity", "fails_after", "test_result")
    assert "57–59" in profile.normal_display_text


@pytest.mark.parametrize("name", ["../storage", "storage.json", "STORAGE"])
def test_load_profile_rejects_names_that_are_not_category_ids(name):
    with pytest.raises(ValueError, match="Invalid category profile name"):
        load_profile(name)


def test_load_profile_identifies_a_missing_category():
    with pytest.raises(FileNotFoundError, match="missing_category"):
        load_profile("missing_category")


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"tolerance": "1.01"}, "tolerance"),
        ({"tolerance": 0}, "tolerance"),
        ({"promise_unit": "Wh"}, "promise_unit"),
        ({"measured_roles": ["unlisted_role"]}, "measured_roles"),
        ({"normal_display_text": " "}, "normal_display_text"),
        ({"approved_by": " "}, "approved_by"),
        ({"unexpected": True}, "unexpected"),
    ],
)
def test_category_profile_rejects_invalid_fields(changes, message):
    data = load_profile().model_dump()
    with pytest.raises(ValidationError, match=message):
        CategoryProfile.model_validate({**data, **changes})


def test_category_profile_rejects_nonpositive_measurement_factors():
    data = load_profile().model_dump()
    data["units"]["GB"]["measurement_factors"] = [0, 2**30]
    with pytest.raises(ValidationError, match="measurement_factors"):
        CategoryProfile.model_validate(data)


def test_category_profile_rejects_unit_aliases_collision_ignoring_case():
    data = load_profile().model_dump()
    data["units"]["TB"]["aliases"] = ["gB"]
    with pytest.raises(ValidationError, match="Duplicate unit token"):
        CategoryProfile.model_validate(data)
