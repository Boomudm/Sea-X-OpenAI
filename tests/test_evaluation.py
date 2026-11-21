import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "synthetic_hero_listing_test_fixture.json"
)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture
def evaluation_inputs(tmp_path):
    project = tmp_path / "project"
    listing = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    listing_id = listing["listing_id"]
    base = listing["options"][0]
    cases = [
        (64, "Q3", "RED", 90, True, False),
        (128, "Q4", "YELLOW", 65, True, True),
        (256, "Q5", "GREEN", 35, False, True),
        (512, "Q1", "RED", 65, False, False),
        (1024, "Q2", "RED", 90, True, True),
    ]
    listing["options"], labels, flags, baseline = [], [], [], []
    for capacity, deciding, colour, score, label, guess in cases:
        key = {"listing_id": listing_id, "option_id": f"fixture-option-{capacity}"}
        variation = f"{capacity} GB"
        listing["options"].append(dict(
            base, option_id=key["option_id"], variation_label=variation,
            capacity_text=variation, promise_gb=capacity,
        ))
        labels.append(dict(key, buyers_report_shortfall=label))
        flags.append(dict(key, colour=colour, deciding=deciding, confidence={"score": score}))
        baseline.append(dict(key, buyers_report_shortfall=guess))

    reviews = listing["reviews"]
    for review, stars in zip(reviews, [2, 5, 5, 5, 5], strict=True):
        review.update(stars=stars, option_id=None)
    reviews.extend([
        dict(reviews[0], review_id="yellow", variation_label="128 GB",
             stars=5, tags=["complaint"]),
        dict(reviews[0], review_id="unmatched", option_id="fixture-option-256",
             variation_label="256 GB + pouch", tags=["complaint"]),
        dict(reviews[0], review_id="price", variation_label="512 GB", stars=5),
        dict(reviews[0], review_id="brand", variation_label="1024 GB", stars=5),
    ])
    reviews.extend(
        dict(reviews[0], review_id=f"green-{index}", variation_label="256 GB", stars=stars)
        for index, stars in enumerate([1, 5, 5, 5, 5, 5])
    )
    image_ref = "https://example.invalid/fixture-photo.png"
    missing_image = "https://example.invalid/missing-reading.png"
    reviews[0]["images"] = [image_ref, missing_image]
    photo = {"review_id": reviews[0]["review_id"], "image_ref": image_ref,
                 "image_type": "completed H2testw/F3", "quantity": 29, "unit": "GB", "read_status": "ok"}
    finding = dict(photo, option_id="fixture-option-64", complaint="capacity_short",
                   role="test result", bytes=31_138_512_896, ratio=0.4865, quote="29 GB")
    write_json(project / "listings" / f"{listing_id}.json", listing)
    write_json(project / "flags" / f"{listing_id}.json", flags)
    write_json(project / "findings" / f"{listing_id}.json", [finding])
    write_json(project / "chatgpt.json", baseline)
    write_json(project / "labels.json", {
        "labeled_by": "fixture annotator", "frozen_at": "2026-11-21T10:00:00+07:00",
        "options": labels,
        "photos": [dict(photo, listing_id=listing_id),
                   dict(photo, listing_id=listing_id, image_ref=missing_image)],
    })
    return project


def run_evaluation(directory, *, output="score.md", reviewer_decisions=None):
    optional_args = ["--reviewer-decisions", reviewer_decisions] if reviewer_decisions else []
    return subprocess.run(
        [sys.executable, "-m", "trongpok.evaluation", "--labels", "labels.json",
         "--chatgpt", "chatgpt.json", "--listings-dir", "listings", "--flags-dir", "flags",
         "--findings-dir", "findings", "--output", output, *optional_args],
        cwd=directory, capture_output=True, text=True, check=False,
    )


def test_evaluation_scores_buyer_checks_and_baselines(evaluation_inputs):
    result = run_evaluation(evaluation_inputs)
    assert result.returncode == 0, result.stderr
    report = (evaluation_inputs / "score.md").read_text(encoding="utf-8")
    assert "## Buyer shortfall detection" in report
    assert "## Price and brand REDs" in report
    assert "**Q1 price:** 1. **Q2 brand:** 1." in report
    assert "| Q1 | fixture-hero-64gb / fixture-option-512 | No |" in report
    assert "| Q2 | fixture-hero-64gb / fixture-option-1024 | Yes |" in report
    assert "## Option-level comparisons" in report
    assert "| ChatGPT | 2 | 1 | 2 |" in report
    assert "## Confidence by score band" in report
    assert "| 50–69 | 1 | 0 | 0% |" in report
    assert "| 85–100 | 1 | 1 | 100% |" in report
    assert "## Photo-reading accuracy" in report
    assert "1/2 correct (50%). Missing readings: 1." in report
    assert "| Method | N | True positives | Misses | False alarms | True negatives |" in report
    assert "| Q3 RED | 5 | 1 | 2 | 0 | 2 |" in report
    assert "| Q3 RED + YELLOW | 5 | 2 | 1 | 0 | 2 |" in report
    assert "| 1–2-star share (≥20%) | 5 | 1 | 2 | 0 | 2 |" in report
    assert "| Shopee complaint tag | 5 | 1 | 2 | 0 | 2 |" in report
    assert "| ChatGPT | 5 | 2 | 1 | 1 | 1 |" in report


