# Mobile horizontal-overflow fixes

Status: resolved and shipped on `main`.

## What failed

The mobile page could extend beyond the viewport, leaving a dead strip and allowing horizontal movement. Four independent containment failures contributed:

- At `<=768px`, `.md-split` must collapse from the desktop `1fr 312px` grid to one column. Keeping the empty `.md-right` track reserves width for a rail that is hidden on mobile.
- `.md-lenstabs` leaked about 9 px past the viewport. Its mobile rule now resets the margin and applies `box-sizing: border-box` with `max-width: 100%`.
- `.md-marquee` is a flex child whose animated track uses `width: max-content`. Without `min-width: 0`, the roughly 3,950 px track could impose its intrinsic width on the page instead of clipping inside the banner.
- `html` and `body` needed explicit `overflow-x` guards and `max-width: 100vw` so a child regression cannot reopen document-level horizontal scrolling.

## Durable rule

Future mobile work must preserve all four layers. Do not treat the global overflow guard as the root fix: the grid, lens tabs, and marquee each need local containment. The mobile breakpoint remains `<=768px`, and the desktop two-column layout remains unchanged above it.

## Evidence

The relevant shipped fixes are in `frontend/index.html`, including commits `460a0b4`, `3dba108`, `e797d9c`, `cdbfce8`, and `21088ea`. These were layout-only changes; MAIN/JIG logic, scoring, payloads, and heatmap/tier colors were untouched.
