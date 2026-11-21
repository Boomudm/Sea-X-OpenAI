# Veritee: project write-up

Prepared for the 21 Nov 2026 submission. This write-up names no shops; product output never says "fake" or "fraud".

**Repo:** https://github.com/Boomudm/Sea-X-OpenAI (branch `prep/research`) · **Demo:** a static, interactive Seller Guard UI with the 10 exported cases and labelled sample data. No database or live AI calls; reviewer decisions are saved in the browser.

## One sentence

For every option of a storage listing, we turn buyers' own measured numbers into one review-priority colour, with the quotes, the rule path and an AI-challenged confidence score. A Shopee reviewer sees in seconds what stars and price hide.

## Problem

- A listing can sell 64 GB, 128 GB and 2 TB under one star rating. Problems are option-specific, but they get mixed together and buried across many reviews.
- A smart seller can write a listing that is perfect on paper. The mismatch shows up only **after the sale**, when buyers measure what they received ("ordered 128, can store only 6 GB").
- Stars and complaint tags miss this. In our captured sample, 2 of the 3 buyer-reported shortfalls were 5-star reviews.
- Not every small number is a problem. A genuine 64 GB drive shows about 57–59 "GB" on a computer (decimal GB vs binary GiB). A naive check raises false alarms.

## Solution

A reviewer queue with **one colour per exact option**:

| Colour | Meaning | Rule (deterministic code) |
|---|---|---|
| RED | Review first | Price far below the official market range, the brand doesn't sell this capacity, or **2+ separate buyers measured below 85%** of the promise |
| YELLOW | Check by hand | One measured buyer, a complaint with no usable number, a low price, an unclear capacity, or a capacity not seen in official Mall offers |
| GREEN | No flags found (not a guarantee) | 10+ matched text reviews, all checked, zero capacity complaints |
| GREY | Not enough data | Everything else; never shown as green |

Every card shows the evidence available for that option (buyer quotes and numbers, the dated market range and sources), the rule path, what's missing, and a confidence score. **A person accepts or dismisses every flag.** The verdict stays "unsure" until they decide.

## How it works

1. **Capture:** people copy target listings with each option's was/now price and the reviews with their exact Variation. Official Mall offers become a dated reference table (KB).
2. **AI reading** (OpenAI Responses API, `gpt-6.2-sol`, structured outputs): the AI extracts each option's promise and turns reviews into findings (number, unit, role: delivered capacity / OS-reported / free space / test result, exact quote). Code rejects any quote that isn't in the copied text.
3. **Rules (code):** match reviews to the exact option, read GB/TB both ways and take the larger, apply the 85% threshold, count separate buyers once, then run the 2-price check and the Q1–Q5 tree.
4. **AI confidence challenge:** one round per flag. The AI asks what could be wrong (GB vs GiB, wrong option, duplicate buyer, sale price). Code accepts a challenge only if it cites a real source, rejects off-topic types, and keeps the total within ±20. **The AI never changes the colour.**
5. **Seller Guard (React) queue:** sorted by colour, then confidence. Low-confidence GREENs are sorted first so they get checked. Each card has the evidence, Shopee source links and shop grouping, and the decision is saved.

## What is real

- **8 captured Shopee listings, 10 options:** 1 RED (price), 4 YELLOW, 4 GREY, 1 GREEN. All captured today from visible pages at normal browsing pace.
- The **GREEN** is a SanDisk 128 GB option: all 22 matched text reviews checked, no capacity complaints.
- The 2 TB YELLOW has two 1-star reports ("1.90 TB shown, really 10-something GB", "2TB, really 20GB"). It stays YELLOW because only one of them gives a usable number, and RED needs 2+.
- A **labelled synthetic sample** shows the 2-buyer RED rule. It is always marked "Sample data".

## Results (honest, N = 5)

Blind labels come from a teammate who didn't write the rules and read only the matched review text and buyer photos: "Do buyers of this exact option credibly report getting less capacity than promised?"