def test_evaluation_compares_web_decisions_without_changing_baselines(evaluation_inputs):
    decisions = [
        (64, "mismatch", "accepted"),
        (128, "unsure", "needs_more_information"),
        (256, "no_mismatch", "dismissed"),
        (512, "mismatch", "accepted"),
        (2048, "no_mismatch", "dismissed"),
    ]
    write_json(evaluation_inputs / "reviewer-decisions.json", [
        {
            "listing_id": "fixture-hero-64gb",
            "option_id": f"fixture-option-{capacity}",
            "verdict": verdict,
            "reviewer_decision": {
                "decision": decision,
                "reason": "A private review note",
                "at": "2026-11-21T12:00:00Z",
            },
        }
        for capacity, verdict, decision in decisions
    ])
    assert run_evaluation(evaluation_inputs, output="baseline.md").returncode == 0

    result = run_evaluation(evaluation_inputs, reviewer_decisions="reviewer-decisions.json")
    assert result.returncode == 0, result.stderr
    report = (evaluation_inputs / "score.md").read_text(encoding="utf-8")
    baseline = (evaluation_inputs / "baseline.md").read_text(encoding="utf-8")

    assert report.startswith(baseline)
    assert "| Shortfall confirmed | 1 | 1 |" in report
    assert "| Not confirmed | 0 | 1 |" in report
    assert "| Need more information | 1 | 0 |" in report
    assert "| No decision exported | 1 | 0 |" in report
    assert "Decisions outside the blind sample: 1." in report
    assert "A private review note" not in report


def test_evaluation_rejects_duplicate_web_decisions(evaluation_inputs):
    decision = {
        "listing_id": "fixture-hero-64gb",
        "option_id": "fixture-option-64",
        "verdict": "mismatch",
        "reviewer_decision": {
            "decision": "accepted",
            "reason": "Reviewer note",
            "at": "2026-11-21T12:00:00Z",
        },
    }
    write_json(evaluation_inputs / "reviewer-decisions.json", [decision, decision])

    result = run_evaluation(evaluation_inputs, reviewer_decisions="reviewer-decisions.json")
    assert result.returncode == 1
    assert "Duplicate option in reviewer decisions" in result.stderr
    assert not (evaluation_inputs / "score.md").exists()


@pytest.mark.parametrize("empty", [False, True], ids=["unknown-option", "empty-labels"])
def test_evaluation_rejects_unscorable_labels(evaluation_inputs, empty):
    labels_path = evaluation_inputs / "labels.json"
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    if empty:
        labels["options"].clear()
    else:
        labels["options"][0]["option_id"] = "missing-option"
    write_json(labels_path, labels)

    result = run_evaluation(evaluation_inputs)

    assert result.returncode != 0
    message = "no blind-labeled options" if empty else "missing-option"
    assert message in result.stderr.lower()
    assert not (evaluation_inputs / "score.md").exists()


def test_evaluation_rejects_output_outside_project(evaluation_inputs, tmp_path):
    sentinel = tmp_path / "sentinel.md"
    sentinel.write_text("original content", encoding="utf-8")

    result = run_evaluation(evaluation_inputs, output="../sentinel.md")

    assert result.returncode == 1
    assert "Path must stay inside" in result.stderr
    assert sentinel.read_text(encoding="utf-8") == "original content"


def test_evaluation_rejects_listing_symlink_outside_project(evaluation_inputs, tmp_path):
    listing = evaluation_inputs / "listings" / "fixture-hero-64gb.json"
    external_listing = listing.rename(tmp_path / listing.name)
    listing.symlink_to(external_listing)

    result = run_evaluation(evaluation_inputs)

    assert result.returncode == 1
    assert "Path must stay inside" in result.stderr
    assert not (evaluation_inputs / "score.md").exists()
