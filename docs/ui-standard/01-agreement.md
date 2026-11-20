# 01 - Working agreement (the user and the building agent)

This is the contract between the user and whoever builds the UI. Each rule came from a defect the user caught
by hand. Format: rule, then "Why:" naming the defect it prevents. Process rules are tagged [MUST] = cheap, catches the defects the user points out most, never skip, or [THOROUGH] = deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).

## 1. The approved design is the contract

- [MUST] Once the user approves a design (mockup, prototype, named option), the build matches it exactly. A build
  that diverges is not approved. Compare the rendered design and the rendered build side by side yourself; do not
  trust a worker's or a model's claim of parity.
  Why: a build "from the description" drifted in colour, size, copy and layout and the user said "this is not like
  my approval".
- [MUST] Reference the approved design by an immutable version (commit hash, tagged folder), never by a path that
  can differ per branch. Verify the version your workers hold is the approved one before they start.
  Why: builders were cut from a branch that still held an older round of the demo, so they faithfully built the
  wrong design and the approved interactions were missing.
- [MUST] Hand the builder the design's SOURCE (markup, script, styles) and per-state screenshots, never your own
  summary of it. Copy shared label tables and state words verbatim from the design.
  Why: every detail you leave unwritten drifts, and a renamed state is a spec change the user never approved.
- [MUST] Behaviour is part of the design. Everything the design does on click, hover, key and close counts, not
  only how it looks.
  Why: pixel parity alone shipped a build where clicking a chart cell, row or header did not open the modal the
  design opened.
- [MUST] An inventory of the design's behaviour (every handler: what opens, filters, guards, closes) is built from
  its script before porting. Each row ends as exactly one of: works with real data; disabled with a visible reason;
  not ported with a written reason.
  Why: a feature-list check cannot see interactions, so missing interactions were reported as "parity 0 missing".
- [THOROUGH] Pin parity by named tests on the inventory rows and gate on click-by-click parity, not on looks.
  Why: screenshots prove appearance only; a missing click target passes every visual check.
- [MUST] A state or view the design shows that the builder did not build is a GAP that blocks the unit. It is never
  recorded as a "deviation".
  Why: "deviations" accumulate silently until the shipped screen no longer resembles the approved one.

## 2. Build everything in the approved design

- [MUST] Every control, field, column and chart in the approved design is in scope, including the backend it needs
  (store, writer, API). If a worker reports "no backend for this", plan and build that backend; it is not a
  question for the user.
  Why: the user was asked "build or drop this?" about items already in the demo and answered "why do you ask me
  about something we have in the demo, build it".
- [MUST] Questions to the user are only about things the design does NOT decide (true policy, or a contradiction
  between the design and live data). Before listing an open question, check the design: if it shows it, build it. Building a missing backend for an approved design is not a question for the user; only if it cannot be built within the agreed scope, list the gap to the user (never hide it).
  Why: asking about decided items wastes the user's attention and signals the design was not read.
- [MUST] Items the demo adds BEYOND the existing product are built too. Keep a list of the approved extras and give
  each one its own acceptance line in the port.
  Why: user-approved additions (new actions, changed disabled states, motion) are easy to lose between the demo
  and the port because the old product has nothing to compare against.
- [MUST] Parity with an existing surface means subtract: anything not in the approved design is removed, moved to
  the surface that owns it, or reported - never kept and labelled a deviation. EXCEPTION: an element that already
  exists in the live product and the design merely omits stays (live product wins); ask only if the design
  visibly replaces it.
  Why: leftover panels below the approved layout made the screen "dirty" to the user.

## 3. Never cut an existing feature

- [MUST] Every feature the live product shows stays in a redesign or port on every surface where it shows today.
  Do not switch one off, even behind a flag "until approved", to keep an approved screen pixel-frozen. If adding it
  changes an approved screen, add it and tell the user.
  Why: a status pill was kept off the cards to leave the approved layout unchanged; the user said "do not cut a
  production feature without my approval".
