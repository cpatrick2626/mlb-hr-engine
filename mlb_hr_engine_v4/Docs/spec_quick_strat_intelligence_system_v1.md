# QUICK STRAT INTELLIGENCE SYSTEM — Doctrine v1
**Owner:** Claude (Visual Doctrine Authority)
**Phase:** Step 2/8 — Tactical Rail Doctrine
**Status:** Doctrine Only — No Runtime Implementation
**Replaces:** "Quick Navigation" placeholder block in `_render_sidebar_shell_zones()` (app.py:1007–1013)

---

## 1. SYSTEM PURPOSE

Quick Strat is a **live tactical deployment intelligence surface** embedded in the sidebar right rail.

It surfaces:
- Highest-qualified strategy deployments derived from the existing strategy engine
- Active offensive opportunities scored by the model's EV, Edge, and barrel signals
- Dangerous matchup combinations that cross multiple edge thresholds
- Elite HR threat clusters organized by strategic lens
- Rotating strategy concepts from the 10-type strategy rotation

Quick Strat is **not** a recommendation widget. It is a deployment intelligence layer that makes strategy selection operationally readable at a glance, without requiring the operator to navigate to the ADVANCED STRATEGIES view.

### Identity Formula

> 80% tactical realism · 20% cinematic escalation

The cinematic layer supports focus, intelligence readability, and deployment clarity. It never overpowers legibility.

---

## 2. RAIL LOCATION AND OWNERSHIP

**Location:** Streamlit sidebar — `with st.sidebar:` block in `app.py`

**Replaces:** The entire `#### 🧭 Quick Navigation` block (app.py lines 1007–1013) inside `_render_sidebar_shell_zones()`

**Position within sidebar zone order:**
1. Live Slate Summary
2. Top Escalations
3. Deployment Queue
4. Tactical Alerts
5. Suppression Warnings
6. Live HR Environment
7. Source Indicators
8. **QUICK STRAT** ← replaces Quick Navigation here
9. Operator Shortlist

**Do not alter:**
- Any other sidebar zone
- `_render_sidebar_shell_zones()` function signature
- `_render_deployment_tray()` or any zone below Quick Strat
- Session state architecture
- Viewport ownership of any other section

---

## 3. RAIL STRUCTURE HIERARCHY

```
QUICK STRAT (rail container)
├── TOP BAR
│   ├── Title: "QUICK STRAT"
│   ├── LIVE indicator pill
│   └── B-QTY dropdown (1–5)
│
├── STRATEGY GROUP CARD [0]  ← highest-scored strategy
│   ├── Strategy icon background (faded, behind player layer)
│   ├── Strategy title
│   └── Player rows × B-QTY
│       ├── Player portrait (routes → FD deployment)
│       ├── Player name (routes → Player Card modal)
│       └── Compact stat strip
│
├── STRATEGY GROUP CARD [1]  ← second strategy
│   └── (same structure)
│
└── STRATEGY GROUP CARD [2]  ← third strategy
    └── (same structure)
```

Three strategy group cards visible simultaneously. Rail scrolls vertically if cards overflow sidebar height. Cards do not paginate horizontally.

---

## 4. TOP BAR SPEC

### Title
- Label: `QUICK STRAT`
- Typography: all-caps, letter-spacing ≥ 1.6px, tactical weight (700)
- Color: `#e2e8f0` (near-white, not pure white)
- Size: 11px

### LIVE Indicator
- Label: `LIVE`
- Style: small pill, no border, background `rgba(74, 222, 128, 0.12)`, text `#4ade80`
- Behavior: static on initial load; single-pulse animation when data refreshes (inherits motion governance — justified by data state change)
- Size: 9px, all-caps

### B-QTY Dropdown
- Label: `B-QTY`
- Options: 1, 2, 3, 4, 5
- Default: 3
- Controls: number of player rows shown inside each strategy group card
- Persists in `session_state["quick_strat_bqty"]` — survives reruns
- Does not trigger data reload; re-filters already-loaded player pool

---

## 5. STRATEGY ROTATION ARCHITECTURE

### Strategy Pool (10 types)

