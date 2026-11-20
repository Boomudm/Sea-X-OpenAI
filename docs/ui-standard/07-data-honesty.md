# 07 - Data honesty: numbers, time, money, words, sample data

Every figure, label and sentence on screen must be true of its source. Tags: **[MUST]** = cheap, catches the defects the user points out most, never skip. **[THOROUGH]** = deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).

---

## 1. Numbers reconcile with the source

- Every number on a screen is reconciled against the real data source for the same data copy: write the expected value beside the rendered one. It is never excused as "preview data" or "test data". [MUST] Why: a headline of 0 / 0 was waved off as preview data, was a real bug, and shipped.
- A headline that reads 0, empty or a dash is suspect until proven. Audit prompts list the key numbers with their expected values and never list "known non-defects" for a metric. [MUST] Why: the audit was told to ignore the one number that was wrong.
- Before any UI ship, list every count and metric on the screen with its expected value; a mismatch blocks the ship. [THOROUGH] Why: a green suite plus a clean-looking screenshot proves nothing about values.
- Prove UI on real data in a neutralised copy; seed fixtures hide defects. [THOROUGH] Why: fixtures pass where live data breaks.
- Open the page in a real browser and diff rendered numbers against the data; passing types, build and tests do not prove UI. [MUST] Why: defects lived in the seam between two independently correct modules.
- Count must equal the figure it came from: every modal or drill-down total equals the bar, tile or cell that opened it. Why: a click-through list that disagrees with its source destroys trust.
- Related counts reconcile on screen: attention counts, hero counts, badges and queue lengths come from ONE blocker/decision list. Why: an item present in a row but missing from the queue that counts it.
- One quantity, one value everywhere. Define each number once (one function, one scope label); two readers of one fact share one helper. A scope-bound value names its scope. Why: one metric had four different values across a page.
- Every sentence, time or count about an entity is derived from one function over one event history, shared by row, tooltip, modal, footer and log. Why: hard-coded per-branch sentences were false for some state.
- Arithmetic is shown and honest: derive from real counts, clamp visibly ("-7 -> 0"), net out refunds, and make dialog and tooltip print the same formula result. [THOROUGH] Check each formula against two fixtures. Why: a release count and a displayed formula disagreed.
- Comparisons show both sides: previous -> current, not only a delta. Why: a bare delta hides the baseline.
- Never rank or sort quantities in different units; normalise or group by unit. Why: a gain-rate ranking across units looks authoritative and means nothing.

---

## 2. Unknown, failed, stale, partial

- A failed, unknown or stale read shows "unknown" (or a stale strip) with a neutral status; it never renders as 0, empty or calm. [MUST] Why: a zero standing in for unknown is how a proxy becomes a lie.
- Stale or partial data is marked as such: a source silent for minutes is not drawn as fresh; a partial period is not drawn as a dimmed "disabled" bar; a capped read says it is capped and every item stays reachable (pager or "show more"). Why: silent caps and fresh-looking stale data mislead.
- Show coverage wherever it is computed: partial basis renders `n/m`; no basis renders a dash. Why: users cannot judge a figure without its basis.
- Thin evidence is marked in the cell with its own word (low sample, short window) and an ETA or forecast states its window. Why: a days-to-target from one sale shown at full confidence.
- Snapshot panels (alerts, forecasts, queue ages) state "as of <time>". Why: users cannot judge whether to act on an undated snapshot.
- Numbers that are not final yet (costs allocated at period close) show as an estimate: "~" or a low-high band, labelled with the method and basis, replaced by the actual after close; never shown as actual and never left blank. Why: an open-period figure presented as final.
- A not-yet-live policy reads "New policy: ... (starts <date>)" everywhere it appears, through one helper, and no sample event shows it having happened. Why: sample data presented a future rule as current.
- Panels never repeat the same aggregate per panel on first paint; memoise per request, never in a module-level map that never evicts, and never with a cache key that omits a filter the query uses. [THOROUGH] Why: heap leaks and wrong cached numbers.

---

## 3. Labels, populations, caveats

