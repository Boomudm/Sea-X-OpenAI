# 12 - General UX baseline

> General UX baseline from common practice - NOT the user's own lessons. Where anything here differs from files 01-11, files 01-11 win.

## Tier legend

- **[MUST]** - cheap, catches the defects the user points out most, never skip.
- **[THOROUGH]** - deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).
- Untagged lines are design rules.

This file fills gaps the other files do not cover: first run, forms, message wording, undo, latency feedback,
wayfinding, accessibility and perceived speed. Each rule is one line plus a "Why:" line. Where 01-11 already
decide a topic, this file only points to them.

---

## 1. Onboarding and first run

- A first-use empty state names what will appear here and offers the one next action (a button, not prose). See 03 Part B for the empty state itself; this rule adds that first use also teaches. Why: a blank first screen gives a new person nothing to do, and the first action is where most people leave.
- The first screen offers one primary next action that produces a real result with no setup beyond the required fields; teach the one or two concepts needed for it, not the whole product. Why: onboarding exists to reach the first useful outcome, not to explain every feature.
- Ask for the minimum at sign-up and collect the rest later, at the moment it is needed; say why when a field is not obvious. Why: every extra up-front field loses people, and unexplained requests feel intrusive.
- Disclose features progressively: show the common path first, reveal advanced options where the person meets them. Why: showing every option at once hides the one that matters.
- No forced tours. Any tour or hint is skippable, short (a few steps), replayable from a help entry, and never blocks the product. Why: people who already know the product are punished by a mandatory walkthrough.
- Hints appear at the point of use, once, dismissible, and say the benefit ("Drag to reorder"), not the widget name. Why: help shown out of context is forgotten before it is needed.
- Sample or demo content used to illustrate first use is tagged as sample everywhere it renders (07 §7), and should be removable in one action. Why: untagged sample content is read as the person's own data.
- A multi-step setup shows where the person is ("Step 2 of 3"), allows going back, and keeps what was entered (see section 2). Why: an unknown length and a lost answer both cause abandonment.
- [THOROUGH] Walk the product as a brand-new person with no data: can they reach a first result without reading anything outside the screen? Why: builders always test with their own populated account.

## 2. Forms

- Every field has a visible, persistent label; a placeholder is an example, never the label. Why: a placeholder vanishes on typing, so the person forgets what the field asked.
- Mark required vs optional consistently, in one way across the product (for example mark the minority). Why: mixed marking forces people to guess.
- Group related fields under a short heading and put required and identifying fields first, then details, grouped by topic with headings; one column on narrow screens. Why: a scattered form reads as longer and harder than it is.
- Use the right input type, autocomplete hint and mobile keyboard (numeric, email, phone, date); size a field to its expected value (field width rules: 04 item 8). Why: the wrong keyboard turns a ten-second field into a chore.
- Text inputs use at least 16 px type on touch screens. Why: smaller text makes some mobile browsers zoom the page on focus and break the layout.
- State format and eligibility rules before submission (next to the label), not only after a failure. Why: an error for a rule the person was never shown feels like a trap.
- Validate on blur or after the person has interacted, never while they are still typing the first time and never under an untouched field (06 §2 Defaults). Re-validate live once a field has shown an error so it clears the moment it is fixed. Why: an error shown mid-typing is wrong by definition, and a stale error after the fix reads as a bug.
- Show the error inline, next to its field, in text (not colour alone); on submit also show a summary at the top that links to each failing field and moves focus to the first one. Why: people miss a lone error far from the field, and keyboard users lose their place.
- Preserve everything the person typed when an error occurs, on a failed save, a timeout or a navigation back. Why: wiping a form on error is the fastest way to lose a person.
- Never block submission for something the system can fix itself (trimming spaces, normalising a phone format). Why: errors for fixable input are the system's work, not the person's.
- Disable the submit button only with a stated reason beside it that tracks the input (03 Part B "Disabled with reason"); otherwise leave it enabled and explain on press. Why: a silently grey button gives no way forward.
- On submit show a busy state on that button and lock a double press until the result returns. Why: double submits create duplicate records and double charges.
- Protect long forms: autosave a draft or guard a dirty close with the shared close handler (06 §2). Why: losing ten minutes of input to a stray click is not forgivable.
- Confirmation of a destructive form action follows 06 §3 (preview, named confirm, lock, toast). Why: this file adds nothing to that flow and must not weaken it.
- [MUST] Complete one form by keyboard only (Tab order follows reading order, Enter submits, Esc cancels, errors reachable). Why: a form that needs a mouse excludes keyboard and assistive-tech users and slows power users.
- [THOROUGH] Submit each form empty, with a wrong value in every field, with maximum-length values, and with a simulated server failure; check the message, focus and preserved input each time. Why: the happy path is the only path most builders try.

