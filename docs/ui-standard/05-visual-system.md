# 05 - Visual System: colour, density, layout

Portable rules for colour meaning, density/typography and layout. Each rule is one line plus a "Why:" naming the defect it prevents.

- **[MUST]** - cheap, catches the defects the user points out most, never skip.
- **[THOROUGH]** - deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).
- Untagged lines are design rules.

---

## A. Colour semantics

### A1. The palette: five hues, each with one family of meanings

| Colour | Meaning (each hue has one family of meanings) |
|---|---|
| Green | Good: healthy, done, saved, goal reached. The one fully saturated hue. |
| Blue | Actively running / in progress. Also action, selection, info. |
| Red | Bad: failed, broken, blocked, unsafe. One red; the reason is text, not a second hue. |
| Grey | Neutral state: idle, queued, scheduled, upcoming, ended, disabled, unknown, expected absence. |
| Amber | Only "the user must decide or act". Never a softer red, a hint, or a category. |

- Status palette = five hues, each a family of meanings (blue: in progress / action / selection; grey: neutral / queued / scheduled / ended / disabled / unknown). Use only these five hues for status. Chart categorical hues are a separate thing: they are not capped and are chosen by whoever leads the UI work (the person or agent responsible for the screen's design decisions). Add no extra status-like hue (violet, teal, orange, pink, cyan, indigo) for variety.
  Why: extra hues were shipped for "variety" and the user read each one as a meaning that did not exist.
- Use plain, normal red / green / blue. Tints and pills use soft versions; nothing neon or high-contrast.
  Why: the user rejected a "contrasty" custom palette: "normal red green blue is ok".
- Amber only when the user must decide. System waiting, a customer reservation, nothing-to-send and a recoverable state the system clears itself are blue or grey, never amber.
  Why: amber on system waiting was repeated in many rounds and made every amber unreadable as "needs me".
- Active progress is blue; queued, scheduled, upcoming and ended are grey. A scheduled item is never blue.
  Why: blue means "running now"; blue for "scheduled" made two different states look identical.
- A finished progress value is green, an in-progress one blue (100% bars are not blue).
  Why: state colour follows the outcome; a done bar in the in-progress colour reads as unfinished.
- Red is for real problems only. A normal action button is neutral, a "sold out" or "expected" state is grey, and a time-running-out countdown is bold ink, not red. One red hero per incident, on the page that owns it; elsewhere a muted line plus link.
  Why: red on non-problems (normal buttons, a red hero on every sub-view) trained users to ignore red.
- Error styling is never used for good news; show success/info outcomes in a success/info card.
  Why: a success message in a plain red error slot read as a failure.

### A2. Colour never works alone

- Colour is never the only signal: every status colour ships with an icon and a label (and shape/position where relevant).
  Why: colour-only state fails colour-blind users and greyscale prints.
- Unknown or future values are explicit in text and neutral in tone; they never imply success.
  Why: a neutral-looking blank next to green was read as "fine".
- Data values are never grey. Values use a semantic tone or a chart hue chosen by meaning; grey is for neutral states and for a folded "other" group.
  Why: grey/dim data bars were rejected on sight as "still dim colour". Grey *states* (an ended segment, a disabled control) are allowed; the ban is on values.
- A partial period or a row state is never shown by dimming (opacity). Only the status pill carries row state; a partial bar keeps its series colour and says so in the axis label and tooltip.
  Why: a 50%-opacity current-month bar read as "disabled", and a dimmed row duplicated its own pill.
- Status pills show only when the state is not normal.
  Why: a pill on every row out-shouts the data.

### A3. One fact = one colour = one label

- Keep ONE token table (a single map from meaning to colour value, used by every component) covering light and dark. Every surface reads from it; no component picks its own colour.
  Why: the same fact drew amber in one place and blue in another, grey in one modal and red in the next.
- A meaning that already has a token never gets a second colour or a second definition. A genuinely new meaning gets exactly ONE new token (light + dark) added to the table in the same change.
  Why: parallel definitions drift; a fix to one copy leaves the other wrong.
- One meaning per colour inside one view/chart: if green means "good" there, nothing else in it is green for another reason.
  Why: a category hue that equals a status hue reads as a status it is not.
- Use tokens only; no raw hex in components. Use the product's own theme tokens, never the framework's defaults (radius, fonts, colours).
  Why: a reused markup block rendered with the framework's default radius scale instead of the product's, and the user noticed every squarer button.
- Text red and fill red may need two tokens. If the dark-theme "danger" used for text fails 4.5:1 on cards/popovers while the stronger value is wanted for borders, icons and fills, split it: a text token (lighter in dark) and a "strong" token for borders, rings, backgrounds, solid fills and SVG marks. A solid red background with white text uses the strong token.
  Why: one token cannot serve both text contrast and a strong red mark; the user wanted both and measured text at 4.43:1.
- Disabled controls are neutral and readable in both themes (text >= 4.5:1); never faded red; the disabled rule must out-rank other rules.
  Why: faded red disabled buttons, then near-black-on-grey text at 1.2:1 in dark.

### A4. Categories, identity colours, sub-types

- Category colour is split by surface:
  - **Charts:** categorical series get clearly different hues, chosen by meaning per chart by whoever leads the UI work. No fixed cap on categories; a long, small tail may be folded into one grey "other" when that reads better. (Details in 08-charts.md.)
  - **Cards, lists, pills:** colour = state only. Category is shown by icon or label, not by a hue per category.
  Why: a hue per category on cards made every card look "meaningful" and hid the real state; a grid of grey cards looked like a wireframe, so state gets colour and category gets an icon.
- A card grid shows state with colour: blue tint = in progress / taking part, green = goal reached or unlocked, red = failed or blocked only, grey = upcoming or ended. Each category keeps its own icon, not its own hue.
  Why: an all black/white/grey grid told the user nothing about which item was live, theirs or done.
- Keep established colours. Before any colour change, list what the surface shows today and keep it unless the user asked to change it; an established identity colour (a payment method, a rank, a brand mark) is never recoloured by stretching a rule past its scope. Mark such elements as identity exceptions so a colour audit exempts only them.
  Why: a whole established chart was recoloured blue to apply a rule that did not cover it; the user: "r u serious???".
- A sub-type of an existing category takes a tint/tone of its PARENT's hue, never a new hue. Mix toward white, not toward a dark surface (mixing toward dark turns orange brown).
  Why: splitting one category by adding a new pink hue was rejected: "use orange with orange family... why new color??".
- A flag/label pill has ONE tone per meaning, each from a token, never a raw colour; flags are facts, so amber is never a flag tone.
  Why: a flag meaning silently picked its own hue and collided with the neutral fallback.
- A category pill (a method, a type) is visibly different from a status pill: dot in the category colour + plain text on a faint tint, versus coloured text + icon for status. Put the status pill beside it; never merge them. A null value shows a muted "-", never an empty pill.
  Why: a category pill that looked like a status was read as good/bad.
- A card/row that reuses a category set takes its label + colour from ONE map, never a local copy.
  Why: local label/colour maps drift apart.

### A5. Contrast, surfaces, portals

- Contrast floors: ordinary text 4.5:1, large text 3:1, meaningful UI components and keyboard focus indicators 3:1.
  Why: the user rejected low-contrast surfaces and a dark-mode button with white text on near-white.
- Surfaces are opaque in both themes: cards, notices, sticky table headers and overlays never let page art show through. Text is never laid directly on background art.
  Why: translucent status cards and text over art were rejected as unreadable.
- Dialogs, menus, popovers and other portals leave the page's DOM tree, so they must receive the same colour scope/tokens explicitly. Cover every dialog, confirmation, filter menu, column menu and nested portal.
  Why: portaled dialogs rendered with default colours while the page was themed.
- A class name or CSS variable that exists proves nothing: confirm the utility is actually generated by the build and the computed colour is right.
  Why: a status variable existed while its utility class registration was missing, so nothing was coloured.
- **[MUST]** Verify colours by computed value in BOTH light and dark, not by source or class string. Check text, icons, borders, selected tints, hover, focus, error, disabled and dialog/menu states.
  Why: a colour fix verified in one theme left the other wrong (brown instead of amber, a key sentence false in dark).
- **[MUST]** Walk every screenshot for: a hue outside the palette (and not a marked identity exception), an amber that is not a user decision, grey data, one fact in two colours.
  Why: designer self-QA passed all of these and the user caught them at a glance.
- **[THOROUGH]** Review the light and dark shots of the SAME state as a pair, and cover desktop + narrow widths for every colour fix.
  Why: a meter was 72px wide in light and full width in dark because of a theme branch.

---

## B. Density and typography (dense UIs)

- Dense desktop rows: table row ~40px, header ~34px, card padding 12-14px, card radius ~12px. Body 14px, table 13px, captions 12px, headline numbers 24px / 700. Tabular figures wherever numbers line up.
  Why: legacy pages were loose and unscannable; the approved standard is compact.
- 12px is the floor for any text; use type tokens, never raw 11px.
  Why: sub-12px text was illegible (and breaks tone marks in some scripts).
- Touch/mobile targets are at least 44x44px (padding or an invisible hit area; do not just inflate the visual). Dense desktop rows may be 40px; that is the only exception.
  Why: 40px rows are fine for a pointer; a thumb needs 44px.
- Use a fixed type/weight scale (12 / 13 / 14 / 24 px: captions / table / body / headline; weights 400/600/700) and standard container widths; no ad-hoc 11/15/17/20px sizes.
  Why: ad-hoc sizes made parallel authors' screens look like four dialects.
- Hierarchy comes from size, weight and spacing, not colour. Status colour is reserved for state. One primary focus per screen, at most ~3 competing emphases; secondary text goes into a tooltip.
  Why: a second boxed stat strip put 12 boxes before the main chart ("too many text, dirty").
- One font family from the product; one icon family at a consistent stroke; no emoji as icons; every icon id must resolve (an unknown id renders a blank gap).
  Why: an unknown icon name left an empty hole inside every button.
- Short copy: labels of 1-3 plain words, explanation in an (i) tooltip, no developer text, raw codes or internal names in the UI (keep a raw code in a copyable tooltip). Use the user's own word for a state everywhere (one label table), and an English/common noun when clearer than a stiff translation.
  Why: raw engine strings and synonyms for the user's own terms were rejected on sight.
- Every number carries its unit; a label names exactly the quantity shown.
  Why: "per hour 83" had no unit; a "last synced" label showed a start time.
- One time formatter per surface; use the relative and absolute ladders in 07-data-honesty.md (do not define another here).
  Why: "0 s ago", "15:30" and "7 h ago" appeared for one action.

---

## C. Layout

### C1. Structure

- One view = one job. Top-level tabs use short words; how many is the call of whoever leads the UI work. Then an optional sub-view segmented control, then content. Never mix unrelated jobs into one place just because they share data.
  Why: four independent groups stacked on one page forced several screens of scrolling to find one.
- No long multi-segment scroll pages. A "jump to" chip row, anchors or a table of contents do NOT fix it; they decorate it. Split independent segments into sub-views or master-detail (list left, selected segment right).
  Why: a long stacked tab was rejected even with jump links.
- Desktop dashboards do not page-scroll: the default view fits ~1440x900. Long lists and tables scroll inside their own card, with a visible cue (edge fade or "N more"); full-height views cap to the pane (flex:1; min-height:0) and let toolbars shrink.
  Why: a table ran off a shorter screen with no height guard; rows hidden in an inner scroller read as missing.
- Filters live on ONE compact inline row directly under the tabs (range, scope pickers, "updated" time, at most one primary action). A long hint becomes an (i) tooltip; the row wraps cleanly when narrow.
  Why: filters alone on a near-empty row, or range and scope on separate rows, wasted space ("bad empty space").
- Sibling tabs and pages in one area share the same components and look: one metric tile, one pill, one chip, one filter-row layout, one shell. Never a local copy per tab.
  Why: a tab built with a different card/chip/table style than its siblings was rejected; parallel authors drifted into four dialects.
- An expansion shows only what its row cannot (how a number was built, a chart, history), not values already in the row's columns.
  Why: cards in an opened row repeated the row's own cost/price/margin.
- Extend an existing surface in place instead of building a new tab that duplicates a live one; list the live parts and classify each new part as duplicate / overlap / new first.
  Why: a new tab rebuilt 8 of 14 existing parts ("dont build something dup").

### C2. Compactness

- Stat strips are compact: one short row of small tiles, label and value close together. No tall full-width boxes with a tiny label over one number.
  Why: tall stat cells were rejected repeatedly ("make 3 kpi card be compact").
- No full-width summary bars as their own band. Draw a segmented summary compactly next to or under the table or chart it filters.
  Why: a long full-width problem/reason bar added height and no information.
- The same count is shown ONCE. Pick the place that also acts (a filter chip, the pager) and move any behaviour of the removed copy onto it; footers carry sums only. When two related populations overlap, show the bridge (A . B . C) with the arithmetic in an (i).
  Why: the same per-type counts appeared as chips, legend and badges; related counts did not add up for a reader.
- Key-value rows: label beside value at content width: a fixed muted label column (~9rem), value LEFT-aligned beside it, list capped (~40rem); fact strips shrink-to-fit. Never justify label and value to opposite ends of a wide container; check every tab of a modal, not only the one you shot.
  Why: the user said "I ask you multiple times": labels at far left and values at far right across a wide modal; each fix touched only the rows in front of it.
- A field is as wide as its value: numbers ~10ch with the unit beside, times and dates fixed small, short selects content-width; only free text is wide. One shared rule for all tabs and modals.
  Why: a "3 minutes" field filled half the page with the unit pushed far right.
- A card head holds the title, an (i) and tools only; extra facts go on their own short line under the head.
  Why: longer head copy wrapped the title and pushed the view switch past the card edge.
- Controls never shift when used: segmented options reserve their bold width; a header keeps the same content in every mode (disable an option instead of hiding it).
  Why: toggles that moved under the cursor on click were rejected.

### C3. State, selection, status

- Selected state uses the segmented-control look (a tint/outline), never an inverted full-ink fill. The selected filter must not be the brightest thing on screen.
  Why: an inverted chip out-shouted the data.
- No duplicate controls: one way to do each job (no exact-id field when search matches ids; no row button repeating the row click).
  Why: duplicate controls made users unsure which one was real.
- Every focus/filter state has an obvious way back: a removable chip naming the filter, plus a "back to all" at the place where the view changed.
  Why: a filter set from a chart was hard to clear.
- A control that renders must work; if it cannot be wired, say so rather than showing it enabled. A disabled action states why beside it.
  Why: a filter that filtered nothing, and grey buttons with no reason, were worse than none.
- Sticky table headers are opaque; the whole header cell is the click target (not only its text), with hover tint, focus ring and Enter/Space.
  Why: text-only hit areas on header cells were missed.
- Unchanged values are not shown as changes: a before -> after row shows only fields that change.
  Why: "7% -> 7%" implied a change.

### C4. Modals and menus (layout parts)

- Modal height: a tabbed modal keeps ONE fixed height across tabs (long content scrolls inside the body behind an edge fade, footer never moves); a single-body detail modal hugs its content.
  Why: a footer that jumped between tabs, and half-empty full-height detail modals, were both rejected.
- Use modals, not drawers, for detail on one shared shell with a few standard widths and a sticky footer. An action list is an anchored menu (anchored to the clicked button, also inside modals and scrollers), never a centred modal. No chevrons on actions; risky items last, after a separator, red and confirmed.
  Why: a centred modal used as a 3-item menu was rejected as "bad modal".
- Close = X = Esc = backdrop through one handler; a dirty draft asks first. After any action, the launching menu closes through one shared path and the open modal rebuilds from the new state.
  Why: a stale menu stayed open over other rows with old actions.

### C5. Overflow

- Text never overflows or truncates over a digit. A line carrying a figure is shortened in copy until it fits; ellipsis is for names only, with a tooltip. Every text box fits at the widths you target after inner scrollers are scrolled to their end.
  Why: KPI sub-lines read "Email 433 · Guest 120 · Web ..." - the figures the line existed for were cut.
- A table fits its card at your smallest supported desktop width: low-value columns hide first (their value moves into a neighbour as a second line); a multi-chip cell shows one chip plus "+N"; a table that truly cannot fit scrolls inside its card with an edge fade. The page body never scrolls sideways.
  Why: columns and chips were cut at 1280px.
- Tab / chip / sub-nav rows on narrow screens scroll horizontally with an edge fade, never wrap or clip; dialogs never scroll sideways.
  Why: tab rows wrapped to 2-4 lines at phone width.
- A cell control is width:100%; min-width:0; never a min-width wider than its narrowest column. A view's own component gets a view-prefixed class, never a bare shared class name (shared CSS reshapes it).
  Why: a fixed min-width select ran past its column; a shared class name boxed a different component.
- A hover card inside a table or expansion stays short and clears the WHOLE row; content the reader needs is visible content, never only a hover card. Open every hover/focus card in a screenshot before calling the screen done.
  Why: a tall cost card covered the very row it explained.

### C6. Desktop-first vs mobile-first

- Dense tools (admin, operator, back-office) are desktop-first: mobile must stay clean and unbroken but need not be rich, and a mobile-only cosmetic issue does not block shipping. Still capture one phone shot to catch real breakage (overlap, unusable controls).
  Why: the user: "mobile ui is lower priority, main is desktop use".
- Consumer-facing surfaces are mobile-first, with 44px targets and no horizontal page scroll.
  Why: customers use phones; dense-tool leniency does not apply to them.
- Prove layout in a real browser at the user's actual viewport. Measure their screenshot (image px / pixel ratio, sidebar width) and audit there plus breakpoint edges, not a viewport guessed from a device name.
  Why: an audit at 1440 never showed a card pushed to a third row at ~1280.
- **[MUST]** Screenshot every view and modal tab at desktop dark + light and one phone width; scroll every inner scroller to its end before judging clipping.
  Why: a viewport-only sweep missed content below the fold for many rounds.
- **[THOROUGH]** Run an independent critic over the full theme x width matrix with its own screenshots and real clicks before the user sees it; every new layout probe must first FAIL on the previous round's build.
  Why: a probe blind to the last bug is not a gate.
