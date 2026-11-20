# 08 - Charts and timelines

Portable rules for choosing, colouring and verifying charts and time axes. Each rule is one line plus a "Why:" naming the defect it prevents. Colour meanings are defined in 05-visual-system.md; this file only applies them to charts.

- **[MUST]** - cheap, catches the defects the user points out most, never skip.
- **[THOROUGH]** - deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).
- Untagged lines are design rules.

---

## A. Choosing the form

- Pick the chart form from the data's job; never default to a line.
  Why: one default line chart for everything hid ranking, composition and comparison.

| Job | Form |
|---|---|
| Progress so far vs a comparable period | Cumulative area + dashed ghost of the comparison + a "now" marker |
| Value per bucket vs previous period | Columns; previous period = a tick across each column |
| Ranking / contribution | Ranked horizontal bars with share % and delta chip; change mode = diverging bars |
| Comparing chosen entities | Picker (<= ~6) then small multiples on ONE shared scale, or totals with a previous tick |
| An all-entities total that hides who drives it | An "all / split" switch; split = stacked by entity, legend names open that entity; give split mode the height it needs |
| Day by day | Heat calendar that follows the selected period; compact cells; per-week total |
| Two time dimensions (weekday x hour) | Heatmap, one sequential scale (below); hours grouped into day-parts with gaps |
| Part-to-whole / status mix | 100% stacked bar + legend list with count and % |
| Mix over time | Stacked columns with small gaps |
| Value vs target | Bullet bar with zones and a target line |
| Two measures per entity | Quadrant bubble with median lines; label only the top few |

- Activity-type charts show composition (stack by event kind), compare with the previous period, and let a click on a bucket filter the list below.
  Why: a bare count per bucket did not say what kind of activity drove it.
- Do not merge two metric charts into one paired chart unless the user asks for that exact form.
  Why: merging "reached target" and "sold" into one paired-bar chart was rejected as not working.
- Heatmap: ONE sequential scale (single hue), light = low, dark = high, zero = a dashed empty cell, the same scale in both themes; more = full opacity, less = faint. A legend must document the actual mapping (a linear gradient must not describe a sqrt scale).
  Why: a per-theme or mismatched scale made the same cell read as two different values.
- Charts have a capped, natural height (main ~260-340px, small multiples ~120-160px, compact cells for heatmaps/calendars). Never stretch a chart to fill the screen; use leftover space for compact companions (best/worst, averages, change vs previous, top movers).
  Why: a sales chart that filled the whole screen pushed every other fact below the fold.
- Never draw bars/columns/meters by hand (CSS boxes sized from a value, square tops, no hover). Use the shared chart components so every bar has rounded ends and the standard tooltip. When asked to standardise a visual, scout the WHOLE area by data shape (values driving height/width, svg rects, "bar"/"seg" classes, meters, mini row bars); fixing only the screen in front of you is a miss.
  Why: hand-drawn bars were off-format and had no hover; fixing one screen left the rest.
- A progress value the user works toward gets a bar, not only text ("2/3", "880/1,000"): value from data, `role="progressbar"` with aria-valuenow / aria-valuemax, blue while in progress, green when done.
  Why: progress printed as text only gave no sense of how far along.
- A summary tile names a cause the user can act on and drills to the rows behind it; a count with no drill and no decision is noise.
  Why: "succeeded 72 / failed 1" gave nothing to act on; the user wanted exit reasons, each clickable.

## B. Colour by meaning

- Before colouring a chart, name what each series MEANS, then pick; write the chosen mapping and its reason into the work packet so a critic checks the meaning, not the hue family.
  Why: chart hues were chosen by feel and the user read them as meaning.

