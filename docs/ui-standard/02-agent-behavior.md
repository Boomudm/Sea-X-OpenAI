# 02 - Agent behaviour: how to verify UI

How the building agent proves a UI works before the user sees it. Rule, then "Why:" naming the defect it prevents.
Tags: [MUST] = cheap, catches the defects the user points out most, never skip. [THOROUGH] = deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).

## 1. Look at it yourself

- [MUST] Open and inspect EVERY screenshot yourself, full size, each viewport x theme you shot. A peer's, a
  worker's or an automated judge's "clean" does not replace this.
  Why: the user was served a screen with visible defects after the builder had looked at 2 of 10 shots.
- [MUST] Crop and zoom real pixels, and read the text. Never call text readable from layout numbers alone, and do
  not rely on scaled composites.
  Why: scaled composites missed misaligned columns and header-vs-card edges; number-only checks missed truncated
  counts and an overlay covering the cart button.
- [MUST] Measure the user's real viewport before a layout audit: take their screenshot, divide image pixels by
  device pixel ratio, note sidebar width, and audit at that size plus the breakpoint edges. Do not infer the
  viewport from a device name.
  Why: an audit at 1440 wide never showed the wrapped card that appeared at the user's real ~1280.
- [MUST] Review the WHOLE screen the way the user uses it, not only your diff: what job does each part do; can the
  user find the broken item, act on a reason, trust each number? Fix or list every pre-existing defect found.
  Why: several defects were already live because every review covered only the lead's own diff.
- [MUST] Row heights, alignment and baselines count: inline controls share height and baseline, nothing clips.
  Estimate row heights against the standard (see 04).
  Why: a table cell stacked three lines (rows twice the standard) and passed a content-and-colour audit.

## 2. Green tests do not prove UI

- [MUST] Type-check, build and unit tests passing is NOT evidence a UI works. Open the page, read the rendered
  value, query the data source for the same field, and diff them.
  Why: a freshly built, twice-reviewed change passed thousands of tests and found two real defects within minutes
  in a browser (runtime-vs-DOM gap, and a cast that disabled the type checker so a form showed values the server
  never had).
- [MUST] A wrong value that looks like a value is the signature of a silent bug: forms that render plausible
  numbers and a Save that returns ok while the server ignored the keys. Compare rendered vs stored.
  Why: "the page rendered" proves nothing.
- [MUST] Test layout and interaction in a real browser. A DOM-simulation test environment has no CSS engine and
  its media-query stub is fixed; it cannot prove a responsive fix, and cannot see a dialog nested in a dialog.
  Why: simulated tests passed layout fixes that were broken at the real mobile size.
- [MUST] Never accept a class-name or source-string assertion as evidence of layout or behaviour. It is a source
  scrape in a costume. Assert rendered behaviour, geometry or accessibility.
  Why: such assertions stay green while the rendered result breaks.
- [MUST] Prove mobile layout at the measured size: inspect element rects, container scroll width and
  document scroll width; a same-origin iframe at the target size is a workable way when the window cannot be
  resized.
  Why: a maximized window silently ignored the resize, so "mobile" checks ran on desktop.
- [MUST] Prove motion without relying on pixels when needed: pause the animations at fixed times and read
  computed styles per item.
  Why: timing measured in a hidden or throttled pane is wrong.

## 3. Data and copy truth

- [MUST] Reconcile every number on screen against the data source for the same copy, with the expected value
  written beside the rendered one. A 0, empty or "-" headline is a suspect until proven. Never excuse a number as
  "preview data" or tell an audit to ignore a metric.
  Why: a headline read "0 / 0" while many items were active; the lead told the audit it was preview data and the
  user found the bug in production.
- [MUST] Audit prompts list key numbers with their expected values. They never list "known non-defects" for a
  metric.
  Why: an audit told to ignore the wrong number approves it.
- [MUST] Two readers of the same fact must return the same answer: one shared helper per derived fact plus a test
  that every reader agrees with the reference reader.
  Why: two surfaces kept different attributes for one entity and showed different rates.
- [MUST] Verify copy in the accessibility tree of the deployed page, in EVERY locale, after deploy and after each
  fix. Text that lives only in `aria-label`, `alt` or `title` is invisible to text sweeps. Diff locale A against
  locale B: a control identical in both is the tell. Attribute-only defects cluster across sibling components.
  Why: a stripped-text sweep came back clean while the page announced the wrong language to screen readers.
- [MUST] Tooltip-only (native title) text is invisible in screenshots: read the attribute to verify it.
  Why: wording could not be checked from a shot.
