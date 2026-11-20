# 09 - Motion and vector animation

Portable rules for animating inline SVG, full-viewport artwork, and live re-sorting lists. Each rule is one line plus a "Why:" naming the defect it prevents. Process rules are tagged **[MUST]** = cheap, catches the defects the user points out most, never skip, or **[THOROUGH]** = deeper checking when time allows (independent critic, full theme x width matrix, parity diff, deeper measurement).

---

## A. Crisp inline SVG animation

- Animate SVG paint properties only: `fill-opacity`, `stroke-opacity`, `stroke-dashoffset`, `fill`. Never `opacity`, `transform`, `filter` or `will-change` on the SVG or its paths.
  Why: those three properties promote the element to a compositor layer, which rasterises the vector into a bitmap; it renders blurry (worst on high-DPI) and can stay blurry after the animation ends.
- Hover fades on chart marks use `fill-opacity` / `stroke-opacity`, never `opacity`.
  Why: the same rasterisation blur applies to a hover fade.
- Draw-on (self-drawing) effects animate `stroke-dashoffset`; add a real stroke first (source paths are usually fill-only) and remove the hairline after the sweep.
  Why: a fill-only path has nothing to draw; leaving the stroke changes the final look.
- Stagger per element: set an index variable on each path in script (`--i`) and use `animation-delay: calc(var(--i) * step)`.
  Why: per-path delays in CSS alone cannot be authored for hundreds of paths.
- When two visual groups (e.g. text and illustration) should finish together, spread EACH group across the same index window instead of using one running index; order by on-screen position (use bounding-client coordinates when groups sit under different transforms).
  Why: with one running index the smaller group finishes long before the larger.
- Theme via `fill="currentColor"` and a wrapper text colour.
  Why: a hard-coded fill breaks light/dark.
- Scroll-triggered reveal: use `IntersectionObserver`, render visible for server rendering, arm (hide) only when off-screen at mount, and add the "in" class on intersect.
  Why: hiding by default leaves no-JS and reduced-motion users with nothing.
- Always honour reduced motion: animation none and the final value under `prefers-reduced-motion: reduce`.
  Why: motion ignoring the user's setting is an accessibility defect.
- No first-paint flash: hide the animated paths from first paint in CSS, but only inside `prefers-reduced-motion: no-preference`; script then sets inline values that override the base rule.
  Why: otherwise the complete graphic flashes before it animates; an unconditional hide leaves reduced-motion users with an invisible graphic.
- Escape hatch only if a design truly forces a composited property: release the layer when the animation ends (a class that sets `animation: none` and the final value). Prefer paint properties, which never create the layer.
  Why: a lingering layer keeps the vector blurred at rest.
- Diagnose the medium first: "blurry SVG" may be a pre-rendered video or sprite being upscaled, not a compositor problem. Ask "is this still a vector at paint time?" - uniform softness at rest and during animation, worse on high-DPI, points to rasterisation in the build.
  Why: a full-bleed intro obeyed every paint-property rule and was still soft because it had been pre-rendered at a fixed resolution.
- **[MUST]** Verify crispness by checking that no animated element carries opacity/transform/filter/will-change in its computed style, in a real visible window.
  Why: class strings and source rules do not prove the rendered style.

## B. Full-viewport vector art (intros, splashes, animated backgrounds)

- Ship the vector, injected inline. Never pre-render full-viewport vector animation to video or sprite frames.
  Why: a raster is pinned to its encode resolution and a full-bleed layer is always upscaled (a ~1.65x upscale left under two-thirds of the needed resolution per axis), so it is soft on every non-matching display; video chroma subsampling also attacks hard edges. Do the upscale arithmetic for the target displays before accepting a raster.
- Load it by `fetch()` then inserting into a container; not as `<img>`, not bundled into the component's JavaScript.
  Why: an `<img>` SVG cannot see the page's CSS variables (theming breaks) or be driven; bundling parses megabytes of art as JavaScript for users who never see it. Fetching keeps it cacheable, loaded only when it plays, and theme-aware.
- Injected `<style>` is global: scope every emitted selector to the artwork's root id at build time, and rename keyframes (selector prefixes cannot scope them). Assert it in the build, and mutation-test the assertion by stripping the prefix from all rules and from exactly one rule.
  Why: generic class names in the injected art hit unrelated page elements, now or in a future component.
- Geometry: the animation must land exactly on the static layer it hands off to: same box, same crop rule (cover = slice), same source aspect ratio, at every viewport aspect.
  Why: a mismatched box makes the handoff visibly jump.

### Animation clocks

When CSS animations and a JavaScript driver share one timeline:
- Set the pause variable on the container BEFORE inserting, so no CSS animation starts.
  Why: setup cost (hundreds of ms) would otherwise run ahead of the timeline.
- Insert, size the root explicitly, and apply any seek while still paused.
  Why: the one-time style invalidation across thousands of elements must land in setup, not mid-animation.
