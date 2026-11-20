# 04 - Pre-show gate: run this before showing ANY screen to the user

One checklist. A screen is shown only when every [MUST] item is true and checked by you in person (a worker's
report is a claim). Each item: rule, then "Why:" naming the defect it prevents.
Tags: [MUST] = cheap, catches the defects the user points out most, never skip. [THOROUGH] = deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).

When context is missing (the pack is reference; adapt and say so):
- No approved design yet: the compare/demo step creates one and the user approves it.
- No live data: use representative data, tag it as sample everywhere, and say so.
- No real browser: report the UI as unverified instead of claiming done.
- A [MUST] item that cannot be met is reported to the user, never silently skipped.

A single hit on a rejected pattern means redesign first, not "approve with a note".

## A. [MUST] items - the cheap core

1. [MUST] Look at every shot yourself, full size. Every tab, view, modal, menu, desktop and narrow, light and
   dark. Zoom in on text and numbers.
   Why: the user was served screens the builder had not opened ("how dare you serve me this").
2. [MUST] Every number reconciles with the data. List every number on screen (headline, headers, totals, tiles,
   counts, rates, units), write the expected value from the same data copy beside the rendered one, and fix any
   mismatch. A 0, empty or "-" headline is a suspect. Never excuse a number as preview data. Related counts add
   up on screen (when two populations overlap, show the bridge). A figure set against a budget uses the budget's
   own period and says it in its label. A headline, its legend and its footer derive from the SAME rows. Two
   measures of one idea each have their own label.
   Why: a headline read "0 / 0" while items were active and shipped; related counts that did not add up could not
   be reconciled by the reader.
3. [MUST] Every state is rendered once: loading, empty, filtered-empty, error with retry, stale, partial, disabled
   with reason, unknown (03 Part B).
   Why: states nobody looked at shipped broken or dishonest.
4. [MUST] Every click target is clicked. Menus, rows, headers, chart marks, links, toggles, close paths, keyboard.
   The result matches the approved design. A toggle clicked twice leaves the row correct. A row click behaves by
   table type: a table with a batch action selects on row-body click (the entity name opens the detail); any
   other table opens the detail on row click. Inline controls in a row (switch, link, button, menu, input) never
   select the row.
   Why: the user clicked a row and nothing happened; clicking charts and headers did not open the design's modal.
5. [MUST] Both themes, with contrast. Text at least 4.5:1 and UI components/focus rings at least 3:1 (opaque status surfaces in both
   themes); check dark explicitly and look at light and dark shots of the same state as a pair. Disabled controls
   stay readable. No translucent surfaces that show page art through. A fix to contrast is measured by computed
   style in both themes.
   Why: dark confirm button with white text on near-white; a meter drawn at different widths per theme.
6. [MUST] No debug text. No raw codes, function names, internal ids, English engine notes or developer words as
   visible copy or tooltips; map codes to short plain wording and keep the raw code in hover. Use the user's own
   words for labels.
   Why: a rank-id debug label and "product omitted by ..." left on screen.
7. [MUST] No duplicate counts and no duplicate controls. Each count lives in ONE place (the one that also acts as
   a filter or highlight, plus the badge); no chip row AND legend, no pager count repeated in a footer; one
   clear-filter button, one selection bar, one search box per table. An expansion shows only what its row cannot
   (how a number was built, a chart, history), never values already in the row's columns. Do not add a sub-tab
   that repeats what another part of the modal shows.
   Why: the same counts appeared three times on one screen and cards inside a row repeated its columns.
8. [MUST] No stretched rows and no tall stat boxes. Key-value rows are a fixed muted label column with the value
   left-aligned beside it, capped to a readable width (never label-far-left, value-far-right across a wide
   container); fact strips are content width; a field is as wide as its value (numbers about 10 characters with
   the unit beside, short selects content-width); stats are a compact strip, not tall boxes with a small label
   over one number; filters (range, scope, hint, updated time) share ONE compact row; a summary bar is compact
   next to the table it filters, not a full-width band; a card head holds title, info and tools only. Check every
   tab of a modal, not only the one shot.
   Why: label and value were pushed across an 856px modal, three KPI boxes took a screen, filters sat alone on
   near-empty rows.