| Method | Shortfalls caught (of 3) | False alarms (of 2 normal) |
|---|---|---|
| **Veritee, RED + YELLOW** | **3** | **0** |
| Veritee, RED only (buyer rule Q3) | 0 | 0 |
| One ChatGPT prompt (same input) | 2 | 0 |
| 1–2-star share ≥ 20% | 1 | 0 |
| Shopee complaint tag | 0 | 0 |

- We caught every reported shortfall at the hand-check level with no false alarms, and the GREEN was correct.
- We produced no buyer RED in the real sample: no option had 2+ separate buyers with a usable measured number. With weaker evidence we route to a person instead of auto-RED.
- **N = 5 is exploratory.** We make no accuracy claim. Thresholds, prompts and baseline cut-offs were frozen before scoring. The ChatGPT baseline ran through the Codex CLI with the frozen prompt; one run was discarded for an input error and is logged.
- Confidence isn't calibrated yet at this sample size.

## Build direction

- **Deep Domain AI:** storage-specific knowledge in rules: GB vs GiB, fake drives reporting a fake size, write-and-verify tests (H2testw/F3), per-option reviews, and the 2-price check against dated official Mall prices.
- **AI-Native Operations:** the AI does many small, checkable steps (reading, challenging), code makes the decision, and a person makes the call. The queue is shaped by AI evidence, not stars.

## Use of Codex

- Codex built most of the product today in parallel subagent "units": capture, readers, rules, Seller Guard integration, evaluation, shop grouping. Each change is logged in `docs/codex-log/` with time, model and how it was checked: 45 rows across 4 teammates, 17 merged PRs.
- Codex ran parallel capture and verification agents; verifier agents re-checked imported reviews against their sources before merge.
- The Codex CLI ran the **ChatGPT baseline** and the **AI confidence challenges** in isolated, ephemeral sessions with no tool calls. First runs are kept, except one baseline run discarded for an input error and one GREEN challenge re-run after a rule change; both are logged with their raw output.
- Claude Code acted as research and orchestration lead: plans, reviews, merges on the lead's approval, and the evaluation run.

## Safeguards

- Flags are review priority, not accusations. A person decides every flag.
- Positive reviews never cancel credible negative evidence.
- Masked buyer names only. Shop names and source links appear inside the reviewer tool for the reviewer; this write-up and the pitch name no shops.
- Review text is untrusted input. The AI's output is validated (quotes must exist, sources must exist), and the colour comes only from code.
- Data access only on a user's request, at normal pace, never bypassing login or CAPTCHA.

## Roadmap

1. **Generic category profiles.** The Q1–Q5 tree is not storage-specific: promise vs. measured delivery, 2+ separate buyers, a category tolerance. Category knowledge moves into a profile that AI drafts and a person approves once: units, the normal display gap, tolerance, what counts as a measurement. Example: power banks. A 20,000 mAh rating is at the 3.7 V cell (74 Wh), so after 5 V conversion about 60–65% at the USB port is normal (Xiaomi specifies 12,000–13,000 mAh at 5 V for 20,000 mAh models). A USB-tester reading of Wh, or mAh at a stated voltage, counts as a measurement; Thai TIS 2879-2560 adds a checkable certification mark. Other categories with a measurable promise and a published tolerance: rechargeable batteries (typical vs minimum mAh), cables (length ± mm), clothing (measured chest width ± cm). Mismatches with no number (wrong model, different item) are classified with a quote and compared with the category's normal complaint rate. A first version is in draft PRs (#34 profiles; #36 worldwide categories and the automatic pipeline, still in review); in both, the storage profile reproduces today's 10 flags byte-for-byte.
2. **Automatic pipeline.** A new listing or a reviewer-pasted link triggers: AI readers → rules → AI confidence challenge → queue. It needs:
   - jobs keyed by listing, option, evidence revision and pipeline version, so a replay never creates duplicate cases;
   - strict structured outputs and prompt caching;
   - per-job token and attempt caps plus a project spend limit;
   - bounded retries that stop on quota errors;
   - **fail-closed behaviour: if an AI step fails, the option becomes "not checked", never GREEN**;
   - production evaluation that samples every colour for human labels and replays Thai, duplicate-buyer and unit-ambiguity cases on every change.

   Review text is untrusted input (OWASP LLM01, indirect prompt injection). The model gets no tools or write access, quotes must exist, and the colour stays in code.