| Strategy ID | Display Name | Source Computation |
|-------------|-------------|-------------------|
| `POWER_PROFILE` | POWER PROFILE | `_cached_power_parlays()` top single players |
| `MATCHUP_EDGE` | MATCHUP EDGE | Players with `pitcher_factor ≥ 1.10` AND `platoon_factor ≥ 1.03` |
| `DEPLOYMENT_EDGE` | DEPLOYMENT EDGE | Qualified picks sorted by `edge_pct` descending |
| `FULL_SLATE` | FULL SLATE | All qualified picks today with lineup confirmed |
| `STARS_ALIGNED` | STARS ALIGNED | `_cached_stars_aligned()` alignment_score ≥ 1.08 |
| `MULTI_EDGE` | MULTI-EDGE | `_cached_multi_edge()` edge_count ≥ 3 |
| `CORRELATION` | CORRELATION | `_cached_corr_parlays()` top-scored individual legs |
| `PARK_MONSTER` | PARK MONSTER | `_cached_park_parlays()` top individual players by park_factor |
| `PITCHER_TARGET` | PITCHER TARGET | `_cached_pitcher_targets()` stacked hitters per pitcher |
| `PORTFOLIO` | PORTFOLIO | `portfolio/optimizer.py` barrel_focused preset top N |

### Rotation Rules

- On load: select top 3 strategies that have **at least 1 qualifying player** for today's slate
- Selection priority: strategies are scored by `qualifying_count × avg_strategy_signal_strength`
- Empty strategies (0 qualifying players) are skipped, next strategy promotes
- On manual expand/collapse of a card: the card's strategy does not change; it only reveals/hides player rows
- On data refresh: re-evaluate which 3 strategies qualify; update cards with slide transition (see Motion Doctrine)
- Rotation does **not** auto-advance on a timer — it is state-driven, not animated-carousel-driven

### Strategy Display Ordering

Within each strategy group card, players are ordered:
1. By `confidence_tier` ascending index (S=0, A=1, B=2, C=3)
2. Then by `ev_pct` descending
3. Truncated to B-QTY count

---

## 6. STRATEGY GROUP CARD SPEC

### Card Container

```
Background:    linear-gradient(170deg, #07070e 0%, #04040a 100%)
Border:        1px solid #13131f
Border-radius: 12px
Padding:       10px 10px 8px 10px
Margin:        0 0 8px 0
Min-height:    auto (shrinks to content + B-QTY rows)
```

Glow: apply tier glow per `visual_primitive_standards.md §2 GLOW LANGUAGE`
- Strategy with ELITE-tier players present → ELITE glow
- Strategy with HIGH-tier players → HIGH glow
- All other → no glow

### Strategy Icon Background

**Purpose:** Identity marker. Reinforces strategic type without cluttering readability.

**Specification:**
- Position: absolute, centered in card background layer
- Opacity: 0.04–0.07 (never higher — preserves player data readability)
- Size: 80% of card width, constrained to card height
- Color: single muted tint matching strategy's dominant signal color (see color map below)
- Style: filled SVG or Unicode glyph scaled — NOT a gaming badge, NOT a cartoon icon

**Strategy icon color map:**

| Strategy | Icon Concept | Tint Color |
|----------|-------------|-----------|
| POWER PROFILE | Blast radius / shockwave ring | `#f59e0b` (amber) |
| MATCHUP EDGE | Crossed targeting reticles | `#60a5fa` (blue) |
| DEPLOYMENT EDGE | Compass bearing / azimuth mark | `#34d399` (emerald) |
| FULL SLATE | Grid / full roster spread | `#818cf8` (indigo) |
| STARS ALIGNED | Celestial alignment / orbital arc | `#fbbf24` (gold) |
| MULTI-EDGE | Stack/convergence mark | `#f97316` (orange) |
| CORRELATION | Network node cluster | `#a78bfa` (violet) |
| PARK MONSTER | Stadium outline / home plate | `#22d3ee` (cyan) |
| PITCHER TARGET | Crosshair / scope reticle | `#f87171` (red) |
| PORTFOLIO | Distribution curve / allocation grid | `#86efac` (light green) |

