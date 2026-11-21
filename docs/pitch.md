# ตรงปก Queue demo rehearsal

**Build-day milestones (Bangkok time)** · Evaluation 15:30 · Rehearsal 16:00 · Code freeze and hand-in 17:00. The official demo length and submission format are pending organiser confirmation in the [README](../README.md).

## Run of show

If the live path is still unavailable at 15:00, use the [fallback demo script](fallback-demo.md).

1. **Open with the reviewer’s problem.** “A Shopee listing can sell several capacities under one rating. Reports of delivered capacity are buried in reviews for different options. ตรงปก Queue gives reviewers one priority colour per option, with the exact quotes, rule path and confidence.”
2. **Follow the 64 GB hero `[listing and option IDs pending]`.** Start with the hand-copied listing and the option’s Variation. The AI readers extract claims, quotes and numbers. Code matches reviews to the exact option, looks up approved reference data and applies Q1–Q5. Open the queue card, read one quote aloud, and point to the four target buyer quotes, dates, normalised sizes and rule path. Show the rating and price if verified. Then show the 58-reading comparison `[IDs pending]`. If the four-buyer hero is unavailable, use a captured one-buyer YELLOW and explain what a second independent measured report would change.
3. **Show the two-price pair `[IDs pending]`.** Open the Q1 RED card and point to both prices and the dated market range. On the inflated-discount card, show that the paid price falls inside the range. The ฿2,990/฿299 pair is a rule illustration. Use captured prices for marketplace claims. [AGENTS.md §4.3](../AGENTS.md)
4. **Close the review loop.** Show the initial “unsure” verdict, accept or dismiss the flag, enter a reason, and reopen the queue after restarting to show the saved decision. “The colour tells the reviewer where to look first. The reviewer decides what the evidence supports.”
5. **Show the evaluation and one real Codex transcript.** Read the verified results below. Open `[build-day transcript link or excerpt pending]` beside the matching log entry. Point to what Codex produced, what the team decided and how the team verified the change. [Codex log](codex-log/)

## Rules to explain on screen

- **Buyer evidence.** A promised GB is decimal (`10⁹` bytes) and a GiB is binary (`2³⁰` bytes). For an ambiguous GB reading, use the larger interpretation. On a 64 GB option, 58 × 2³⁰ bytes is about 62.3 GB, or 97% of the promise. A measured shortfall is strictly below 85%, and Q3 RED takes at least two separate buyers of that Variation. A completed H2testw or F3 test can supply a measurement. An OS Properties screen shows reported capacity.
- **Two prices.** `L` and `H` are the lowest and highest “now” prices from at least three dated official Mall offers of the same type and capacity. Q1 fires if `now < L/2`, or if `now < 0.75 × L` and a recorded `was` is outside `[L, H]`. If Q1 clears, `L/2 ≤ now < L` adds a Q4 YELLOW reason.
- **Deciding reason and confidence.** When multiple RED rules fire, the strongest deciding reason is **Q3 buyers > Q2 brand page > Q1 price**. The card shows the additional reasons. Confidence never changes the colour. It orders cards within each colour. [AGENTS.md §§4.2–4.6](../AGENTS.md)

## Evaluation talking points

**Sample** · `[N blind-labeled options across M listings pending]`.

| Method | True positives | Misses | False alarms | Q3 RED wins / ties / losses |
|---|---|---|---|---|
| Q3 RED | `[pending]` | `[pending]` | `[pending]` | — |
| Q3 RED + YELLOW | `[pending]` | `[pending]` | `[pending]` | — |
| 1–2-star share at the preselected cutoff | `[pending]` | `[pending]` | `[pending]` | `[W / T / L pending]` |
| Shopee complaint tag | `[pending]` | `[pending]` | `[pending]` | `[W / T / L pending]` |
| One ChatGPT prompt on the same captured input | `[pending]` | `[pending]` | `[pending]` | `[W / T / L pending]` |

- Q1 and Q2 RED counts with blind buyer labels `[pending]`. Confidence-band correctness `[correct / total per band pending]`. Photo-reading agreement with a person `[matches / photos pending]`.
- Use the same verified values in the talk and slides. If the evaluation is still pending at judging, say so and show the working review path. [Evaluation results](../eval/results.md)

## Judges’ Q&A

| Question | Answer |
|---|---|
| Which direction, and why? | Deep Domain AI. The readers extract evidence and the rules account for capacity units, option matching and the market range. The queue puts that evidence into the reviewer’s workflow. |
| How do you know a review is about that option? | We match its captured Variation to the option, skip unmatched or ambiguous reviews, and count each masked buyer once. Identical review text across buyer names counts once. |
| Is a genuine 64 GB card showing 58 GB flagged? | The capacity reading clears the threshold. At 58 GiB it’s about 62.3 decimal GB, or 97% of the promise. |
| What are your false alarms and sample size? | Give the Q3 RED false alarms and sample size from the results. A teammate who did not write the rules blind-labels whether buyers report a shortfall. The report shows Q1 and Q2 RED counts alongside their blind labels. [Evaluation results](../eval/results.md) |
| Did you tune 85% after seeing the results? | The rule was specified before evaluation. Show the pre-run freeze of thresholds, prompts and baseline cut-offs. [Evaluation protocol](../eval/protocol.md) |
| Show one Codex transcript. | Open the selected transcript and matching log entry. Point to the contribution, the team decision and the verification. |
