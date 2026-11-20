# 10 - Feature completeness

A feature is not done when its first screen works. It is done when every writer, reader and screen that touches its data is accounted for.

- **[MUST]** - cheap, catches the defects the user points out most, never skip.
- **[THOROUGH]** - deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).
- Untagged lines are design rules.

---

## 1. Trace the whole slice before editing

- Name the semantic owner of the value, then trace it end to end: owner page, list/row/summary visibility, edit surface, API, query, writer, and every downstream display or reader. [MUST] Why: a half-traced feature ships live, working, and invisible.
- List every screen that renders the same data (grep the reader, model and field name across the codebase) and state for each one: changed, or unchanged with a reason. [MUST] Why: a change to one activity feed shipped while the overview feed that renders the same rows was missed until the user found it.
- Trace loading, explicit empty, error, disabled, stale and permission states for the new surface. Why: only the happy path is usually built.
- Operational state is discoverable without opening an edit modal; a modal may edit state but is never its only display. Why: state hidden behind an edit dialog cannot be monitored.
- Global data lives on its semantic owner page, not on whichever entity page first needed it. Why: an editor for a global mapping, mounted on one entity page and hidden in another's edit modal, was unfindable.
- Related displays use the identity the user acts on as the primary label; raw provenance stays secondary. Why: a row showed a place label when the user needed the category id.
- Keep scope to directly related surfaces; ask before unrelated product expansion. Why: scope creep hides the real change.

## 2. One route, one writer

- Reuse the existing route, client and writer; find the template first. There is never a second mutation path for the same field. [MUST] Why: a second writer silently omitted cache invalidation, so edits looked stale until the cache expired.
- A whole-object save (create/edit form writing many fields atomically) is a different operation and keeps its own route; the rule forbids a second way to flip ONE field. Why: forcing an atomic save through a batch endpoint splits it into two requests that can half-fail.
- N = 1 is a case of N: an action available per-row in a modal also gets a batch action over the selection; a boolean field also gets a one-click inline toggle through the same route (a batch of one). Why: turning something off once took four interactions.
- Batch routes return `{ok, results, counts}` with a verdict per row, never one pass/fail. Why: a single verdict hides partial failure.
- Coupled fields are batched as a pair, never alone (a sub-category only with its parent category); if the invalid part is one scalar shared by the batch, reject the whole request rather than skipping rows. Why: a batch could put a child under the wrong parent.
- Cached listings that the change affects are invalidated per change kind, not per route. Why: a route-level list goes false the moment a new shape arrives.
- Reuse one component for every surface that edits the same setting; add a setting to that one component, never to a page's own markup. [MUST] Why: a setting added to one of two pages was live but invisible on the other.
- A setting reaches the user only if something reads it. Before closing a parity gap, grep for a READER, not just a writer. Why: two sessions proposed adding the missing control to a setting that nothing consumed, which would have shipped a lying toggle.
- A condition or flag the engine genuinely acts on gets its checkbox in the same change. Why: backing with no UI is silent forever.
- When fetching a setting, the fetch must parse the new field; an unparsed field gives a toggle that appears to work and reverts on reload. [MUST] Why: it looks like a save bug, not a missing line.
- A boolean-gated value is traced across the wire (client expression, request body, server type guard, writer); a type mismatch can be read as "unchanged" while a success toast fires. [THOROUGH] Why: no compile error, no unit failure, no effect.

## 3. Per-row results and batch honesty

- Per-row verdicts are mapped back to rows by id carried in each result, never by array index. A row with no matching result renders as unknown, never success; a result matching no row is surfaced, not dropped. [MUST] Why: a reordering stage displayed one account's success against another account.
- Pure mapping logic lives in a plain module, not in the component file, and is tested behaviourally. Why: logic buried in a component can only be source-scraped, which does not catch a revert to positional mapping.
- Cross-row statistics are banned (a union minimum, a merged ratio, an average over selected rows): they describe no row. Batch forms hide per-row feedback unless it has a defined batch meaning. Why: a combined statistic is a plausible lie.
- Show an AFFECTED COUNT instead: "N of the M selected would change". An option that would apply to nothing stays listed and is flagged, not filtered out. Why: the count is true of the selection and the only warning that a choice applies to nothing.
- The count and the real render use ONE predicate (never a retyped condition). Why: otherwise the picker promises a render the real surface suppresses.
- A preview owes the engine's ORDER, not just its FILTER: a surface claiming "which one is next" must apply the same ordering as the engine. Name the query the surface actually runs. Why: a correctly filtered list sorted from the wrong end made everything on screen true and the conclusion false.
- A batch of N consumes N of anything it takes from a pool; show or limit the consumption. Why: an unpaced batch can silently drain shared inventory.

## 4. Controls that narrow or claim

