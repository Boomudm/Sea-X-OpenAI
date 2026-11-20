# UI standard - a portable knowledge pack

This is one user's accumulated UI lessons, written project-agnostic: the mistakes they caught in
review, how they expect an agent to work, their quality-of-life defaults, and the build lifecycle
from brief to live. It is **reference context, not a binding rule set**. Whoever uses it decides
what to apply to their project; where a rule does not fit, adapt it and say so.

## How to use

- Read **01 and 04** before any UI work.
- Read **05, 06, 07, 08, 09** while building (visual system, interaction, data, charts, motion).
- Read **04 and 11** before showing anything to the user.
- Read **10** when changing a field or feature that appears on several screens.
- Read **02 and 03** when planning how to verify and which states a surface must ship.

## File index

| File | What it covers |
|------|----------------|
| `01-agreement.md` | Working agreement: the approved design is the contract, build all of it, never cut a feature, "check the whole X", scope, live choices, what needs the user's ask, extend what exists. |
| `02-agent-behavior.md` | How an agent verifies UI: look yourself, green tests are not proof, data and copy truth, real data in a neutralised copy, falsifiable probes, an independent critic, browser-automation traps. |
| `03-lifecycle.md` | The flow from brief to live, the UI states every surface ships (loading, empty, error, ...), and the mistake-ledger loop. |
| `04-pre-show-gate.md` | The checklist to run before showing any screen: `[MUST]` core items and `[THOROUGH]` items for large rounds. |
| `05-visual-system.md` | Colour semantics, density and typography for dense UIs, layout. |
| `06-interaction-qol.md` | Tables, modals, mutation flow, menus/focus/keyboard, state in the URL, drill-through and consistency. |
| `07-data-honesty.md` | Numbers reconcile with the source; unknown/failed/stale/partial; labels and populations; time; money and locale; plain words; sample data. |
| `08-charts.md` | Choosing the chart form, colour by meaning, marks/axes/legends, states and accessibility, timelines, verification. |
| `09-motion.md` | Crisp inline SVG animation, full-viewport vector art, live re-sorting lists, verification traps. |
| `10-feature-completeness.md` | Trace the whole slice, one route one writer, per-row results, controls that narrow or claim, shared displays, parity when replacing a surface, proof before "complete". |
| `11-mistakes-ledger.md` | The ledger of caught mistakes by area (text/numbers, colour, layout, flows, charts, copy, data, process, rejected anti-patterns), each with its rule and a check. |

## Tier legend

- **[MUST]** - cheap, catches the defects the user points out most, never skip.
- **[THOROUGH]** - deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).
- Untagged lines are design rules.

## When context is missing

The pack is reference context you choose to apply; where a precondition is absent, adapt like this
and say so:

- No approved design yet: the compare/demo step creates one and the user approves it.
- No live data: use representative data, tag it as sample everywhere, and say so.
- No real browser: report the UI as unverified instead of claiming done.
- A [MUST] item that cannot be met is reported to the user, never silently skipped.

## Key rulings (generalised)

- **Category colour is split by surface.** In charts, categorical series get distinct hues chosen
  by meaning, with no fixed cap; a long, small tail may be folded into one grey "other" when that
  reads better. In cards, lists and pills, colour means **state only**; category is shown by icon
  or label.
- **Status colour as a chart series:** meaning wins. A series that means good, bad or in progress
  uses that status colour; other series use non-status hues.
- **Row click depends on table type.** A table with a batch action: clicking the row body
  selects, and the entity-name link opens the detail. Any other table: clicking the row opens the
  detail modal.
- **State colours:** blue = actively running; grey = queued, scheduled, upcoming or ended; amber
  = waiting on the user's decision only; green = good; red = bad.
- **Tap targets:** touch/mobile targets are at least 44 px; dense desktop rows may be 40 px
  (header 34 px).
- **Modal height:** a tabbed modal keeps one fixed height; a single-body detail modal hugs its
  content.
- **Modal close:** backdrop, the close button and Esc go through one handler, and a dirty draft
  asks first.
- **Chart hover fade** uses `fill-opacity`/`stroke-opacity`, never `opacity`.
- **Defects your own audit finds are fixed before showing.** Parity with an approved design needs
  no ask; any change in look, layout or behaviour needs the user's OK.

## Top 10 recurring themes the user corrects

1. **The approved design is the contract.** Build all of it, match it, and do not substitute your
   own taste (01).
2. **Look at every screen yourself before showing it.** Screenshots, light and dark, every width;
   green tests do not prove UI (02, 04).
3. **Numbers must match the data.** Every figure on screen reconciles with its source; unknown,
   stale and partial are shown as such, never as zero (07).
4. **"Check the whole X" means fix every sibling** in the same pass, not a findings list and an
   ask (01, 10).
5. **Never silently drop a feature.** Replacing a surface needs a parity check; a cut is the
   user's call (01, 10).
6. **Colour means one thing.** One token per meaning, state colour for state, no decorative
   status colours (05, 08).
7. **Compact layout.** Dense, aligned, no stretched label/value rows, no wasted height, nothing
   clipped or overflowing (05, 11).
8. **Every entity name, count and chart mark is clickable** to its detail, wired without being asked (06).
9. **Plain words, no debug text.** Clear English, units on numbers, no internal identifiers or
   developer wording in the UI (07).
10. **Prove UI in a real browser,** with the real data shape, before saying "done"; the screenshot
    is the evidence (02, 03).