- [THOROUGH] Make a missed translation call site fail the compiler: type translation-bearing props as catalogue
  keys, with required props. There is no compile-time gate for label attributes, so keep the a11y-tree pass.
  Why: display strings passed where keys were expected rendered as missing keys.

## 4. Real data, in a neutralised copy

- [MUST] Prove UI on real data in a neutralised copy of the live data store, not on an empty test template or
  seed fixtures. Neutralise external side effects first (unreachable endpoints, no push subscriptions, workers
  off) so a preview can never reach the real world. Test fixtures are not live bugs.
  Why: template-only shots hid wrong counts, raw backend codes and phantom states; an unneutralised copy could
  send real external calls.
- [MUST] Keep display flags (kill switches, policy toggles, per-machine settings) as live; isolate only the side-effect
  paths.
  Why: a harness that reset them showed a screen production would never show.
- [MUST] Delete preview copies and build folders after every shoot; check free disk first.
  Why: leftovers from many parallel working copies filled the system disk.
- [MUST] Do not reuse a page across states: each captured state loads a fresh page (new page or cache-busting
  query) and asserts the URL/view after load. Hash-only navigation never reloads.
  Why: every "state" shot showed the first view.
- [MUST] Redact real personal data in shots AFTER the last recompile and re-check the saved shot shows the
  placeholders before sending.
  Why: a dev recompile re-rendered the page and wiped the DOM redaction; real emails reached the screen.

## 5. Probes and tests must be able to fail

- [MUST] Every new probe or test must FAIL on the previous build (the one with the bug) before it counts as a gate.
  Give each probe a negative control.
  Why: a probe blind to the last bug passed round after round.
- [MUST] Any "everywhere / always / never" claim is backed by probe output quoted in the report.
  Why: unmeasured claims such as "the same number everywhere" were false.
- [MUST] Prove interaction with real clicks, hovers and keys, not a demo hook that fakes the state.
  Why: a hook opened a menu correctly while the real click anchored it elsewhere.
- [MUST] A hook or step that opens nothing is a failure, not a pass.
  Why: probes measured the wrong view because the state hook did nothing.
- [MUST] Sweeps scroll every inner scroller to its end and read the text, not only the viewport; a probe checks
  every history-bearing surface, not only the one just fixed.
  Why: content below the fold went unchecked for many rounds.
- [MUST] Fix the pattern in every copy in one change: search all instances before closing.
  Why: a rule was fixed in one of four places.
- [MUST] A contrast fix is measured in both themes by computed style (assert the ratio, not "not red").
  Why: a fix made disabled controls neutral and left dark-theme danger buttons at 1.2:1.
- [THOROUGH] A layout move re-runs the label, legend and overlap probes together; a truncation rule names its exact
  target and a probe asserts no figure is truncated.
  Why: fixes caused new defects (clipped labels, hidden figures, leaked page-scoped rules).

## 6. The critic is independent

- [MUST] The critic is never the builder. A designer's self-QA does not count; self-QA passed four screens the
  user rejected in one glance.
  Why: a builder's blind spots are the same in review.
- [THOROUGH] An independent critic with its own screenshots and real clicks returns 0 blocker / 0 major before the
  user sees a round. It treats the mistake ledger as a checklist, checking entries seen before first on the screens
  where they were seen. Its audit covers a per-view x theme table.
  Why: user-found defects came after green builder QA.
- [THOROUGH] The critic's brief names the rejected patterns explicitly (see 04) and carries the density numbers
  and expected data values, plus each card's text and token class next to its image.
  Why: an audit that did not name a pattern could not find it; small shots made a model misread a blue pill as
  amber.
- [THOROUGH] The critique is visual, not just a pixel diff: debug text left on screen, duplicated information
  across a screen and its modals, wasted height, related facts placed apart, approved components not reused,
  interactions inconsistent with the layout (a split pane means a click opens in the pane). Keep the
  parity/measurement audit as a separate lens.
  Why: a parity audit inherits the old product's UX debt and checks nothing against the new design system.
- [THOROUGH] Verify a critic's colour finding against the CSS before acting on it; judge each parity finding
  (a legacy field that is wrong or meaningless stays out, with the reason recorded).
  Why: low-resolution shots cause false positives.
- [THOROUGH] Rows scrolling inside a card behind an edge fade are inner scroll, not a cut. A layout defect is a
  card edge below the viewport, a cut figure or chart, or a word broken mid-word.
  Why: critics repeatedly reported scrolling rows as "cut".
- [THOROUGH] If a judge refuses a plain screenshot audit (a false-positive safeguard), rerun it on a stronger
  judge with neutral wording rather than skipping the audit.
  Why: skipping the audit lets defects through.
