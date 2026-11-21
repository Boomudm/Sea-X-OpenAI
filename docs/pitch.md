# ตรงปก Queue demo rehearsal

**Build-day milestones (Bangkok time)** · Evaluation 15:30 · Rehearsal 16:00 · Code freeze and hand-in 17:00. The official demo length and submission format are pending organiser confirmation in the [README](../README.md).

## Run of show

1. **Open with the reviewer’s problem.** “A Shopee listing can sell several capacities under one rating. Buyers’ reports of delivered capacity are buried in reviews for different options. ตรงปก Queue gives reviewers one priority colour per option, with the exact quotes, rule path and confidence.”
2. **Open the copied listing and its 64 GB option `[listing ID / option ID pending]`.** Show the option’s Variation, then open the queue card. The target is a Q3 RED backed by four independent buyer quotes. Read one quote aloud and point to all four quotes, their dates, the normalised sizes and the rule path. Show the captured price and listing rating if verified. Open the comparison option `[ID pending]` and explain why a 58 reading for 64 GB clears the 85% threshold. If the four-buyer hero is unavailable, use a captured one-buyer YELLOW and explain what a second independent buyer report would change.
3. **Show the two-price pair `[IDs pending]`.** On the Q1 RED card, show both prices and the dated range from at least three same-type, same-capacity official Mall offers. On the inflated-discount card, point to the paid price inside the range and the absence of a price flag. The ฿2,990/฿299 pair in [AGENTS.md §4.3](../AGENTS.md) is a rule illustration. Use captured prices for marketplace claims.
4. **Close the review loop.** Show the initial “unsure” verdict. Act as the reviewer, accept or dismiss the flag using the on-screen evidence, and enter a reason. Reopen the queue after restarting to show the saved decision. “The colour tells the reviewer where to look first. The reviewer decides what the evidence supports.”
5. **Show the comparison and the build evidence.** Use the committed `eval/results.md` table. Open the relevant [Codex log](codex-log/) entry and one real build-day Codex transcript `[link or excerpt pending]`. Point to a concrete contribution, the team’s decision and the verification recorded in the log.

## Evaluation talking points

- Read the sample size, true positives, misses and false alarms for Q3 RED and for the broader buyer check with YELLOW. Compare the same options against the share of 1–2-star reviews at the preselected cutoff, the presence of a Shopee complaint tag, and one ChatGPT prompt on the same copied listing. Report wins, ties and losses for each baseline.
- Give separate Q1 and Q2 RED counts with their blind buyer labels. Show correctness by confidence band and photo-reading agreement with a person, including the denominator for each.
- Results are pending. Use the same verified values in the talk and slides, including any unavailable comparisons. If the evaluation is still pending at judging, say so and show the working review path. Test fixtures are for testing.

## Judges’ Q&A

| Question | Answer |
|---|---|
| Which build direction did you choose? | Deep Domain AI. The readers extract evidence and the rules account for capacity units, option matching and the market range. The queue puts that evidence into the reviewer’s workflow. |
| How do you know a review is about that option? | We match its captured Variation to the option, skip unmatched or ambiguous reviews, and count each masked buyer once. Identical review text across buyer names counts once. |
| Would 58 GB on a genuine 64 GB drive trigger a shortfall? | A 58 reading interpreted as GiB is about 62.3 decimal GB, or 97% of the promise, which clears the threshold. For an image alone, a completed H2testw or F3 write-and-verify test can supply a measured number. |
| What are your false alarms and sample size? | Read the Q3 RED counts and the denominator from `eval/results.md`. A teammate who did not write the rules labels whether buyers report a shortfall. Q1 price and Q2 brand-page REDs have their own rows. Any conclusions apply to this sample. |
| Did you tune 85% after seeing the results? | The rule is strictly below 85%, as specified before evaluation in [AGENTS.md §4.4](../AGENTS.md). Show the pre-run freeze of the thresholds, prompts and baseline cut-offs alongside the results. |
| How did you use Codex? | Show the selected transcript and matching log entry. Point out what Codex produced, what the team decided, and the specific check that verified the change. |
