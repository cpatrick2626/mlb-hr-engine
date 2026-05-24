# Playwright Validation Doctrine

## Purpose

Playwright is the MLB HR ENGINE runtime validation layer.

It is used to verify that the app actually works in the browser after code changes, not merely that Python compiles or Streamlit launches.

Playwright validation must protect:
- persistent shell stability
- MAIN / JIG / STRATEGY separation
- navigation continuity
- tactical visual hierarchy
- rerender stability
- viewport usability
- deployment control visibility
- absence of fatal Streamlit/runtime errors

Playwright is not a redesign tool. It validates behavior, visibility, layout integrity, and runtime safety.

---

## Startup Validation Rules

Before running Playwright checks:

1. Confirm the repo root:
   `C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master`

2. Start Streamlit from repo root only:
   `streamlit run mlb_hr_engine_v4/app.py`

3. Confirm localhost is reachable:
   - default: `http://localhost:8501`
   - alternate ports may be used only if explicitly stated

4. Wait for Streamlit hydration before judging layout.

5. If validation cleanup confirms:
   - no active Streamlit PID
   - no listening port  
   then terminate immediately and return results. Do not remain in polling/watch mode.

6. Validation must report:
   - port used
   - browser used
   - viewport size
   - route tested
   - pass/fail result
   - any visible errors
   - screenshots or logs if available

---

## Fatal Failure Detection

Playwright must immediately flag:

- DuplicateWidgetID errors
- Streamlit red error boxes
- Python traceback visible in browser
- missing primary navigation
- blank page after hydration
- route reset loop
- repeated reload/rerun loop
- unclickable navigation
- missing MAIN shell
- missing JIG shell
- broken top navigation
- collapsed content that cannot be recovered
- horizontal body overflow
- permanent loading state

Any fatal failure blocks visual polish work until resolved.

---

## Rerender Detection Standards

A rerender problem exists when:

- the same action causes repeated full-page rebuilds
- navigation resets unexpectedly
- selected tab changes without user action
- session_state-controlled view returns to default after interaction
- widgets duplicate or disappear
- browser scroll position jumps unexpectedly after non-navigation actions
- repeated Streamlit “Running...” states occur without meaningful user input

Playwright should observe the app for at least 30 seconds after critical interactions when checking rerender stability.

Critical interactions include:
- switching MAIN tabs
- switching JIG tabs
- moving between MAIN and JIG
- opening Full Slate
- opening JIG Builder
- using filters
- expanding tactical cards
- triggering deployment or context controls

---

## Shell Persistence Tests

The tactical shell must remain stable across navigation.

Validate that these shell regions persist unless intentionally hidden:

- top tactical navigation
- active workspace indicator
- Live Player Banner if enabled
- right tactical rail if enabled
- Live Strategy Picks if enabled
- main dynamic content region
- command/deployment context controls
- route-specific tab layer

The shell must not behave like a normal scrolling webpage where core command elements disappear unpredictably.

Protected shell regions must not be rewritten during validation fixes unless explicitly authorized.

---

## Navigation Validation

Playwright must verify that navigation is clickable, visible, and stable.

Required navigation checks:

- MAIN opens correctly
- JIG opens correctly
- STRATEGY opens correctly if present
- HITS opens correctly if present
- PERFORMANCE opens correctly if present
- 26 opens correctly if present
- Full Slate opens from MAIN
- JIG Builder opens from JIG
- returning from JIG to MAIN preserves expected shell state

Navigation labels must not wrap into uneven heights at standard desktop widths.

Buttons must maintain:
- uniform height
- readable label text
- no clipped text
- clear active state
- clear disabled state

---

## Viewport Test Sizes

Minimum viewport checks:

- 1440 × 900: primary desktop validation
- 1366 × 768: compressed laptop validation
- 1024 × 768: stress layout validation
- 929 × 951: observed user desktop window validation

At each viewport, check:
- no horizontal body overflow
- navigation remains usable
- primary controls remain visible
- metric text does not clip
- tactical hierarchy remains readable
- deployment controls are not buried too far below fold

---

## Layout Overflow Rules

Playwright must flag:

- body horizontal overflow
- clipped metric labels
- clipped odds or EV labels
- wrapped tactical nav buttons
- overlapping cards
- hidden controls caused by fixed containers
- content trapped inside overflow-hidden parents
- scrollbars inside small metric cells unless intentional
- text cut off inside pills, cards, or buttons