| Series meaning | Colour |
|---|---|
| Good / bad / in progress / neutral | Green / red / blue / grey |
| Direction around zero (in vs out, earned vs spent) | Use green/red only when "in" means gain (good) and "out" means loss (bad): in = green pair, out = red pair; otherwise use non-status hues. A secondary series is a lighter tone of the SAME hue, never another hue |
| Health or stage of a thing (customer segments, funnel) | By meaning: healthy/done green, new/in progress blue, at risk light red, lost/failed red, not started/other grey |
| Distinct categories with no good/bad meaning | Clearly DIFFERENT hues a reader tells apart at a glance, chosen by whoever leads the UI work (defined in 05 A4); no fixed cap; they may fold a long small tail into one grey "other" |
| One measure across ordered steps (histogram, ladder, heatmap intensity) | One hue, tonal steps. The ONLY place a single-hue family is right |

- Never draw different categories as shades of one hue.
  Why: all-blue charts were rejected: "lead must decide the appropriate color. not strictly blue."
- Status colour as a series: meaning wins. A series that means good, bad or in progress uses that status colour; other series use non-status hues. One meaning per colour inside one chart (nothing else in a "good" chart is green for another reason).
  Why: a category hue equal to a status hue reads as a status it is not.
- Key colour on a fixed entity list captured from the unfiltered set, never on render order or the filtered set. Filtering must not repaint survivors, and an "other" bucket gets its own name.
  Why: a category changed shade when the split changed.
- Use the same colours in the legend, list and tooltip swatches. Every series keeps a text label; text is never drawn in a series colour.
  Why: swatches that disagreed with the marks made the legend untrustworthy.
- Established identity colours (a category with a production colour) are kept and marked as identity exceptions, not forced into the palette.
  Why: forcing identity colours into blues was rejected by the user.
- Never use grey/dim bars for data; ended/exit segments in a timeline may be grey because grey = the ended state.
  Why: dim data bars were rejected ("still dim colour"); the ban is on values, not states.
- Do not generate or cycle extra hues past the available ones.
  Why: cycling colours implied meaning that does not exist.

## C. Marks, axes, legends

- Every mark reacts: hover and keyboard focus show a tooltip with exact values; the hovered/focused mark stays at full strength while the others fade (~150 ms, using fill-opacity/stroke-opacity only, see 09-motion.md); arrow keys move between marks; click drills into the matching list. Decorations (now-line, grid, axes) never take pointer events. Applies to every chart, including KPI micro-charts.
  Why: users could not tell which bar they were reading; a bare title attribute is not enough.
- Whole-bar hit areas: the invisible hit rects of a chart must be transparent (not default black) in every context the chart is placed.
  Why: a chart dropped into a card without its chart class painted a black slab behind the plot.
- One y-axis per plot. Two measures = two charts. Nice tick steps (0, 10, 20; never 12.5). Gridlines are solid hairlines (dashed reads as a threshold).
  Why: two scales on one grid assert a correlation the data does not contain.
- Legend only for 2+ series (one series: the title names it), and it shows exactly the marks drawn - no key for an absent mark, no drawn mark without a key. A collapsed mark takes the worst state it hides. Keep it one line (extra entries in an info popover).
  Why: legends listed marks not on screen and omitted marks that were.
- Category axes never skip labels; only time axes thin out. Labels that do not fit get shorter or wrap, never vanish.
  Why: a 5-group chart dropped two group labels at 1280px.
- Segments always sum to the drawn bar height and to the printed total; an over-target/excess state is visibly flagged. No floating segments or detached target ticks.
  Why: a "today" column lost its segment and a label hovered over a shorter bar.
- Markers (events, pills) live on a reserved strip or in gaps, never over a bar; the hover time label sits in the opaque axis band; when there is no room, collapse into the tooltip.
  Why: pills drawn over bar ends were rejected ("overlap pill + bar").
- Compact lanes use one-line labels (detail in the tooltip) or size to the label.
  Why: two-line labels were clipped in short lanes.
- Comparisons show both sides: previous -> current, not only a delta or %.
  Why: "vs last week +12%" without the two values could not be checked.
