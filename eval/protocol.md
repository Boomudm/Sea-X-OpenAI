# Evaluation protocol

Freeze these settings before running the tool or baselines on the labeled sample.

## Blind labels

1. Pick captured USB-drive options with at least one hand-copied review of the exact, unambiguous Variation. Freeze the chosen listing JSON and image files. Leave options with no matched review out of the evaluation.
2. Have a team member who did not write the rules read only the captured listings and buyer photos. For each selected option, set `buyers_report_shortfall` to true if the matched reviews credibly report a real delivered-capacity shortfall. Read the copied evidence in context, including GB/GiB display and the kind of test. Set it to false if the reviewed evidence contains no credible report. Hide flags, model findings and baseline predictions during labeling.
3. In `eval/labels.json`, record the labeler's name, the Bangkok freeze time in ISO 8601 format with UTC offset, and an `options` array of objects with `listing_id`, `option_id`, and `buyers_report_shortfall`. Commit this before scoring. Retain the dataset and rules commit IDs with the results.
4. If there are captured buyer photos, label them before seeing reader output. Each `photos` row has `listing_id`, `review_id`, `image_ref`, `read_status` (`ok` or `cannot_read`), `image_type` (the reader's category or null), `quantity` (number or null), and `unit` (reader unit or null). Use null for details a person cannot establish. Select only captured buyer photos from options in the sample.

## Frozen comparisons

- **Buyer detection.** Positive if the deciding rule is Q3 and the flag is RED. Also report Q3 RED plus all YELLOWs as a second operating point. Q1 and Q2 REDs contribute no buyer-positive predictions. Report them separately with their blind labels.
- **Stars.** Positive when at least 20% of the copied reviews for that exact Variation have 1 or 2 stars. Use all copied ratings with that Variation. The sample contains captured reviews only.
- **Shopee complaint tag.** Positive when at least one copied review for that exact Variation has a Shopee complaint tag in `tags`.
- **ChatGPT.** Use [the frozen prompt](chatgpt-prompt.txt) once per listing in a fresh chat. Supply the same copied listing JSON and captured photos used for the tool. Keep flags and human labels out of the input. Record the ChatGPT model and run time. Save the returned option objects as one array in `eval/chatgpt.json`. Keep the first run, including errors.
- **Confidence.** Score buyer-detection correctness in the 0–49, 50–69, 70–84 and 85–100 bands. Leave Q1/Q2 REDs out of these bands because their confidence concerns different evidence.
- **Photo reading.** Compare readability, image type, and the visible number and unit against the human label. A missing reading is counted separately and remains in the denominator. Repeated reads of the same captured image count as one photo.

## Run and report

After freezing the labels, use U2/U3 on every listing in the sample. Retain the combined analysis flags in `out/flags/` and the separate buyer-photo findings in `out/findings/`. Record the code revision, data revision and ChatGPT model/run time alongside the report.

```sh
uv run python -m trongpok.evaluation
```

The scorer writes `eval/results.md` after checking the sample has flags and a ChatGPT prediction for each labeled option. Check sample size, per-option comparisons and photo coverage before quoting results. Report any missing result or incomplete baseline as pending.
