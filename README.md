# Sea-X-OpenAI

## Evaluation and hand-in

Follow the [evaluation protocol](eval/protocol.md) and use the [pitch notes](docs/pitch.md) for rehearsal.

Bangkok time on 21 November 2026. Code freeze and submissions at **17:00**. Round One judging at **17:15**. Finalist presentations at **19:30**. [Official event agenda](https://luma.com/39zve8ph)

Submission method, required materials, and demo/Q&A duration are pending confirmation from the organisers.

Hackathon preparation in progress. Documents will be added after team review.

## Run locally

Install Python 3.12 and `uv`, then run:

```sh
uv sync
uv run pytest
```

The sample records in `tests/fixtures/` are labeled test data.
Use the shared record shapes in `src/trongpok/shapes.py` when exchanging JSON.

## Generate flags

```sh
uv run trongpok-analyze
```

The command reads `data/listings/*.json` and `data/kb/kb.json`. For each listing ID,
it uses any matching JSON in `out/claims/` and `out/findings/` and writes
`out/flags/<listing_id>.json`. Pass an individual listing path to run just that
listing. See `uv run trongpok-analyze --help` for directory overrides. Run the
CLI from the project root and keep generated reports and the reviewer database
inside that directory.

When reader claims carry only capacity, U3 uses a KB row only if exactly one
approved brand and product line are named in the captured title and the
storage type is named in the specs.

To run the U2 reader and U3 rules in one command, configure the local
`.env` from `.env.example`, then run:

```sh
uv run trongpok-analyze --read data/listings/<listing_id>.json
```

The reader writes claims and findings before the rules generate flags. Omit
`--read` to reuse saved reader results and run without an API key.

The engine needs one text finding per checked review, including clean reviews
(`complaint: "none"`). Unchecked matched reviews can leave an option GREY.
For an image-only measurement, provide both the original read and the re-read
as separate findings for the same captured image. The engine requires them to
agree before that image can contribute to a RED buyer-evidence flag.

For optional confidence challenges, provide a JSON object keyed by option ID
in `<listing_id>.json` under the directory passed to `--challenges-dir`.
Each option's list contains `points` (−10, −5, 5, or 10), `reason`, and
`source` (an exact quote, review ID, image reference, or evidence source URL).

## Review options in Streamlit

```sh
uv run streamlit run src/trongpok/reviewer_app.py
```

The app listens on 127.0.0.1 only (`.streamlit/config.toml`), because it saves reviewer decisions.

Open a row to see the deciding reason, other signals, evidence and confidence
adjustments for that option. Accept or dismiss with a reviewer note. Decisions
are saved to `out/decisions.sqlite3` and appear again after restarting the app.
New captured reports can be loaded with **Refresh queue**.

Choose **Sample data** for the demo. Open **Compact** and **Standard** to compare
the four measured shortfalls with the normal 58 GB reading. Open **Discount**
and **Reference · 1 TB · Black** to compare the ฿299 price flag with a ฿2,000
current price. The [labelled samples](tests/fixtures/u4/README.md) use a separate
`out/sample-decisions.sqlite3` database and can run without an API key.
The [pitch screenshots](docs/u4-demo/) show these same labelled samples.

To open another saved capture, pass its paths after `--`:

```sh
uv run streamlit run src/trongpok/reviewer_app.py -- \
  --flags-dir out/flags --listings-dir data/listings --decisions-db out/decisions.sqlite3
```