- A partial (current) period keeps the normal series colour and is labelled in the axis label and tooltip ("this month, to the 15th"), never dimmed.
  Why: a 50%-opacity bar read as disabled, and the hover fade made it near-invisible.
- Never encode meaning in opacity inside a chart (except the heatmap intensity scale).
  Why: opacity-as-meaning reads as disabled/less, not as data.
- A figure set against a budget or target uses that budget's own period (month-to-date for a monthly budget) and says so in its label.
  Why: a rolling 30-day figure was compared with a monthly budget.
- Reads of the same data must agree: one shared helper per derived fact; headline, legend and table footer derive from the SAME rows and window.
  Why: a headline, its legend and its footer each summed a different set.

## D. States, twins, accessibility

- Every chart has a table twin (a toggle to the same data as a table). A chart is never the only way to read a value.
  Why: low-contrast categorical marks and screen-reader users need a non-visual path.
- Every chart panel has its own loading, empty, error-with-retry and partial states, wired per panel; one failing panel never blanks its neighbours. Partial data is shown as partial, never as zero; no basis renders a dash, and "n/m" shows partial coverage. A zero never stands in for unknown.
  Why: a primitive that accepted a state prop nobody passed was decorative, and a zero for unknown made a proxy look like a fact.
- Snapshot panels state "as of" time; live panels show live / paused / stale.
  Why: without a timestamp the user cannot judge whether to act.
- Keep the previous data on screen while a same-window refresh loads (stale-while-revalidate); read keys use a stable window, never "now"; hover state survives a same-data re-render.
  Why: a 30 s refresh remounted the chart to Loading and closed the open tooltip ("blink").
- A chart is not a role="img" with only a title; give it a textual alternative and keyboard parity.
  Why: an image role with no text gave screen readers nothing.
- Chart containers need an explicit height: a percentage height resolves against the parent's height, not its min-height, and collapses to zero otherwise. Legends and tables flow outside the plot stage. Do not wrap non-chart-library content (a div-tree heatmap) in a responsive container.
  Why: a chart collapsed to zero height in the browser while tests stayed green.
- Label every metric with its population ("Orders paid" / "Orders placed"); each label must be re-derivable from its query; one row = one cohort.
  Why: a "net income" label over a sales query was read as profit.
- Put view state a colleague would paste in chat (tab, period, granularity, measure, filter) in the URL.
  Why: shared links must restore the exact screen.
- Sample/demo data: tag every sample figure wherever it renders, anchor sample series to the real totals beside them, and never put invented facts on a real person.
  Why: a sample series contradicted the real KPI beside it.

## E. Timelines and time axes

Apply to positional time axes and time-bucketed bars; mark an item N/A with a reason when it has no concept in the chart.

- Positional axes MUST zoom: zoom presets (24h / 7d / 30d only when shorter than the range, All), zoom in/out, reset; preset buttons expose aria-pressed.
  Why: a fixed full-range axis made short events unreadable.
- Gestures: Ctrl/Cmd + wheel and pinch zoom around the pointer, drag empty plot space to pan, Shift-drag brush to zoom, double-click an event to fit it. Plain wheel still scrolls the page. Keyboard on the focused plot: + - 0 and arrow keys.
  Why: zoom that traps page scrolling, or is mouse-only, is unusable.
- One clamped view window inside the full range with a minimum span (~5 minutes); every mark, tick, cursor and guide uses the same time-to-position mapping; ticks recompute from the view; under 24h show time only.
  Why: separate mappings drifted so marks and ticks disagreed.
- Put a draggable, resizable overview strip under the axis whenever the range exceeds 24h, showing the whole range, faint marks and the current window.
  Why: users lost their place when zoomed.
- Store zoom bounds in the URL (minute-precision ISO); restore valid bounds and drop malformed or stale values. Do not animate zoom.
  Why: shared links must reopen the same view; animated zoom adds lag and motion sickness.
