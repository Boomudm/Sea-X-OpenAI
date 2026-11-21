import pytest

from trongpok.capture import normalize_marketplace_fields
from trongpok.errors import ReaderInputError
from trongpok.profiles import load_profile
from trongpok.publication import publish_flag


def test_capture_rejects_conflicting_values_for_mapped_variation():
    profile = load_profile("clothing", allow_draft=True)
    listing = {
        "options": [{"variation_label": "L", profile.marketplace_fields.variation: "M"}],
        "reviews": [],
    }

    with pytest.raises(ReaderInputError, match="Conflicting marketplace field"):
        normalize_marketplace_fields(listing, profile)


def test_public_flag_masks_buyer_and_omits_restricted_words_without_mutating_sources():
    flag = {
        "listing_id": "sample-listing",
        "colour": "RED",
        "evidence": [{"buyer_masked": "Unmasked Person*", "quote": "Measured 3 m. Looks FAKE."}],
        "confidence": {"adjustments": [{"reason": "May suggest fraud."}]},
    }

    published = publish_flag(flag)

    assert published["listing_id"] == flag["listing_id"]
    assert published["colour"] == flag["colour"]
    assert published["evidence"][0]["buyer_masked"].endswith("***")
    assert "Unmasked Person" not in str(published)
    assert published["evidence"][0]["quote"] == "Measured 3 m. Looks [word omitted]."
    assert published["confidence"]["adjustments"][0]["reason"] == "May suggest [word omitted]."
    assert flag["evidence"][0]["quote"] == "Measured 3 m. Looks FAKE."
