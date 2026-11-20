# 06 - Interaction and quality-of-life rules

Tables, modals, mutation flows, menus, focus, live data. These are the rules users corrected most often.
Tags: **[MUST]** = cheap, catches the defects the user points out most, never skip. **[THOROUGH]** = deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).

---

## 1. Tables

### 1.1 One component, full toolbar
- One shared table component for every list; never hand-roll a table with its own sort or pager. Why: hand-rolled copies drift, and each one loses a different feature.
- Search, filter, sort and pagination are always present. Search may be dropped only on a fixed table of about ten rows that cannot grow. Why: a table that can grow without search becomes unusable.
- One control per job: one search box, one clear-filter button, one selection bar per table. Why: duplicate controls confuse and drift apart.
- Pager appears above AND below every paged table; a table that fits one page may hide it (next rule). Why: users scroll down, lose their place, and had to ask for this repeatedly.
- A single-page client table (rows fit one page) may hide the pager, but the clear-filter control stays in the top toolbar so a filter never strands the user. Why: pager is noise at one page, a stranded filter is a dead end.
- Page sizes are a short fixed set (for example 50 / 100 / 200) with one default; an invalid stored size clamps to the default. Why: stale or odd stored sizes otherwise produce broken pagers.
- Tables hug their rows: no empty band under a 2-5 row table; the minimum height applies only to empty and loading states. Why: dead space looks broken.

### 1.2 Search
- Where users look up records by identifier, search accepts pasted multi-line input (one id/name per line, OR-union). Why: users paste lists from elsewhere and expect all of them found.
- Paste-many search over a loaded picker list is client-side; a page search over the whole dataset is server-side. Why: a client-only search over a capped page silently misses most records.
- Never gate searchable results to the first server page limit. Why: the search then looks complete while covering a fraction of the data.
- On a server-paged table, the search box is either implemented in the query or not rendered. Why: an inert search box tells the user "no matches" when it never searched.
- A search term never goes in a URL or log if it can be sensitive (post it, count-only audit). Why: URLs leak into history and logs.

### 1.3 Filters
- Filtering is per column: a filter-row toggle shows a filter row under the header, with an active-count badge on the toggle. Why: one global search cannot express "status = X and amount > Y".
- Opening the filter row must not change column widths or the table layout. Text filters are compressible inputs; select, range and date filters are one compact button that opens a popover (Enter applies, Esc closes). Why: widths jumping when the row opens made the table unreadable. [THOROUGH] Verify by measuring column widths with the row closed and open: zero change, zero overflow.
- Every active filter shows as a removable chip, plus one "clear filters" control. Why: users could not tell why a list was short or how to get back.
- When a view is narrowed by a click-through (chart bar, tile, link), show a removable chip naming the filter and a "back to all" button at the place the view changed, not only in a toolbar picker. Why: every focus state needs an obvious way back.
- A filter control must truly narrow the result. A list-narrowing control needs a round-trip check: UI state -> request params -> server -> query -> row count, asserting narrowed != unnarrowed. [MUST] Why: a chip that highlights but returns the unfiltered list asserts something false and nothing errors.
- A filter that narrows only the current page while the count beside it counts all rows is a lie. Ask "before or after the page limit?"; a page-scoped count is labelled "in page", never like a total. [MUST] Why: "100 of 2459" under a filter that excluded hundreds.
- Every filter the table mounts with (including defaults) must also be in the server-rendered first-page request, built by the same helper and the same default constant. Why: otherwise first paint is unfiltered while the control claims otherwise, and the first paginate fails on a foreign cursor.
- Adding a filter changes the query identity: reason about pagination cursors, not just rows. Why: cursors minted under the old query become invalid.

