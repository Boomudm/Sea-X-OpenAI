# Buyer-evidence evaluation

**Sample:** 3 options across 3 listings. Blind labels frozen by Thiti at 2026-11-21T14:46:35+07:00.

## Buyer shortfall detection

| Method | N | True positives | Misses | False alarms | True negatives |
|---|---:|---:|---:|---:|---:|
| Q3 RED | 3 | 0 | 2 | 0 | 1 |
| Q3 RED + YELLOW | 3 | 2 | 0 | 0 | 1 |
| 1–2-star share (≥20%) | 3 | 0 | 2 | 0 | 1 |
| Shopee complaint tag | 3 | 0 | 2 | 0 | 1 |
| ChatGPT | 3 | 1 | 1 | 0 | 1 |

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

| Baseline | Wins | Ties | Losses |
|---|---:|---:|---:|
| 1–2-star share (≥20%) | 0 | 3 | 0 |
| Shopee complaint tag | 0 | 3 | 0 |
| ChatGPT | 0 | 2 | 1 |

## Confidence by score band

Correctness uses the Q3 RED buyer prediction. Q1/Q2 REDs are excluded here.

| Confidence | N | Correct | Accuracy |
|---|---:|---:|---:|
| 0–49 | 0 | 0 | — |
| 50–69 | 2 | 1 | 50% |
| 70–84 | 1 | 0 | 0% |
| 85–100 | 0 | 0 | — |

## Photo-reading accuracy

No independently labeled buyer photos in this sample.

These results describe this sample.

## Run notes

- Code and data revision: `7e75e0f` on `prep/research` (captured listings unchanged since U1 merge `4770685`). Thresholds, prompt and baseline cut-offs were frozen in [the protocol](protocol.md) before the run.
- Blind labeler read only the matched review text and buyer photos, with flags, findings and baseline output hidden.
- ChatGPT baseline: run with the Codex CLI (ChatGPT login, model `gpt-6.2-sol` requested, reasoning effort medium) instead of the ChatGPT app. One isolated session per listing, frozen prompt verbatim plus the same listing JSON and captured images; no tool use; first run kept. Details and raw responses: [chatgpt-run.json](chatgpt-run.json).
- Each labelled option has one matched text review, so Q3 (2+ separate buyers) cannot fire by design; both reported shortfalls were routed to YELLOW for a person to check. N = 3 is exploratory and supports no accuracy claim.
