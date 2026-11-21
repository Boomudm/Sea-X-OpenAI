# ตรงปก Queue demo rehearsal

**Confirmed format.** Round 1 has 6 minutes for demo and pitch, followed by 2 minutes of Q&A. The final has 6 minutes followed by 4 minutes of Q&A. Judges prioritize the working product. Rehearsal is 16:00 Bangkok time. [Hand-in notes](../README.md)

## Six-minute demo

Open **Captured data** and have the source evidence ready. Use the [offline fallback](fallback-demo.md) if the live reader or web preview is unavailable.

| Time | Show and say |
|---|---|
| 0:00–0:25 | One listing can sell several capacities under one rating. Buyers’ reports get buried across options. Show the queue that gives reviewers one priority per exact option. |
| 0:25–1:25 | **Real 512 GB price RED.** Open the captured card. Show ฿3,948 was, ฿1,389 now, and the ฿3,350–5,145 range from three dated official Mall offers. Half the low end is ฿1,675, so this option gets Q1 review priority. Point to the sources and date. [Captured listing][price] · [Approved KB][kb] |
| 1:25–2:20 | **Real 128 GB one-buyer YELLOW.** Point to exact Variation `สีเงินเมทัลลิก-128G` and the buyer’s “ที่เก็บได้6gเองครับ” (could store only 6 GB). One measured buyer sets Q4. Q3 RED requires at least two independent measured buyers of this same Variation. [Captured review][buyer] |
| 2:20–3:00 | **Real 64 GB, normal reading.** Show the buyer’s approximately 57 GB report and Windows Properties at 57.2 GB. Explain binary display and the 85% cutoff. One matched review leaves this option GREY. [Captured review][comparison] · [Windows screenshot][screenshot] |
| 3:00–3:30 | **GREY abstention.** Open the 2 TB option. Its listing’s only captured review is for 1 TB, leaving 2 TB with zero matched text reviews. [Captured options][grey] |
| 3:30–4:15 | **Synthetic sample, buyer RED.** Switch to **Sample data** and keep the sample label visible. Say “This is a synthetic example for the buyer rule.” Open the 64 GB option with four sample measurements and show why Q3 fires. [Sample documentation][sample] |
| 4:15–5:15 | **Human decision.** Return to Captured data. Show the 128 GB verdict as unsure, record the reviewer’s choice and reason, and reopen the saved decision. The priority tells the reviewer where to look first. The reviewer decides what the evidence supports. |
| 5:15–6:00 | **Evaluation and Codex.** Show the scored results when available. Until then, say “Evaluation pending.” Open one [Codex log](codex-log/) entry with the matching transcript `[pending]`, and point to the actual contribution and check. |

## Six judging criteria

| Criterion | Evidence in the demo |
|---|---|
| Problem & solution fit | One listing-wide rating hides option-specific complaints. The queue matches exact Variations. |
| Build quality | Open a real captured card, follow its report and evidence, then save and reopen a reviewer decision. |
| Insight & originality | Show GB/GiB normalization, two independent measurements for Q3, and the two-price rule with a dated market range. |
| Real-world value | Sort options by review priority and show the source evidence so the reviewer can decide. |
| Alignment with build direction | Deep Domain AI models storage capacities and measurements. AI-native operations turn the captured evidence into a human review queue. |
| Use of Codex | Show one transcript and log entry that connect a concrete build contribution to its check. |

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