3. **Sharper AI challenges.** Challenges must address the question that decided the colour. Code already rejects GB/GiB and sale-price challenges that can't apply; next is a relevance check for capacity-only GREENs.
4. **Production backend (Supabase).**
   - One queue row per listing option, linked to reviews, findings, versioned rule results, challenges and decisions.
   - Reviewer login with row-level security, and an append-only audit table (actor, time, inputs).
   - Buyer photos in a private bucket served through short-lived signed URLs.
   - Pipeline trigger: an `AFTER INSERT` trigger enqueues work with `pgmq`, a webhook wakes the worker, and `pg_cron` drains the backlog. Writes are idempotent because queue messages can reappear.
   - LLM keys in function secrets.
   - Edge Functions have tight limits (150–400 s wall time, 2 s CPU), so the LLM calls and the Python rules engine run in a separate worker. The rules stay in tested code, not in the database.
5. **Bigger evaluation.**
   - A random sample from the real queue, with options from one listing kept together.
   - Two blind labellers, with Cohen's κ reported before adjudication.
   - 95% Wilson intervals on every proportion. Even 5/5 would only show 57–100%; a ±5-point interval needs about 380 cases in the denominator.
   - Confidence calibration with a reliability plot and Brier score, before and after the AI challenge.
6. **Thailand fit.**
   - The 2022 Digital Platform Services Royal Decree (ETDA) requires covered marketplaces to publish complaint and review-handling processes; a review-priority queue with evidence supports that.
   - Overstated capacity can fall under the Consumer Protection Act's misleading-advertising rule (§22), which is one more reason a person, not the model, decides.
   - PDPA: masked review text can still be personal data, so strip identifiers before any LLM call, minimise retention and use a processor agreement.
7. **Platform signals in production:** return reasons, courier parcel weight vs expected, test buys. Shopee may already have internal checks we can't see; this queue would plug into them.

**Prior art (we don't claim to be first):**
- SOSFakeFlash collected buyers' H2testw/F3 results to publish alerts about fake-capacity sellers.
- Research systems (OnCDS; an Amazon listing study) score counterfeit risk from review text.
- Amazon, Alibaba and Shopee describe proactive listing monitoring and brand-protection programs.

What we did not find in public material is per-option extraction of buyers' measured capacity, combined with GB/GiB-aware rules, a deterministic priority colour, a confidence-only AI challenge, and a person deciding every flag.

## Declarations

- **Before the event (17–20 Nov):** idea, planning documents and `AGENTS.md` design; the `docs/ui-standard` UI lesson pack. Our selection email said ideas only: no entry code or datasets.
- **Seller Guard web app:** entered the repository at 12:55 on 21 Nov (PR #16, which describes it as an existing React/Vite app). Its original build date is not recorded in the repository.
- **Open-source libraries:** Python `openai`, `pydantic`, `streamlit`; web `react`, `react-router-dom`, `@tanstack/react-table`, `recharts`, `lucide-react`, `jspdf`, `tailwindcss`, `vite`, `typescript` and helpers.
- **AI tools:** OpenAI Codex (app and CLI), OpenAI API (`gpt-6.2-sol`), Claude Code (orchestration and review).
- **Built today:** all other code, data capture, KB rows, rules, readers, evaluation, and the integration of Seller Guard with the pipeline.