- Interval bars are at least ~4px wide; narrower intervals use a raised stem-and-pin above the bar at the same time position with a keyboard-reachable target; never lay a tiny dot on the next bar. Group colliding marks into a count pin and keep every item reachable in the evidence card; zooming must separate them again. Collision grouping may fold same-lane neighbours, never the latest event into another lane's marker.
  Why: unreadable tiny dots and a vanished "latest" marker hid real events.
- Clip marks at the view edges and show a small edge arrow.
  Why: marks half cut at the edge looked like rendering bugs.
- A proposed/non-executed event is a visibly distinct marker (e.g. dashed diamond), never the same as executed work.
  Why: a plan drawn like a fact misled the reader.
- One event, one mark: do not draw a marker row repeating what a bar already encodes; the bar itself is the named button carrying the evidence.
  Why: duplicate marks doubled the visual noise and the click targets.
- One entity, one story: a chart may not show "unknown" for an event another surface of the same entity explains; every evidence source a sibling surface reads must feed every chart that draws that event. Grey/unknown means no source anywhere has it.
  Why: grey exits in one chart were fully explained in the detail view.
- Multi-row plots draw each day boundary as one shared, non-interactive full-height guide across all rows, above opaque bars but below pins and overlays, labelled on the axis.
  Why: per-row boundary gaps broke continuity across rows.
- Hide phase captions when a segment is narrower than ~32 minutes or ~40px.
  Why: captions on tiny segments overlapped and were unreadable.
- Colour status by severity: confirmed terminal failures red; pending, unknown, cleared and unsupported evidence neutral/muted.
  Why: neutral evidence painted red cried wolf.
- Touch: with no hover, open no hover card; a tap opens the detail. Every mark is a named button; wide grids are focusable and scroll with arrow keys.
  Why: hover-only detail does not exist on touch.
- Evidence cards expose role="tooltip" and aria-describedby; Escape closes the topmost popup/card/dialog in order and restores focus to its trigger; on bar-to-bar pointer handoff cancel the outgoing card's hide timer.
  Why: focus fell to the page body after Escape, and cards flickered on handoff.
- Respect reduced motion in every transition and keyframe; zoom is instant.
  Why: motion that ignores the user's setting is an accessibility defect.
- Event times render in the viewer's local time; business-day boundaries use the one business time zone.
  Why: two timestamps on one page that disagree destroy trust.
- Time and bucket maths (day keys, buckets, ticks, zoom, clamp) live in shared modules; never copy them per chart.
  Why: copied time maths drifted between charts.
- Label mock and illustrative data honestly in the surface itself.
  Why: invented data presented as real misleads decisions.

## F. Verification

- **[MUST]** Open every chart in a real browser: hover a mark on each chart (fade feedback works), render loading / empty / error per panel, check both themes. A unit test cannot prove a chart rendered (no layout engine reports real size).
  Why: height, overflow and tooltips are browser-only questions.
- **[MUST]** Check every number against the data source and reconcile related counts; a 0 / empty / dash headline is a suspect, never "preview data".
  Why: a wrong 0/0 header was waved off as preview data and shipped.
- **[MUST]** Assert on rendered output, never source text; break each assertion you add with a named one-line mutation and confirm it fails.
  Why: assertions built from the value they pin could never fail and stayed green.
- **[THOROUGH]** Run a timeline marker/bar overlap probe, a legend-vs-drawn-marks probe, and a "labels shown = bars" count at several zoom levels and widths; each new probe must first fail on the previous build.
  Why: a probe blind to the last bug is not a gate.
- **[THOROUGH]** Open an independent critic pass on the whole screen (duplicates, interaction, parity) not just a pixel diff; do not let it call inner scroll behind an edge fade a "cut".
  Why: a pixel diff cannot see a duplicate count; a critic that misreads inner scroll wastes rounds.
