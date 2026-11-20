# 03 - Lifecycle: from brief to live, and the states every surface ships

- **[MUST]** - cheap, catches the defects the user points out most, never skip.
- **[THOROUGH]** - deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).
- Untagged lines are design rules.

## Part A - The flow

    brief -> research -> compare options -> interactive demo -> self-audit -> independent critic
          -> ask the user with screenshots -> port -> side-by-side parity (light + dark) -> ship -> live check

Do not skip a stage because the previous one was green. Each stage exists because a defect passed the one before.

### A1. Brief and research

- [MUST] Build the NEW shape the user will use; do not restyle the old one. Judge each screen by how it looks and
  reads, not by whether the code satisfies a requirement list.
  Why: legacy pages "met the spec in code but not visually".
- [MUST] Pages are one-stop work surfaces: the user opens a page to see what is happening and act on it; related
  jobs live together; scattered old pages are retired once the new one has parity.
  Why: split surfaces forced users to hunt across pages.
- [MUST] Before designing, list every live component of the area and mark each new part DUP / OVERLAP / NEW
  (01 section 8). Extend the live view in place.
  Why: a new tab duplicated most of an existing one.
- [MUST] Research current UX conventions for the job before inventing a look; follow global conventions for
  hierarchy so the screen reads at a glance.
  Why: invented hierarchy produced screens the user called dirty or confusing.
- [THOROUGH] Whole-area scout by data shape before standardising any visual (01 section 4).
  Why: fixing only the screen in front of you leaves siblings behind.

### A2. Compare options, then an interactive demo

- [MUST] For any look-and-feel decision, show a compare page first (01 section 6); the user picks by looking.
  Why: guessing wastes rounds.
- [MUST] The demo is interactive HTML the user can click, not a static picture: every state has a way to reach it
  (a sidebar or index of screens, one click each; add every new page or state as a row).
  Why: the user said "do not make me drive through it myself".
- [MUST] The demo reuses the product's real shell, tokens and components, not placeholders (real logo, real
  header, real theme tokens), and is compared with a screenshot of a real page at the same width before the user
  sees it.
  Why: placeholder chrome and default radii made the demo differ from the product the user knows.
- [MUST] Sample data rules in demos:
  - every sample figure carries a visible "sample" tag in EVERY place it renders (list, footer, KPI), driven by the
    record's sample flag, never by hand per screen;
  - real names carry only snapshot facts; a missing field is "-" with a tip; sample events use clearly fake
    people; sample contacts use reserved test domains and zero-padded IDs;
  - sample series are anchored to the real totals beside them (split the real total across the sample shape);
  - one row list per sample person feeds every figure and chart about them (one order sequence across people);
  - a snapshot demo shows its snapshot time and renders shell badges and live timers only if it has a source;
  - a policy not yet live reads "new policy: ... (starts ...)" everywhere (one helper), and no sample event shows
    it having happened.
  Why: sample figures contradicted real totals, invented facts sat on real names, and a countdown that never
  ran appeared in a static demo.
- [MUST] A demo has no fake controls in the product sense: an unbuilt backend is a full layout with a disabled
  control and a visible "not built yet" reason, a real value or an explicit UNKNOWN. No demo counts, no
  "simulate" buttons in production; in the production build the backend is built (01; not a question for the user), and only if it cannot be built within the agreed scope is the gap listed to the user (never hidden).
  Why: invented behaviour gets approved and then cannot be built.
- [MUST] Once the demo is approved, commit it somewhere permanent immediately (a docs commit on the main line) so
  the preview and every later check use it, and name the approved version by hash.
  Why: the approved demo lived on one branch while builders were cut from another.
- [THOROUGH] Every captured demo state loads a fresh page; a demo lint and the mechanical probes (label centred,
  garbage text, forbidden colour, control shape, overlap) run before every publish and the same two label checks
  run in any demo with its own checker.
  Why: an unknown icon id rendered as a blank gap inside every button and off-centre labels went out.

### A3. Self-audit, critic, ask

- [MUST] Self-audit is the pre-show gate (04 [MUST] items), run by the builder on every screen.
  Why: the builder is the cheapest place to catch a defect.
- [THOROUGH] An independent critic runs the full gate (04 [THOROUGH] items) and returns 0 blocker / 0 major
  (02 section 6). Every new mistake class it finds is appended to the mistake ledger (Part C).
  Why: builder self-QA passed screens the user rejected in one glance.
- [MUST] Ask the user only with screenshots, only after the gate is clean, with every view and state the user
  will land on first. Say aloud which controls are live and which are disabled with a reason.
  Why: the user was asked to approve a screen the builder had not opened.