- Every label is re-derivable from its query: read the label, read the query, say the query in the label's words. If they disagree, the label is wrong. [MUST] Why: "Net income" over a sum of net sales was read as profit.
- One word, one population: "orders paid" and "orders placed" carry the population in the label; never a glossary the reader must open. Why: two comparable-looking numbers meant different sets.
- One cohort per row: a scorecard row whose columns come from different populations is wrong even if each column is correct; report any number that moves after the fix. Why: a mixed-cohort vendor row.
- Computed caveats, not hard-coded: a coverage or proxy note is generated from the data and expires with it. Why: a hard-coded "coverage 0%" outlived the change that made it false.
- Every query function has a render site, or it is deleted; grep exports against call sites. [THOROUGH] Why: panels built first and queries added after left dead queries over two rounds.
- Every number carries its unit ("83 per hour", not "83"). Why: a bare figure is ambiguous.
- A status pill never reads as the opposite state; read each sentence as the user would, with no double negatives or double meanings. Why: "Auto update - stop" beside "Pause".
- A flag, filter or control present in the backend appears in the UI as part of the same change; a UI control without a reader on the backend is not shipped. Why: a toggle with a writer and no reader changed a row and nothing else.
- Every chart has a table twin and keyboard/screen-reader parity; a legend matches its own scale. Why: a chart must never be the only way to read a value.
- Chart units: one y-axis per plot; two measures means two charts. Why: two scales on one grid assert a correlation the data does not contain.
- Chart segments sum to the drawn total and the printed total; check by eye. Why: floating segments contradicted totals.

---

## 4. Time

- One time formatter for the whole product. Never slice or replace an ISO string for display (`.slice(0, 19)`, `.split("T")`); never hand-roll a date string or a second copy of relative-time wording. [MUST] Why: a sliced UTC stamp shows UTC wall-clock and is hours off for the viewer.
- Person-facing times render viewer-local; schedules and business cutoffs render in one fixed named zone. Server-rendered components run in the server's zone, so a per-viewer value must render in a client component. Why: a schedule that shifts with the viewer is wrong; a viewer value in server zone is wrong.
- Know your storage families: UTC with a zone marker, naive local, and UTC mislabelled as naive. Never append a zone marker to a naive-local value. Why: a +7h double shift on money and order times.
- Age and staleness math must use the same clock family as the stored column; a negative age is the tell that you crossed families. [MUST] Why: ad-hoc queries read 7 hours too young and a row appeared "in the future".
- Relative labels are TRUE elapsed time (just now / N min / N h / N days), floor to ONE coarse unit, never claim more elapsed than passed, clamp a future stamp to "just now", and return null on empty or unparseable input so the caller owns the empty wording. Why: a formatter comparing calendar midnights showed a 51-minute-old event as "1 day ago".
- Pair a relative label with an absolute stamp, never instead of it. Absolute stamp ladder: same day "HH:MM"; older "D MMM HH:MM"; the tooltip carries the full date-time. Why: three different formats for one action, and a relative label alone cannot compare two rows.
- Make relative formatters take an injectable "now" guarded against NaN; build test fixtures with the local-date constructor, not a literal with a zone suffix. Why: an invalid "now" printed "NaN days ago"; zone literals make expected values move by runner timezone.
- Shared components that format time (badges, tooltips) are force multipliers: one raw interpolation broke every surface that used the badge. [THOROUGH] Grep every consumer when changing one. Why: one raw stamp, thirteen wrong surfaces.
- One time-boundary helper for period bounds, buckets, forecasts and ages; re-basing moves rows between buckets and is an owner decision, not a refactor. Why: each panel computing its own "today" disagreed.

---

## 5. Money and locale

- Store money in minor units (integers); display in major units. One formatter per context; never mix symbols ("$" and "USD") in one string; catalog strings take a pre-formatted amount. Why: float rounding and mixed symbols read as errors.
- Use the display-currency component for catalog prices and the exact-charge formatter for wallet, held, transfer and order totals. Why: a charged amount must never be converted by display preferences.
- One locale convention per surface. Why: mixed separators and formats on one page look broken.
- i18n: pass catalog keys, never display strings, into translation calls, and type translation-bearing props as catalog keys; no hard-coded user-visible literals or currency symbols in rendered strings; keys match across all locales (enforced by a parity test). [MUST] Why: a hard-coded label rendered as a missing key; untranslated literals leaked into one locale.
- Historical records (orders, receipts) show purchase-time snapshot values; names localise only when a viewer locale is passed, never by default to the record's own locale in admin or tooling. Why: a default rewrote names that admin and tools needed as stored.
- Verify copy in the deployed accessibility tree, in every locale; aria-labels escape text sweeps. [THOROUGH] Why: a text scrape cannot see an aria-label.