- [MUST] Run a parity check against the legacy surface's code before sign-off on a redesign.
  Why: legacy features silently disappeared in redesigns and were found in production.
- [MUST] When a change deletes a surface because a replacement exists, list the concrete artifacts the user looked
  at on the old surface (image, link, download, modal, copy button, count) and the endpoint or component that
  renders each in the replacement. "The data is available" is not evidence. Read the deleted file to build the list.
  Why: a replacement carried the stuck-evidence text but not the screenshot the operator opened the modal for; the
  concept-level gate passed while a capability was lost.
- [MUST] Side effects of a wanted change are reverted and the wanted part kept. When a change can move layout,
  measure row and element heights before and after.
  Why: an image preview added a min-height that grew every row by 24px.

## 4. "Check the whole X" means fix the whole X

- [MUST] When the user points at one instance of a behaviour and says "check the whole app/area for this", the
  deliverable is every instance fixed in the same pass. Do not return a table of findings and ask whether to fix.
  Why: after one chart got its click-through modal, five sibling charts were found, listed, and the user had to
  say "and fix, I already told you what I want".
- [MUST] Fix the first reported instance, then search every sibling (same component family, same card family,
  same data shape) for the same gap before reporting. A sibling needing a new backend filter is part of the job.
  Why: fixing only the screen in front of you is a miss.
- [MUST] Scout by data shape, not by wording: for "standardise this visual", find everything driven by the same
  kind of value (values driving height or width, svg rects, bar/segment styles, meters), not everything named
  "chart".
  Why: hand-drawn bars were fixed on one screen while the rest of the area kept the old form.
- [MUST] Counts must equal what they summarise: prove every modal or drill-through total against the figure it
  came from.
  Why: a drill-through list that disagrees with its bar destroys trust in both.
- [MUST] Every entity reference (customer, order, product, account) in a list, modal, ledger or result is a
  drill-through link that opens the same detail view the main lists use. Plain text is a defect. Every QoL audit
  brief and every UI packet carries a "drill-through" line. (Author names of staff are not customers.)
  Why: a list with dead names forced a manual search; the audit brief had nine categories and none was
  drill-through, so no reviewer could see it.
- [MUST] A shared component is fixed in the shared code, not in one caller.
  Why: a row-click fix landed in one table while the shared table kept the old rule.

## 5. Scope and interruptions

- [MUST] Stay in the scope of the session's task. Ignore unrelated operational alerts and nags unless the user
  asks; at most one line if asked.
  Why: a UI session spent turns diagnosing an unrelated outage; the user said "your work is not that, focus".
- [MUST] Split a small user ask out of a big demo instead of bundling it.
  Why: a bundled round hides what the user actually asked for and slows approval.
- [MUST] Files another stream asked to stay out of are a coordination note, not a blocker on the user's own
  request: say it in one line and do the work.
  Why: stalling on a courtesy boundary cost the user a round.
- [MUST] Do not merge metric charts into one "compare" chart unless the user asks for that exact form.
  Why: a merged paired-bar chart was rejected as "not working"; the two separate charts were kept.
- [MUST] Do not start the next design round until the user says go; after every round that lands, serve it and
  send the user the link (with the critic verdict if one ran). A user who says "this critic is the last one" ends
  critic rounds; their own review decides.
  Why: unrequested rounds burn the user's review time and bury the item they are waiting on.

## 6. Give live choices when unsure

- [MUST] For look-and-feel decisions (font, table variant, motion, before/after) build a compare page: all
  options side by side, light/dark toggle, real copy, a live selector or slider with no reload, then implement the
  pick. The compare page is the record.
  Why: guessing cost rounds; the user picks fast by looking.
- [MUST] A perceptual defect you cannot reproduce: ship a live tuner and let the user set the value.
  Why: tuning blind by number never converged.
- [MUST] Compare pages show ONLY this round's changed views (before = previous round or live, after = this round).
  Why: re-showing settled views makes the user re-review approved work and hides the new change.

## 7. What needs the user's ask, and what does not

