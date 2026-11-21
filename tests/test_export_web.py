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
    assert read_json(bundled) == build_cases(FIXTURES / "flags", FIXTURES / "listings")


def test_export_uses_exact_option_prices_and_pipeline_evidence(tmp_path, monkeypatch):
    shutil.copytree(FIXTURES / "flags", tmp_path / "out/flags")
    shutil.copytree(FIXTURES / "listings", tmp_path / "data/listings")
    listing_path = tmp_path / "data/listings/sample-compact-64.json"
    listing = read_json(listing_path)
    listing["listing_images"] = ["listing.jpg"]
    listing["reviews"][0]["images"] = ["proof.jpg", "proof.jpg"]
    listing["reviews"][1]["images"] = ["unmatched.jpg"]
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
        "listing_url": listing["url"], "was_thb": 256, "now_thb": 224, "photo_count": 2,
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
