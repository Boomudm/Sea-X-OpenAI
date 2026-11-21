from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel

from trongpok.cache import ReviewCache
from trongpok.client import OpenAIReaderClient, load_api_key
from trongpok.errors import (
    InvalidReaderOutput,
    ReaderConfigurationError,
    ReaderUnavailableError,
)
from trongpok.models import (
    ChallengeBatch,
    ClaimDraftBatch,
    ImageDraftBatch,
    Listing,
)
from trongpok.readers import (
    assess_confidence,
    extract_claims,
    process_listing_file,
    read_images,
    read_reviews,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "synthetic_hero_listing_test_fixture.json"
)


class ScriptedReader:
    def __init__(self, *outputs: BaseModel | dict[str, Any] | Exception) -> None:
        self.outputs = list(outputs)
        self.calls: list[dict[str, Any]] = []

    def generate(
        self,
        schema: type[BaseModel],
        *,
        developer: str,
        user_text: str,
        image_refs: list[str] | None = None,
    ) -> BaseModel:
        self.calls.append(
            {
                "schema": schema,
                "developer": developer,
                "user_text": user_text,
                "image_refs": image_refs,
            }
        )
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return (
            output if isinstance(output, BaseModel) else schema.model_validate(output)
        )


def fixture_listing() -> Listing:
    return Listing.model_validate_json(FIXTURE_PATH.read_text(encoding="utf-8"))


def hero_review_batch() -> dict[str, Any]:
    quantities = [29, 30.5, 29, 30.5, 58]
    quotes = [
        "only 29 GB",
        "measured 30.5 GB",
        "capacity is 29 GB",
        "found 30.5 GB usable capacity",
        "shows 58",
    ]
    listing = fixture_listing()
    return {
        "findings": [
            {
                "review_id": review.review_id,
                "option_id": "fixture-option-64",
                "complaint": "none",
                "quantity": quantity,
                "unit": "none" if quantity == 58 else "GB",
                "role": "delivered capacity",
                "quote": quote,
            }
            for review, quantity, quote in zip(
                listing.reviews, quantities, quotes, strict=True
            )
        ]
    }


def test_hero_reviews_make_four_short_findings_and_parse_58(tmp_path: Path) -> None:
    cache = ReviewCache(tmp_path / "readers.sqlite3")
    try:
        findings = read_reviews(
            fixture_listing(),
            client=ScriptedReader(hero_review_batch()),
            cache=cache,
        )
    finally:
        cache.close()

    short = [finding for finding in findings if finding.complaint == "capacity_short"]
    normal = next(finding for finding in findings if finding.quantity == 58)
    assert len(short) == 4
    assert {finding.quantity for finding in short} == {29, 30.5}
    assert all(finding.role == "delivered capacity" for finding in short)
    assert all(
        finding.quote in fixture_listing().reviews[index].text
        for index, finding in enumerate(findings)
    )
    assert normal.unit == "GB"
    assert normal.ratio == pytest.approx(0.973078528)
    assert normal.complaint == "none"


def test_extract_claims_uses_decimal_tb_and_marks_title_conflict() -> None:
    raw = fixture_listing().model_dump(mode="json")
    raw["title"] = "Synthetic test fixture 2 TB only"
    raw["options"] = [
        {
            "option_id": "fixture-option-1tb",
            "variation_label": "1 TB",
            "capacity_text": "1 TB",
            "promise_gb": None,
            "was_thb": None,
            "now_thb": 1,
        }
    ]
    raw["reviews"] = []
    client = ScriptedReader(
        ClaimDraftBatch.model_validate(
            {
                "options": [
                    {
                        "option_id": "fixture-option-1tb",
                        "promise_gb": 1000,
                        "capacity_unclear": False,
                    }
                ]
            }
        )
    )
    claims = extract_claims(raw, client=client)
    assert claims.options[0].promise_gb == 1000
    assert claims.options[0].capacity_unclear is True


def test_missing_capacity_in_option_label_stays_unclear() -> None:
    raw = fixture_listing().model_dump(mode="json")
    raw["options"][0]["variation_label"] = "Red"
    raw["reviews"] = []
    claims = extract_claims(
        raw,
        client=ScriptedReader(
            {
                "options": [
                    {
                        "option_id": "fixture-option-64",
                        "promise_gb": None,
                        "capacity_unclear": False,
                    }
                ]
            }
        ),
    )
    assert claims.options[0].promise_gb is None
    assert claims.options[0].capacity_unclear is True


