# Mobile Sticky React Structure

## Status

Implemented locally and validated in a fresh cache-disabled Chrome Incognito session at 390 x 844 and desktop at 1440 x 1000. Not committed, pushed, or deployed.

## Structure

Slate now has one mobile `.md-sticky-head` JSX container owning the topbar, `SlateCommandStrip`, `StaleBanner`, and `LiveTargets`. At desktop width the same wrapper uses `display: contents`, and `LiveTargets` remains under `.md-left`, preserving the existing desktop layout. The responsive layout switch keeps the topbar DOM node stable so the separately mounted auth and slip roots are not remounted when crossing the breakpoint.

TCC now has one `.md-cc__sticky-head` JSX container around the title row, the ACTIVE / RESET / SAVE BUILD / LOAD BUILD row, and the APPLY TO ROOM / close row. `.md-cc__body` remains the independent filter scroll region beneath the header.

## Validation

- Slate rendered 302 batter rows with the document as the only vertical slate scroller. The sticky wrapper and LIVE TARGETS ticker held the same viewport positions from scrollY 0 through the true document bottom at scrollY 81,409.
- Full Slate and Top Targets controls were tappable. MAIN and JIG navigation both retained the mobile sticky structure.
- TCC filter body scrolled 1,952 px to its true bottom while all three header rows, including APPLY TO ROOM and close, remained visible and tappable. MAIN and JIG TCC surfaces both passed.
- Desktop retained the original flex/grid layout, LIVE TARGETS parent, stage scroll behavior, and single-row TCC command bar. A desktop-mobile-desktop resize kept the original auth root connected.
- Browser runtime reported no page errors. `git diff --check` passed.

## Boundaries preserved

No scoring, formula, tier, ordering, payload, data, backend, pipeline, build-saver, MAIN/JIG separation, or component business logic changed. The implementation is frontend layout structure and mobile-only sticky styling.

## Sticky Offset Checkpoint — 2026-07-21

Measured `ResizeObserver` offsets were added for the mobile slate sticky head and TCC sticky head. The slate split uses equal measured padding and negative layout offset; the TCC filter body uses the same pattern. At 390 x 844, the slate header measured 311px and the first player row cleared the pinned header at its top-scroll position. TCC measured 136px and its first filter panel cleared the header at body scroll position 0. At 1440px, both offset properties remained 0px.

This checkpoint was run in a fresh cache-disabled local Chrome tab with a cache-busting URL; an actual Incognito profile was not available through the connected browser surface. No code errors were observed beyond the existing in-browser Babel transformer warning. No scoring, data, payload, backend, reorder, build-saver, or MAIN/JIG logic changed.

## Sticky Offset Correction — 2026-07-21

The equal measured padding plus negative margin cancelled the sticky wrapper's normal-flow space and allowed scroll content to move beneath the pinned header. Removed that compensation from the mobile-only slate split and TCC filter body. Both remain normal-flow siblings below their variable-height sticky wrappers; the existing `ResizeObserver` measurement remains in place for the sticky structure.

At local mobile width (390 x 844), the slate stage begins at the sticky head's bottom (247px). The opened TCC header ended at 421px and the first filter panel began at 437px (the grid's normal 16px gap), with no negative offset or padding applied to the scroll body. Desktop selectors are unaffected because the change is inside the existing max-width 768px media blocks.