Icon must:
- Remain behind all player data layers (z-index below text)
- Never animate in steady state
- Not include player numbers, team logos, or league marks
- Feel metallic and operational, not decorative

### Strategy Title

```
Font:           All-caps, weight 700, letter-spacing 1.4px
Size:           10px
Color:          #94a3b8 (muted slate — not competing with player names)
Margin-bottom:  6px
```

No subtitle. No description. Strategy name only.

---

## 7. PLAYER ROW SPEC

Each player row within a strategy group card contains:

### Player Portrait

```
Size:     40px × 40px
Shape:    Rounded rectangle (border-radius: 6px)
Source:   MLB headshot CDN — existing pattern in strategies_ui.py
          https://img.mlbstatic.com/mlb-photos/image/upload/
          d_people:generic:headshot:67:current.png/
          w_96,q_auto:best/v1/people/{pid}/headshot/67/current
Fallback: Generic silhouette — same CDN fallback already in place
Fit:      object-fit: cover; object-position: top center
Style:    Cinematic sports portrait feel; no border by default;
          ELITE tier adds 1px amber border (border: 1px solid #f59e0b)
```

**Portrait click behavior:**
- Routes directly to FanDuel deployment URL for that player
- URL pattern: `https://sportsbook.fanduel.com/search?q={encoded_player_name}`
- Cursor: `pointer`
- No intermediate modal
- Visual feedback: brief opacity pulse on click (single cycle, 150ms — justified: deployment action acknowledged)

### Player Name

```
Font:   12px, weight 600
Color:  #f1f5f9 (high-contrast near-white)
Cursor: pointer
```

**Name click behavior:**
- Opens Player Card modal (existing `st.session_state["show_modal"]` pattern)
- Sets `st.session_state["show_modal"] = player_data_dict`
- Triggers `st.rerun()`
- Does NOT route to FD — name is intelligence layer only

This separation is **mandatory**:
- Name = intelligence layer (Player Card)
- Portrait = deployment layer (FanDuel)

### Compact Stat Strip

```
Font:     10px
Color:    #64748b (muted)
Margin:   2px 0 0 0
Content:  {MODEL%}  ·  {EV%}  ·  {TIER}
```

Example: `14.2%  ·  +8.4%  ·  A`

Model% and EV% use existing color convention:
- EV positive → `#4ade80`
- EV negative → `#f87171`
- Tier color → tier color map from `visual_primitive_standards.md`

### Player Row Layout

```
[Portrait 40px] [Name + Stat Strip]  [right-margin: FD arrow? NO]
```

No separate FD button per row. The portrait IS the FD deployment trigger. No duplicate routing surface.

---

## 8. PLAYER INTERACTION RULES

| Interaction Surface | Behavior | Target |
|--------------------|----------|--------|
| Player portrait (click) | FD deployment URL opens new tab | FanDuel search for player |
| Player name (click) | Player Card modal opens | `session_state["show_modal"]` → rerun |
| Strategy card header (click) | Expand/collapse player rows | In-place toggle, no route change |
| B-QTY dropdown change | Re-filter player count in all 3 cards | Sidebar-only state, no data reload |
| LIVE indicator | No click interaction | Status only |

### Prohibited Interactions

- No drag-to-reorder on strategy cards
- No swipe gesture (sidebar is not a carousel)
- No right-click context menus
- No hover tooltips on portraits (too small a surface, Streamlit limitations)
- No inline bet-sizing controls in this rail (belongs to Deployment Tray)

---

## 9. ESCALATION BEHAVIOR

Quick Strat participates in the existing threat escalation system passively.

### Glow Escalation

Strategy group cards adopt the glow tier of their **highest-confidence player**:
- Any ELITE (Tier S, confidence ≥ 70) player in the card → ELITE card glow
- Any HIGH (Tier A, confidence ≥ 55) → HIGH card glow
- Otherwise → no glow

### Ordering Escalation

When a new data refresh produces a player crossing into ELITE tier inside a strategy not currently shown, that strategy promotes to the #1 card position on next render. No animation — state change on rerun cycle only.

### Alert Escalation

