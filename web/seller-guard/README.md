# Seller Guard

Review USB flash drive options by priority, confidence, and evidence.

## Run the captured demo

Capture the listing and buyer evidence under `data/listings/`. Run these
commands from the repository root.

```sh
uv run trongpok-analyze
uv run python -m trongpok.export_web
cd web/seller-guard
npm ci
npm run dev
```

Open the local URL from Vite. The overview is at `/` and the case table is at
`/review`. **Captured data** loads the exported U3 option records, including
their scores and adjustments. **Sample data** shows labelled USB flash drive
cases generated from the team's U3 test scenarios. If the export is missing,
the app opens **Sample data** by default.

The U3 reports in `out/flags/` cover the six U1 listings merged in PR #12 on
21 Nov 2026. The eight options include one red price warning, three yellow
checks, and four with insufficient evidence. The yellow checks cover a low
price, one measured shortfall on the 128 GB option, and a 1 TB capacity
complaint without a usable number. The 64 GB option's 57 GB reading clears
the capacity threshold and stays grey with one checked review.

`out/findings/` records manual text readings for the three captured reviews.
The reader validator checked the exact quotes, matched options, units, and
measurements. Reuse these findings with `uv run trongpok-analyze` to replay
the capture. See the [U1 handoff](https://github.com/Boomudm/Sea-X-OpenAI/issues/8#issuecomment-7058627939).

The exporter writes local capture and evaluation reports and copies the original
captured photos under `public/data/`.
These generated files are ignored by Git. Export again after the pipeline
updates. When using `npm run build` and `npm run preview`, export before building.
The default export publishes `eval/results.md` to `public/data/results.md`
when the report exists. Use `--no-results` to export cases alone.
Browser submissions enter the captured queue as unscored listing links.

Use the listing icon and shop chip in the queue to open Shopee in a new tab.
Inside a case, **Copy case link** shares the exact option. The recipient needs
the same deployed reviewer URL and captured export. In the evidence section,
select a photo to open its original and **View on listing** to open the listing
behind a buyer quote.

## Review outcomes and evaluation

Reviewer decisions and notes stay in the current browser. Use **Export
decisions** from the captured queue to download option-level reviewer
decisions for U5. Copy the downloaded `reviewer-decisions.json` to `out/`
and run this from the repository root once the frozen U5 inputs are ready.

```sh
uv run python -m trongpok.evaluation --reviewer-decisions out/reviewer-decisions.json
uv run python -m trongpok.export_web
```

The scorer keeps the reviewer comparison separate from its blind labels and
baselines. **Results** reads the exported U5 report and displays its pending
status until results are available.

## Update the bundled samples

From the repository root, regenerate the bundled web samples after the U3
test fixtures change.

```sh
uv run python -m trongpok.export_web --flags-dir tests/fixtures/u4/flags \
  --listings-dir tests/fixtures/u4/listings --output web/seller-guard/src/data/sampleCases.json --no-results
```