### 1.4 Header, columns, sorting
- Header is sticky and opaque, against whichever scroll box the table lives in. Why: translucent or non-sticky headers lose column meaning mid-scroll.
- The table scrolls sideways inside its container; the page body never scrolls horizontally. Tables fit their card. Why: a wide table that widens the page breaks the whole layout.
- Wide tables offer column hide; identity and action columns are never hideable. Do not pin (sticky) columns that can cover data. Why: hidden identity columns make rows unreadable; sticky columns cover data when the table is wider than its box.
- Columns without a set size size to content; an actions column sizes to its buttons. Why: default fixed widths clip action buttons.
- Sort compares the RAW stored value (ISO string, number), never the formatted label; null maps to one end so never-set rows group together. Why: "3 days ago" sorts before "43 days ago" as text.
- A default auto-sort is a default, not a lock: it re-applies only when the filtered state changes, so a header click still sorts. An ordering that encodes policy must not use the auto default at all. Why: a clamp made header clicks do nothing on several tables.
- When the server already ranks rows, a new sortable column must not replace that rank by default. Why: the user reads the top row as "next" and it is not.
- No two columns showing the same value; merge them under one header. The current amount (stock, balance) is always its own visible column. Why: duplicate columns waste width; folded amounts hide the key number.
- Empty cells are a muted dash, not repeated words. Secondary columns are muted; weight goes to identity and the one key value. Why: rows of equal-weight white text read as a wall.
- A number that sums several sources drills down to them (small breakdown with the parts and outliers flagged). Why: an unexplained total cannot be trusted or acted on.
- Memoise column definitions with stable dependencies; an unstable dependency remounts cells on every render and resets per-cell state (open popovers, copied flashes), loudest on polled pages. Why: a 3-second poll closed an open detail modal every 3 seconds.

### 1.5 Counts and honesty on tables
- A page-only count is never labelled as a total. In server mode omit "hidden by filter" counts. Why: a page number read as a total misleads decisions.
- Select-all in server mode is page-scope only; no "select all N matching". Why: a mis-click must not act on thousands of rows.

### 1.6 Selection
- Selection (checkbox column, selection bar) exists only where a real batch action exists. No dead checkboxes. Why: checkboxes that do nothing teach users to distrust controls.
- When rows are selected, a selection bar replaces the search at the same height: "N selected - actions - clear selection". Overflow actions fold into an anchored menu. Every batch action confirms. Why: a bar that changes height shifts the table under the cursor.
- Row click is decided by table type (ruling): a table with a batch action - clicking the row body selects, and the entity-name link opens the detail. Any other table - clicking the row opens the detail modal. Why: both behaviours on one table made users either lose selections or fail to open details.
- Gestures on a selectable table (fine pointer): plain row-body click = exclusive select (clicking an already-selected row keeps it selected alone); Ctrl/Cmd+click = additive toggle; Shift+click = range in the current filtered and sorted order; row checkbox = additive toggle (never exclusive); checkbox + Shift = range; keyboard: focused row + Space/Enter toggles, Shift+Enter ranges, Esc clears. [MUST] Why: a demo that selected only via the checkbox read as broken; users expect desktop-file-manager behaviour. Never invent a different click rule, and prototypes follow the same rules as production.
- Touch: tap on the row body is additive (no modifier keys on a phone); range select is fine-pointer only; a drag or scroll never toggles a row; a swipe must not paint neighbouring checkboxes. Why: exclusive-by-default on touch makes multi-select checkbox-only.
- Header checkbox: click = this page only; Shift+click = all filtered rows in a client-side table (all rows loaded); server-paged tables stay page-scope (see 1.5); checked/indeterminate reflects the current page; tooltip states both. Selection bar says "(this page)" or "(all pages)" when it applies. Why: users cannot otherwise tell what "select all" will act on.
- Selection persists across paging, sorting and filtering; it does not persist across reload and is never stored in preferences. Why: selection across a view change is expected; stale selections after reload are dangerous.
- Selected rows are tinted; selectable rows show hover and a pointer cursor. Why: users must see what is selected and what is clickable.
- Row ids are stable and globally unique across pages. Duplicate ids (or a missing id function) fail closed: no checkboxes, row click disabled, a visible error, and the selection callback is emptied so the action is dead, not just the checkbox. Why: duplicate ids collapsed a whole page into one selection slot and one click selected 100 rows.
- Rows from different sources (seeded vs fetched) must have one shape before they reach the table. Why: a wire-shaped row after page 2 produced undefined ids and mass selection.
- In-row controls (switch, link, button, menu, input) never select the row; mark them with an opt-out attribute. A click inside a portaled modal never toggles a row. A text-drag never toggles a row. [MUST] Why: toggling a switch also selecting its row was a standing annoyance.
- Two tables on one page keep two independent selections. Why: shared state leaks actions across tables.
- Query lock: while a batch or row action is loading, search, filters, sort, paging, selection bar and row clicks are inert; only Cancel stays clickable. Why: input during a write races the write.