Metric cells must prioritize readable threat information over decorative spacing.

---

## Tactical Hierarchy Validation

The first viewport must communicate operational priority immediately.

Above the fold should prioritize:
- active route
- top tactical navigation
- primary threat/intelligence module
- current player or slate context
- deployment readiness context
- escalation indicators

Avoid above-fold domination by:
- decorative hero images
- oversized empty panels
- disconnected navigation layers
- duplicate headers
- low-value banners
- dead disabled controls

Hero visuals may support atmosphere but must not split navigation hierarchy or bury operational controls.

---

## Deployment Tray Visibility Rules

Deployment controls are operational elements, not footer decoration.

Playwright must flag deployment or command controls if they appear:
- more than one major scroll below initial viewport
- below decorative content
- disconnected from active tactical context
- visually disabled without explanation
- hidden beneath card stacks
- separated from the decision workflow

Deployment controls should appear close enough to support tactical decision-making.

---

## Visual Density Standards

MLB HR ENGINE should feel like a premium intelligence terminal, not a generic dashboard.

Playwright should flag:
- oversized whitespace
- sparse metric rows
- low-density cards with clipped text
- excessive vertical scrolling
- repeated empty containers
- decorative assets consuming too much first-screen space
- important controls placed below low-value content

Density must remain readable. Compression should improve scanning, not create clutter.

---

## Z-Index And Layering Rules

Playwright or DevTools validation must check:

- modals appear above content
- tooltips do not hide behind shell layers
- sidebar does not permanently cover main content
- sticky headers do not block controls
- overlays do not trap clicks
- command rails do not collide with Streamlit chrome
- future z-index additions do not create fragile stacking conflicts

Any new overlay layer must define its intended stack position.

---

## Screenshot Evidence Rules

For UI validation, screenshots should be captured for:

- initial load
- MAIN default view
- JIG default view
- Full Slate view
- JIG Builder view
- any reported visual failure
- before/after comparison when a layout fix is made

Screenshots should be saved under:

`mlb_hr_engine_v4/reports/screenshots/`

Use descriptive filenames with date, route, and viewport when possible.

---

## Validation Ownership

Claude should use Playwright primarily for:
- tactical UX validation
- shell hierarchy checks
- visual regression review
- navigation flow observation
- screenshot-based findings

Codex should use Playwright primarily for:
- runtime safety validation
- rerender detection
- route stability checks
- session_state verification
- post-patch regression testing

Both agents must preserve:
- deterministic behavior
- MAIN/JIG isolation
- scoring logic
- filter ownership
- session_state governance
- protected shell architecture

---

## Forbidden Validation Behavior

Do not:

- modify files during a findings-only validation
- run endless polling loops
- leave Streamlit processes running after cleanup validation
- infer success from compile-only checks
- ignore visible browser errors
- use screenshots as proof if the app has not hydrated
- validate the wrong port
- validate from the wrong repo directory
- treat cosmetic success as runtime success
- rewrite app architecture during validation
- merge visual polish with scoring/filter changes

---

## Standard Playwright Validation Report Format

Every Playwright validation report should include:

1. Repo path
2. App launch command
3. Port tested
4. Browser used
5. Viewport size
6. Routes tested
7. Interactions tested
8. Errors observed
9. Overflow findings
10. Navigation findings
11. Rerender findings
12. Shell persistence findings
13. Screenshots saved
14. Final verdict:
    - PASS
    - PASS WITH FINDINGS
    - FAIL
15. Recommended next action

---

## Pass / Fail Standard

PASS means:
- app loads
- no fatal runtime errors
- navigation works
- no rerender loop
- shell persists
- no major overflow
- primary tactical hierarchy is usable

PASS WITH FINDINGS means:
- app is usable
- no fatal runtime errors
- issues exist but do not block operation

FAIL means:
- app cannot be reliably used
- runtime errors appear
- navigation breaks
- shell disappears
- rerender loop occurs
- major controls are inaccessible
- wrong app/port was validated

---

## MLB HR ENGINE Specific Validation Priorities

Highest priority checks:

1. MAIN/JIG separation remains intact
2. tactical shell persists across route changes
3. Full Slate remains accessible
4. JIG Builder remains accessible
5. deployment controls are visible enough to be operational
6. nav labels do not wrap unevenly
7. no hidden sidebar padding steals viewport width
8. no clipped EV/odds/metric labels
9. hero visuals do not dominate operational space
10. no duplicate widget or session_state instability appears