- On the first animation frame, flip to running and request another frame - nothing else. On the SECOND frame callback (the first following a genuinely rendered frame) record the start time and arm the end timers.
  Why: a frame callback runs before that frame's style/layout/paint; anchoring there started the JS clock hundreds of ms ahead of CSS, and a slow machine painted the completed artwork for one frame instead of animating.
- Use a pause-aware clock: if a frame gap exceeds a ceiling (~250 ms; a 60 Hz frame is 16.7 ms) shift the start time forward by the excess; keep it a pure, unit-testable function.
  Why: garbage collection and tab switches caused the same jump.
- Split timeouts: a driver-relative safety net armed at the anchor, plus a larger mount-anchored net for "driver never started". Do not anchor the outer timeout at mount.
  Why: a mount-anchored net lets slow setup eat the animation's budget; dropping the mount net risks a permanently stuck full-screen overlay.
- Seek with a CSS custom property and a negative `animation-delay` (`calc(var(--d) * var(--dur) - var(--seek, 0ms))`), not a per-element JS loop writing `currentTime`.
  Why: a variable seeks thousands of animations in one invalidation.
- Split work by what CSS can express: per-element fades with delay/duration in CSS; non-cubic-bezier curves (windowed ramps, power curves) for the few elements that need them in the JS driver.
  Why: CSS would need sampled keyframes per element for those curves.

### One-shot gates

- Mark an intro "seen" only on the success path; every failure path must never mark it.
  Why: a wrongly marked intro stops appearing forever with no error anywhere.
- One AbortController, aborted from BOTH finish paths (not only unmount); every post-fetch continuation guarded on active / not finished / not aborted before touching the DOM; an AbortError is a consequence of finishing and is swallowed silently; injection and driver start wrapped in their own try/catch onto the never-mark path.
  Why: a click or timeout can finish the animation while the fetch is in flight, and the continuation then takes the success path and marks seen.
- Re-derive the readiness timeout from measured setup cost (fetch, parse, construct animations), not from a video's ready state.
  Why: a 1200 ms budget against 392-1087 ms measured setup left ~113 ms headroom and silently skipped the intro on slower machines.

## C. Live re-sorting lists

- Items that cross each other in flight must look like cards, never ghosts: when an item's own surface is translucent (a sold-out opacity, a tinted selected row) or items are dense rows, give each item wrapper an opaque backing in the PARENT panel's colour, and fade the item moving down out beneath the risers.
  Why: see-through rows and a text strip peeking between rows were rejected.
- The backing colour is the parent panel's, not the page background.
  Why: a backing in the page colour showed as a darker band.
- Prove it with paused mid-flight frames (pause all running animations at ~25 / 50 / 75%) at desktop and phone width, never with a class-string test.
  Why: ghosting only exists in rendered mid-flight frames.
- Use one shared component for every live re-sort so every list gets the same motion.
  Why: per-list copies drifted.

## D. Verification and its traps

- **[MUST]** Test motion in a real, visible window. A browser pane that reports the document as hidden throttles `requestAnimationFrame` to nothing: frame-rate and timing numbers measured there are meaningless. If you need timings, build a harness a person opens in a visible window that invalidates itself on lost visibility, or measure the synchronous cost directly.
  Why: neither a test suite nor an automated pane caught the clock-anchor bug; direct measurement did.
- **[MUST]** Verify with pixel/alpha comparison against an external invariant produced by a different code path (e.g. compare the runtime's final frame with the static asset: coverage and mean alpha difference), not by eye.
  Why: that single check proves completeness, geometry and handoff continuity at once.
- **[THOROUGH]** Compare the ALPHA channel, not luminance after flattening.
  Why: transparent regions decode to black, so a luminance threshold classified the whole frame as ink and printed MATCH.
- **[THOROUGH]** Print the match count before trusting a regex-based reconstruction of generated art.
  Why: a regex that matched 0 of 3460 elements still reported MONOTONIC over the 7 leftovers.
- **[THOROUGH]** Do not read an easing parameter as a coverage fraction; measure actual coverage.
  Why: a parameter of 0.813 was called "81% swept" when real coverage was already 95% down.
- **[THOROUGH]** Beware tests that pass for the identity function: pin interior points of an easing curve (eased(0.25) = 0.125), not only 0, 0.5 and 1.
  Why: a linear driver would silently desync JS-driven elements from CSS-driven ones and every endpoint test would still pass.
- **[THOROUGH]** Pin curve constants with literals, not expressions derived from the constant under test; mutation-test each.
  Why: an assertion computed from the constant moves with the mutant and can never fail.
- **[THOROUGH]** Keep the testable logic (clock maths, continue/stop decisions) in pure functions; a UI component with no browser harness cannot be unit-tested.
  Why: the logic was untestable inside the component until extracted.
- **[THOROUGH]** Measure the synchronous setup cost of injection (insert, forced layout, animation resolution) on a slow-machine multiplier before choosing timeouts.
  Why: a cost that is trivial on a fast desktop exceeded the narrow-screen budget at 2x slower.
