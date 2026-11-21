import json
import shutil
import sys
from pathlib import Path

import pytest

from trongpok.errors import ReaderInputError
from trongpok.export_web import DEFAULT_OUTPUT, build_cases, main


FIXTURES = Path(__file__).parent / "fixtures" / "u4"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def test_bundled_web_samples_match_pipeline_fixtures():
    bundled = FIXTURES.parents[2] / "web/seller-guard/src/data/sampleCases.json"
    samples = read_json(bundled)
    for sample in samples:
        sample.setdefault("shop", {
            "id": None, "name": "not captured", "url": None, "badge": None, "ships_from": None,
        })
    assert samples == build_cases(FIXTURES / "flags", FIXTURES / "listings")


def test_export_uses_exact_option_prices_and_pipeline_evidence(tmp_path, monkeypatch):
    shutil.copytree(FIXTURES / "flags", tmp_path / "out/flags")
    shutil.copytree(FIXTURES / "listings", tmp_path / "data/listings")
    listing_path = tmp_path / "data/listings/sample-compact-64.json"
    listing = read_json(listing_path)
    images_dir = listing_path.with_suffix("") / "images"
    images_dir.mkdir(parents=True)
    (images_dir / "listing.jpg").write_bytes(b"listing photo")
    (images_dir / "proof.jpg").write_bytes(b"buyer photo")
    (images_dir / "unmatched.jpg").write_bytes(b"different option photo")
    listing["listing_images"] = [str((images_dir / "listing.jpg").relative_to(tmp_path))]
    listing["reviews"][0]["images"] = [
        str((images_dir / "proof.jpg").relative_to(tmp_path)),
        str((images_dir / "proof.jpg").relative_to(tmp_path)),
        "https://cdn.example.org/evidence.jpg?size=original",
    ]
    listing["reviews"][1]["images"] = [str((images_dir / "unmatched.jpg").relative_to(tmp_path))]
    listing["reviews"][1]["variation_label"] = "128 GB"
    listing["options"].insert(0, {
        "option_id": "128-gb", "variation_label": "128 GB", "capacity_text": "128 GB",
        "promise_gb": 128, "was_thb": None, "now_thb": 399,
    })
    write_json(listing_path, listing)

    results = tmp_path / "eval/results.md"
    results.parent.mkdir()
    results.write_text("# Evaluation results\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["trongpok.export_web"])
    main()

    cases = read_json(DEFAULT_OUTPUT)
    assert [item["priority"] for item in cases] == ["red", "red", "yellow", "unknown", "green"]
    assert {item["deciding"]: item["findings"] for item in cases} == {
        "Q1": ["price"], "Q3": ["capacity"], "Q4": ["reports"], "Q5": ["clear"], "grey": [],
    }
    case = next(item for item in cases if item["listing_id"] == listing["listing_id"])
    (flag,) = read_json(Path("out/flags/sample-compact-64.json"))
    assert case["capture"] == {
        "listing_url": listing["url"], "was_thb": 256, "now_thb": 224, "photo_count": 3,
        "listing_images": ["/data/images/sample-compact-64/images/listing.jpg"],
        "buyer_images": [
            "/data/images/sample-compact-64/images/proof.jpg", "https://cdn.example.org/evidence.jpg?size=original",
        ],
    }
    assert case["title"] == listing["title"]
    assert case["variation_label"] == "64 GB"
    assert case["confidence"] == flag["confidence"]["score"]
    assert case["base"] == flag["confidence"]["base"]
    assert case["adjustments"] == flag["confidence"]["adjustments"]
    assert case["missing_evidence"] == flag["confidence"]["missing_evidence"]
    assert case["path"] == flag["path"]
    assert case["reasons"] == flag["reasons"]
    assert case["evidence"] == flag["evidence"]
    assert case["evidence"][0]["ratio"] == 0.486539264
    assert DEFAULT_OUTPUT.with_name("results.md").read_bytes() == results.read_bytes()
    published = DEFAULT_OUTPUT.parent / "images/sample-compact-64/images"
    assert (published / "listing.jpg").read_bytes() == (images_dir / "listing.jpg").read_bytes()
    assert (published / "proof.jpg").read_bytes() == (images_dir / "proof.jpg").read_bytes()
    assert not (published / "unmatched.jpg").exists()


def test_export_does_not_publish_unsafe_photo_references(tmp_path, monkeypatch):
    flags_dir = tmp_path / "out/flags"
    listing_dir = tmp_path / "data/listings"
    shutil.copytree(FIXTURES / "flags", flags_dir)
    shutil.copytree(FIXTURES / "listings", listing_dir)
    listing_path = listing_dir / "sample-compact-64.json"
    listing = read_json(listing_path)
    outside = tmp_path / "unrelated.jpg"
    outside.write_bytes(b"Unrelated file")
    (listing_dir / "linked.jpg").symlink_to(outside)
    listing["listing_images"] = [
        "data/listings/linked.jpg", "unrelated.jpg", "https://example.invalid/sample.jpg",
        "https://user:pass@cdn.example.org/evidence.jpg", "javascript:alert(1)",
    ]
    write_json(listing_path, listing)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["trongpok.export_web"])

    main()

    case = next(item for item in read_json(DEFAULT_OUTPUT) if item["listing_id"] == listing["listing_id"])
    assert "listing_images" not in case["capture"]
    assert not (DEFAULT_OUTPUT.parent / "images").exists()