- Any control that narrows a list needs a round-trip test: UI state -> request params -> server parse -> query -> row count, asserting narrowed != unnarrowed through the real builder. [MUST] Why: a chip highlighted and refetched while the builder ignored it; the user saw a plausible wrong list.
- A count and the list beside it use one predicate and the same side of pagination. Why: a client filter on a server-paged list hid rows while the total kept counting them.
- Moving such a filter server-side changes default-view numbers: announce the change; do not let a correctness fix read as data loss. Why: a total dropped by hundreds after the fix.
- The UI must not land before its backing: if plumbing splits across units, land them together or say so. Why: an intermediate commit ships a control that lies.
- In a demo, a control whose backing is unbuilt is disabled with a visible "not built yet" reason, not hidden and not enabled-looking; in the production build the backend is built (01; not a question for the user), and only if it cannot be built within the agreed scope is the gap listed to the user (never hidden). Why: a dead control that looks live erodes trust.

## 5. Explanations and shared displays

- An explanation of a value (tooltip, cost breakdown, rule text) appears on EVERY screen that shows the value: grep the field across all render forms, not only the reader. [MUST] Why: a cost breakdown shipped on one list tooltip while the tab showing the same cost got nothing until the user asked.
- A number that sums several sources drills to them wherever it appears. Why: the explanation was reachable from only one screen.

## 6. Replacing or deleting a surface (parity)

- Parity is a checklist, not a copy: enumerate what the OLD surface rendered and could do, then mark each item kept, moved to a named home, or recorded as dropped with a reason. A legacy field whose data is meaningless in the new context is dropped with the reason written down. [MUST] Why: a migration silently deleted ten working affordances, and everyone had checked only what the new table added.
- Enumerate from the OLD source (read the file being replaced or the version before deletion), not from memory or from the new component's data. [MUST] Why: reasoning about what the old surface did missed its warnings, banners, empty states and fallback labels.
- Inventory every control, warning, banner, link, download, modal, copy button, empty state, status line, fallback label and count. Fallback labels are the easiest to lose: a generic "item #id" is not equivalent to the recognisable label users had. [THOROUGH] Why: these never show up in a diff read.
- The parity gate names the concrete ARTIFACT the user sees, not the concept: "the stuck screenshot, from endpoint X" rather than "stuck evidence is reachable". "The data is reachable" passes while the capability is lost. [MUST] Why: a replacement rendered evidence as text while the deleted panel rendered a screenshot, and the gate passed.
- Every capability with a route but no UI in the replacement is deleted, not migrated, even though the API still exists. Why: the capability was merely unreachable.
- Verify each item survives, pinned by contract tests so the next migration cannot repeat the loss; a green suite proves the new surface renders, never that the old one's capabilities survived. [THOROUGH] Why: the type-check, suite and build were green on three consecutive losing rounds.
- Production wins over a design that merely omits an existing element; subtract only what a build ADDS beyond the approved design. Ask only if the design visibly replaces it. Why: removing an element production already has is a regression.
- "Done" is what renders: merging a shared component does not migrate a page. Done means the screenshot shows it; when something is "being built", say where (file, URL). Why: the shared table existed while the page still rendered the old one.

## 7. "Check the whole X" means fix the whole X

- When the user points at one fixed instance and says check the whole X for that behaviour, the deliverable is every instance fixed, not a findings table plus a question. [MUST] Why: five charts lacking click-through were found, listed in a table, and the user had to say "and fix" again.
- Fix the first instance, then grep every sibling (same components, same card family) for the same gap in the same turn. Why: a one-instance fix leaves the family inconsistent.
- A sibling that needs a new backend filter is part of the job, not a reason to ask. Why: asking converts an assigned task back into a question.
- Prove every drill-down total against the figure it came from (data-oracle test plus a live read). [THOROUGH] Why: count must equal the bar.
- Files another stream asked to stay out of are a coordination note, one line, not a blocker on the user's own request. Why: the user's request outranks a soft boundary.
- Build every item the approved design includes; demo-only extras are built too, and nothing is silently dropped in a redesign or port. Why: cutting a production feature silently is a regression the user finds later.
- Audit and fix on the same QoL bar, including side-session UI, before it reaches the user; a QoL audit brief includes a drill-through line (section 6 of 06-interaction-qol). Why: a missed category in the brief meant eight reviewers could not see the gap.

## 8. Proof before "complete"

- Test the real boundary behaviourally, with mutation checks named for the behaviour they protect: break the production guard and see a test fail by name, or the guard is decorative. [THOROUGH] Why: a guard duplicated across several places tends to be tested zero times.
- Prove placement, discoverability, state handling and responsive controls in a real browser, with accessibility-tree evidence. [MUST] Why: defects lived in the seam between two correct modules while the suite was green.
- Click the new control end to end: change it on one surface and confirm it persists and shows on the others, including after reload. [MUST] Why: a setting that reverts on reload looks like a save bug.
- For actions that already exist, drive them through their API or command rather than UI clicks; use the browser to prove NEW UI. Why: clicking existing admin controls is slow and risks flipping a master switch.
- A deferral is written down as a "Known deferral", never left implicit. Why: a silent corner cut surfaces as a surprise at audit.