## 3. Error, empty and success messages

- An error says what happened, why when it is known and useful, and what the person can do next. Why: a message missing any of the three leaves the person stuck.
- Use plain everyday words; never raw codes, internal ids or stack text as the message (04 item 6, 07 §6). Keep the code in a copyable tooltip or a support detail. Why: codes mean nothing to the reader and look broken.
- Do not blame: describe the input or the system ("That date is in the past"), not the person ("You entered an invalid date"). Why: blame makes people defensive, and the neutral version is also shorter.
- Do not promise a cause or a fix the system cannot know ("Try again in a few minutes" only if that is true). Why: a wrong explanation costs more trust than none.
- Name the real object and use the product's own terms ("Could not save the order", not "Operation failed"). Why: vague nouns force the reader to work out what broke.
- Treat money, deletion, lost access and blocked work with a calm, serious tone; no jokes or exclamation marks on failures. Why: humour at the moment of loss reads as mockery.
- Offer a recovery control with the error (retry, edit, contact) and keep the person's input (see 03 Part B "Error with retry"). Why: an error with no way out is a dead end.
- Distinguish the empty cases in words: first use, no results, filter hides rows, no permission, failed to load. Why: each needs a different next step, and one generic "No data" serves none.
- A success message confirms the completed outcome in the person's terms ("Order 18 marked shipped") and mentions a next step only when it changes what they should do; routine success stays brief. Success is never shown in the error slot (04 item 15). Why: confirmation lets people stop worrying; long celebration slows them down.
- Write whole translatable sentences; do not glue fragments or hard-code plurals around a number. Why: concatenated strings break in other languages and with counts of one.
- Keep one terminology list for the product: same noun and verb for the same concept, same capitalisation. Why: three names for one thing look like three things.
- Buttons name their action ("Delete order", "Save changes"); never bare "OK", "Yes" or "Submit" on a consequential confirm. Why: a named button states the choice without rereading the dialog.
- [MUST] Read every message as the person with no product knowledge: do they know what to do next? Why: authors read their own copy with all the context the reader lacks.

## 4. Undo and reversibility

- For a low-risk, reversible toggle that is frequent (archive, move, hide, mark as read) and that 06 §3 does not require a preview and confirm for, apply it at once and offer Undo in a toast that stays long enough to click (about 5-8 seconds, longer for keyboard and assistive-tech users, paused on hover or focus). Why: undo is faster than a confirm and makes people bolder, not more careless.
- Destructive or irreversible actions still use the confirm dialog required by 06 §3. Undo complements the confirm; it never replaces it and never excuses a missing preview, reason or lock. Why: an undo window cannot recall a sent message, a payment or a hard delete.
- Prefer a recoverable state (trash, archive, soft delete with a stated retention) over permanent removal where the product allows it; say how long and where to find it. Why: a recovery path is the cheapest safety net.
- The undo must really restore the previous state, counts and every surface that shows it (03 Part B "Every action re-renders ..."), and its own failure shows an error toast. Why: an Undo that leaves one screen stale is worse than none.
- Undo is also reachable by the keyboard shortcut people expect (Ctrl/Cmd+Z) where an editing surface exists, and does not depend on the toast being visible. Why: the toast disappears; the person's intent does not.
- Batch actions follow the 06 §3 confirm (preview, named confirm, lock, toast). An Undo toast may complement the confirm, never replace it; the result says what was done to how many and offers one Undo for the whole batch where it is safe. Why: ten separate undos for one click is unusable, and an undo window does not excuse a missing confirm.
- [THOROUGH] For each reversible action: do it, undo it, reload, and compare the data to the start. Why: undo bugs show only in the round trip.