def test_invalid_quote_is_rejected_and_not_cached(tmp_path: Path) -> None:
    bad = hero_review_batch()
    bad["findings"][0]["quote"] = "invented words 29 GB"
    cache = ReviewCache(tmp_path / "readers.sqlite3")
    with pytest.raises(InvalidReaderOutput, match="not exact copied text"):
        read_reviews(fixture_listing(), client=ScriptedReader(bad), cache=cache)
    assert cache.get("fixture-review-29-a", "read_reviews.v1") is None
    cache.close()


def test_unit_must_match_exact_quote(tmp_path: Path) -> None:
    bad = hero_review_batch()
    bad["findings"][0]["unit"] = "TB"
    cache = ReviewCache(tmp_path / "readers.sqlite3")
    with pytest.raises(InvalidReaderOutput, match="unit.*does not match"):
        read_reviews(fixture_listing(), client=ScriptedReader(bad), cache=cache)
    cache.close()


def test_cached_reviews_survive_reader_outage(tmp_path: Path) -> None:
    cache = ReviewCache(tmp_path / "readers.sqlite3")
    first = read_reviews(
        fixture_listing(), client=ScriptedReader(hero_review_batch()), cache=cache
    )
    unavailable = ScriptedReader(RuntimeError("model is down"))
    second = read_reviews(fixture_listing(), client=unavailable, cache=cache)
    cache.close()
    assert [item.model_dump() for item in second] == [
        item.model_dump() for item in first
    ]
    assert unavailable.calls == []


def test_cached_finding_is_revalidated_against_current_review(tmp_path: Path) -> None:
    cache = ReviewCache(tmp_path / "readers.sqlite3")
    read_reviews(
        fixture_listing(), client=ScriptedReader(hero_review_batch()), cache=cache
    )
    cached = cache.get("fixture-review-29-a", "read_reviews.v1")
    assert cached is not None
    cached["quote"] = "invented 29 GB"
    cache.put("fixture-review-29-a", "read_reviews.v1", cached)
    with pytest.raises(ReaderUnavailableError, match="1 review"):
        read_reviews(
            fixture_listing(),
            client=ScriptedReader(RuntimeError("model is down")),
            cache=cache,
        )
    cache.close()


def test_conflicting_option_id_and_variation_is_not_read(tmp_path: Path) -> None:
    raw = fixture_listing().model_dump(mode="json")
    raw["reviews"][0]["variation_label"] = "128 GB"
    batch = hero_review_batch()
    batch["findings"] = batch["findings"][1:]
    client = ScriptedReader(batch)
    cache = ReviewCache(tmp_path / "readers.sqlite3")
    findings = read_reviews(raw, client=client, cache=cache)
    cache.close()
    assert len(findings) == 4
    sent = json.loads(client.calls[0]["user_text"])
    assert {review["review_id"] for review in sent["reviews"]} == {
        review["review_id"] for review in raw["reviews"][1:]
    }


def test_image_can_be_reread_exactly_once_before_image_red() -> None:
    raw = fixture_listing().model_dump(mode="json")
    raw["reviews"][0]["images"] = ["tests/fixtures/synthetic-capacity-image.png"]
    client = ScriptedReader(
        ImageDraftBatch.model_validate(
            {
                "images": [
                    {
                        "image_ref": "tests/fixtures/synthetic-capacity-image.png",
                        "review_id": "fixture-review-29-a",
                        "option_id": "fixture-option-64",
                        "image_type": "other",
                        "quantity": None,
                        "unit": "none",
                        "role": "other",
                        "visible_text": None,
                        "read_status": "cannot_read",
                    }
                ]
            }
        ),
        ImageDraftBatch.model_validate(
            {
                "images": [
                    {
                        "image_ref": "tests/fixtures/synthetic-capacity-image.png",
                        "review_id": "fixture-review-29-a",
                        "option_id": "fixture-option-64",
                        "image_type": "completed H2testw/F3",
                        "quantity": 29,
                        "unit": "GB",
                        "role": "test result",
                        "visible_text": "29 GB verified",
                        "read_status": "ok",
                    }
                ]
            }
        ),
    )
    readings = read_images(
        raw,
        client=client,
        reread_image_refs=["tests/fixtures/synthetic-capacity-image.png"],
    )
    assert len(client.calls) == 2
    assert readings[0].image_type == "completed H2testw/F3"
    assert readings[0].ratio is not None and readings[0].ratio < 0.85


