# MLB HR ENGINE — Final Shell Lock + Tactical Polish Doctrine
## Phase 4 · Room 10 · v1.0 · 2026-05-23

---

## Table of Contents

1. [Final Shell Lock Doctrine](#1-final-shell-lock-doctrine)
2. [Tactical Viewport Doctrine](#2-tactical-viewport-doctrine)
3. [Tactical Continuity Doctrine](#3-tactical-continuity-doctrine)
4. [Cinematic Hierarchy Doctrine](#4-cinematic-hierarchy-doctrine)
5. [Tactical Spacing Doctrine](#5-tactical-spacing-doctrine)
6. [Interaction Continuity Doctrine](#6-interaction-continuity-doctrine)
7. [Tactical Animation Doctrine](#7-tactical-animation-doctrine)
8. [Shell Identity Doctrine](#8-shell-identity-doctrine)
9. [Validation Doctrine](#9-validation-doctrine)
10. [Codex Implementation Boundaries](#10-codex-implementation-boundaries)
11. [Runtime Contamination Risks](#11-runtime-contamination-risks)
12. [UX Anti-Patterns](#12-ux-anti-patterns)
13. [Final Dashboard Hierarchy Summary](#13-final-dashboard-hierarchy-summary)

---

## 1. Final Shell Lock Doctrine

### Core Principle

The MLB HR ENGINE shell is a **locked tactical operating system**, not a webpage. Once mounted, the shell skeleton never re-renders from scratch. Only the dynamic content zone repaints.

### Protected Shell Zones

| Zone | Element | Mutation Rule |
|------|---------|---------------|
| **T0 — Global Header** | Engine identity, date, status indicator | Never re-renders. Reads `session_state` once at mount. |
| **T1 — Section Rail** | MAIN / JIG / STRATEGY / HITS / PERFORMANCE | Repaint on section change only. No position shift. |
| **T2 — Sub-Room Rail** | Full Slate / Command Center / Top Targets / Match Edge / Portfolio | Repaint on sub-room change only. Height reserved even when empty. |
| **T3 — Context Bar** | Breadcrumb display (`MAIN › NYY@BOS › Judge › Investigation`) | Update in-place. Never collapse. Min-height enforced. |
| **T4 — Sidebar** | Filter controls, operator shortlist, data integrity status | Persist across sub-room switches. Collapse allowed only by operator action. |

### Dynamic Content Zone

- Bounded region below T3 and inside sidebar boundary
- Only this zone receives full Streamlit rerun repaints
- Never overflows into protected zones
- Scroll anchor: top of dynamic zone, not top of page

### Shell-State Continuity Rules

1. `active_route` (T1) and `active_sub_room` (T2) — owned exclusively by `nav_state.py`. No other module writes these keys.
2. Investigation context (`investigation_state`) — persists across sub-room switches. Cleared only by explicit operator dismiss or section change.
3. Operator shortlist (`operator_shortlist`) — persists for full session. Never cleared by navigation.
4. Restoration stack (`nav_restoration_stack`) — depth-capped at 10. Never cleared by sub-room switch.
5. Recovery prompt state — persists until `clear_recovery_prompt()` called. Never auto-dismissed by rerun.

### Shell Transition Behavior

- **Section switch (T1):** sub-room resets to section default. Investigation context clears. Breadcrumb updates.
- **Sub-room switch (T2):** investigation context preserved. Sidebar preserved. Breadcrumb updates. No scroll reset.
- **Player drill-down:** investigation context pushed to restoration stack. Breadcrumb extends. Modal layers over dynamic zone.
- **Back / recovery:** pop restoration stack. Breadcrumb contracts. Dynamic zone restores to last snapshot.

### Shell Forbidden Actions

- No `st.experimental_rerun()` calls from sidebar callbacks
- No layout re-definition inside conditional blocks
- No `st.columns()` calls at shell level outside designated column regions
- No `st.empty()` placeholders in protected zones
- No page reload equivalents triggered by filter changes

---

## 2. Tactical Viewport Doctrine

### Viewport Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│ T0 — GLOBAL HEADER (FIXED, NEVER SCROLLS)               │
├─────────────────────────────────────────────────────────┤
│ T1 — SECTION RAIL (FIXED, NEVER SCROLLS)                │
├─────────────────────────────────────────────────────────┤
│ T2 — SUB-ROOM RAIL (FIXED HEIGHT, RESERVED)             │
├─────────────────────────────────────────────────────────┤
│ T3 — CONTEXT BAR / BREADCRUMB (FIXED, NEVER SCROLLS)   │
├─────────────┬───────────────────────────────────────────┤
│ T4 SIDEBAR  │ T5 — DYNAMIC CONTENT ZONE                 │
│ (fixed pos) │ (ONLY SCROLLABLE REGION)                  │
│             │                                           │
│             │                                           │
└─────────────┴───────────────────────────────────────────┘
```

### Fixed-Region Rules

- T0–T3: `position: sticky; top: 0; z-index: 100+` via injected CSS
- Sidebar (T4): `position: sticky; top: header_height; height: calc(100vh - header_height); overflow-y: auto`
- T2 (Sub-Room Rail): even when section has no sub-rooms, height placeholder preserved to prevent layout jump
- T3 (Context Bar): minimum height `32px` enforced. Never collapses to zero even when breadcrumb is empty.

### Scroll Governance

**Allowed scroll:** T5 (dynamic content zone) only.

**Forbidden scroll:**
- T0 through T3 scrolling out of view on any content length
- Sidebar scrolling out of frame independently of content zone
- Horizontal scroll at any shell tier
- Scroll behavior that orphans the context bar from the content it describes

**Scroll anchor rule:** On sub-room switch, T5 scrolls to top. On player drill-down, T5 preserves scroll position for restoration on back-navigation.

### Responsive Locking

- Below 1280px: sidebar collapses to icon rail. T1–T3 maintain full height.
- Below 1024px: sub-room rail converts to dropdown. Context bar truncates at 2 stages.
- Below 768px: sidebar fully hidden. T1 converts to hamburger. Emergency-mode shell — full tactical pacing not guaranteed.
- **Do not** build custom breakpoint logic in Streamlit Python. CSS injection via `st.markdown(..., unsafe_allow_html=True)` only.

### Focus Preservation

- Keyboard focus stays within T5 after navigation — never jumps to T0
- After modal close, focus returns to the triggering element in T5
- Filter sidebar focus changes do not cause T5 scroll reset

---

## 3. Tactical Continuity Doctrine

### Core Principle

Operator should feel inside **one persistent intelligence environment** across all surfaces. Context is never lost without explicit operator action.

### Cross-Surface Continuity Map

| Transition | Preserved | Cleared |
|-----------|-----------|---------|
| MAIN → JIG | Nothing (section switch clears investigation) | Investigation context, active player, shortlist item priority resets |
| Full Slate → Command Center | Investigation context, shortlist, filters | None |
| Command Center → Top Targets | Investigation context, shortlist | None |
| Any sub-room → Player Modal | Investigation context snapshot pushed to stack | None |
| Modal close (back) | Stack popped, T5 restored | Modal state only |
| Filter change | All navigation state | Filter values only change |
| Date change | Shortlist cleared (stale data), restoration stack cleared | Everything except section |

### Escalation Continuity

- Escalation tier visible in breadcrumb (`T3`) at all times when active
- Escalation badge persists through sub-room switches
- Escalation tier resets only on: date change, section change, explicit operator dismiss
- High-escalation (CRITICAL / ALERT tier) state: restoration stack always holds a snapshot — operator can always return to last context

### Investigation Continuity

`investigation_state` carries:
- `active_player` (player_id, name, team, game_pk)
- `active_game` (game_pk, away_team, home_team, game_label)
- `current_route` (which investigation surface is active)
- `escalation_tier` (WATCH / ALERT / CRITICAL / DEPLOY)

This dict persists across sub-room switches. Cleared only by:
1. Section change (T1 nav)
2. Explicit "close investigation" operator action
3. Date change

### Deployment Continuity

Deployment workflow state (pick queue, bet amounts, logged picks) persists for full session. Never cleared by navigation. Written to `pick_tracker.csv` immediately on log — not held in memory only.

### Operational Rhythm Continuity

Pacing between Full Slate scan → Command Center review → Deployment should feel sequential, not fragmented:
1. Full Slate: surface threats (escalation tier visible)
2. Command Center: investigate top threats (investigation context set)
3. Top Targets: confirm deployment candidates (shortlist populated)
4. Deployment: execute from shortlist

Each step should feel like moving **deeper into the same operation**, not navigating to a different page.

---

## 4. Cinematic Hierarchy Doctrine

### Visual Dominance Hierarchy

```
ESCALATION BADGE (CRITICAL)          ← highest visual weight
  ↓
PLAYER CARD HEADER (top pick)
  ↓
PROBABILITY BAR + HR PROBABILITY
  ↓
EV / EDGE VALUES (qualifying picks)
  ↓
SUPPORTING METRICS (barrel, pitch mix, weather)
  ↓
STATUS INDICATORS (deployment state)
  ↓
CONTEXTUAL LABELS + TIMESTAMPS      ← lowest visual weight
```

Higher weight = higher brightness, heavier font, more prominent position. Never invert this hierarchy.

### Escalation Rhythm

| Tier | Visual Signal | Glow | Animation |
|------|--------------|------|-----------|
| WATCH | Amber label, normal weight | None | None |
| ALERT | Amber bold, amber border on card | Restrained amber edge | None |
| CRITICAL | Red bold, red border, badge dot | Red pulse glow, 1.5s cycle | Single pulse on first appearance |
| DEPLOY | Green bold, green card border | Green ambient edge | None — deployed = stable |

### Glow Rules

**Glow allowed:**
- CRITICAL escalation badge (red pulse)
- Active deployment target card edge (green ambient)
- Probability bar at high-confidence thresholds (≥20% probability, barrel≥10%)
- Selected player card in investigation mode (subtle blue ambient)

**Glow forbidden:**
- Header elements
- Static data labels
- Empty/placeholder cards
- Navigation elements (T1/T2 rails)
- Status indicators not tied to escalation tier
- Any decorative use not tied to escalation or selection state

**Glow intensity cap:** No element exceeds `box-shadow: 0 0 12px` spread. Larger glows = noise, not signal.

### Spacing Choreography

Spacing communicates hierarchy. Tighter = more related. Wider = boundary between sections.

- Within a card: 8px internal padding
- Between related metrics within a card: 4px gap
- Card-to-card spacing: 12px
- Section boundary (e.g., escalation tier break): 20px
- Shell tier boundary (T2→T3→T5): 0px (no gap — shell tiers are continuous)

### Depth Layering

```
z-index 500+  : Modal overlays
z-index 200   : Sidebar (T4)
z-index 100   : Fixed shell tiers (T0–T3)
z-index 50    : Escalation badges (float above cards)
z-index 10    : Active card (selected/hover state)
z-index 1     : Default card
z-index 0     : Background / shell canvas
```

---

## 5. Tactical Spacing Doctrine

### Core Principle

High information density with clear escalation readability. Never trade density for whitespace. Never trade readability for density.

### Density Targets

| Surface | Target Rows Visible Without Scroll | Max Column Count |
|---------|-----------------------------------|------------------|
| Full Slate table | 12–15 batters | 10 |
| Top Targets cards | 4–6 cards above fold | — |
| Player card expanded | All key metrics above fold | 2 |
| Command Center | Full summary + top 3 threats above fold | — |
| Portfolio view | All active positions above fold (n≤20) | 4 |

### Spacing Rhythm

- **Dense zone** (tables, metric grids): 4px row padding, 8px column padding
- **Card zone** (player cards, threat cards): 12px inner padding, 12px card gap
- **Decision zone** (deployment, confirmation): 16px inner padding — breathing room signals importance
- **Shell frame** (T0–T3 tiers): 8px vertical padding each — compact but not cramped

### Forbidden Spacing Patterns

- `margin-top: 2rem` or larger between related content elements
- Empty `st.write("")` or `st.markdown("")` calls used as spacers
- Full-width `st.divider()` used more than once per view section
- Cards with padding > 16px (signals low-density lifestyle dashboard, not tactical system)
- Row heights > 48px in dense tables

### Card Spacing Hierarchy

```
╔══════════════════════════════════╗  ← card border (1px, tier-color)
║ PLAYER NAME  [ESCALATION BADGE] ║  ← 12px top padding
║ Team · Opponent · Ballpark       ║  ← 4px below name
║─────────────────────────────────║  ← 1px divider, 8px margin
║ HR PROB: 22.4%  EV: +8.1%       ║  ← primary metrics row
║ Barrel: 12.1%   Edge: +5.3%     ║  ← secondary metrics row, 4px gap
║─────────────────────────────────║
║ [INVESTIGATE]   [ADD TO QUEUE]  ║  ← 8px bottom padding
╚══════════════════════════════════╝
12px gap to next card
```

### Shell Breathing Balance

T0–T3 tiers must not eat more than 15% of viewport height. If combined header/rail height exceeds 15vh:
1. T0 header: reduce to single row (logo + date + status inline)
2. T2 sub-room rail: use compact button variant (28px height)
3. T3 context bar: single line, truncate breadcrumb at 4 stages

Never sacrifice T3 (context bar) to reclaim space — operator orientation is non-negotiable.

---

## 6. Interaction Continuity Doctrine

### Core Principle

Every interaction must feel like operating a system, not clicking a website. Interactions are deliberate, feedback is immediate, context is preserved.

### Hover Continuity

- Hover states: `150ms` transition. No instant snap, no slow drift.
- Hover should reveal **one** additional piece of information or one action (not both).
- Hover tooltip: position above or to the right — never obscures the triggering element.
- Hover state must not shift surrounding layout (no `padding` or `margin` changes on hover).
- Hover on metric value: show raw underlying figure if displayed value is formatted/rounded.

### Click Continuity

- Click feedback: immediate visual state change (no latency illusion). Use `st.spinner()` only for operations > 500ms.
- Destructive clicks (remove from shortlist, clear queue): require confirmation inline — no full modal for small actions.
- Navigation clicks: breadcrumb updates before content finishes loading.
- Double-click behavior: undefined — do not rely on it for any core action.

### Modal Continuity

Modal layering rules:
1. Only one modal open at a time. Second modal trigger: dismiss first or stack behind.
2. Modal always contains a visible close affordance (top-right × or escape key).
3. Modal backdrop: `rgba(0,0,0,0.65)` — dark enough to indicate focus, not so dark it loses shell context.
4. Modal width: max 800px, centered. Never full-screen.
5. Modal scroll: internal scroll only. Shell behind modal does not scroll.
6. Modal close: returns focus to triggering element. Context preserved in restoration stack.

### Player Investigation Flow

```
Full Slate row click
  → investigation_state populated
  → breadcrumb extends: MAIN › [Game] › [Player] › Investigation
  → modal OR inline expansion (sub-room dependent)
  → T4 sidebar shows player-specific filter context
  → All investigation surfaces available (arsenal, splits, pitch mix, matchup)
  → Dismiss/back: pop restoration stack, breadcrumb contracts
```

### Deployment Interaction Flow

```
"Add to Queue" click
  → shortlist updated
  → queue badge count increments (visible in T4 sidebar)
  → no navigation change

"Deploy" from queue
  → confirmation inline (pick_tracker.log_picks_bulk)
  → success: badge turns green, entry locked
  → failure: inline error with retry — no page reload
```

### Interaction Pacing

- Clicks that trigger data fetches: disable button immediately, show inline `[Loading...]` label, re-enable on completion
- State transitions visible within 100ms of click
- No spinner that runs longer than 3s without a status update message

---

## 7. Tactical Animation Doctrine

### Core Principle

Animation communicates **state change**, not aesthetics. Every animation has a functional justification. If the animation were removed, the interface should still be fully usable — animation is enhancement only.

### Allowed Animations

| Animation | Target | Timing | Purpose |
|-----------|--------|--------|---------|
| CRITICAL badge pulse | Escalation badge | 1.5s, ease-in-out, repeating | Alert operator to active critical tier |
| Card border flash | New CRITICAL pick appearing in slate | Single 500ms flash on mount | Signals new high-priority item |
| Probability bar fill | On first render of player card | 300ms linear | Makes probability value scannable |
| Modal fade-in | Modal mount | 200ms ease-out | Smooth focus shift |
| Modal fade-out | Modal dismiss | 150ms ease-in | Clean return to shell |
| Sub-room content fade | On sub-room switch | 100ms opacity | Prevents jarring content swap |

### Forbidden Animations

- Sliding panels from off-screen (esports / entertainment pattern)
- Parallax or depth scrolling effects
- Rotating / spinning elements except explicit loading states
- Entrance animations on every render (only on first mount or state change)
- Any animation on static elements that don't represent state change
- Hover scale transforms (`transform: scale(1.05)`) — shifts layout, breaks density
- Glow intensity oscillation on non-critical elements

### Escalation Animation Hierarchy

```
CRITICAL badge pulse: highest priority animation, never suppressed
ALERT badge appearance: single flash, then static
WATCH badge: no animation — informational only
DEPLOY state: no animation — stable state, not urgency state
```

### Timing Standards

```
Instant    (0ms): Button active states, focus rings
Micro     (100ms): Opacity crossfades, sub-room transitions
Short     (200ms): Modal entrance, card mount on first render
Medium    (300ms): Probability bar fill, chart draws
Long      (500ms): CRITICAL badge flash (entry only)
Cycle    (1500ms): CRITICAL pulse repeat
```

Nothing exceeds 500ms for a single-fire animation. Nothing repeats except CRITICAL pulse.

### Streamlit Implementation Note

Streamlit does not natively support CSS animations on Python-rendered elements. All animations must be injected via `st.markdown(css_block, unsafe_allow_html=True)`. Scope CSS classes tightly to avoid bleeding into Streamlit's own UI chrome.

---

## 8. Shell Identity Doctrine

### Platform Identity Statement

MLB HR ENGINE is **operational intelligence software for professional sports betting analysis**. The shell communicates:
- Machine precision
- Tactical seriousness
- Premium tooling
- Data authority

It does not communicate:
- Consumer entertainment
- Sports fan enthusiasm
- Startup product energy
- Sci-fi fantasy

### Realism / Futurism Balance

```
←── PURE REALISM ────────────────── PURE FUTURISM ──→
    Bloomberg Terminal                Minority Report HUD
              ↑
         MLB HR ENGINE
         (70% realism, 30% cinematic polish)
```

The 30% cinematic polish means: dark canvas, restrained glow on escalation tiers, confident typography, layered depth. Not: holograms, animated backgrounds, neon gradients, excessive transparency.

### Typography Hierarchy

| Element | Weight | Size | Case |
|---------|--------|------|------|
| Engine title | 700 | 18px | UPPERCASE |
| Section labels (T1) | 600 | 14px | UPPERCASE |
| Sub-room labels (T2) | 500 | 13px | Title Case |
| Breadcrumb (T3) | 400 | 12px | Mixed |
| Card player name | 600 | 15px | Title Case |
| Primary metrics | 700 | 14px | Normal |
| Secondary metrics | 400 | 12px | Normal |
| Labels / captions | 400 | 11px | UPPERCASE, letter-spaced |

**Font choice:** System monospace stack preferred for metric values (`font-family: 'JetBrains Mono', 'Consolas', monospace`). Sans-serif for names and labels (`font-family: 'Inter', system-ui, sans-serif`).

### Color System

| Role | Value | Usage |
|------|-------|-------|
| Shell canvas | `#0d1117` | Background |
| Shell surface | `#161b22` | Card backgrounds |
| Shell border | `#30363d` | Card/section borders |
| Shell text primary | `#e6edf3` | Primary content text |
| Shell text secondary | `#8b949e` | Labels, captions |
| Escalation amber | `#f0883e` | WATCH / ALERT |
| Escalation red | `#f85149` | CRITICAL |
| Escalation green | `#3fb950` | DEPLOY / positive ROI |
| Data blue | `#58a6ff` | Probability bars, active selection |
| Data neutral | `#8b949e` | Below-threshold metrics |

**No gradients** except subtle depth gradient on shell canvas (`#0d1117` → `#101820` top-to-bottom, 1px difference only).

### Shell Visual Consistency Rules

1. All cards same border-radius: `6px`
2. All cards same border-width: `1px`
3. Card border color = tier escalation color when escalated, `#30363d` when neutral
4. No card has a drop shadow (use border color for depth, not shadow)
5. No icon that isn't system-standard (no custom SVG illustrations)
6. No colored background fills except escalation tier indicators (use border, not fill)

---

## 9. Validation Doctrine

### Shell Polish Validation Checklist

Run this checklist against every major shell change before marking a room complete.

#### Viewport Locking
- [ ] T0 header stays fixed on scroll to bottom of Full Slate
- [ ] T1 section rail stays fixed on all sub-rooms
- [ ] T2 sub-room rail height preserved when section has no sub-rooms
- [ ] T3 context bar visible at all times, never collapses
- [ ] Sidebar does not detach from frame on long content lists

#### Shell Continuity
- [ ] Sub-room switch preserves investigation context
- [ ] Filter change does not clear breadcrumb
- [ ] Date change correctly clears shortlist and restoration stack
- [ ] Back navigation from modal returns to correct T5 scroll position
- [ ] Restoration stack depth does not exceed 10 after repeated drill-downs

#### Escalation Continuity
- [ ] CRITICAL badge visible in T3 breadcrumb across all sub-rooms
- [ ] Escalation tier resets only on explicit section change or date change
- [ ] ALERT tier cards persist in Top Targets after switching to Command Center and back

#### Interaction Continuity
- [ ] Button click states update within 100ms
- [ ] Modal opens with correct player context
- [ ] Modal close returns to correct shell state
- [ ] Shortlist badge count accurate after add/remove
- [ ] Deployment confirmation flow completes without page reload

#### Responsive Behavior
- [ ] 1280px: full layout intact
- [ ] 1024px: sub-room rail dropdown functional
- [ ] No horizontal scrollbar at any viewport width ≥ 1024px

#### Hover Stability
- [ ] Hover states do not shift card dimensions
- [ ] Hover tooltips do not obscure triggering element
- [ ] Hover on metric shows correct underlying value

#### Modal Stability
- [ ] Only one modal mountable at a time
- [ ] Modal backdrop correct opacity
- [ ] Modal internal scroll independent of shell scroll
- [ ] Modal close affordance always visible

#### Spacing Consistency
- [ ] No card padding exceeds 16px
- [ ] No inter-card gap exceeds 12px
- [ ] Dense table rows visible 12–15 above fold at 1280px
- [ ] No `st.write("")` spacers in any view

#### Tactical Pacing
- [ ] CRITICAL pulse animation present and limited to 1.5s cycle
- [ ] No animation on static, non-escalated elements
- [ ] Sub-room transition completes within 200ms visual settle

#### Operational Realism
- [ ] No sci-fi language in UI labels
- [ ] No consumer-style call-to-action copy
- [ ] All metric labels use domain-standard terminology (HR%, EV%, Barrel%, CLV, Edge)
- [ ] No decorative emojis in tactical surfaces

---

## 10. Codex Implementation Boundaries

### What Codex MAY Polish

CSS injection (`st.markdown` blocks):
- Card border colors, radii, padding
- Typography sizing and weight adjustments
- Hover state transitions
- Glow effects on escalation badges
- Table density adjustments
- Z-index layering for fixed elements
- Sub-room rail button styling
- Modal backdrop and sizing

Component-level rendering adjustments:
- Player card layout within `output/display.py`
- Threat card escalation tier rendering
- Probability bar fill logic
- Metric formatting (decimal places, sign display)
- Empty-state messaging

### What Codex MAY NOT Touch

**Routing and navigation ownership:**
- `nav_state.py` — any function or constant
- `navigation_continuity.py` — any function or state key
- `investigation_state.py` — state schema or ownership rules
- `active_route` and `active_sub_room` session_state keys from any other module

**Session state hydration:**
- `_build_startup_context()` in `app.py`
- Any `st.session_state` initialization block that runs at module scope
- `ensure_navigation_continuity_state()` call sites

**Trust and deployment systems:**
- `engine/trust.py`
- Deployment lifecycle state keys
- Pick tracker write paths (`tracking/pick_tracker.py`)
- CLV logging write paths (`tracking/clv.py`)

**Data pipeline:**
- `pipeline.py` — any function
- `engine/probability.py` — any function
- `engine/calibration.py` — any function
- `config.py` — any constant

**Shell-state coordination:**
- `app.py` section routing conditionals
- `filter_controls.py` state ownership
- `strategies_ui.py` rendering orchestration

### Dangerous Rewrite Zones

These areas have caused prior regressions. Codex must treat as read-only unless explicitly instructed:

1. `app.py` lines 1–200 (startup, imports, context init)
2. Any `st.set_page_config()` call
3. `session_state` keys prefixed with `_` (internal framework state)
4. CSS selectors targeting `.stApp`, `.main`, `.block-container` (Streamlit internals)

---

## 11. Runtime Contamination Risks

### Shell Fragmentation

**Symptom:** Shell tiers (T0–T3) repaint independently on sub-room switch, causing visible flash or layout jump.

**Cause:** Component rendering order changed; shell tier rendered inside conditional block that re-evaluates on rerun.

**Prevention:** Shell tiers always rendered unconditionally at top of `app.py` render pass. Never inside `if active_route == X:` blocks.

**Containment:** Isolate shell tier rendering into dedicated functions (`render_header()`, `render_section_rail()`, etc.) called before any content routing.

**Rollback:** Revert to last committed `app.py` before structural change.

---

### Escalation Desync

**Symptom:** Escalation badge in T3 breadcrumb shows different tier than card badge in T5.

**Cause:** Two code paths writing escalation tier independently (one in pipeline, one in display layer).

**Prevention:** Single source of truth for escalation tier: `investigation_state["escalation_tier"]`. Display layer reads only.

**Containment:** Add assertion in `render_breadcrumb()`: escalation tier read from `investigation_state`, not local variable.

---

### Interaction Pacing Drift

**Symptom:** Button clicks feel delayed or unresponsive. Spinner persists after operation completes.

**Cause:** `st.spinner()` context wrapping operations that already have internal loading states; or spinner not dismissed on exception path.

**Prevention:** Spinner only for operations > 500ms. Always use `try/finally` to ensure spinner dismissal.

**Containment:** Remove all `st.spinner()` wrapping sub-200ms operations.

---

### Viewport Collapse

**Symptom:** Fixed shell tiers scroll off-screen on long content in T5.

**Cause:** CSS `position: sticky` requires all ancestor elements to have `overflow: visible`. Streamlit's `.block-container` often overrides this.

**Prevention:** Target `.stApp > header, .stApp > section > div:first-child` for sticky positioning, not Streamlit internal classes.

**Containment:** Inject override CSS explicitly after Streamlit's own stylesheet injection. Use `!important` only where Streamlit's inline styles fight.

---

### Rerender Visual Jitter

**Symptom:** Cards flash or jump position on filter change or metric update.

**Cause:** `st.columns()` ratios recalculated on rerun with different values; card heights change due to conditional content.

**Prevention:** Fixed column ratios. Min-height on all cards. Conditional content uses `st.empty()` placeholder to preserve height.

**Containment:** Audit all `st.columns()` calls — verify ratios are constants, not computed values.

---

### Modal Contamination

**Symptom:** Modal opens with stale player context from previous investigation.

**Cause:** Modal renders before `investigation_state` updated; or `investigation_state` not cleared on previous modal dismiss.

**Prevention:** Modal rendering always reads `investigation_state` at render time, not captured in closure. Modal dismissal calls `clear_investigation_context()`.

**Containment:** Add guard: if `investigation_state["active_player"]` is empty, do not render modal body — render empty state instead.

---

### Shell-State Drift

**Symptom:** Session state contains stale keys from previous session (Streamlit hot-reload scenario). Navigation appears correct but behavior is wrong.

**Cause:** `st.session_state` persists across hot-reloads in development. Old schema keys conflict with new schema.

**Prevention:** All session state keys version-tagged in key name (e.g., `_v4_active_route`). `init_nav_state()` validates key existence AND value validity.

**Containment:** Add `_validate_session_schema()` call at app entry point. Wipe and reinitialize if schema version mismatch detected.

---

## 12. UX Anti-Patterns

### Fake Cyberpunk Syndrome

**Symptoms:**
- Cyan/magenta neon color scheme with no functional meaning
- HUD overlay elements that display data already shown elsewhere
- Scan-line texture on backgrounds
- "SYSTEM ONLINE" / "NEURAL NETWORK ACTIVE" labels
- Animated grid lines or particle effects

**Cause:** Confusing "tactical aesthetic" with "sci-fi entertainment aesthetic."

**Prevention:** Every visual element must map to a functional role. If it has no data or action behind it, remove it.

---

### Dashboard Wallpaper Syndrome

**Symptoms:**
- Large hero image or background graphic taking >30% of viewport
- Charts with no interaction sitting decoratively in shell frame
- Metric numbers displayed at 72px+ font size purely for visual impact
- Empty whitespace > 40px used as "breathing room"

**Cause:** Designing for screenshot/demo appeal rather than operational use.

**Prevention:** Every inch of viewport must be either actionable data, contextual information, or navigation affordance.

---

### Glow Abuse

**Symptoms:**
- More than 3 glowing elements visible at once
- Glow on static/neutral elements (headers, labels, metric values not tied to escalation)
- Glow intensity competing with escalation badges
- Glow used as hover state on every card

**Cause:** Treating glow as "premium feel" rather than as escalation signal.

**Prevention:** Glow is reserved for: CRITICAL escalation badge, active DEPLOY target, selected investigation target. Nothing else.

---

### Whitespace Addiction

**Symptoms:**
- `st.write("")` calls between every component
- `margin-top: 40px` on every section header
- Cards with >20px padding
- "Airy" layouts that show 4–5 items above fold instead of 12–15

**Cause:** Confusing consumer app spaciousness with tactical density.

**Prevention:** See spacing targets in Section 5. Dense ≠ cluttered when hierarchy is clear.

---

### Animation Addiction

**Symptoms:**
- Every card has an entrance animation
- Hover causes scale, translate, and color change simultaneously
- Navigation transitions take >300ms
- Loading states use custom animated logos instead of spinners

**Cause:** Using animation as engagement signal rather than state-change signal.

**Prevention:** See animation doctrine in Section 7. One functional animation per state change. Never animate static states.

---

### Floating Layout Syndrome

**Symptoms:**
- Cards float at different vertical positions on same row
- Column heights inconsistent causing ragged bottom edge
- Metrics aligned to different baselines across adjacent cards

**Cause:** CSS flexbox/grid not applied; relying on Streamlit's default flow layout.

**Prevention:** Use explicit column ratios. Enforce min-height on cards. Align metric rows to shared baseline grid.

---

### Over-Widgetization

**Symptoms:**
- 3+ dropdowns to select a single filter value that changes infrequently
- Multi-select for options that are always selected together
- Sliders for thresholds the operator never adjusts
- Expanders nested inside expanders

**Cause:** Exposing model configurability as UI affordance.

**Prevention:** Only controls that the operator meaningfully adjusts per session belong in the UI. Model constants stay in `config.py`.

---

### Tactical Clutter Collapse

**Symptoms:**
- More than 8 metric columns in a single table
- Player cards showing 12+ metrics simultaneously
- Color coding on 6+ different dimensions simultaneously
- Font size < 10px for any visible metric

**Cause:** Showing everything known instead of showing what's decision-relevant.

**Prevention:** Primary view shows: Player, HR%, EV%, Edge, Barrel%, Escalation tier. Everything else is drill-down.

---

### Visual Democracy

**Symptoms:**
- All cards same visual weight regardless of escalation tier
- CRITICAL picks visually indistinguishable from WATCH picks
- All metrics displayed at same size and weight

**Cause:** Treating all data as equal.

**Prevention:** Visual hierarchy must exactly mirror escalation hierarchy. CRITICAL picks must dominate the visual field.

---

### Cinematic Overproduction

**Symptoms:**
- More than 2 restrained glow elements visible at once
- Sub-second animations on every user action
- "Intelligence feed" style typewriter text effects
- Sound or haptic feedback attempts
- Dashboard feels like a product demo reel, not a work tool

**Cause:** Optimizing for impressiveness over usability.

**Prevention:** After every visual addition, ask: "Would this be in Bloomberg Terminal?" If no: remove or justify.

---

## 13. Final Dashboard Hierarchy Summary

### Platform Hierarchy

```
╔══════════════════════════════════════════════════════════════╗
║           TACTICAL COMMAND CENTER (Shell Frame)              ║
║   Global header · Section rail · Sub-room rail · Context bar ║
╠══════════════════════════════════════════════════════════════╣
║         FULL SLATE ORCHESTRATION                             ║
║   All starting batters · Escalation tier assignment          ║
║   Threat surface · Portfolio-level exposure view             ║
╠══════════════════════════════════════════════════════════════╣
║         BATTERS TABLE                                        ║
║   Dense sortable view · Escalation filtering                 ║
║   Barrel tier color coding · EV/Edge ranking                 ║
╠══════════════════════════════════════════════════════════════╣
║         PLAYER CARD                                          ║
║   HR probability · Pitch mix matchup (HVY modifier)          ║
║   Statcast profile · Park/weather/pitcher context            ║
║   Arsenal drill-down · Historical H2H                        ║
╠══════════════════════════════════════════════════════════════╣
║         DEPLOYMENT + TRACKING                                ║
║   Shortlist queue · Bet sizing · Pick logging                ║
║   CLV capture · P&L tracking · pick_tracker.csv write        ║
╠══════════════════════════════════════════════════════════════╣
║         TRUST + RESILIENCY                                   ║
║   Data integrity checks · Drift monitor alerts               ║
║   API health · Stale data warnings · Trust state indicators  ║
╠══════════════════════════════════════════════════════════════╣
║         WORKFORCE GOVERNANCE                                 ║
║   AI workforce command routing · Escalation doctrine         ║
║   Session continuity · Operator override controls            ║
╚══════════════════════════════════════════════════════════════╝
```

### Shell Relationship Hierarchy

```
nav_state.py (T1/T2 routing authority)
    └── navigation_continuity.py (restoration, shortlist, breadcrumb)
        └── investigation_state.py (active player/game context)
            └── app.py (render orchestrator — reads state, never owns it)
                └── components/ (pure renderers — no state ownership)
```

No component below `nav_state.py` writes routing state. No component below `investigation_state.py` writes investigation context. State ownership flows strictly downward — never bidirectionally.

### Escalation Visibility Hierarchy

At any moment, operator must be able to answer in ≤2 seconds:
1. **What date am I analyzing?** — T0 header
2. **What section am I in?** — T1 rail active state
3. **What sub-room am I in?** — T2 rail active state + T3 breadcrumb
4. **What player/game am I investigating?** — T3 breadcrumb
5. **What is the escalation tier?** — T3 breadcrumb badge + active card highlight
6. **How many picks are in my queue?** — T4 sidebar queue badge

If any of these answers requires scrolling or clicking, the shell is broken.

### Interaction Sequencing

```
SCAN (Full Slate)
  └─→ SURFACE THREAT (escalation badge appears)
        └─→ INVESTIGATE (player card + arsenal + matchup)
              └─→ QUALIFY (add to shortlist if ALERT/CRITICAL tier)
                    └─→ DEPLOY (bet sizing + pick logging)
                          └─→ TRACK (CLV capture + P&L settlement)
                                └─→ LEARN (drift monitor + calibration drift alerts)
```

Each step is a sub-room or modal within the same shell. Operator never leaves the operating environment.

### Tactical Continuity Flow

```
MAIN Engine → Full Slate → identify ALERT-tier threats
                ↓
           Command Center → investigate top threats by game
                ↓
           Top Targets → shortlist qualifying DEPLOY candidates
                ↓
           Portfolio → check exposure concentration before deploying
                ↓
           STRATEGY tab → verify EV threshold + arbitrage overlaps
                ↓
           Deployment confirmation → pick_tracker.log_picks_bulk()
                ↓
           Daily ops → ops_daily.py + capture_closing_lines.py
```

This is the **canonical operational workflow**. The shell must make this flow feel inevitable — each next step visible and accessible from the current step.

---

*Doctrine version: 1.0 · Phase 4 Room 10 · 2026-05-23*
*Next review: after n≥200 real settled picks OR Phase 5 shell changes*
*Author: Claude (Phase 4 orchestration) · MLB HR ENGINE*