## 5. Feedback and latency

- Acknowledge every click or tap at once (pressed state, spinner on the button or the row) even when the result is slow. Why: no response within about 100 ms reads as a missed click and causes repeat presses.
- Show a spinner or skeleton only after a short delay (about 300 ms) and keep it up for a minimum time (about 500 ms) once shown. Why: a flash of loader is more distracting than a brief wait.
- Use skeletons that match the final layout for content, a determinate progress bar for long tasks with a known size, and an honest wording for waits ("Importing 120 of 480 rows") rather than invented progress. Why: honest progress sets expectation; a fake bar destroys trust (see also 04 item 17).
- A task that takes more than a few seconds gives the person a way to leave and be told later, and a way to cancel when the work can stop safely. Why: a locked screen with no exit is a trap.
- Optimistic updates only for reversible low-risk toggles that nearly always succeed; every write covered by 06 §3 still follows its steps (lock while pending, re-render every surface from the new state). On failure roll back the visible state and show an error toast that names the cause. Why: an optimistic change that silently stays wrong is a lie.
- Never fail silently: every failed write, read, upload or background job surfaces a visible message and a retry. Why: a person who sees nothing assumes it worked.
- Keep layout stable while loading and after content arrives; reserve space for images and late content. Why: content that jumps under the pointer causes mis-clicks.
- Reflect the result of an action in the same place the person is looking (the row, the badge), not only in a toast elsewhere. Why: feedback away from the focus is easy to miss.
- [MUST] Throttle the network to a slow connection and use the screen: loading, failure and retry all look right. Why: builders test on a fast local copy where none of these states appear.

## 6. Navigation and wayfinding

- The current location is always visible: highlighted nav item, page title, and breadcrumbs when the hierarchy is more than two levels deep. Why: people who cannot tell where they are cannot tell how to get elsewhere.
- Back is predictable: the browser back button returns to the previous screen and view state (06 §5 for state in the URL); a modal closes before the page goes back. Why: broken back behaviour is the most reported navigation annoyance.
- No dead ends: every page, empty state, error and success screen offers a way back or onward. Why: a page with no exit forces the person to use the address bar.
- Link and button labels say where they lead or what they do, and make sense out of context. Why: "Click here" fails for scanning and for screen-reader link lists.
- Keep primary navigation in the same place with the same order on every page; the same destination has the same name everywhere. Why: moving items forces relearning on each screen.
- A modal or panel opened from a page returns the person to the same scroll position and focus when it closes (06 §4 for focus). Why: losing position in a long list wastes the next minute.
- Deep links to a record or view work when opened cold, including after sign-in redirects and for a record that no longer exists (say so and offer the list). Why: shared links are the main way people return to work.
- [THOROUGH] Starting from each page, count the clicks to reach the main areas and to get back; follow every error and empty screen to a way out. Why: wayfinding gaps hide in rarely visited corners.

## 7. Accessibility baseline