---

## 6. Plain words

- Map every raw code and backend enum through ONE label table to plain user wording; the raw code may appear only in a copyable tooltip. [MUST] Why: table names, event codes and developer words showed in the UI.
- One concept, one word, everywhere; use the user's exact words for states, and the user's plain term over the internal one (for example "computer", not "server node"). Why: one undecided state appeared under four names.
- Identity is the stable entity, not a throwaway id; the transient id is a muted "now" value. Why: a disposable instance number read as the identity of a long-lived record.
- Names of items never carry variable attributes (level, tier, size); put them in the description. Why: names repeat and become stale when the attribute changes.
- Labels are 1-3 plain words; explanations go in an (i) tooltip; no developer text, jargon or debug strings visible anywhere (including `title` attributes). [MUST] Why: operator UI is not a log viewer.
- Ensure disabled controls are readable and state their reason. Why: an unexplained greyed control reads as a bug.
- Legal text (terms, privacy, refund, consent) starts from published standard templates, never invented prose: cite the source per section, fill in only your own facts, mark any section with no standard as "[custom - no standard]", keep translations clause-for-clause parallel. Why: invented legal wording is untrustworthy and misses accepted clauses.

---

## 7. Sample and demo data

- Sample or demo data is tagged "sample" in EVERY place it renders (list, table footer, KPI, chart), driven by the record's own flag, never by hand per screen; real figures carry no sample tag. [MUST] Why: a real figure beside an untagged sample figure contradicted it.
- Sample data must sum to the real totals it sits beside: anchor every sample series to the real total (split the real total across a sample shape) and check each sum by eye. Why: sample charts summed to numbers other than the real KPIs next to them.
- One coherent fixture: one row list per person feeds KPI, chips, status bar, ledger and chat; one id sequence across people; every date consistent. Why: a person's facts drawn from separate generators contradicted each other.
- Build the fixture FROM the real API types and routes (same keys, casing, code lists, caps); every backend state has a designed row; never state a fact the backend cannot supply or an invented refusal it does not enforce. [THOROUGH] Why: invented vocabularies and field names collapsed on first real data.
- A "before" view in a comparison is production byte-for-byte. List demo-only markers so they can be removed. Why: hidden real rows and leftover demo chrome.
- Fake contacts use reserved domains and obviously fake identifiers (`@example.test`, zero-padded ids); sample people are clearly fake ("Sample customer A"). Why: realistic fake emails and ids look like leaked personal data.
- A real name carries only snapshot facts. Never attach invented signup dates, roles, notes, ledgers or history to a real person; show a missing field as a dash with a tip, and demo a state on a fake person instead. Why: invented facts on a real person.
- Real names are fine in internal demos and screenshots (names are not credentials); credentials (passwords, cookies, tokens) never appear, and avoid emails or chat identifiers unless the screen needs them. Why: masking names made the demo less real, but leaking credentials is a defect.
- A pager shows the real population, not the number of sample rows; a segment chip and its pager agree. Why: "VIP 46" next to "1-25 of 25".
- A footer or row offers only actions valid for the record's state (no "close" on an already expired item). Why: actions on invalid states mislead.
- No invented fields, history, deadlines or generated references in production either: if there is no source, leave it out. No "simulate" buttons or demo counts in production; in a demo an unbuilt backend ships the full layout with the control disabled and a visible "not built yet" reason; in the production build the backend is built (01), or the gap is listed to the user. Why: fake data looks real.
- A test or preview harness keeps live display flags (emergency-stop, policy, toggles) copied from production and isolates only side effects. [THOROUGH] Why: an isolated server that reset flags showed a screen production never shows.
