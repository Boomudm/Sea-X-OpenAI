# Real-first fallback demo

Use this runbook if the live reader or Seller Guard preview is unavailable. Round 1 has **6 minutes for demo and pitch, then 2 minutes of Q&A**. The final has **6 minutes, then 4 minutes of Q&A**. Keep the product on screen and follow the [six-minute talk track and judging criteria](pitch.md).

## 1. Open the captured cases

From the repository root, run the blocks in the same Bash shell with Python 3.12, `uv`, and `jq`. This uses the six merged Shopee listings from [#12 at `4770685`](https://github.com/Boomudm/Sea-X-OpenAI/tree/477068568fe48c525524231e11894a17f8fb12ae/data/listings). The manual readings below come from exact captured quotes. The existing validator and rules produce the findings and flags with no live API call.

```sh
git fetch origin prep/research
fallback_dir=$(mktemp -d "${TMPDIR:-/tmp}/trongpok-fallback.XXXXXX")
git archive 477068568fe48c525524231e11894a17f8fb12ae | tar -x -C "$fallback_dir"
cd "$fallback_dir"

uv run python - <<'PY'
from pathlib import Path

from trongpok.models import Listing, ReviewDraft
from trongpok.paths import write_json
from trongpok.validation import normalize_review_draft

readings = [
    ("16397222698", "ความจุจริงอยู่ประมาณ 57GB", 57, "GB", "delivered capacity"),
    ("28894372103", "ความจำในข้อมูล มีไม่ถึง ใส่ข้อมูลไป แป้บเดียวหายหมด่", None, "none", "fails after"),
    ("47255645924", "ที่เก็บได้6gเองครับ", 6, "none", "fails after"),
]
findings_dir = Path("out/findings")
findings_dir.mkdir(parents=True, exist_ok=True)
for listing_id, quote, quantity, unit, role in readings:
    listing = Listing.model_validate_json(
        Path(f"data/listings/{listing_id}.json").read_text(encoding="utf-8")
    )
    [review] = [review for review in listing.reviews if quote in review.text]
    [option] = [option for option in listing.options if option.variation_label == review.variation_label]
    draft = ReviewDraft(
        review_id=review.review_id, option_id=option.option_id, complaint="none",
        quantity=quantity, unit=unit, role=role, quote=quote,
    )
    finding = normalize_review_draft(review, option, draft)
    write_json(findings_dir / f"{listing_id}.json", [finding.model_dump(mode="json")])
PY

uv run trongpok-analyze --output-dir out/fallback/real \
  --decisions-db out/fallback/real-decisions.sqlite3

show_real() {
  jq --arg option "$2" '.[] | select(.option_id == $option) |
    {listing_id, option_id, colour, deciding, path, evidence, verdict}' \
    "out/fallback/real/$1.json"
}

show_real 50570965257 512GB
show_real 47255645924 128gb
show_real 16397222698 SDCZ73_064G_G46
show_real 28894372103 2tb
```

1. **512 GB price RED.** Was ฿3,948, now ฿1,389, against the ฿3,350–5,145 range. The paid price is below ฿1,675, half the low end. Show the dated offers and Q1 path.
2. **128 GB one-buyer YELLOW.** Read “ที่เก็บได้6gเองครับ” from the exact `สีเงินเมทัลลิก-128G` review. One measured buyer sets Q4. Q3 takes two independent measured buyers of the same Variation.
3. **64 GB normal reading.** Open the captured 57 GB quote and [Windows Properties screenshot](https://github.com/Boomudm/Sea-X-OpenAI/blob/477068568fe48c525524231e11894a17f8fb12ae/data/listings/16397222698/images/review-40946425908-02.jpg) showing 57.2 GB. Windows reports the binary capacity. This clears the 85% cutoff. The report stays GREY with one checked text review. The image is an OS reading.
4. **GREY abstention.** Show the 2 TB option with zero matched text reviews. The 1 TB review belongs to its own Variation.

This pinned manual replay produced **1 price RED, 3 YELLOW, and 4 GREY** across eight options. The reviewer verdict is `unsure` at the start. Buyer Q3 on real data remains pending.

## 2. Show the synthetic buyer RED

Keep **SYNTHETIC SAMPLE** visible and say “This is a synthetic example for the buyer rule.” In the web queue, use **Sample data**. The CLI uses separate output and decision paths.

```sh
mkdir -p out/fallback/sample-findings
cp tests/fixtures/findings.json out/fallback/sample-findings/fixture-listing.json
uv run trongpok-analyze --findings-dir out/fallback/sample-findings \
  --output-dir out/fallback/sample --decisions-db out/fallback/sample-decisions.sqlite3 \
  tests/fixtures/listing.json

printf '\nSYNTHETIC SAMPLE — buyer RED\n'
jq '.[0] | {colour, deciding, verdict, quotes: [.evidence[] | .quote? // empty]}' \
  out/fallback/sample/fixture-listing.json
```

Four independent sample buyers supply the Q3 measurements. Use the captured cases for marketplace claims.

## 3. Let the reviewer decide

Return to the captured 128 GB YELLOW. Save the reviewer’s chosen outcome and reason in the temporary demo database. Reopen the card from a new process to show the saved verdict and unchanged priority.

```sh
printf 'Reviewer choice (accepted / dismissed): '
read -r reviewer_choice
printf 'Reviewer reason: '
read -r reviewer_reason
uv run python - "$reviewer_choice" "$reviewer_reason" <<'PY'
import sys

from trongpok.decisions import save_decision

choice, reason = sys.argv[1:]
if not reason.strip():
    raise SystemExit("Enter a reviewer reason.")
save_decision("out/fallback/real-decisions.sqlite3", "47255645924", "128gb", choice, reason)
PY
uv run trongpok-analyze --output-dir out/fallback/real \
  --decisions-db out/fallback/real-decisions.sqlite3 data/listings/47255645924.json
jq '.[0] | {colour, deciding, verdict, reviewer_decision}' out/fallback/real/47255645924.json
```

## 4. Show the evaluation status

Sample size, false alarms, misses, and baseline comparisons are **pending** until the labels are frozen and the scorer runs. Open the [results page source](../eval/results.md) and say “narrow path, evaluation next” if scoring is still pending.