Quick Strat does not fire its own alerts. It visually surfaces the outcome of alerts already fired by `_render_sidebar_shell_zones()` zones above it. The LIVE indicator pulse is the only signal Quick Strat fires independently.

---

## 10. TACTICAL DENSITY RULES

Quick Strat must remain operable at sidebar width. Streamlit sidebar max-width is typically 300–360px.

**Hard density limits:**
- Maximum 3 strategy group cards visible simultaneously
- Maximum 5 player rows per card (B-QTY ceiling = 5)
- Maximum 2 lines of text per player row
- No horizontal scrolling within the rail
- No nested tabs within Quick Strat
- No expanders within player rows (expand is card-level only)

**Soft density targets:**
- At B-QTY=3 (default), total rail height ≤ 420px for all 3 cards
- Card title + player rows = compact unit; no decorative whitespace between rows
- No empty-state placeholders longer than 1 line

**Density justification:**
The sidebar already contains 8 other zones above Quick Strat. Every pixel counts. Quick Strat earns its position by being actionable, not by being large.

---

## 11. MOTION AND ANIMATION DOCTRINE

Quick Strat inherits all rules from `spec_motion_governance_v1.md` and `spec_tactical_animation_hierarchy_v1.md`.

### Permitted Animations in Quick Strat

| Element | Animation | Duration | Justification |
|---------|-----------|----------|---------------|
| LIVE indicator | Single opacity pulse on data refresh | 400ms | Data state changed |
| Card reorder after refresh | Slide-in from left edge (first card only) | 250ms | Strategy ranking changed |
| Portrait click | Single opacity dip (0.7 → 1.0) | 150ms | Deployment action acknowledged |
| Strategy card expand/collapse | Height transition | 200ms ease-out | Content state changed |

### Forbidden Animations in Quick Strat

| Element | Forbidden Behavior |
|---------|-------------------|
| Strategy cards | Continuous ambient pulse |
| Icon backgrounds | Any motion at any time |
| Player portraits | Hover zoom or scale |
| Card borders | Breathing glow |
| LIVE indicator | Continuous loop animation |
| Strategy title | Typewriter or fade-in on every render |

**Rule:** Quick Strat fires exactly one type of animation per rerun cycle — the LIVE indicator pulse. All other motion is user-triggered (click, expand/collapse).

---

## 12. VISUAL HIERARCHY DOCTRINE

### Layer Stack (bottom to top)

```
Layer 0: Card background gradient
Layer 1: Strategy icon (faded background, z-index: 0)
Layer 2: Card border + glow
Layer 3: Strategy title text
Layer 4: Player portrait images
Layer 5: Player name + stat strip text
Layer 6: Interactive cursor regions (click zones)
```

Icon background MUST stay in Layer 1. It exists to identify strategy type subliminally. It never competes with player data.

### Color Temperature Rules

- Background: cool, very dark (`#04040a` → `#07070e`)
- Strategy icon tint: warm to mid per strategy type (see §6 icon map)
- Player name: near-white (`#f1f5f9`)
- Stat strip: muted slate (`#64748b`)
- EV positive values: emerald (`#4ade80`)
- EV negative values: red (`#f87171`)
- LIVE indicator: emerald (`#4ade80`)
- Tier S badge: gold (`#FFD700`)
- Tier A badge: emerald (`#4ade80`)
- Tier B badge: yellow (`#facc15`)
- Tier C badge: red (`#f87171`)

### Typography Hierarchy

```
STRATEGY TITLE:    10px, 700, all-caps, letter-spacing 1.4px, #94a3b8
PLAYER NAME:       12px, 600, title-case, #f1f5f9
STAT STRIP:        10px, 400, #64748b
QUICK STRAT TITLE: 11px, 700, all-caps, letter-spacing 1.6px, #e2e8f0
B-QTY LABEL:       10px, 500, all-caps, #94a3b8
```

---

## 13. RUNTIME-SENSITIVE WARNINGS

**Warning — Session State Ownership:**
`quick_strat_bqty` is owned by Quick Strat. Do not read or write this key from any other component. If the Deployment Tray, Shortlist, or any other sidebar zone needs batter count context, it must request it through a separate key.

