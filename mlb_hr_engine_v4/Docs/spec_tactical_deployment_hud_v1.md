# SPEC: Tactical Deployment HUD Systems v1
## MLB HR Engine — Step 7/12

**Version:** 1.0
**Date:** 2026-05-20
**Phase:** Step 7/12 — Deployment, Portfolio & Operations
**Status:** ARCHITECTURE / UX / DOCTRINE ONLY — no runtime code modified
**Author:** Claude (Visual Doctrine Authority)
**Cross-reference:** `deployment_command_center_doctrine.md`, `spec_deployment_queue_v1.md`, `spec_bankroll_command_layer_v1.md`, `spec_portfolio_exposure_system_v1.md`, `spec_clv_intelligence_system_v1.md`, `spec_risk_governance_v1.md`

---

## A. PURPOSE

The Tactical Deployment HUD is the ambient situational awareness layer of the Deployment Command Center. It surfaces critical session state without demanding attention. It escalates when conditions require attention.

**Core doctrine:** The HUD is a cockpit instrument panel, not a dashboard. It is always on. It renders in the background. It reads at a glance. When a needle enters the danger zone, the operator sees it without having to look for it.

---

## B. HUD LAYER ARCHITECTURE

The Tactical Deployment HUD operates across four persistent layers. Each layer has a specific scope, information density, and attention demand.

```
┌─────────────────────────────────────────────────────────────────┐
│  HUD LAYER 4 — SESSION OVERSIGHT STRIP (always visible, top)   │
│  Compact horizontal strip. 6 core readings. Never expands.     │
├─────────────────────────────────────────────────────────────────┤
│  HUD LAYER 3 — PORTFOLIO STATE PANEL (expandable, right side)  │
│  Exposure heatmap, N_eff, CLV summary. Opens on demand.        │
├─────────────────────────────────────────────────────────────────┤
│  HUD LAYER 2 — DEPLOYMENT QUEUE (main content area, center)    │
│  Active queue with all pick rows, states, and controls.        │
├─────────────────────────────────────────────────────────────────┤
│  HUD LAYER 1 — PICK PANEL (contextual overlay, opens on pick)  │
│  Full 9-zone deployment panel per spec_deployment_panel_v1.    │
└─────────────────────────────────────────────────────────────────┘
```

Layers 4 and 3 are always available. Layer 2 is the primary interaction surface. Layer 1 appears only when a specific pick is under review.

---

## C. HUD LAYER 4 — SESSION OVERSIGHT STRIP

Persistent horizontal strip at the top of the Command Center. Six readings. Always visible. Never collapses.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  SESSION: 2026-05-20 19:14 ET                                                │
│  ████░░░░░ $138/$250 (55%)  │  12/15 deployed  │  N_eff 4.2  │  CLV +1.1pp │
│  GOVERNANCE: ● FULL  ● HEALTHY  ● BALANCED      │  ⚠ 2 advisories          │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Six Session Oversight Readings

**Reading 1: Session Bankroll Bar**
Horizontal progress bar showing deployed capital vs session budget.
- 0–50%: solid `#4a4a70` fill
- 50–70%: amber fill begins blending in
- 70–85%: majority amber `#F5A623`
- 85%+: orange-red `#E87040`

Number displays: `$138/$250 (55%)` — deployed, total, percentage.

**Reading 2: Deployment Counter**
`12/15 deployed` — picks deployed vs session cap.
- Normal: `#9090C0` (secondary text)
- At 80% of cap: amber
- At cap: orange-red + COMPLETE badge

**Reading 3: N_eff**
Current session effective N. Updates after each deployment.
- ≥ 5.0: `#4CAF50` (green) — well diversified
- 3.0–5.0: `#9090C0` — acceptable
- 2.0–3.0: `#F5A623` (amber) — elevated correlation
- < 2.0: `#E87040` (orange-red) — extreme correlation

**Reading 4: Session CLV**
Average CLV across all picks with captured closing lines. Updates when new CLV is available.
- Positive: green value
- Zero to +0.5pp: neutral gray
- Negative: orange-red value

**Reading 5: Governance State**
Three color-coded dots: Trust-state · Bankroll tier · Portfolio state.
- All green: no concerns
- Any amber: advisory active
- Any orange-red: gate active
- Any crimson: hard stop or hard gate active

**Reading 6: Active Advisories Count**
`⚠ 2 advisories` — number of Level 4 advisories currently active.
Clicking opens advisory list panel.

### Session Oversight Strip Visual Rules