- [MUST] After EVERY round lands, serve it and send the user the link; do not start the next round until told.
  Why: the user wants to steer each round, not discover three rounds later.

### A4. Port the approved design to the real build

- [MUST] Start every port packet from one shared worker-rules template (demo extract by hash, reference
  screenshots, crosswalk of demo states to build screens, per-unit string files, guard block, verification
  order).
  Why: each hand-written packet omitted details that then drifted.
- [MUST] Hand the porter the demo's SOURCE (every file the views use, scripts AND styles) and the regenerated
  per-state screenshots of the approved version (light + dark, every state) with a one-line index state -> file.
  Never a lead summary of the demo.
  Why: a port written from a summary produced about 90 differences against the demo.
- [MUST] Shared strings, state words, tone maps and icon tables are copied verbatim from the demo's own table
  (file:line), never rewritten.
  Why: a renamed state is an unapproved spec change.
- [MUST] Behaviour inventory from the demo's script before porting; each row ends as works with real data /
  disabled with reason / not ported with written reason (01 section 1). Close rules count; feedback is inline or
  a toast, never a blocking alert.
  Why: pixel parity missed every modal behaviour.
- [MUST] Packets for UI units say: "report defects, propose the fix, do not commit UI changes beyond the approved
  design" (01 section 7), and carry the user's standing rules verbatim (palette, density, drill-through).
  Why: a packet that only says "read the standard" lets a worker skip the numbers.
- [THOROUGH] Port the approved demo's CSS mechanically: generate ONE stylesheet scoped under a single root class
  from the demo's layered styles (with a staleness test), then make components emit the demo's markup and class
  names. A screenshot diff then equals a markup diff, not a styling guess. Data, actions and guards stay owned by
  the app.
  Why: re-creating the look by eye left dozens of partial views because every hand rebuild drifted.
- [MUST] Full-page reference and port shots scroll the whole page first so scroll-reveal content is visible and
  fixed docks are hidden.
  Why: shots came back blurred or blank below the fold.
- [MUST] A shared component's styles travel with it (its own stylesheet scoped on its root, with the dark
  variant). Prove a reused component on every route that mounts it.
  Why: an approved panel was unstyled on a route that did not load its page-scoped stylesheet.

### A5. Parity diff, ship, live check

- [MUST] Before ship, screenshot every ported view (light + dark, desktop + narrow) on a real-data copy and compare
  it side by side with the matching demo screenshot; list each difference and fix it or name it to the user.
  Tests and code reviews prove behaviour, not parity.
  Why: a function-verified build "was not like my approval".
- [THOROUGH] Run a read-only demo-source vs build-source audit (wording, tone, size, order, presence, interaction,
  per view) as part of the integration gate, before ship, not after. Lead acceptance maps every demo state named
  in the packet to a built screen or a screenshot.
  Why: an after-the-fact audit found about 90 differences post-ship.
- [MUST] After deploy, look at the live page and compare the same numbers with live data (02 section 9).
  Why: pre-deploy environments differ from the live one.
- [THOROUGH] Behaviour parity gate: any "missing, keep" inventory row blocks the link to the user unless it is
  listed for them as a gap naming the missing backend.
  Why: silent gaps ship as "done".

## Part B - The UI state lifecycle every surface ships

Every surface (page, panel, modal, chart, list, form) renders each of these states, and each is shown at least once
in the screenshots. A state you cannot reach is a state you cannot review.

Source note: the user's rule is "loading, empty, error, stale, unreachable - each rendered once", plus honest
reads and disabled-with-reason. The wording for loading, empty, filtered-empty and permission below is the minimal
reading of that rule; the other states trace to specific defects.

- [MUST] **Loading:** skeleton or placeholder in the final shape; no layout jump on arrival; page chrome (status
  strip, badges, primary actions) follows the same state as the body.
  Why: a load-error and empty state kept a "running" strip and a live Run button.
- [MUST] **Empty:** names what is empty and what to do; a screen with nothing is zero, not unknown.
  Why: a bare blank gives no next step.
- [MUST] **Filtered-empty:** distinct from empty; says a filter hides rows and offers one clear-filters control.
  Why: users could not tell "no data" from "nothing matches".
- [MUST] **Error with retry:** visible, human wording (raw codes only in hover), a retry control, and the error is
  not styled as good news (a success outcome never uses the error slot).
  Why: failed reads rendered as zero or calm, and a success appeared in red.