### 1.7 Row content
- Any entity named in a row (person, account, order, product) is a drill-through link to its detail view, except staff/author names. Why: a dead name forces a manual search. See section 6.
- Rows may be 40px on dense desktop admin tables (header 34px); touch targets elsewhere are at least 44px. Why: density and tap size are different contexts.
- On phones, tables become row cards or a prioritised compact view; wide content scrolls in its own container. Why: a bare horizontal scroller is unusable on a phone.
- A table with a short-viewport risk caps its height to the pane and scrolls inside its card. [THOROUGH] Check at three viewport sizes. Why: a table ran off the bottom on a shorter screen while the main check only shot one size.

---

## 2. Modals

- Use modals for detail, not drawers or bare page jumps; a list of actions is an anchored menu, never a modal. Why: a centred modal used as a three-item menu was rejected.
- Frame: kicker, title with status pill, copy-link and close (top); facts strip of 4-6 key values; optional sub-tabs; body; footer with a hint on the left and actions on the right. Why: one frame makes every detail screen learnable.
- Close = X = Esc = backdrop click, all through ONE handler; a dirty draft asks before discarding; a dialog whose close is locked during a write also ignores the backdrop. Never add a per-dialog backdrop opt-out; put the guard in the close handler. [MUST] Why: users click outside to dismiss and expect it to work like the close button.
- An outside press while a select, menu or popup is open closes only that popup; on stacked dialogs only the top one closes. Why: one click should not dismiss two layers.
- A modal opened from a modal stacks with a Back control. Deep links open a modal on load (its id lives in the URL). Why: users share and refresh screens.
- Height (ruling): a tabbed modal keeps one fixed height across tabs, with long content scrolling inside the body; a single-body detail modal hugs its content. The control you clicked stays under the cursor when a choice changes content. Why: footers and tab strips jumped when tab content changed; empty bands appeared in sparse modals.
- Show only real fields. No generated references, fixed deadlines or invented history; with no source, leave it out. Why: invented facts look like data.
- One story, one place: no sub-tab that repeats what another part of the modal already shows (for example no "history" tab beside timeline steps). Why: duplicate stories drift and waste attention.
- Actions with related outcomes are ONE action with the outcomes inside: radio options, each with a bold plain-words name and a one-line consequence; fields appear only for the chosen option; the result toast lists per-item outcomes with reasons. Never two sibling buttons whose difference only an engineer knows. Why: two near-identical buttons were misread and misused.
- The same entity offers one action set and one vocabulary wherever it opens (row, modal, global modal). Why: different actions per surface for one state confuse users.
- Defaults: no context means "all" or a forced choice; default to an entity that has data; validation errors show after interaction or submit, not under an untouched field. Why: a default pointing at an empty entity or a premature red error misleads.

---

## 3. Mutation flow

Every write follows this order:
1. Show a before -> after preview of the change (with numbers, e.g. "25 back on sale, 6 keep running").
2. Require a reason where money, points, rank or access changes.
3. Confirm with a dialog that names the action; danger tone if irreversible; focus lands on Cancel for danger confirms (never autofocus a destructive or overwrite button).
4. Lock the UI while loading: all actions inert except Cancel; the dialog says what is happening.
5. Re-render counts, badges, hero numbers and any open modal from the new state BEFORE the success toast; reopening must show only the new state.
6. Toast the result (success and error); errors name the cause.

- Never use `alert()` or native `confirm()`; use the shared toast and confirm components. [MUST] Why: they block, cannot be styled, and are inconsistent.
- Every destructive action confirms, single AND batch. Why: unconfirmed bulk delete is a bug.
- Status-changing actions appear only in states that allow them; an empty target refuses with a reason instead of opening a "0 items" dialog with Send enabled. Why: a button that cannot succeed is a trap.
- Confirm text promises only what is built; say what will happen with numbers, or drop the sentence. Why: a confirm claiming a rule "can be cancelled" when it could not was a lie.
- Show a before/after for comparisons: "previous -> current", not only the delta. Why: a bare % hides the baseline.
- Where a mutation needs input, the bar or button owns confirm, lock, toast summary and done-callback; the form lives in its own modal. Why: a bar that renders fields becomes a second table component.

---

## 4. Menus, focus, keyboard

