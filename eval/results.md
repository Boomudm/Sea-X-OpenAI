# Buyer-evidence evaluation

**Sample:** 5 options across 5 listings. Blind labels frozen by Thiti at 2026-11-21T15:08:24+07:00.

## Buyer shortfall detection

| Method | N | True positives | Misses | False alarms | True negatives |
|---|---:|---:|---:|---:|---:|
| Q3 RED | 5 | 0 | 3 | 0 | 2 |
| Q3 RED + YELLOW | 5 | 3 | 0 | 0 | 2 |
| 1–2-star share (≥20%) | 5 | 1 | 2 | 0 | 2 |
| Shopee complaint tag | 5 | 0 | 3 | 0 | 2 |
| ChatGPT | 5 | 2 | 1 | 0 | 2 |

## Price and brand REDs

**Q1 price:** 0. **Q2 brand:** 0.

| Deciding rule | Listing / option | Blind buyer label |
|---|---|---|

## Option-level comparisons

A win means Q3 RED mode predicted the blind label correctly and the baseline missed it.

| Option | Blind buyer label | Flag | Low stars / matched | vs stars | vs tag | vs ChatGPT |
|---|---|---|---:|---|---|---|
| 16397222698 / SDCZ73_064G_G46 | No | GREY (grey) | 0/1 | Tie | Tie | Tie |
| 28894372103 / 1tb | Yes | YELLOW (Q4) | 0/1 | Tie | Tie | Tie |
| 47255645924 / 128gb | Yes | YELLOW (Q4) | 0/1 | Tie | Tie | Loss |
| 8082164236 / 8082164236-option-2tb | Yes | YELLOW (Q4) | 2/2 | Loss | Tie | Loss |
| 22165813567 / SDCZ74_128G_G46 | No | GREEN (Q5) | 0/22 | Tie | Tie | Tie |

| Baseline | Wins | Ties | Losses |
|---|---:|---:|---:|
| 1–2-star share (≥20%) | 0 | 4 | 1 |
| Shopee complaint tag | 0 | 5 | 0 |
| ChatGPT | 0 | 3 | 2 |

## Confidence by score band

Correctness uses the Q3 RED buyer prediction. Q1/Q2 REDs are excluded here.

| Confidence | N | Correct | Accuracy |
|---|---:|---:|---:|
| 0–49 | 1 | 1 | 100% |
| 50–69 | 2 | 1 | 50% |
| 70–84 | 1 | 0 | 0% |
| 85–100 | 1 | 0 | 0% |

## Photo-reading accuracy

No independently labeled buyer photos in this sample.

These results describe this sample.

## Run notes

- Code and data revision: `63c1a07` on `prep/research` (captured listings include U1 #30 (22165813567, 8082164236)). Thresholds, prompt and baseline cut-offs were frozen in [the protocol](protocol.md) before the run.
- Blind labeler read only the matched review text and buyer photos, with flags, findings and baseline output hidden.
- ChatGPT baseline: run with the Codex CLI (ChatGPT login, model `gpt-6.2-sol` requested, reasoning effort medium) instead of the ChatGPT app. One isolated session per listing (one run for the two U1 listings was discarded for an operator input error and is logged), frozen prompt verbatim plus the same listing JSON and captured images; no tool use; first run kept. Details and raw responses: [chatgpt-run.json](chatgpt-run.json).
- No labelled option has 2+ separate buyers with a usable measured number, so Q3 RED did not fire; all 3 reported shortfalls were routed to YELLOW for a person to check, with no false alarms and one GREEN confirmed as No. The main comparison scores Q3 RED only, which is why ChatGPT and the star baseline show wins there. N = 5 is exploratory and supports no accuracy claim.