- **Strip height:** Fixed 48px. Never grows.
- **Typography:** 11px for labels, 13px for values.
- **Background:** `#0a0a18` (deepest slate) — recedes behind primary content.
- **Alert state:** When any Level 1 Hard Stop is active, strip background transitions to `#1a0a0a` (dark crimson) and all readings mute except governance state which shows full-width HARD STOP banner.

---

## D. HUD LAYER 3 — PORTFOLIO STATE PANEL

Collapsible right-side panel. Default state: collapsed to a 40px-wide indicator strip. Expands to 280px on click.

### Collapsed State (indicator strip)

```
│ ■ BAL │
│ ██ 4.2 │
│ CLV+ │
│ ▾ EXP │
```

Four compact indicators in 40px column:
- Portfolio balance state (BALANCED / ELEVATED / CONCENTRATED / FRAGILE)
- N_eff sparkline micro-bar
- CLV positive/negative/neutral indicator
- Exposure expansion control

When any indicator is at elevated or above, its color escalates to amber or orange-red — visible without expanding.

### Expanded State (280px panel)

```
PORTFOLIO STATE
──────────────────────────────────
State: ● ELEVATED (1 dimension)

EXPOSURE HEATMAP (compact)
     NYY  HOU  SD  BOS
NYY  ████      ·    ·   34%⚠
HOU   ·   ██   ·    ·   16%

Pitcher Targets:
  G. Cole: 3 picks
  F. Valdez: 2 picks

──────────────────────────────────
N_eff: 4.2 / target ≥ 5.0
Correlation: MODERATE

──────────────────────────────────
CLV INTELLIGENCE
Session avg: +1.1pp  EFFECTIVE
Best: Judge +3.1pp  EARLY STRIKE
Worst: Alonso -2.8pp  PRICE COLLAPSE

──────────────────────────────────
[Full Heatmap]  [CLV Detail]
──────────────────────────────────
```

The expanded panel is informational. No deployment actions occur in the portfolio panel. Actions happen in the queue (Layer 2).

---

## E. HUD LAYER 2 — DEPLOYMENT QUEUE

The primary interaction surface. See `spec_deployment_queue_v1.md` for full architecture.

### HUD Queue Header

The queue header provides the session context before the first pick row:

```
DEPLOYMENT QUEUE — 2026-05-20
────────────────────────────────────────────────────────────────
PRIORITY         │ 1 pick
STANDARD         │ 5 picks
WATCH HOLD       │ 3 picks
────────────────────────────────────────────────────────────────
Sort: COMPOSITE SCORE ▾   Filter: ALL   Slate: CONFIRMED 🟢
────────────────────────────────────────────────────────────────
```

The queue header is always visible when scrolling within the queue. It is sticky — it does not scroll away.

### Queue Scroll Behavior

The queue uses standard scroll with these rules:
- Queue header: sticky at queue top
- Session oversight strip (Layer 4): sticky at viewport top (above queue)
- Portfolio panel (Layer 3): fixed at right edge
- Pick panel (Layer 1): opens inline (push-down within queue) — NOT a full-page overlay

**No modals for queue operations.** Queue state changes (suppression acknowledgements, override confirmations) happen inline within the pick row. This preserves scroll context and prevents disorientation.

---

## F. HUD LAYER 1 — PICK PANEL

The per-pick deployment panel. Opens inline below the selected pick row in the queue (push-down). Does not replace the queue view — it expands within it.

Full specification in `spec_deployment_panel_architecture_v1.md`. HUD-specific rules:

**Inline expansion protocol:**
1. Operator taps/clicks "REVIEW" on a queue row
2. Pick row expands downward to reveal the full 9-zone deployment panel
3. Queue rows below the expanded pick scroll down to accommodate
4. Layer 4 strip remains visible at top
5. Layer 3 portfolio panel remains visible at right

**Active review indicator:**
While a pick panel is open, the pick row shows a `REVIEWING` badge. Other picks in READY state show their normal state but their REVIEW buttons are dimmed. Only one pick panel is open at a time.

**Panel close behavior:**
Pick panel closes when:
- Operator presses [Deploy] (pick moves to DEPLOYED)
- Operator presses [Abandon] (pick moves to ABANDONED)
- Operator presses [Close] (no state change — panel collapses back to standard row)
- Operator opens a different pick's panel (current panel closes first)

---

## G. MARKET TIMING HUD

A compact timing indicator appears on each queue row during active sessions.

```
QUEUE ROW — TIMING INDICATORS

[FIRE] Aaron Judge NYY +220    MDL:21.4%  EV:+5.8%  EDGE:+4.2%  [READY]
       ○ 2h 14m before first pitch  │  Market: NORMAL  │  ◉ LINKED: Torres
```