- A menu is anchored to its trigger button everywhere, including inside modals and scrollers. Why: menus opening at screen centre or a corner looked broken.
- Every action closes its launching menu through one shared path; reopening lists only the current state's actions. Why: a stale open menu hovered over other rows with outdated actions.
- Risky menu items go last, after a separator, in red, and are confirmed. Why: a red item mid-menu invites mis-clicks.
- Focus returns to the opener on close; re-mount keeps the focused control; focus never falls to the document body after Esc, a confirm, an inline toggle, a batch apply or a re-render. [MUST] Why: lost focus breaks keyboard flow. Menus rove with arrows, Home/End, and Esc returns to the trigger.
- Every control works or is disabled with a stated reason. A control that renders and does nothing (toast stub, dead-end list, no-op footer action) is a defect. [MUST] Why: silent dead controls erode trust.
- A control that implies a state change must be wired end to end: a boolean sent as the wrong type may be read as "unchanged" and still toast success. Trace client expression -> request body -> server guard -> writer. [THOROUGH] Why: tsc and single-side tests pass; only the trace exposes it.
- Controls never shift when used: segmented options reserve their bold width; a header shows the same content in every mode (disable an option instead of hiding it); legends live in the card body. Why: a toggle moving under the cursor on click was rejected.
- One selected-state look across segmented controls, chips and tabs; never an inverted full-ink fill that out-shouts the data. Why: the selected filter must not be the brightest thing on screen.
- Quiet defaults: show a status pill only when the state is not normal. Why: pills on every row bury the exceptions.
- Hover reactions: interactive rows, cells and marks visibly react on hover; hover cards stay one line, never cover their own detail or row, and anything the reader needs is visible content, not hover-only. [THOROUGH] Screenshot every hover and focus card OPEN. Why: a tall hover card covered the breakdown it described.
- Desktop vs touch: hover is an enhancement on fine pointers only; every hover-only information or action has a touch path (tap, long-press, visible control). Why: phones have no hover.
- Copy buttons: icon-only copy controls with idle / loading / copied / error states and a toast on failure; one control visible for the target (selection when rows are selected, all filtered otherwise), showing the eligible count. Why: copy flows with no feedback leave users unsure whether it worked.
- Interactive targets are at least 44px on touch; dense desktop admin rows may be 40px. Why: small targets cause mis-taps.
- Never put keyboard listeners on the whole document that paginate more than one table; turn arrow-key paging off for a table inside a modal over another table. Why: one keypress paginated two tables.

---

## 5. State in the URL, live data

- View state a colleague would paste in chat lives in the URL: tab, period, sub-view, filters, sort, and the id of an open modal. Use a plain GET form or link for query-only changes, not a client router push. Why: links and refresh must restore the exact screen.
- Live updates patch rows; they never reset a focused input (value and caret survive), close an open popover, or remount a view. A refresh of the same window keeps the previous data on screen (stale-while-revalidate) and read keys use the stable window, never "now". [MUST] Why: a polling repaint reversed typed text, and a 30 s refresh swapped a chart to Loading and closed its hover card.
- Refresh on a timer only while the tab is visible; show a live / paused / stale indicator with pause and reload. Where push exists, show connection state. Why: hidden tabs should not poll, and users must know how fresh the screen is.
- Search results from a global search group by kind and match every identifier the old pages matched (ids, names, email, linked records). Why: a narrower search is a silent regression.
- Wire panel states (loading, empty, error with retry) per panel from the page; one failing panel never blanks its neighbours. Why: a state prop the page never passes is decorative.

---

## 6. Drill-through and consistency

- Every entity reference (customer name, username, id; order; product; account) in any list, modal, ledger, funnel or chart result is a link opening that entity's detail view. Plain text is a defect. [MUST] Why: a modal listing customers with no link forced manual searching. Every QoL audit brief and UI task carries a "drill-through" line.
- Clicking a chart bar, segment, tile or cell opens the matching list or modal, and the count in the list equals the figure it came from. Why: a clickable chart that stops partway looked broken.
- When one chart or card family has the interaction, sweep every sibling in the same family for the same gap in the same pass. [MUST] Why: fixing one chart and listing the other five as questions wasted a round.
- One component per pattern across tabs and pages: one metric tile, one pill, one chip, one filter-row layout, one product label. Why: parallel authors drifted into four dialects.
- Every product (or similarly-named entity) list shows its disambiguating category beside the name, because names repeat across categories. Why: same-named items from different categories were indistinguishable.
- Extend an existing surface or tab rather than building a duplicate one. Why: duplicate surfaces drift apart.
- Reuse one shared hook/component for any state that two pages need; do not copy it per page. Why: duplicated implementations get fixed on one side only.