def test_export_keeps_missing_option_metadata_empty(tmp_path):
    (flag,) = read_json(FIXTURES / "flags/sample-compact-64.json")
    flag["option_id"] = "no-capture"
    flag["deciding"] = "Q2"
    write_json(tmp_path / "flag.json", [flag])

    (case,) = build_cases(tmp_path, FIXTURES / "listings")
    assert case["findings"] == ["unsupported"]
    assert case["variation_label"] is None
    assert set(case["capture"]) == {"listing_url"}
    (without_listing,) = build_cases(tmp_path, tmp_path / "absent")
    assert without_listing["title"] is None
    assert without_listing["capture"] == {}
    assert without_listing["shop"] == {
        "id": None, "name": "not captured", "url": None, "badge": None, "ships_from": None,
    }


@pytest.mark.parametrize("listing_url", [
    "https://shopee.co.th/product/123/456?shop_id=987",
    "http://www.shopee.co.th/%E0%B8%82%E0%B8%AD%E0%B8%87-i.123.456?shop_id=987#i.987.456",
])
def test_export_joins_shop_from_listing_url(tmp_path, listing_url):
    listings_dir = tmp_path / "custom/listings"
    listings_dir.mkdir(parents=True)
    listing = read_json(FIXTURES / "listings/sample-compact-64.json")
    listing["url"] = listing_url
    write_json(listings_dir / "sample-compact-64.json", listing)

    # Synthetic shop metadata tests the export projection only.
    shop_url = "https://shopee.co.th/shop/123"
    shop = {
        "shop_id": "123", "name": "Example Shop", "url": shop_url, "badge": "preferred",
        "ships_from": "Example Province", "rating": 4.9, "joined": "1 year ago",
    }
    write_json(listings_dir.parent / "shops.json", [shop])

    cases = build_cases(FIXTURES / "flags", listings_dir)
    case = next(case for case in cases if case["listing_id"] == listing["listing_id"])
    assert case["shop"] == {
        "id": "123", "name": "Example Shop", "url": shop_url,
        "badge": "preferred", "ships_from": "Example Province",
    }


@pytest.mark.parametrize(("listing_url", "shop_id"), [
    ("https://shopee.co.th/product/123/456", "123"),
    ("https://shopee.co.th/item-i.123.456", "123"),
    ("https://example.invalid/trongpok-sample/sample-compact-64", None),
    ("https://shopee.co.th.example.invalid/product/123/456", None),
    ("https://shopee.co.th@example.invalid/product/123/456", None),
    ("https://example.invalid@shopee.co.th/product/123/456", None),
    ("ftp://shopee.co.th/product/123/456", None),
    ("https://shopee.co.th/?next=/product/123/456", None),
    ("https://shopee.co.th/product/123/456/more", None),
    ("https://shopee.co.th/item-i.123.456.ext", None),
])
def test_export_preserves_uncaptured_shop_context(tmp_path, listing_url, shop_id):
    listings_dir = tmp_path / "listings"
    listings_dir.mkdir()
    listing = read_json(FIXTURES / "listings/sample-compact-64.json")
    listing["url"] = listing_url
    write_json(listings_dir / "sample-compact-64.json", listing)

    cases = build_cases(FIXTURES / "flags", listings_dir)
    case = next(case for case in cases if case["listing_id"] == listing["listing_id"])
    assert case["shop"] == {
        "id": shop_id, "name": "not captured",
        "url": f"https://shopee.co.th/shop/{shop_id}" if shop_id else None,
        "badge": None, "ships_from": None,
    }