- [MUST] Needs the user's OK BEFORE it ships: any change of look, layout, copy or behaviour, including small
  defect fixes a visual worker finds. Visual workers render and REPORT defects, they do not redesign.
  Show before/after screenshots and ask.
  Why: a visual pass silently fixed mobile date labels and a tag wrap; the user said "if UI needs to change, ask me
  first".
- [MUST] Does NOT need an ask: fixing defects your own audit finds in your own work before showing it; restoring
  parity with an already-approved design; integration merges and bug or overflow fixes that do not alter the
  approved look (ship without a new screenshot round).
  Why: asking about these wastes the user's time; the user said "do not show me a screen if it looks like my
  approved one".
- [MUST] Screenshots and an ask are needed only for NEW or CHANGED visual design.
  Why: same as above.
- [MUST] Any screenshot the user sees counts as an approval shot, even a quick "proof" sent to answer a question.
  Hold it to the full pre-show gate.
  Why: one quick shot showed a link box and button at different heights and drew "do not send me dirty UI".

## 8. Extend what exists

- [MUST] Before designing a new tab or screen, list every live component of the area and classify each new part
  DUP / OVERLAP / NEW. Extend the live view in place (rename it if the job grew), keep its labels and columns,
  and mark only the NEW parts.
  Why: a new tab rebuilt 8 of 14 parts of an existing one and the user said "do not build something duplicate".
- [MUST] Reuse a component the user already approved in the same demo (receipt design, cards, chips) instead of
  the older production version. "Existing markup, chrome only" never overrides an approved component.
  Why: an order modal ignored the receipt design approved earlier in the same demo.
- [MUST] Established colours and identity colours (a brand, a payment method, a rank) keep their existing look.
  A sub-type takes tones of its parent's hue, never a new hue. Before any colour change, list what the surface
  shows today and keep it unless the user asked to change it.
  Why: a chart was recoloured wholesale to split one category, then a new hue was invented for the sub-type.
- [MUST] Reused markup brings the host product's theme tokens (radius, fonts, colours) with it, not framework
  defaults. Prove it with a cropped side-by-side against a real page.
  Why: identical class names rendered squarer buttons because the theme behind them differed.

## 9. The user's words

- [MUST] When the user names a state or term, that exact word is the label everywhere (one label table), never a
  synonym. Use the user's plain term in copy, not the internal one.
  Why: an opt-in state was labelled with a synonym the user had rejected.
- [MUST] An English noun is allowed when it is clearer than a stiff literal translation; no developer-internal
  names, codes or engine notes as visible copy (put the raw code in a tooltip).
  Why: operators read "plain words"; internal jargon and raw codes were rejected.
- [MUST] Variable attributes (level, size) stay out of entity names; they live in the description or a
  structured field. Keep names in two languages clean and parallel.
  Why: names carrying a changing attribute go stale and clutter lists.
- [MUST] Legal text (terms, privacy, refund, consent) starts from published standard templates, cites the source
  per section, fills only the business facts, and marks any section with no standard "[custom - no standard]".
  Language versions are clause-for-clause parallel.
  Why: invented legal wording is untrustworthy.
- [MUST] Internal demos show real display names. Keep credentials (passwords, cookies, tokens) out, and avoid
  emails and chat IDs unless the screen needs them.
  Why: masking made the demo less real and the user asked "why hide it, it is not credential data".
- [MUST] Usability beats brand feel. When a brand look and readability pull apart, choose readability and say so.
  Contrast floors are the minimum, not the target.
  Why: a dark brand theme was dropped for a readable one on exactly this ground.
- [MUST] Chat with the user in the language they asked for (here: English only), while UI copy stays in the
  product's language.
  Why: mixed-language replies were rejected.
- [MUST] Dense work tools are desktop-first and a mobile-only cosmetic issue does not block a ship (note it, still
  capture one mobile shot to catch real breakage like overlap or unusable controls). Customer-facing surfaces are
  mobile-first.
  Why: the user said "mobile is lower priority, desktop is main" for work tools only.