- Target WCAG 2.2 level AA as the floor. Contrast numbers and theme checks are in 04 item 5 and 05; motion is in 09; do not restate them here. Why: AA is the common legal and practical baseline.
- Everything operable with a mouse is operable by keyboard in a logical order, with no keyboard trap; custom controls expose role, name and state. Why: keyboard and assistive-tech users reach only what the keyboard reaches.
- Focus is always visible (a ring of at least 3:1 against its background) and never removed without a replacement; a sticky header must not hide the focused element. Why: people cannot use what they cannot see focused.
- Every form field has a programmatic label; every icon-only control has an accessible name; informative images have a text equivalent and decorative ones are empty (icon-only controls: 04 item 19). Why: unlabeled controls are announced as just "button".
- Do not carry meaning by colour, shape or position alone; pair status colour with text or an icon. Why: colour-blind people and monochrome screens lose colour-only signals.
- Announce dynamic changes (errors, toasts, loading complete) to assistive tech through live regions, without stealing focus. Why: a change that is only visual does not exist for a screen-reader user.
- Respect the reduced-motion setting by replacing movement with a calm alternative that keeps the state change visible (09). Why: motion triggers nausea and distraction for some people.
- Layout works at 200% browser zoom and larger text with no loss of content or function and no horizontal scroll (see 02 for narrow widths); do not disable pinch-zoom. Why: low-vision users rely on scaling.
- Give touch and pointer targets enough size and spacing (see 05); give interactions that need dragging or a path gesture a single-tap alternative. Why: people with tremor or one hand cannot perform precise gestures.
- Time limits and auto-refresh can be paused or extended, and nothing flashes more than three times per second. Why: timed content excludes slower readers and flashing can cause harm.
- [MUST] Tab through every new screen once with the keyboard, then read it with a screen reader or the accessibility tree. Why: automated checks catch only a minority of accessibility defects.
- [THOROUGH] Run an automated accessibility scan on every route in light and dark and fix every serious or critical finding. Why: it is a cheap safety net for regressions.

## 8. Responsive and input

- Touch target size follows 05; a hit area may be larger than the visual (padding), never overlapping a neighbour. Why: small or crowded targets fail real thumbs.
- No information or action exists only on hover; every hover enhancement has a tap, focus or visible path (06 §4 Desktop vs touch). Why: touch screens have no hover.
- Respect device safe areas (notch, home bar, rounded corners) for fixed bars and docks; keep primary actions within thumb reach on phones. Why: controls under a system bar cannot be pressed.
- Do not rely on a fixed viewport height on mobile; account for the browser bars and the on-screen keyboard so the focused field stays visible. Why: a field hidden behind the keyboard looks like a frozen form.
- Support both orientation and a range of widths by content-driven breakpoints, not just two device sizes. Why: real screens fall between the sizes designers pick.
- Prefer native controls (date, select, file) on touch unless a custom one is fully accessible and tested. Why: native pickers already handle keyboard, voice and platform habits.
- [MUST] Open every screen at a real narrow width (see 02) and at the narrowest supported width, including with the keyboard open. Why: a desktop-sized check misses the layout most phone users see.

## 9. Perceived performance

- Never block the whole screen for something that affects one panel; load and fail per panel (06 §5). Why: one slow query should not hide everything else.
- Show the shell and the important content first; defer secondary and below-the-fold parts. Why: people judge speed by when they can start, not when everything finishes.
- Keep the previous data on screen while refreshing (stale-while-revalidate) and mark it as refreshing (06 §5, 03 Part B "Stale"). Why: swapping to a spinner on every refresh feels slower than the refresh is.
- Lazy-load heavy parts (charts, editors, large images, long lists) and reserve their space to avoid layout jumps. Why: unloaded heavy code delays everything above it.
- Prefetch the likely next step only when it is cheap and safe; never prefetch an action with side effects. Why: speculative work must not change data or cost the person.
- Page long lists on the server or window them; do not render thousands of rows. Why: huge DOMs make scrolling and typing lag.
- Keep input response under about 100 ms during typing and scrolling; defer, debounce or move long work off the main thread. Why: input lag is felt more than a slow load.
- [THOROUGH] Measure the main flow on a mid-range phone with a throttled network and compare against a budget the project states. Why: speed on a fast desk machine says nothing about the person on the slowest device.