def test_export_rejects_shops_file_outside_listings_parent(tmp_path):
    listings_dir = tmp_path / "capture/listings"
    listings_dir.mkdir(parents=True)
    outside = tmp_path / "shops.json"
    write_json(outside, [])
    (listings_dir.parent / "shops.json").symlink_to(outside)

    with pytest.raises(ReaderInputError, match="Path must stay inside"):
        build_cases(FIXTURES / "flags", listings_dir)


@pytest.mark.parametrize(("name", "ships_from", "exported_name", "exported_location"), [
    (None, None, "not captured", None),
    ("Fake Example Shop", "Example FRAUD Province", "[redacted] Example Shop", "Example [redacted] Province"),
])
def test_export_preserves_raw_shop_capture(tmp_path, name, ships_from, exported_name, exported_location):
    listings_dir = tmp_path / "listings"
    listings_dir.mkdir()
    listing = read_json(FIXTURES / "listings/sample-compact-64.json")
    listing["url"] = "https://shopee.co.th/product/123/456"
    write_json(listings_dir / "sample-compact-64.json", listing)
    shops_path = tmp_path / "shops.json"
    raw = [{"shop_id": "123", "name": name, "ships_from": ships_from, "badge": None}]
    write_json(shops_path, raw)

    cases = build_cases(FIXTURES / "flags", listings_dir)
    case = next(case for case in cases if case["listing_id"] == listing["listing_id"])
    assert case["shop"]["name"] == exported_name
    assert case["shop"]["ships_from"] == exported_location
    assert case["shop"]["badge"] is None
    assert read_json(shops_path) == raw


def test_export_rejects_conflicting_flags_for_one_option(tmp_path):
    (flag,) = read_json(FIXTURES / "flags/sample-compact-64.json")
    write_json(tmp_path / "first.json", [flag])
    flag["confidence"]["score"] += 1
    write_json(tmp_path / "second.json", [flag])

    with pytest.raises(ReaderInputError, match="Conflicting flag reports"):
        build_cases(tmp_path, FIXTURES / "listings")


def test_cli_rejects_output_outside_project(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / "external").symlink_to(outside, target_is_directory=True)
    monkeypatch.chdir(project)
    monkeypatch.setattr(sys, "argv", ["trongpok.export_web", "--output", "external/cases.json"])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 1
    assert "Path must stay inside" in capsys.readouterr().err
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("linked_path", ["eval/results.md", DEFAULT_OUTPUT.with_name("results.md")])
def test_results_export_rejects_redirected_files(tmp_path, monkeypatch, capsys, linked_path):
    project = tmp_path / "project"
    source = project / "eval/results.md"
    source.parent.mkdir(parents=True)
    destination = project / DEFAULT_OUTPUT.with_name("results.md")
    destination.parent.mkdir(parents=True)
    unrelated = tmp_path / "unrelated.md"
    unrelated.write_text("Unrelated contents", encoding="utf-8")
    if linked_path != "eval/results.md":
        source.write_text("# Buyer-evidence evaluation\n", encoding="utf-8")
    (project / linked_path).symlink_to(unrelated)
    monkeypatch.chdir(project)
    monkeypatch.setattr(sys, "argv", ["trongpok.export_web"])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 1
    assert "Evaluation report paths" in capsys.readouterr().err
    assert unrelated.read_text(encoding="utf-8") == "Unrelated contents"
    assert not (project / DEFAULT_OUTPUT).exists()


def test_custom_cases_output_does_not_publish_results(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = Path("eval/results.md")
    source.parent.mkdir()
    source.write_text("# Buyer-evidence evaluation\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["trongpok.export_web", "--output", "scratch/cases.json"])

    main()

    assert read_json(Path("scratch/cases.json")) == []
    assert not Path("scratch/results.md").exists()
    assert not DEFAULT_OUTPUT.with_name("results.md").exists()