9. [MUST] Sibling views consistent. Same area uses the same cards, chips, tables, buttons and header sizes as its
   siblings; one story in one place; same entity = same number everywhere (label names the quantity shown; paired
   tiles share the same anchor); every entity name is a drill-through link; every table has column filters and
   pagination above AND below.
   Why: a rebuilt tab used legacy cards inside a modern area; a label named a start time while showing an end
   time.
10. [MUST] Layout fits. Desktop views fit one screen (about 1440x900) without page scroll; long lists scroll inside
    their own container behind an edge fade; no horizontal scroll anywhere; a table fits its card at the narrow
    desktop width (low-value columns hide first). Nothing is truncated, clipped or overlapped; an ellipsis never
    covers a digit (shorten the copy); essential text never truncates; legends fully visible and show only drawn
    marks. Checked at the user's real viewport, not only one size.
    Why: a table card ran off the bottom on a shorter screen; KPI sub-lines read "Source A 433 - Source B 120 - web ...".
11. [MUST] Colour means something and nothing else. State only: green = good or done; blue = actively running / in progress (also primary action and selection; never a waiting or queued state); red = failed or blocked (one red); grey = queued, scheduled, upcoming or ended; amber = waiting
    on the user's decision (and nothing else). Finished progress is green, not blue. Data is never drawn grey
    (an ended state may be grey; "data never grey" covers values). Cards, lists and pills: colour = state, the
    category shows by icon or label. Chart categories: distinct hues chosen by meaning, no fixed cap; a long tail
    may fold into a grey "other"; a status colour is used for a series only when the series means that status.
    Do not dim rows or bars to encode state; hover fade is by fill/stroke opacity only. No decorative extra hues.
    Established and identity colours keep their existing look.
    Why: user said "normal red green blue is OK"; teal, violet and one-hue-per-category screens were rejected;
    dim bars read as disabled.
12. [MUST] Tap and click targets. Touch targets at least 44 by 44 px (use padding or a hit area, do not just
    inflate the visual); dense desktop admin rows may be 40 px with a 34 px header. Hover and focus visibly react
    on every chart and table row.
    Why: small targets failed real thumbs; marks that did not react left users unsure which bar they read.
13. [MUST] Modals. Detail views are modals on one shared shell, not drawers; clicking outside = the close button =
    Escape through one handler, and a dirty draft asks first; a tabbed modal keeps ONE fixed height so the footer
    never moves, a single-body detail modal hugs its content. Menus anchor to their button (never a centred modal
    used as an action menu, no arrows on actions, risky items last, red and confirmed). Table headers sticky and
    opaque. Hover cards never cover the row they explain.
    Why: footers jumped between tabs; a centred modal served as a three-item menu; a tall hover card covered its
    row.
14. [MUST] Compact hierarchy. One primary focus, at most three competing emphases, secondary text in tooltips.
    Count the emphases after adding any strip. Dense tools: no endless scroll; split independent segments into
    sub-views (one view = one job), not stacked sections with a "jump to" row.
    Why: "too much text, dirty"; stacked segments forced scrolling several screens.
15. [MUST] Simple honest wording. Plain everyday words, one label table, one time form; real states, not demo
    values. A sample is tagged as a sample in every place. Success and info are not shown in the error slot.
    Why: invented numbers and error styling for good news were rejected.
16. [MUST] Aligned and centred. Inline controls share height and baseline; a centred button label is actually
    centred (no invisible icon or hidden span taking width); icon ids all resolve.
    Why: a button text was off-centre because an icon lookup returned nothing ("how dare you serve me this").
17. [MUST] Progress is shown as a bar, not only text: "2/3", "880/1000", "streak 3" get a bar derived from the data,
    with `role=progressbar` and value attributes, blue while in progress and green when done.
    Why: text-only progress is invisible at a glance.
