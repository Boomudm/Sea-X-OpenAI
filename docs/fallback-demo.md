# 15:00 fallback demo

Use this if the full path is still unavailable at 15:00 Bangkok time. Show the saved listing, its priority colour, the rule path and the available evidence. Keep confidence and evaluation out of the fallback. Close with “narrow path, evaluation next.”

## 1. Run the four captured Shopee listings

From the repository root, assemble the merged U2/U3 code and the capture data from draft [PR #12](https://github.com/Boomudm/Sea-X-OpenAI/pull/12) in a temporary directory. Use Python 3.12, `uv` and `jq`. Run the blocks in the same shell.

```sh
git fetch origin prep/research u1/capture-kb
fallback_dir=$(mktemp -d "${TMPDIR:-/tmp}/trongpok-fallback.XXXXXX")
git archive 9d728a29825156224dd3f592d650819f86a3e167 | tar -x -C "$fallback_dir"
git archive b80cb383f67165a9a6957d2e5ec0ea519585b990 data/listings data/kb |
  tar -x -C "$fallback_dir"
cd "$fallback_dir"

uv run trongpok-analyze --output-dir out/fallback/real \
  --decisions-db out/fallback/real-decisions.sqlite3 \
  data/listings/1005965919.json data/listings/1005966198.json \
  data/listings/50908347169.json data/listings/7455133332.json

jq -sr '
  add | sort_by(
    (.colour as $colour | ["RED", "YELLOW", "GREY", "GREEN"] | index($colour)),
    (if .colour == "GREEN" then .confidence.score else -.confidence.score end),
    .listing_id, .option_id
  )[] | [.listing_id, .option_id, .colour, .deciding, (.reasons | join(", "))] | @tsv
' out/fallback/real/*.json

jq '.[0] | {path, evidence, verdict}' out/fallback/real/50908347169.json
```

The pinned build-day snapshot produced these results.

| Listing ID | Captured 64 GB option | Result |
|---|---|---|
| `50908347169` | SanDisk Ultra Flair, NAVA IT MALL | YELLOW · Q4, price is low |
| `1005965919` | SanDisk Ultra Flair, SanDisk Thailand Official Shop | GREY · 0 matched and checked text reviews |
| `1005966198` | SanDisk Ultra | GREY · 0 matched and checked text reviews |
| `7455133332` | SanDisk Ultra Shift | GREY · 0 matched and checked text reviews |

Open the YELLOW record. It shows ฿1,716 was, ฿620 now, and a ฿624–714 range from three dated Mall offers. Q1 is clear and Q4 fires. The reviewer's verdict starts at “unsure”.

**Buyer evidence pending.** The four pinned records have no captured buyer text, exact review Variation or buyer photos. The marketplace text-review ratio and evaluation are pending. If U1 delivers verified buyer reviews and the LLM is unavailable, put the corresponding saved reader JSON in `out/claims/<listing_id>.json` and `out/findings/<listing_id>.json` and run the same CLI without `--read`.

## 2. Show the synthetic acceptance cases

Keep **SYNTHETIC ACCEPTANCE FIXTURE** visible throughout this step. Use the four test quotes for case 1, with a dedicated output directory and SQLite file.

```sh
mkdir -p out/fallback/fixture-findings
cp tests/fixtures/findings.json out/fallback/fixture-findings/fixture-listing.json
uv run trongpok-analyze --findings-dir out/fallback/fixture-findings \
  --output-dir out/fallback/fixture --decisions-db out/fallback/fixture-decisions.sqlite3 \
  tests/fixtures/listing.json
jq '.[0] | {colour, deciding, verdict, quotes: [.evidence[] | .quote? // empty]}' \
  out/fallback/fixture/fixture-listing.json

uv run pytest -q tests/test_u3_acceptance.py -k 'test_01 or test_02 or test_03 or test_10'
```

- Case 1 produces RED · Q3 from four independent test buyers reporting 29 or 30.5 GB for a 64 GB option.
- Case 2 shows 58 on a 64 GB option and ten checked clean matched reviews. The result is GREEN · Q5.
- Case 3 tests a synthetic 1 TB range of ฿1,800–2,400. Was ฿2,990 and now ฿299 triggers Q1 RED. Was ฿6,000 and now ฿2,000 clears the price rules.
- Case 10 checks that the reviewer decision survives a new process.

## 3. Replay a human decision

Keep the fixture label visible. Enter the acceptance as the reviewer, then re-run the CLI in a fresh process. Show the saved decision and the unchanged Q3 priority.

```sh
uv run python - <<'PY'
from trongpok.decisions import save_decision

save_decision(
    "out/fallback/fixture-decisions.sqlite3",
    "fixture-listing",
    "fixture-64",
    "accepted",
    "Four independent matching measurements in the synthetic example.",
)
PY
uv run trongpok-analyze --findings-dir out/fallback/fixture-findings \
  --output-dir out/fallback/fixture --decisions-db out/fallback/fixture-decisions.sqlite3 \
  tests/fixtures/listing.json
jq '.[0] | {colour, deciding, verdict, reviewer_decision}' \
  out/fallback/fixture/fixture-listing.json
```
