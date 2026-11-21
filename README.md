# Sea-X-OpenAI

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
uv run python -m trongpok
```

The command reads `data/listings/*.json` and `data/kb/kb.json`. For each listing ID,
it uses any matching JSON in `out/claims/` and `out/findings/` and writes
`out/flags/<listing_id>.json`. Pass an individual listing path to run just that
listing. See `uv run python -m trongpok --help` for directory overrides.

U4 can sort flags across listings using `trongpok.rules.queue_key` and call
`trongpok.decisions.save_decision` and `load_decision` with the same SQLite path
as the CLI (default `out/decisions.sqlite3`). U3 takes the confirmed brand,
product line, and storage type from U2's per-option claim when looking up a KB row.

The engine needs one text finding per checked review, including clean reviews
(`complaint: "none"`). Unchecked matched reviews can leave an option GREY.
For an image-only measurement, provide both the original read and the re-read
as separate findings for the same captured image. The engine requires them to
agree before that image can contribute to a RED buyer-evidence flag.

For optional confidence challenges, provide a JSON object keyed by option ID
in `<listing_id>.json` under the directory passed to `--challenges-dir`.
Each option's list contains `points` (−10, −5, 5, or 10), `reason`, and
`source` (an exact quote, review ID, image reference, or evidence source URL).