def test_confidence_challenge_requires_real_quote_and_source() -> None:
    evidence = [{"review_id": "fixture-review-29-a", "quote": "only 29 GB"}]
    valid = assess_confidence(
        {"listing_id": "fixture", "option_id": "fixture-option-64", "colour": "RED"},
        evidence,
        client=ScriptedReader(
            ChallengeBatch.model_validate(
                {
                    "challenges": [
                        {
                            "kind": "gb_vs_gib",
                            "reason": "The unit interpretation should be checked.",
                            "quote": "only 29 GB",
                            "source": "fixture-review-29-a",
                        }
                    ]
                }
            )
        ),
    )
    assert valid.rounds == 1

    with pytest.raises(InvalidReaderOutput, match="source is absent"):
        assess_confidence(
            {"listing_id": "fixture", "option_id": "fixture-option-64"},
            evidence,
            client=ScriptedReader(
                {
                    "challenges": [
                        {
                            "kind": "wrong_option",
                            "reason": "Check matching.",
                            "quote": None,
                            "source": "missing-review",
                        }
                    ]
                }
            ),
        )

    with pytest.raises(InvalidReaderOutput, match="needs a quote or source"):
        assess_confidence(
            {"listing_id": "fixture", "option_id": "fixture-option-64"},
            evidence,
            client=ScriptedReader(
                {
                    "challenges": [
                        {
                            "kind": "other",
                            "reason": "No evidence citation.",
                            "quote": "",
                            "source": None,
                        }
                    ]
                }
            ),
        )


def test_process_listing_writes_contract_outputs(tmp_path: Path) -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    image_ref = "data/listings/fixture-hero-64gb/images/fixture-result.png"
    raw["reviews"][0]["images"] = [image_ref]
    listing_path = tmp_path / "synthetic-listing.json"
    listing_path.write_text(json.dumps(raw), encoding="utf-8")
    client = ScriptedReader(
        {
            "options": [
                {
                    "option_id": "fixture-option-64",
                    "promise_gb": 64,
                    "capacity_unclear": False,
                }
            ]
        },
        hero_review_batch(),
        {
            "images": [
                {
                    "image_ref": image_ref,
                    "review_id": "fixture-review-29-a",
                    "option_id": "fixture-option-64",
                    "image_type": "completed H2testw/F3",
                    "quantity": 29,
                    "unit": "GB",
                    "role": "test result",
                    "visible_text": "29 GB verified",
                    "read_status": "ok",
                }
            ]
        },
    )
    cache = ReviewCache(tmp_path / "cache.sqlite3")
    claims_path, findings_path = process_listing_file(
        listing_path,
        output_root=tmp_path / "out",
        client=client,
        cache=cache,
    )
    cache.close()
    claims = json.loads(claims_path.read_text(encoding="utf-8"))
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    assert claims["listing_id"] == "fixture-hero-64gb"
    assert len(findings) == 5
    assert findings[0]["image_ref"] == image_ref
    assert set(findings[0]) == {
        "review_id",
        "option_id",
        "complaint",
        "quantity",
        "unit",
        "role",
        "bytes",
        "ratio",
        "quote",
        "image_ref",
        "image_type",
        "read_status",
    }


def test_responses_request_has_required_model_effort_and_no_temperature() -> None:
    captured: dict[str, Any] = {}

    class Responses:
        def create(self, **kwargs: Any) -> SimpleNamespace:
            captured.update(kwargs)
            return SimpleNamespace(output_text='{"options": []}')

    sdk = SimpleNamespace(responses=Responses())
    client = OpenAIReaderClient(project_root=".", sdk_client=sdk)  # type: ignore[arg-type]
    output = client.generate(
        ClaimDraftBatch, developer="stable developer prompt", user_text="{}"
    )
    assert output.options == []
    assert captured["model"] == "gpt-6.2-sol"
    assert captured["reasoning"] == {"effort": "medium"}
    assert "temperature" not in captured
    assert captured["input"][0]["role"] == "developer"
    assert captured["text"]["format"]["strict"] is True


