# ตรงปก Queue demo rehearsal

**Build-day milestones (Bangkok time)** · Evaluation 15:30 · Rehearsal 16:00 · Code freeze and hand-in 17:00. The official demo length and submission format are pending organiser confirmation in the [README](../README.md).

## Run of show

Lead with the captured listings. If the live reader is unavailable, use the manual-read handoff for this capture. The [fallback demo script](fallback-demo.md) shows the separate synthetic acceptance cases.

1. **Open with the reviewer’s problem.** “A Shopee listing can sell several capacities under one rating. Reports of delivered capacity are buried in reviews for different options. ตรงปก Queue gives reviewers one priority colour per option, with the exact quotes, rule path and confidence.”
2. **512 GB, Q1 RED.** Start with the hand-copied listing, then open its queue card. Show ฿3,948 was and ฿1,389 now against the ฿3,350–5,145 range from three official Mall offers captured 21 November. ฿1,389 is below half the low end (฿1,675), so this option goes to the front of the review queue on price evidence. [Captured listing][price] · [Approved KB][kb]
3. **128 GB, Q4 YELLOW.** Show the exact Variation `สีเงินเมทัลลิก-128G`. One matched buyer says “ที่เก็บได้6gเองครับ” (could store only 6 GB). Point to the copied quote, its date and the rule path. A second independent measured report from the same Variation would satisfy Q3. [Captured listing and review][buyer]
4. **64 GB, GREY after one matched review.** The text reports about 57 GB and Windows Properties displays 57.2 GB. The display is OS-reported capacity, and the reading clears the 85% cutoff. One matched review is below the ten-review minimum for GREEN. Then open the captured 2 TB option with zero matched text reviews. Its listing’s review belongs to 1 TB, so the 2 TB option stays GREY. [64 GB review][comparison] · [Windows screenshot][screenshot] · [2 TB capture][grey]
5. **Close the review loop.** On the 128 GB card, show the initial “unsure” verdict, record a reviewer decision with a reason, then reopen the queue after restarting. “The colour tells the reviewer where to look first. The reviewer decides what the evidence supports.”
6. **Separate sample mode.** If showing the four-buyer 64 GB Q3 RED, switch the queue to **Sample data**, display **Synthetic sample** on screen and introduce it aloud as a rule demonstration. Use the real capture for marketplace claims and the scored results for evaluation claims. [Sample documentation][sample]
7. **Show the evaluation status and one real Codex transcript.** Read the scorecard once verified. Open `[build-day transcript link or excerpt pending]` beside the matching log entry. Point to what Codex produced, what the team decided and how the team verified the change. [Codex log](codex-log/)

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

[price]: https://github.com/Boomudm/Sea-X-OpenAI/blob/477068568fe48c525524231e11894a17f8fb12ae/data/listings/50570965257.json
[kb]: https://github.com/Boomudm/Sea-X-OpenAI/blob/477068568fe48c525524231e11894a17f8fb12ae/data/kb/kb.json
[buyer]: https://github.com/Boomudm/Sea-X-OpenAI/blob/477068568fe48c525524231e11894a17f8fb12ae/data/listings/47255645924.json
[comparison]: https://github.com/Boomudm/Sea-X-OpenAI/blob/477068568fe48c525524231e11894a17f8fb12ae/data/listings/16397222698.json
[screenshot]: https://github.com/Boomudm/Sea-X-OpenAI/blob/477068568fe48c525524231e11894a17f8fb12ae/data/listings/16397222698/images/review-40946425908-02.jpg
[grey]: https://github.com/Boomudm/Sea-X-OpenAI/blob/477068568fe48c525524231e11894a17f8fb12ae/data/listings/28894372103.json
[sample]: https://github.com/Boomudm/Sea-X-OpenAI/blob/477068568fe48c525524231e11894a17f8fb12ae/tests/fixtures/u4/README.md