- [MUST] **Stale:** while data refreshes, keep the previous data on screen (stale-while-revalidate); keys use a
  stable window, never "now". Live data refreshes only while the tab is visible and shows a live / paused / stale
  indicator with pause and reload. A refresh must not remount the view, close an open hover card, or reset a
  focused input (patch rows, keep value and caret).
  Why: a 30 s refresh swapped a view to Loading, unmounted a chart and closed hover, and live repaint reversed typed
  text.
- [MUST] **Partial:** a partial period or partial list says so on the figure and its tooltip ("this month, to
  the 15th"; "N more not in the data"), keeps the normal series colour, and the pager counts the population the
  chip states. Never draw a partial period dimmed.
  Why: a dimmed bar read as disabled and vanished under the hover fade; a pager counted the sample, not the
  population.
- [MUST] **Not final yet:** numbers that settle later (period-end allocations) show as an estimate ("about", or a
  low-high band) with the method in a tooltip, and switch to the actual after close. Never show an open-period
  value as actual, never leave it blank.
  Why: open-period costs read as final.
- [MUST] **Permission:** a control the user may not use is disabled with the reason beside it or hidden by a clear
  rule, never silently dead; gate writes, not reads (a read-only mode must not grey out the whole list).
  Why: a read-only gate left a whole list at 45% opacity and untappable.
- [MUST] **Disabled with reason:** every disabled action states why, next to the action, and the reason tracks
  user input. Disabled controls stay neutral and readable in both themes (text >= 4.5:1), never faded red.
  Why: grey Delete and Save with no reason; dark disabled buttons at 1.2:1.
- [MUST] **Unknown:** a failed or missing read shows "unknown" (or "-" with a tip) with a null status badge; it
  never renders as 0, empty or calm.
  Why: unknown looked like a healthy zero.
- [MUST] **Unreachable:** when the data source or a dependency cannot be reached, say so and show what is
  stale or unavailable, not a stuck spinner.
  Why: a never-resolving panel cost a debugging round.
- [MUST] Every action re-renders every surface that reads the changed rows (row, counts, hero, badges) from one
  state BEFORE the toast; a toggle's next click is computed from the re-rendered state. List every other action
  that changes the entity a surface shows; each re-renders or exits it.
  Why: a toggle flipped data but the row stayed old and a second click sent the same value.
- [MUST] Every state the UI asks the user to decide has a real backend action that leaves it (or the copy says it
  is informational and records a deferral).
  Why: a "needs decision" state told the user to act but nothing could clear it.
- [MUST] A confirm states a hidden effect (turning a feature off that expires open bookings) and a danger confirm
  does not focus its OK button; focus returns to a sensible element after confirms, toggles and picks.
  Why: confirms that hid effects and dropped focus to the page body.
- [MUST] After any action, the launching menu closes through one shared path; the open modal rebuilds from the new
  row state and reopening shows only the new state's actions.
  Why: stale menus and actions from the old state remained.
- [MUST] One time formatter on a screen and one date form per modal; inputs use the same format as lists; people
  see viewer-local times, schedules and business cutoffs use one fixed zone.
  Why: a native date input and two year forms in one modal made dates disagree.
- [MUST] Narrow screens: tab, chip and sub-nav rows scroll horizontally with an edge fade, never wrap; dialogs
  never scroll sideways; every tab remains reachable.
  Why: clipped strips hid tabs with no way to reach them.
- [THOROUGH] Each state also checked in dark and light, and at the narrow width, as part of the full matrix (04).
  Why: a meter rendered at one width in light and another in dark.

## Part C - The mistake ledger loop

- [THOROUGH] Keep one growing ledger of mistake classes. The designer reads it before every round and runs every
  gate named in it that applies to the touched screens; the critic treats each entry as a checklist item, checking
  entries seen before first on the screens where they were seen.
  Why: designer self-QA repeated classes the user already rejected.
- [THOROUGH] After every critic round, in the same cycle, append each NEW class as one entry (dedupe by class, never
  per finding), or add the round to an existing entry's "seen" line. Each entry has: rule, the gate that catches it,
  and where it was seen. If no gate exists, write "gate: none yet" and add a probe in that round or the next.
  Why: lessons not written down are re-learned from the user's anger.
- [THOROUGH] A fix that broke something else goes in a "fixes that caused a new mistake" table with the rule that
  would have prevented it (for example: a rule for one page goes under that page's root class; a new global class
  name is scoped or prefixed).
  Why: each fix added a regression somewhere else.
- [THOROUGH] Keep each entry to about three short lines and move detail to that round's findings list (the list of findings written per critic round).
  Why: a long ledger stops being read.