**Warning — Data Source:**
Quick Strat computes its player pools from `data["all_players"]` and `data["ranked"]`, which are already materialized by the time `_render_sidebar_shell_zones()` runs. Quick Strat does NOT trigger data loads. If `data` is `None` (pre-load state), Quick Strat renders an empty-state variant — no spinners, no error panels.

**Warning — Cached Strategy Functions:**
`_cached_power_parlays`, `_cached_stars_aligned`, `_cached_multi_edge`, `_cached_pitcher_targets`, `_cached_park_parlays` are all `@st.cache_data` functions defined at module level in `strategies_ui.py`. Quick Strat must call these functions through the same import path, not redefine them. Redefining them inside Quick Strat's render function will invalidate their caches on every render cycle.

**Warning — Modal Trigger Pattern:**
Player name clicks must use the existing modal pattern: `st.session_state["show_modal"] = player_dict` followed by `st.rerun()`. Do not implement a separate modal system for Quick Strat. Dual modal systems will produce competing reruns.

**Warning — FD URL Pattern:**
Player portrait clicks must use the existing FD URL template from `strategies_ui.py`:
`https://sportsbook.fanduel.com/search?q={urllib.parse.quote(player_name)}`
Do not construct alternate URLs. Do not hard-code team or game routing.

**Warning — Sidebar Width:**
Streamlit sidebar renders at fixed width. Do not use `st.columns()` inside Quick Strat player rows — columns inside the sidebar collapse unpredictably below 300px. Use flex-styled HTML divs for layout within player rows.

**Warning — Route Isolation:**
Quick Strat renders inside `_render_sidebar_shell_zones()`. This function is always called regardless of active route (MAIN, JIG, ADVANCED_STRATEGIES, HITS, PERFORMANCE). Strategy computation must degrade gracefully when `data` is empty or `all_players` is an empty list.

---

## 14. FUTURE EXPANSION GOVERNANCE

### Permitted Future Expansions

| Feature | Condition |
|---------|-----------|
| Manual strategy pin | Operator can pin 1 strategy to always show first |
| Strategy history badge | Small "hit N times" counter on card if strategy_log data available |
| B-QTY memory | Persist B-QTY to user preferences file across sessions |
| Strategy card drill-down | Tapping card title routes to ADVANCED_STRATEGIES pre-filtered to that strategy type |
| 4th strategy card | If viewport height permits AND operator has explicitly enabled dense mode |

### Prohibited Future Expansions (without doctrine revision)

| Feature | Reason |
|---------|--------|
| Odds display in Quick Strat | Belongs to Deployment Panel, not intelligence rail |
| Bet sizing controls | Belongs to Deployment Tray |
| Auto-rotating carousel | Violates motion governance — timer-driven, not state-driven |
| More than 5 B-QTY | Sidebar density ceiling — beyond 5 rows the rail is no longer "quick" |
| Player search within Quick Strat | Out-of-scope for a deployment intelligence rail |
| Cross-game correlation display | Belongs to Correlation strategy view in ADVANCED_STRATEGIES |
| Persistent notification badges on strategy cards | Notification system not yet designed — do not invent |

### Governance Rule

Any expansion not listed in the Permitted table above requires a new doctrine document before implementation. This file (`spec_quick_strat_intelligence_system_v1.md`) is not the authority for those decisions.

---

## 15. IMPLEMENTATION PHASE GATE

This document is **Step 2/8** — Doctrine only.

Before implementation (Step 3/8):
- [ ] Visual mockup approved by operator (player row layout, icon background opacity, card density at default B-QTY=3)
- [ ] Strategy rotation scoring function defined (qualifying_count × signal_strength formula)
- [ ] Portrait click flow confirmed against existing FD slip tracking (does portrait-click also log to pick_tracker?)
- [ ] Empty-state variant spec'd (what renders when no strategies qualify?)
- [ ] Streamlit sidebar flex-HTML approach confirmed against current Streamlit version in requirements.txt

**Do not implement until all 5 gate conditions are cleared.**

---

*End of Doctrine v1*