18. [MUST] Charts: bars and segments use the shared chart components with rounded ends and a hover tooltip
    carrying label and value; no hand-drawn CSS boxes with a height from a value; no dimmed bars; floating
    segments and detached target ticks and ambiguous tiny labels are rejected; a category axis never skips a
    label (only time axes thin out); no solid slab behind the plot; a time axis groups by day part.
    Why: dim bars, floating segments and clipped timelines were rejected in one glance.
19. [MUST] Copy and a11y spot check. Read the accessibility tree for icon-only controls and labels in every
    locale; every sentence about an entity derives from ONE history, never a hard-coded sentence.
    Why: a text sweep missed attribute-only labels; a hard-coded sentence contradicted the row.
20. [MUST] Show only this round. If it sits on top of an approved round, the compare shows only the views this round
    touched.
    Why: re-showing settled views hides the new change.

## B. [THOROUGH] items - run on large or high-stakes rounds

21. [THOROUGH] Independent critic. A separate agent that is never the builder runs the whole of A with its own
    screenshots and real clicks, and returns 0 blocker / 0 major before the user sees the round. Its prompt names the
    rejected patterns above, carries the density numbers and the expected data values, and gives each card's text
    and token class beside the image. It also does a visual critique (debug text, duplicate info across a screen and
    its modals, wasted height, related facts placed apart, approved components not reused, interactions consistent
    with layout) and does not stop at a parity diff.
    Why: self-QA and a parity-only audit passed screens the user rejected.
22. [THOROUGH] Full matrix: every tab, view, modal and state x desktop + narrow (about 390) x light + dark, plus the
    user's real viewport and breakpoint edges (e.g. 1101, 1180, 1280). Check every long-scroll region to its
    end.
    Why: the defect appeared only at a width or theme that was not shot.
23. [THOROUGH] Parity diff vs the approved design: screenshot each view beside the matching demo screenshot (same
    width, light + dark), list every difference, fix or name it; plus the behaviour inventory per 01 and the demo
    source vs build source audit.
    Why: parity of function is not parity of look and clicks.
24. [THOROUGH] Keyboard pass: tab order, focus visible, focus returns after dialogs and toggles, Escape closes only
    the top layer, arrow and Enter flow in tables and selects.
    Why: focus fell to the page body after confirms, toggles and login steps.
25. [THOROUGH] Whole-screen critique against the user's goals: for each part, what job does it do; can the user find
    the broken item, act on a reason, trust each number? A dashboard tile that drives no action (no cause, no
    drill-through) is noise: summaries name a cause the user can act on and click through to the rows behind it.
    Why: tiles of "success 72 / failure 1" gave nothing to act on.
26. [THOROUGH] Measured density: estimate row heights; one-line cells, detail in a tooltip, muted "-" for empty.
    The critic prompt states these numbers, not just "read the standard".
    Why: a table cell stacked three lines (about twice the standard height) and passed an audit that did not
    measure.
27. [THOROUGH] Motion and live-sorted lists: pause animations at 25/50/75% and read the frames at desktop and narrow
    sizes; items crossing in flight look like cards (opaque backing in the PARENT panel's colour), never ghosts.
    Why: see-through rows and a text strip peeking between rows were rejected, and a backing in the page colour
    showed as a darker band.
28. [THOROUGH] A view's own component uses a view-prefixed class name, never a bare shared class; a custom
    radio/checkbox pins its padding and size; a select meant to fill a row lifts its max width. Check cell controls
    against the narrowest column.
    Why: shared CSS reshaped a view's step indicator and stretched a radio; a control ran past its column.
29. [THOROUGH] Honest sample data: sample tags on every render, series anchored to real totals, real names only with
    snapshot facts (03 Part A2). Same product = same number, numbers scoped to one place or server name that scope.
    Why: sample figures contradicted real totals beside them.
30. [THOROUGH] After the critic round, append new mistake classes to the ledger and name each gate (03 Part C).
    Why: unrecorded lessons repeat.
