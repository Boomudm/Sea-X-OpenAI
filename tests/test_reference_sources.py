"""Verify the reference inputs available to the deterministic review rules."""

from decimal import Decimal

import pytest

from trongpok.references import reference_source_for


@pytest.fixture
def approved_reference():
    return {
        "brand": "Example Storage",
        "aliases": ["Example"],
        "product_line": "Pocket Drive",
        "type": "USB flash drive",
        "approved_by": "Sample reviewer",
        "brand_page": {
            "url": "https://example.invalid/spec",
            "date": "2026-11-21",
            "capacities_gb": [64, 128],
        },
        "market_range": [{
            "capacity_gb": 64,
            "low_thb_per_gb": 3.25,
            "high_thb_per_gb": 4.25,
            "offers_used": 3,
            "date": "2026-11-21",
        }],
        "mall_capacities_gb": [64],
        "mall_sources": [
            {
                "url": f"https://example.invalid/mall/{index}",
                "date": "2026-11-21",
                "capacity_gb": 64,
                "now_thb": price,
            }
            for index, price in enumerate([208, 240, 272])
        ],
    }


LISTING = {
    "title": "Example Pocket Drive 64 GB",
    "spec_text": "USB flash drive",
}
CLAIM = {"brand": "Example", "product_line": "Pocket Drive", "type": "USB flash drive"}


def test_storage_adapter_keeps_per_unit_range_and_legacy_evidence(approved_reference):
    source = reference_source_for("storage", [approved_reference])

    result = source.resolve({}, CLAIM, Decimal(64))

    assert result.matched and not result.thin
    assert (result.market.currency, result.market.unit) == ("THB", "GB")
    assert (result.market.low_per_unit, result.market.high_per_unit) == (
        Decimal("3.25"), Decimal("4.25"),
    )
    assert result.market.flag_evidence(Decimal(64), {"was_thb": 250, "now_thb": 208}) == {
        "source": "market_range",
        "was_thb": 250,
        "now_thb": 208,
        "low_thb": 208.0,
        "high_thb": 272.0,
        "date": "2026-11-21",
        "sources": approved_reference["mall_sources"],
    }
    assert result.official.values == (Decimal(64), Decimal(128))
    assert result.official.flag_evidence(Decimal(64)) == {
        "url": "https://example.invalid/spec",
        "date": "2026-11-21",
        "capacities_gb": [64, 128],
        "source": "brand_page",
        "promise_gb": 64.0,
    }


def test_captured_identity_can_match_but_partial_claim_does_not_fall_back(approved_reference):
    source = reference_source_for("storage", [approved_reference])

    assert source.resolve(LISTING, {}, Decimal(64)).matched
    assert not source.resolve(LISTING, {"brand": "Example"}, Decimal(64)).matched


def test_unapproved_and_ambiguous_rows_supply_no_reference(approved_reference):
    unapproved = {**approved_reference, "approved_by": "pending human review"}
    for rows in [[unapproved], [approved_reference, approved_reference]]:
        source = reference_source_for("storage", rows)
        assert not source.resolve(LISTING, CLAIM, Decimal(64)).matched


def test_storage_adapter_keeps_mall_only_evidence_and_marks_duplicate_offers_thin(
    approved_reference,
):
    approved_reference["brand_page"] = None
    approved_reference["mall_sources"][2]["url"] = approved_reference["mall_sources"][1]["url"]
    source = reference_source_for("storage", [approved_reference])

    result = source.resolve(LISTING, {}, Decimal(64))

    assert result.matched and result.thin
    assert result.market is None and result.official is None
    assert result.mall.values == (Decimal(64),)
    assert result.mall.flag_evidence(Decimal(128)) == {
        "source": "mall_capacities",
        "capacities_gb": [64],
        "sources": approved_reference["mall_sources"],
    }


def test_other_categories_skip_references_even_with_a_matching_storage_row(approved_reference):
    source = reference_source_for("cable_length", [approved_reference])

    result = source.resolve(LISTING, CLAIM, Decimal(64))

    assert not result.matched and not result.thin
    assert result.market is None and result.official is None and result.mall is None