def test_invalid_json_from_responses_api_is_caught() -> None:
    sdk = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: SimpleNamespace(output_text="not json")
        )
    )
    client = OpenAIReaderClient(project_root=".", sdk_client=sdk)  # type: ignore[arg-type]
    with pytest.raises(InvalidReaderOutput, match="JSON schema"):
        client.generate(ClaimDraftBatch, developer="prompt", user_text="{}")


def test_api_key_is_read_only_from_project_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    (tmp_path / ".env").write_text("OPENAI_API_KEY=fixture-key\n", encoding="utf-8")
    assert load_api_key(tmp_path) == "fixture-key"


def test_image_path_cannot_escape_captured_listing_root(tmp_path: Path) -> None:
    secret = tmp_path / "secret.png"
    secret.write_bytes(b"not really an image")
    sdk = SimpleNamespace(responses=SimpleNamespace(create=lambda **_: None))
    client = OpenAIReaderClient(project_root=tmp_path, sdk_client=sdk)  # type: ignore[arg-type]
    with pytest.raises(ReaderConfigurationError, match="inside data/listings"):
        client.generate(
            ImageDraftBatch,
            developer="prompt",
            user_text="{}",
            image_refs=[str(secret)],
        )


@pytest.mark.parametrize("confirmation_gb", [29, 30])
@pytest.mark.parametrize("reader_mode", ["combined", "standalone"])
def test_cli_handles_u2_claims_and_preserves_review_evidence(
    tmp_path, monkeypatch, confirmation_gb, reader_mode,
):
    from trongpok import __main__ as analyze
    from trongpok import cli as reader_cli

    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    image_ref = "data/listings/fixture-hero-64gb/images/fixture-result.png"
    raw["reviews"] = raw["reviews"][:2]
    raw["reviews"][0]["images"] = [image_ref]
    source = tmp_path / "listing.json"
    source.write_text(json.dumps(raw), encoding="utf-8")
    first_image = {
        "image_ref": image_ref,
        "review_id": "fixture-review-29-a",
        "option_id": "fixture-option-64",
        "image_type": "completed H2testw/F3",
        "quantity": 29,
        "unit": "GB",
        "role": "test result",
        "visible_text": "29 GB verified",
        "read_status": "ok",
    }
    client = ScriptedReader(
        {"options": [{"option_id": "fixture-option-64", "promise_gb": 64,
                      "capacity_unclear": False}]},
        {"findings": hero_review_batch()["findings"][:2]},
        {"images": [first_image]},
        {"images": [dict(first_image, quantity=confirmation_gb,
                         visible_text=f"{confirmation_gb} GB verified")]},
    )

    monkeypatch.chdir(tmp_path)
    with ReviewCache(tmp_path / "cache.sqlite3") as cache:
        def process(path, **kwargs):
            return process_listing_file(path, client=client, cache=cache, **kwargs)

        monkeypatch.setattr(analyze, "process_listing_file", process)
        reader_args = ["--read", "--reader-output-root", str(tmp_path)]
        if reader_mode == "standalone":
            monkeypatch.setattr(reader_cli, "process_listing_file", process)
            monkeypatch.setattr("sys.argv", [
                "trongpok-read", str(source), "--output-root", str(tmp_path),
            ])
            reader_cli.main()
            reader_args = ["--claims-dir", "claims", "--findings-dir", "findings"]
        monkeypatch.setattr("sys.argv", [
            "trongpok-analyze", str(source), *reader_args,
            "--output-dir", str(tmp_path / "flags"),
            "--kb", str(tmp_path / "absent-kb.json"),
            "--decisions-db", str(tmp_path / "decisions.sqlite3"),
        ])
        analyze.main()

    listing_id = raw["listing_id"]
    findings = json.loads((tmp_path / "findings" / f"{listing_id}.json").read_text())
    flag, = json.loads((tmp_path / "flags" / f"{listing_id}.json").read_text())
    image_findings = [finding for finding in findings if finding["image_ref"] == image_ref]
    assert len(image_findings) == (2 if confirmation_gb == 29 else 1)
    if confirmation_gb != 29:
        assert image_findings[0]["bytes"] is None
    assert (flag["colour"], flag["deciding"]) == ("RED", "Q3")
    assert {item["quote"] for item in flag["evidence"] if item["source"] == "review"} >= {
        "only 29 GB"
    }
