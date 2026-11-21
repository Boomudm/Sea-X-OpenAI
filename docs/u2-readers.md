# U2 LLM readers

`trongpok.readers` exposes four plain functions over the frozen `AGENTS.md` data shapes:

- `extract_claims(listing)` reads one capacity claim per option and code checks the label,
  decimal TB conversion, and title conflicts.
- `read_reviews(listing)` batches uncached matched reviews by option, validates exact quotes
  and written numbers, calculates bytes/ratio in code, and writes only validated results to
  a durable cache keyed by `(review_id, prompt_version)`.
- `read_images(listing, reread_image_refs=[...])` classifies captured images. A listed image
  is read once more, and only once, for the image-dependent RED check performed by U3.
- `assess_confidence(flag, evidence)` performs one no-tools challenge round and rejects a
  challenge unless its quote or source exists in the supplied evidence.

The default client reads `OPENAI_API_KEY` from `./.env` only, uses the Responses API with
`gpt-6.2-sol`, `reasoning.effort=medium`, structured output, and no temperature setting.

Run one captured listing:

```bash
uv run trongpok-read data/listings/<listing_id>.json
```

Outputs are written to `out/claims/<listing_id>.json` and
`out/findings/<listing_id>.json`. If the model is unavailable, review findings already in
the validated SQLite cache are still returned; missing uncached reviews fail explicitly.
The CLI preserves text and photo findings separately. The rules count each buyer once.
Local images must stay under `data/listings/`. The reader rejects other paths and
unsupported file types before upload.

Tests use only the clearly labelled synthetic files under `tests/fixtures/`. They are not
real marketplace data.