**Timing indicator states:**

| Time before first pitch | Label | Color |
|------------------------|-------|-------|
| > 3 hours | `3h+` | `#5A5A80` (muted) |
| 1–3 hours | `Xh Xm` | `#9090C0` (normal) |
| 30–60 minutes | `APPROACHING` | `#F5A623` (amber) |
| 10–30 minutes | `DEPLOY WINDOW` | `#E87040` (orange-red) |
| < 10 minutes | `FINAL WINDOW` | `#C0392B` (crimson) |
| 0 (game started) | `STARTED` | grayed; hard stop applied |

**Why timing matters in the HUD:** A READY pick in the FINAL WINDOW state should be deployed immediately or abandoned. The operator who sees it cannot claim they didn't know time was running out.

---

## H. BANKROLL HUD ELEMENT

The bankroll HUD element is part of the Layer 4 strip but has its own visual rules.

```
BANKROLL
──────────────────────
Session: $250.00
Deployed: $138.50
At Risk:  ████████░░ 55%
Limit:    ████████████ [80% advisory zone]
Units:    1.7 remaining
──────────────────────
State: HEALTHY
```

The bankroll HUD uses a dual-bar system:
- **Deployed bar** — capital committed to the slip builder or already submitted
- **Limit advisory zone** — visual marker at 80% (yellow) and 90% (red)

When the deployed bar crosses the advisory zone marker, the bankroll HUD escalates: border color changes, label brightens.

---

## I. DEPLOYMENT PACING INDICATORS

The HUD surfaces pacing health to prevent the operator from deploying too quickly.

### Picks-Per-Hour Indicator

Displayed in the session strip when deployment rate exceeds 4 picks in a 30-minute window:

`⚡ PACE: 6/hr   Recommended: ≤4/hr`

This advisory is not a gate. It is a pacing mirror — showing the operator their own behavior. Rapid deployment is correlated with lower quality decisions (reduced deliberation per pick).

### Sequential Deployment Timer

After each deployment confirmation, a brief visual indicator shows time elapsed since last deployment:

`Last deployment: 4 minutes ago`

This indicator appears for the first 3 minutes after a deployment, then fades. It creates a visual rhythm of deliberation.

---

## J. ESCALATION FLOW VISUALIZATION

When a pick transitions through states in the queue, the state change is animated (subtle) to draw attention.

**State transition animations:**

- STAGED → READY: pick row brightens (opacity 0.7 → 1.0); READY badge fades in
- REVIEWING: soft left-border pulse (0.5s period, amber)
- DEPLOYED: pick row dims smoothly (1.0 → 0.4); DEPLOYED badge replaces status; row moves to session history section
- SUPPRESSED: pick row dims (1.0 → 0.6); suppression badge fades in with reason text
- ESCALATED: pick row brightens from suppressed state; READY badge replaces SUPPRESSED badge

**Animation doctrine:** All animations complete in ≤ 0.5 seconds. No animations loop. No animations play automatically when the operator is not interacting with a pick. The purpose of animation is to signal state change — not to decorate.

---

## K. HUD VISUAL STANDARDS

### Background Palette

| Element | Color |
|---------|-------|
| Main content area | `#0d0d1f` |
| Session strip (Layer 4) | `#0a0a18` |
| Portfolio panel | `#0a0a1a` with `1px border #1e1e35` |
| Card backgrounds | `#0f0f22` |
| Active/selected state | `#141430` |
| Hover state | `#12122a` |

### Typography Sizes

| Role | Size | Weight | Color |
|------|------|--------|-------|
| Player name (primary) | 15px | 600 | `#E8E8F0` |
| Tier badge label | 11px | 700 | tier-specific |
| Score values | 13px | 500 | `#C0C0E0` |
| Labels/metadata | 11px | 400 | `#6060A0` |
| Timestamps | 10px | 400 | `#4a4a70` |

### Border Standards

- **Card border** (standard): `1px solid #1e1e35`
- **Card border** (elevated, PRIORITY tier): `1px solid #F5A62355` with left 3px accent `#F5A623`
- **Panel divider**: `1px solid #1a1a30`
- **Alert state border**: `1px solid [tier color]` with brightness boost

### Glow Usage (restricted)

Glow appears ONLY on:
- FIRE tier escalation badge (session HUD summary context)
- Active Live game indicator (when game is in progress)
- Deployment confirmation animation (1-second fade after [Deploy] is confirmed)

Glow does NOT appear on:
- Queue rows
- Bankroll bar
- Governance indicators
- Navigation elements

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