- [MUST] Batch the fixes: run the audit on the FIRST round before fixing anything, fix every finding, then
  rebuild once.
  Why: fixing one defect at a time cost four multi-minute rebuilds.
- [MUST] Visual work is done by an agent that renders and looks at its real output, then the lead re-checks the
  screenshots. Pure wiring (no visible change) does not need that. Not verified from code only.
  Why: blind writers produced layouts nobody had seen.

## 7. Do actions through the API, prove UI through the browser

- [MUST] Data and admin actions go through an existing route or CLI with the session credential, then read-back.
  Drive a real browser only to prove NEW UI, or when no API path exists. If no verb exists, add one that reuses
  the server's write function; never a second CLI or raw database writes.
  Why: browser clicks are slow and fragile (extensions mutated pasted text, filters reset, fetch-to-write is
  blocked) and buy nothing for a control already proven.
- [MUST] Never touch a master switch that flips many things at once; use the per-entity control.
  Why: a global toggle changes the whole fleet.

## 8. Browser-automation traps

- [MUST] A hidden or background browser pane returns blank screenshots and throttles timers and animation
  frames. Make the pane visible, or use a headless capture script that is unaffected.
  Why: blank shots looked like a broken page and wasted rounds.
- [MUST] Keep in-page scripts wait-free in a throttled pane; use external waits between calls.
  Why: scripts with timeouts exceeded the tool limit.
- [MUST] Wait for a STABLE element (a header, the target heading) before the screenshot. Pages fade in and a dev
  server compiles on first hit; a shot right after navigate is dim or blank. Automated tabs report hidden, so
  fake the visibility state before reporting a never-resolving panel.
  Why: polls gated on visibility never ran and cost a round.
- [MUST] Do not wait for "network idle" on pages that poll; wait for load plus a fixed delay.
  Why: it never resolves and times out.
- [MUST] Set the theme the way the app reads it (cookie), not by the browser colour-scheme emulation.
  Why: an emulated "light" context still shot dark.
- [MUST] A click by reference inside a contained scroller lands on the wrong element or nothing. Click by
  coordinate from a fresh screenshot, or scroll into view first, then verify by read-back.
  Why: silent misses changed other rows without any error.
- [MUST] Verify by read-back: re-read the option list and selected value before touching a control; check the data
  store and network requests after every step, and after any keystroke on a dense page.
  Why: a "find" returned a per-row select with the same option list as the intended one.
- [MUST] Sticky table headers can render each row control twice; querySelector grabs the hidden copy. Use the
  visible one by coordinate.
  Why: a script `.click()` toggled nothing.
- [MUST] Clicking an option of a native select inside a modal counts as click-outside and closes the modal; Escape
  closes the modal, not just the popup. Use keyboard (arrow keys, Enter) for native selects.
  Why: modals closed unexpectedly mid-test.
- [MUST] The first load of a route or modal in a dev server compiles for seconds; a click sent before it exists
  lands on whatever is under it. Navigate, wait, find, then click. A half-written edit can leave the server
  serving a stale error: restart it.
  Why: a blind coordinate click navigated to an unrelated page.
- [MUST] Hover by coordinate computed from the real rect (frame vs viewport scale); focus can open hover cards.
  Why: a hover with a reference moved to the wrong spot.
- [MUST] Log in on one fixed local address and re-sign in after a hot reload; another local server on
  the same hostname can overwrite the session cookie.
  Why: decryption 401s and dropped sessions.
- [MUST] Dev-server previews balloon in RAM after an edit rebuild. Shoot from a production build, run
  it as a tracked background task, watch memory, and stop it as soon as the shots are taken. Check RAM before a
  ship.
  Why: previews pushed the machine to 97% RAM and killed guarded test runs and ships.
- [MUST] Browser automation may block form input and arbitrary script on a live origin; coordinate clicks
  and keys still work.
  Why: permission blocks look like page failures.
- [MUST] Seed generated or computed columns correctly in preview data (do not insert into a generated column).
  Why: seeding failed silently.
- [THOROUGH] Run one browser per server and re-run serially before calling a failure a defect.
  Why: parallel browsers on one server produced phantom failures.

## 9. Done means the screenshot shows it

- [MUST] Done = the rendered screen shows it. Merging a shared template does not migrate a page.
  Why: a shared table existed while the page still rendered the old one ("table still old one, I told you to
  adapt").
- [MUST] When something is "being built", say where (file, URL, or open it).
  Why: "being where?" is the user's reaction to vague status.
- [MUST] After deploy, look at the live page and compare the same numbers with live data. Without a live session,
  say so instead of claiming it is done.
  Why: green pre-deploy checks do not cover live data and environment differences.
