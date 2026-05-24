# Tactical Command Center & Batters Table — Architecture Doctrine v1
## MLB HR Engine v4 — Room 05: Tactical UI & Design System

**Document Status:** Planning & Architecture Only  
**Runtime Systems:** FROZEN (Codex ownership)  
**This document:** TCC + Batters Table doctrine, interaction hierarchy, escalation system, Codex boundaries  
**Date:** 2026-05-22  
**Phase:** 3A Step 01/10

---

## Table of Contents

1. [System Split — Official Separation Doctrine](#1-system-split)
2. [TCC Layout Governance](#2-tcc-layout-governance)
3. [TCC Visibility Doctrine](#3-tcc-visibility-doctrine)
4. [Batters Table Architecture](#4-batters-table-architecture)
5. [Player Interaction Rules](#5-player-interaction-rules)
6. [HR Threat Icon Doctrine](#6-hr-threat-icon-doctrine)
7. [Tactical Heatmap Doctrine](#7-tactical-heatmap-doctrine)
8. [Pitch Mix Analysis Doctrine](#8-pitch-mix-analysis-doctrine)
9. [Matchup Outlook Doctrine](#9-matchup-outlook-doctrine)
10. [Validation Checklist](#10-validation-checklist)
11. [Codex Implementation Boundaries](#11-codex-implementation-boundaries)
12. [UX Anti-Pattern List](#12-ux-anti-pattern-list)
13. [Runtime Contamination Risks](#13-runtime-contamination-risks)
14. [Mobile Degradation Expectations](#14-mobile-degradation-expectations)
15. [Final Tactical Hierarchy Summary](#15-final-tactical-hierarchy-summary)

---

## 1. System Split

### 1.1 Official System Identities

Two systems. Separate responsibilities. No overlap in ownership.

```
┌─────────────────────────────────────────────────────────────────────┐
│  TACTICAL COMMAND CENTER (TCC)                                      │
│  PURPOSE: CONTROL SYSTEM                                            │
│  Owns: thresholds, filters, presets, tactical modes, sorting,       │
│         visibility controls, operational state, environment,         │
│         section visibility, output configuration                    │
│  DOES NOT: display the intelligence grid                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  BATTERS TABLE                                                      │
│  PURPOSE: TACTICAL INTELLIGENCE DISPLAY SYSTEM                      │
│  Owns: filtered batter display, HR threat visualization,            │
│         matchup escalation, color-coded stat presentation,          │
│         matchup outlook, pitch mix analysis,                        │
│         tactical ranking visibility, player investigation entry     │
│  DOES NOT: own global filters                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

```
[pipeline.py] → picks data
      ↓
[TCC] — applies filter state → filtered_picks
      ↓
[Batters Table] — renders filtered_picks
      ↓
[Player Card] — opens on player-name click (investigation entry)
```

The TCC produces the filter state. The Batters Table consumes it. Neither crosses into the other's domain.

### 1.3 Hard Separation Rules

- TCC widgets write to `session_state` filter keys. Batters Table reads those keys. No exceptions.
- Batters Table never writes filter state. It is a pure consumer.
- TCC never renders player rows, stat cells, or HR threat icons.
- A visibility toggle in TCC that hides a TCC section does NOT alter filter logic for that section. The filter persists even if its section is hidden.

---

## 2. TCC Layout Governance

### 2.1 Section Ordering (Fixed)

The TCC renders sections in this order. Order is non-negotiable — it follows the operator's analytical progression from power → shape → matchup → environment → signals → output.

```
01  Batter Power & Contact
02  Launch & Contact Shape
03  Matchup & Splits
04  Pitcher Vulnerability
05  Environment
06  Advanced HR Signals
07  Momentum & Recency
08  Game Context
09  Output Control
```

Rationale: power/contact is the primary signal (barrel, HH, xSLG). Shape modifies that signal (LA, sweet spot, pull air). Matchup determines pitcher context. Environment modulates the combined signal. Advanced signals add precision. Momentum provides temporal dimension. Game context sets deployment framing. Output control is always last — it configures what the operator sees, not what the engine computes.

### 2.2 Section Grouping Doctrine

**Group A — Batter Intrinsic Quality** (sections 01–02)
- These define the batter's power-contact profile independent of context
- Adjusting these gates the talent pool

**Group B — Contextual Matchup Signals** (sections 03–05)
- These define the situational environment
- Adjusting these refines which talent/matchup combinations qualify

**Group C — Signal Precision** (sections 06–07)
- These add analytical depth for operators running deep reconnaissance
- Compact by default; expanded only on demand

**Group D — Operational Config** (sections 08–09)
- Game-level context and display configuration
- Always rendered last; never collapsed (they're control surfaces, not filter surfaces)

### 2.3 Spacing Rules

```
Section header:     12px top margin, 6px bottom margin
Control group:      8px internal padding, 6px between controls
Section separator:  1px at 12% opacity — structural, not decorative
Inter-section gap:  16px between distinct section blocks
Preset bar:         8px top/bottom padding, pinned to TCC top
```

### 2.4 Density Rules

- Maximum 4 controls per section in compact mode
- Maximum 8 controls per section in expanded mode
- No horizontal control pairs with labels longer than 10 characters each
- Slider labels: 8 characters maximum (use "Barrel%" not "Barrel Rate %")
- Number inputs preferred over sliders — sliders waste vertical space at TCC density

### 2.5 Interaction Hierarchy

```
Tier 1 (Preset Bar)        — one-tap tactical mode switch; highest operator priority
Tier 2 (Power/Contact)     — primary filter gate; second highest
Tier 3 (Matchup/Splits)    — contextual refine
Tier 4 (Environment)       — situational modifier
Tier 5 (Advanced Signals)  — precision analysis
Tier 6 (Output Control)    — display configuration; lowest
```

Operators arrive at Tier 1 first. TCC must be designed so that 80% of operational use requires nothing beyond Tiers 1–2.

### 2.6 Tactical Escalation Hierarchy (TCC-Level)

When an operator uses TCC controls that produce zero qualifying rows:

1. Table renders empty state with diagnostic: `"0 batters match current filters — [section name] threshold too high"`
2. TCC section that caused elimination is visually marked (amber left-border on that section)
3. No automatic threshold relaxation — operator controls all gates
4. Preset bar remains fully accessible (operator can quick-reset to Operational)

---

## 3. TCC Visibility Doctrine

### 3.1 Section Show/Hide Behavior

Each TCC section (except Preset Bar and Output Control) is individually collapsible.

**Collapse behavior:**
- Collapsed state shows section header + current active filter count: `"Power & Contact (3 active)"`
- The number reflects non-default filter values active in that section
- Zero active filters: `"Power & Contact"` (no count — not a distraction)
- Collapsed sections still apply their filters — visibility does not equal inactivity

**Hard Rule:** Collapsing a section NEVER clears or suspends its filter values.

### 3.2 Compact Mode

Compact mode: all collapsible sections rendered collapsed by default, preset bar visible.

Triggered by:
- Operator toggle in Output Control: "Compact TCC"
- Persists in `session_state["tcc_compact_mode"]` — Codex-owned key

In compact mode:
- Each section shows only its header + active filter count
- Expand on single click — expands that section only, not all sections
- Preset bar always expanded in compact mode (it's the primary interaction surface)

### 3.3 Expanded Mode

Expanded mode: all sections rendered open by default.

Used when:
- Operator is doing deep reconnaissance (needs to tune multiple sections simultaneously)
- No default — operator chooses via "Expand All" toggle in Output Control

### 3.4 Quick Tactical Presets

Presets live in the Preset Bar (always pinned, never collapsible).

Existing presets from `filter_controls.py` are preserved:

| Preset | Behavior | Color |
|---|---|---|
| Operational | No batter-profile floor; EV/Edge gates only | `#4ade80` |
| Selective | Barrel ≥ 5%, Hard Hit ≥ 35% | `#60a5fa` |
| Elite Only | Barrel ≥ 8%, HH ≥ 40%, EV ≥ 2%, Edge ≥ 1.5% | `#FFD700` |

Additional presets for Room 05 spec (Codex implementation pending):

| Preset | Barrel | HH | xSLG | Pull Air | Description |
|---|---|---|---|---|---|
| Power Rush | ≥ 10% | ≥ 42% | — | — | Elite power profile only |
| Shape + Power | ≥ 8% | ≥ 38% | ≥ 0.500 | ≥ 38% | Full contact shape gate |
| Matchup Edge | — | — | — | — | No batter gate; pitcher vulnerability focused |

### 3.5 Hidden-Active-Filter Warnings

When a TCC section is collapsed AND contains active (non-default) filter values:

- Section header renders with amber text: `"Power & Contact (3 active) ⚠"`
- Warning disappears when section is expanded or filters reset to default
- Warning does NOT pulse, flash, or animate — it is a static indicator

**Purpose:** Operator who applied filters in an earlier session should not lose track of why the table is narrower than expected.

### 3.6 Visibility Persistence Expectations

- Section collapse/expand state: persists in `session_state` within session
- Compact mode toggle: persists in `session_state` within session
- On full app refresh: TCC resets to default state (expanded, Operational preset)
- Preset selection: resets on refresh (picks always re-run from fresh pipeline)

---

## 4. Batters Table Architecture

### 4.1 Column Ordering

Columns render in this fixed order. No operator-controlled column reordering in v1.

```
Col  01  Player               — fixed left, sticky on scroll
Col  02  Matchup Outlook      — contextual grade; second column
Col  03  HR Threat            — escalation icon; third column
Col  04  Total HRs            — season count; baseline context
Col  05  ISO                  — isolated power; batter quality gate
Col  06  xSLG                 — expected slugging; contact quality
Col  07  Barrel %             — primary power signal
Col  08  Hard Hit %           — contact authority
Col  09  Pull Air %           — HR geometry signal
Col  10  HR Window %          — HR-to-fly-ball rate
Col  11  EV                   — exit velocity mean
Col  12  Launch Angle         — average LA; supplemental
Col  13  Sweet Spot %         — 8-32° contact rate
Col  14  HR/FB %              — ballpark-sensitive rate
Col  15  Contact Shape Score  — composite contact geometry
Col  16  Arsenal Matchup Score — pitch-mix intelligence grade
Col  17  Pitch Mix Analysis   — icon-based; rightmost content
```

### 4.2 Column Grouping (Visual)

Groups are separated by a 1px subtle column separator at 10% opacity.

```
Group A: Identity        — Player, Matchup Outlook, HR Threat
Group B: Power Core      — Total HRs, ISO, xSLG, Barrel%, Hard Hit%
Group C: Geometry        — Pull Air%, HR Window%, EV, Launch Angle, Sweet Spot%, HR/FB%
Group D: Composite       — Contact Shape Score, Arsenal Matchup Score
Group E: Pitch Analysis  — Pitch Mix Analysis
```

Group A columns are sticky (scroll with viewport — player identity always visible).

### 4.3 Column Width Constraints

| Column | Min Width | Max Width | Notes |
|---|---|---|---|
| Player | 140px | 180px | Name + team badge |
| Matchup Outlook | 100px | 120px | Grade pill only |
| HR Threat | 48px | 60px | Icon only |
| Total HRs | 48px | 56px | Integer |
| ISO | 52px | 60px | Decimal |
| xSLG | 60px | 70px | Decimal |
| Barrel % | 64px | 72px | Pct |
| Hard Hit % | 64px | 72px | Pct |
| Pull Air % | 64px | 72px | Pct |
| HR Window % | 80px | 90px | Pct |
| EV | 52px | 60px | Float |
| Launch Angle | 72px | 80px | Float + ° |
| Sweet Spot % | 72px | 80px | Pct |
| HR/FB % | 64px | 72px | Pct |
| Contact Shape Score | 80px | 90px | Float |
| Arsenal Matchup Score | 80px | 90px | Float |
| Pitch Mix Analysis | 120px | 150px | Icon strip |

### 4.4 Readability Hierarchy

**Primary read targets** (operator scans first):
- Player name, Matchup Outlook grade, HR Threat icon, Barrel %, EV

**Secondary read targets** (operator checks after primary):
- xSLG, Hard Hit %, Pull Air %, Contact Shape Score

**Tertiary read targets** (expand for precision):
- ISO, Total HRs, Launch Angle, Sweet Spot %, HR/FB %, Arsenal Matchup Score, Pitch Mix

Visual weight rules:
- Primary columns: full contrast (`#e8e8e8`), normal weight
- Secondary columns: 85% contrast, normal weight
- Tertiary columns: 70% contrast, reduced weight

### 4.5 Density Limits

Maximum visible rows before scroll: **12 rows** at standard desktop viewport (1440px wide).

Row height:
- Standard mode: 36px
- Compact mode: 28px

No infinite scroll. Table has fixed display limit of 40 rows maximum. If filtered picks exceed 40, show `"Showing top 40 of [N] — tighten TCC filters to reduce"` below table.

### 4.6 Hover Behavior

On row hover:
- Row background lifts to `rgba(255,255,255,0.04)` — subtle surface elevation
- Left border of row brightens by 20% opacity
- Player name gets underline cursor indicator (signals clickability)
- HR Threat icon gains 1px glow ring at escalation color (single-frame — not animated)
- Stat cells do NOT reveal additional content on hover at row level

On cell hover (stat cells only):
- Tooltip appears with: field name, player value, league average, percentile rank
- Tooltip placement: above cell, 4px offset
- Tooltip delay: 200ms (prevents accidental trigger on scroll)
- Tooltip style: dark surface `#1a1a1a`, 1px `#3a3a3a` border, 11px text

### 4.7 Tooltip Doctrine

Tooltips are supplemental precision — they enhance, never replace, the cell value.

**Tooltip anatomy:**
```
┌──────────────────────────────────┐
│  Barrel %                        │
│  Player: 11.2%                   │
│  League avg: 5.5%   Pct: 92nd   │
└──────────────────────────────────┘
```

Rules:
- Maximum 3 lines
- No tooltips on Player, Matchup Outlook, HR Threat, Pitch Mix columns (they have own interaction patterns)
- Tooltips render on desktop only — suppressed on mobile (not reliable on touch)
- No HTML in tooltip content — plain text only

### 4.8 Row Escalation Hierarchy

Rows are sorted by composite score (EV×0.4 + Edge×0.35 + Confidence×0.25 — existing ranker logic).

Row visual escalation based on HR Threat tier:
- Elite: left border `#FFD700` at 3px, row surface `rgba(255,215,0,0.04)`
- Dangerous: left border `#b84040` at 3px, row surface `rgba(184,64,64,0.04)`
- Active: left border `#4a7fa5` at 2px, no surface tint
- Elevated: left border `#c8a035` at 2px, no surface tint
- Monitor: no left border, no surface tint

---

## 5. Player Interaction Rules

### 5.1 Player Name Click Behavior

Single click on player name → opens Player Card (investigation modal).

Rules:
- Click target: player name text only (not the entire player cell)
- Visual affordance: player name renders as an underlined link in `#9bb8d3` (muted tactical blue)
- Underline visible only on hover (not permanently underlined — reduces visual noise)
- Cursor changes to pointer on hover over player name
- Click is the only interaction that opens the Player Card

### 5.2 Player Card Open Rules

- Player Card opens as a modal overlay over the Batters Table
- Batters Table visible behind at 30% opacity (preserves spatial context)
- Player Card width: max 560px, centered in viewport
- Player Card does NOT navigate away from the current view
- Only one Player Card open at a time — clicking another player name closes current and opens new

### 5.3 Hover Hierarchy

On row hover:
1. Row surface lifts (subtle background)
2. Player name underline appears
3. HR Threat icon glow ring appears
4. No other interactive affordances are revealed

Player Card is never opened or previewed on hover — click only.

### 5.4 Active Row State

When Player Card is open for a row:
- That row gets a persistent left border flash: 3px `#4a7fa5` solid (regardless of HR Threat tier)
- Row background: `rgba(74,127,165,0.08)` — distinct from hover state
- "Active" state clears when Player Card closes

### 5.5 Selected Row Behavior

No multi-select in v1. Single investigation focus only.

### 5.6 Remove Separate Player-Card Open Box

**Hard Rule:** No separate "Open Player Card" button, icon, or expander column in the Batters Table.

Player-name click is the single, unambiguous entry point to the Player Card.

Rationale: Two mechanisms for the same action (a click affordance AND a button) create interaction confusion and waste column width. Player name as the click target is intuitive, space-efficient, and consistent with modern data grid UX.

---

## 6. HR Threat Icon Doctrine

### 6.1 The Five Tiers

#### ELITE
*Maximum signal convergence — Barrel ≥ 12%, model prob ≥ 20%, favorable matchup confirmed*

**Icon:** Solid diamond shape — 12×12px. Sharp edges. No curves.  
**Color:** `#FFD700` (tactical gold) — fully saturated, not yellow  
**Glow:** Single 2px outer ring at `rgba(255,215,0,0.25)` — visible but restrained  
**Row surface:** `rgba(255,215,0,0.04)` — barely perceptible warm tint  
**Label (tooltip only):** `ELITE`  
**Psychology:** Gold diamond signals maximum conviction. Operator understands this row demands attention.

#### DANGEROUS
*High signal confidence — Barrel ≥ 10%, EV ≥ 2%, strong matchup context*

**Icon:** Solid upward triangle — 12px height, 10px base. Points up.  
**Color:** `#b84040` (tactical red — muted, not bright)  
**Glow:** Single 1.5px outer ring at `rgba(184,64,64,0.20)`  
**Row surface:** `rgba(184,64,64,0.04)`  
**Label (tooltip only):** `DANGEROUS`  
**Psychology:** Upward triangle reads as "ascending threat." Red conveys urgency without alarm.

#### ACTIVE
*Qualified play — passes all filters, EV positive, no extraordinary signals*

**Icon:** Solid circle — 8px diameter  
**Color:** `#4a7fa5` (steel blue)  
**Glow:** None  
**Row surface:** None  
**Label (tooltip only):** `ACTIVE`  
**Psychology:** Circle is neutral — a confirmed pick, not a warning, not a superlative.

#### ELEVATED
*Notable signals — Barrel ≥ 8% OR EV ≥ 15% OR notable matchup factor*

**Icon:** Outline circle (ring only) — 8px diameter, 1.5px stroke  
**Color:** `#c8a035` (tactical amber)  
**Glow:** None  
**Row surface:** None  
**Label (tooltip only):** `ELEVATED`  
**Psychology:** Outline (not filled) communicates "worth watching but not yet confirmed."

#### MONITOR
*Below primary qualification, marginal signals — worth tracking but not deployable*

**Icon:** Small dash/minus — 10px wide, 1.5px height  
**Color:** `#5a5a5a` (neutral gray, muted)  
**Glow:** None  
**Row surface:** None  
**Label (tooltip only):** `MONITOR`  
**Psychology:** Dash communicates neutrality. Renders as a non-event — the eye passes over it.

### 6.2 Icon Size and Alignment

- All icons: 16×16px bounding box, icon centered within
- Vertical alignment: middle of row
- No icon labels in the cell — tier communicated by shape + color alone
- Tooltip reveals tier name on hover (200ms delay)

### 6.3 Glow Rules

- Glow is a static property of Elite and Dangerous tiers only
- Glow does NOT pulse, animate, or change on hover
- On row hover: glow ring opacity increases by +0.10 (single-frame transition — not animated)
- No glow on Active, Elevated, Monitor — preserves visual hierarchy

### 6.4 Color Hierarchy

```
ELITE     #FFD700  — gold     (maximum urgency signal)
DANGEROUS #b84040  — red      (high urgency)
ACTIVE    #4a7fa5  — blue     (confirmed, neutral urgency)
ELEVATED  #c8a035  — amber    (watch signal)
MONITOR   #5a5a5a  — gray     (background presence only)
```

No color is reused across tiers. No tier uses the same hue family as another.

### 6.5 Escalation Psychology

The icon system communicates tier through shape + color simultaneously. Even in peripheral vision (color-impaired operator, low-contrast display), shape alone conveys the tier:

- Diamond = exceptional
- Triangle = alert  
- Filled circle = normal qualified
- Outline circle = watch
- Dash = background

Shape-first design ensures the system works without relying solely on color.

### 6.6 Row-Highlight Interaction

Row surface tint (Elite and Dangerous) extends full row width — not just the icon cell.

The tint is:
- Static (not animated)
- Applied only to Elite and Dangerous
- Does not intensify on hover (hover has its own separate lift)

### 6.7 Avoided Visual Patterns

**Never:**
- Emoji icons (🔥⚡💥)
- Sports-specific icons (baseball, bat shapes)
- Animated icons (pulsing, spinning, flashing)
- Gradient-filled icons
- Icons larger than 16px bounding box
- Neon colors (lime, hot pink, electric blue)
- Multiple icons stacked in one cell

---

## 7. Tactical Heatmap Doctrine

### 7.1 Purpose

Stat cells use background color scaling to encode value relative to thresholds. Operator identifies danger and opportunity through color before reading numbers.

### 7.2 Color Scale System

Three zones: Elite (high-signal green), Neutral (no color), Weak (suppression indication).

```
ELITE ZONE      — rgba(45,106,45,0.35)    dark green tint
STRONG ZONE     — rgba(45,106,45,0.18)    lighter green tint
NEUTRAL ZONE    — transparent              no tint
BELOW ZONE      — rgba(80,40,40,0.15)     subtle red tint
SUPPRESSION     — rgba(80,40,40,0.28)     deeper red tint
```

### 7.3 Elite Thresholds by Column

| Column | Elite (strong green) | Strong (light green) | Neutral | Below |
|---|---|---|---|---|
| Barrel % | ≥ 12% | 8–12% | 5–8% | < 5% |
| Hard Hit % | ≥ 45% | 40–45% | 35–40% | < 35% |
| xSLG | ≥ .550 | .480–.550 | .400–.480 | < .400 |
| ISO | ≥ .220 | .175–.220 | .130–.175 | < .130 |
| Pull Air % | ≥ 45% | 38–45% | 30–38% | < 30% |
| HR Window % | ≥ 18% | 12–18% | 8–12% | < 8% |
| EV | ≥ 93.0 | 90.0–93.0 | 87.0–90.0 | < 87.0 |
| Sweet Spot % | ≥ 38% | 33–38% | 27–33% | < 27% |
| HR/FB % | ≥ 20% | 14–20% | 8–14% | < 8% |
| Contact Shape Score | ≥ 1.20 | 1.05–1.20 | 0.90–1.05 | < 0.90 |
| Arsenal Matchup Score | ≥ 1.25 | 1.10–1.25 | 0.90–1.10 | < 0.90 |
| ISO | ≥ .220 | .175–.220 | .130–.175 | < .130 |
| Total HRs | ≥ 15 | 8–15 | 3–8 | < 3 |
| Launch Angle | 12°–22° | 8°–26° | 4°–30° | < 4° or > 32° |

Note on Launch Angle: heatmap is centered on optimal range (12°–22°), not monotonically increasing. Extreme angles (too low or too high) are suppression signals.

### 7.4 Neutral Threshold Handling

Neutral zone: no background color applied. Cell renders with transparent background.

Do NOT render a "neutral" color (gray, light blue) for neutral. Absence of color IS the neutral signal. Color absence reduces cognitive load — operator's eye is not drawn to unimportant cells.

### 7.5 Unavailable Data Handling

When a stat is unavailable (`--`, `None`, empty):
- Cell renders `--` in muted gray (`#5a5a5a`)
- No heatmap color applied
- No tooltip for unavailable cells
- Unavailable cells do not affect row escalation tier

### 7.6 Contrast Rules

Text value always renders with sufficient contrast against heatmap background:
- Elite zone (dark green): text at `#e8e8e8` (default)
- Below zone (dark red): text at `#e8e8e8` (default)
- Tints are subtle enough that default text remains readable without adjustment

No inverted text (dark text on colored backgrounds) — consistent text color throughout.

---

## 8. Pitch Mix Analysis Doctrine

### 8.1 Column Purpose

Pitch Mix Analysis is a compact icon-based representation of the HVY modifier matchup signal. It provides at-a-glance pitcher arsenal context without requiring the operator to open the Player Card.

**Source:** `hvy_modifier` from `clients/pitch_mix.py` — display-only signal, NOT wired into `model_prob`.

### 8.2 Icon Behavior

The Pitch Mix cell renders 3–5 pitch-type icons in a horizontal strip.

Icon design:
- Each pitch type: 14×14px icon, rounded rect background
- Icon colors encode matchup advantage/disadvantage vs this batter:
  - Green `rgba(45,106,45,0.7)`: favorable (batter tends to hit this pitch well)
  - Amber `rgba(200,160,53,0.6)`: neutral
  - Red `rgba(184,64,64,0.6)`: unfavorable (pitcher dominates with this pitch)
- Pitch type abbreviation inside icon: `FB`, `SL`, `CH`, `CB`, `CT` — 9px, white text

Pitch icons appear in order of the pitcher's usage frequency (highest-usage pitch leftmost).

### 8.3 Hover Behavior

On hover over the Pitch Mix cell (not individual icon — hover the cell):
- Tooltip appears with expanded pitch breakdown:

```
┌──────────────────────────────────────────────────┐
│  Pitch Mix — [Pitcher Name]                      │
│  FB  42%  ▓▓▓▓▓▓▓  Batter xSLG vs FB: .540 ↑   │
│  SL  28%  ▓▓▓▓      Batter xSLG vs SL: .320 ↓   │
│  CH  18%  ▓▓▓       Batter xSLG vs CH: .480 →   │
│  CB  12%  ▓▓         Batter HR/FB vs CB: 12% →   │
│                                                  │
│  HVY Score: 1.18  [FAVORABLE MATCHUP]            │
└──────────────────────────────────────────────────┘
```

- Tooltip max width: 280px
- Tooltip placement: above the cell, or below if near top of viewport
- Tooltip renders only on hover — never auto-visible

### 8.4 Tactical Interpretation Hierarchy

HVY modifier is supplemental intelligence — it annotates the primary `model_prob` signal, never replaces it.

Interpretation:
- HVY ≥ 1.25: favorable matchup (arsenal plays into batter strengths)
- HVY 1.05–1.25: slight advantage
- HVY 0.90–1.05: neutral
- HVY 0.75–0.90: slight disadvantage
- HVY < 0.75: unfavorable matchup (pitcher arsenal suppresses batter profile)

### 8.5 Interaction Expectations

- No click behavior on Pitch Mix cell in the Batters Table
- Full pitch mix detail available in Player Card (investigation depth)
- Pitch Mix Analysis column is not sortable (composite of multiple signals — sort is meaningless)

### 8.6 Compact Readability

In compact row mode (28px height):
- Icon strip reduced to 3 icons (top 3 by pitcher usage)
- Icons: 12×12px
- No label text within icon — color only

---

## 9. Matchup Outlook Doctrine

### 9.1 The Five Grades

Matchup Outlook is a single-grade contextual assessment combining: pitcher vulnerability, park factor, platoon split, and weather modifier.

#### ELITE MATCHUP
*All contextual factors favorable: hittable pitcher, positive park, platoon advantage, weather neutral or positive*

- **Pill color:** `#1a4a1a` background, `#4ade80` text (muted dark green on bright green text)
- **Label:** `ELITE`
- **Placement:** Pill, centered in cell
- **Typography:** 10px, all caps, weight 700
- **Glow:** None on pill — row left border communicates tier

#### STRONG MATCHUP
*Most factors favorable: pitcher hittable or park positive, platoon neutral or better*

- **Pill:** `#1a3a2a` background, `#86efac` text
- **Label:** `STRONG`

#### SOLID MATCHUP
*Mixed factors: one strong positive, others neutral*

- **Pill:** `#1a2a1a` background, `#6ee7b7` text
- **Label:** `SOLID`

#### DANGEROUS MATCHUP
*Ambiguous — strong batter profile but challenging context (elite suppressor pitcher OR unfavorable park)*

- **Pill:** `#2a1a0a` background, `#fbbf24` text
- **Label:** `DANGER`
- **Note:** "Dangerous" here means the pick is riskier — not that the batter is threatening

#### NEUTRAL MATCHUP
*No strong positive or negative context signals*

- **Pill:** `#1a1a1a` background, `#9a9a9a` text
- **Label:** `NEUTRAL`

### 9.2 Color System

```
ELITE    bg: #1a4a1a  text: #4ade80   — dark green surface, bright green label
STRONG   bg: #1a3a2a  text: #86efac   — medium green surface
SOLID    bg: #1a2a1a  text: #6ee7b7   — light green surface
DANGER   bg: #2a1a0a  text: #fbbf24   — amber surface (not red — warns, not alarms)
NEUTRAL  bg: #1a1a1a  text: #9a9a9a   — dark gray, muted
```

### 9.3 Placement

- Pill occupies full Matchup Outlook cell width
- Pill height: matches row height minus 8px padding (total vertical padding 4px top + 4px bottom)
- Centered horizontally and vertically within cell

### 9.4 Hierarchy

Matchup Outlook is a second-level signal — it refines the primary HR Threat tier.

Operator reads: HR Threat first (is this batter qualified and at what tier?), then Matchup Outlook (is the context supporting?).

A DANGEROUS HR Threat + ELITE Matchup = maximum deployment urgency.  
An ELITE HR Threat + DANGER Matchup = power with contextual risk — needs Player Card review.

### 9.5 Typography Scale

- Pill text: 10px, all caps, letter-spacing: 0.08em
- No icons inside the pill
- No glow on pill
- Pill border: 1px at 20% opacity of pill text color — subtle definition

### 9.6 Glow Intensity

No glow on Matchup Outlook pills. Glow is reserved for the HR Threat icon system exclusively. Two glow systems competing in the same row creates visual noise.

---

## 10. Validation Checklist

### 10.1 TCC Visibility

- [ ] Collapsing a section does not clear its filter values
- [ ] Active filter count renders correctly on collapsed section headers
- [ ] Hidden-active-filter warning appears when section collapsed + non-default values active
- [ ] Warning uses amber text — not a badge, not an icon
- [ ] Preset bar never collapses regardless of compact mode state
- [ ] Applying a preset updates all controlled `session_state` keys atomically (no partial-apply state)
- [ ] "Compact TCC" toggle persists within session

### 10.2 Hidden Filter Persistence

- [ ] Set Barrel % ≥ 8%, collapse Power & Contact section — table still filters to Barrel ≥ 8%
- [ ] Confirm active filter count on section header reads "(1 active)"
- [ ] Reset to Operational preset — filter clears, count disappears, table shows full universe

### 10.3 Column Visibility

- [ ] All 17 columns render in specified order
- [ ] Player column is sticky on horizontal scroll
- [ ] Column headers match column content alignment
- [ ] No column exceeds its max width spec
- [ ] Pitch Mix column renders icon strip correctly for all 5 pitch types
- [ ] Missing-data cells render `--` in muted gray

### 10.4 Row Escalation Visibility

- [ ] Elite rows: gold left border 3px, gold diamond icon, subtle gold surface tint
- [ ] Dangerous rows: red left border 3px, red triangle icon, subtle red surface tint
- [ ] Active rows: blue left border 2px, blue circle icon, no surface tint
- [ ] Elevated rows: amber left border 2px, amber outline circle, no surface tint
- [ ] Monitor rows: no left border, gray dash icon

### 10.5 Player Card Open Behavior

- [ ] Clicking player name opens Player Card modal
- [ ] Player Card opens without page navigation
- [ ] Batters Table visible at 30% opacity behind Player Card
- [ ] Row for active player gets persistent left border in `#4a7fa5`
- [ ] Closing Player Card removes active row state
- [ ] No separate "Open Player Card" button exists anywhere in the table
- [ ] No Player Card opens or previews on row hover

### 10.6 Tooltip Rendering

- [ ] Stat cell tooltips appear after 200ms hover delay
- [ ] Tooltips contain: field name, player value, league avg, percentile
- [ ] Tooltips max 3 lines
- [ ] No tooltips on Player, Matchup Outlook, HR Threat, Pitch Mix columns
- [ ] Pitch Mix cell hover renders expanded HVY breakdown tooltip
- [ ] Tooltips do not appear on mobile (touch events)

### 10.7 Hover Activation

- [ ] Row hover: surface lifts (rgba 0.04), player underline appears, HR Threat glow ring brightens
- [ ] No layout shift on hover
- [ ] Hover does not trigger data fetches
- [ ] Hover visual response < 16ms
- [ ] Stat cell hover shows tooltip (200ms delay)

### 10.8 Table Density

- [ ] Standard row height: 36px
- [ ] Compact row height: 28px (when compact mode enabled)
- [ ] Maximum 12 rows visible without scroll at 1440px viewport
- [ ] Table footer shows row count: `"Showing N of M batters"`
- [ ] If N > 40, shows `"Showing top 40 of M — tighten TCC filters to reduce"`

### 10.9 Mobile Degradation

- [ ] On viewport ≤ 768px: columns A–C (Identity group) remain visible, others scroll
- [ ] On viewport ≤ 480px: Player, HR Threat, Matchup Outlook only (minimal view)
- [ ] Tooltips suppressed on mobile
- [ ] Pitch Mix column suppressed on ≤ 480px (replaced by HVY score text)
- [ ] TCC renders as a collapsible drawer on mobile (not persistent sidebar)

---

## 11. Codex Implementation Boundaries

### 11.1 What Codex MAY Modify

- Streamlit widget implementations of TCC sections (number inputs, selectboxes, sliders)
- Batters Table HTML rendering (pandas `to_html()` or custom HTML via `st.markdown`)
- CSS styling for row escalation tiers, heatmap cells, icon rendering
- Player Card modal implementation (via `st.dialog` or HTML overlay)
- Column ordering and column width CSS
- Hover behavior via CSS-only (`:hover` pseudo-class where applicable)
- Tooltip rendering via HTML `title` attribute or custom JS component
- Pitch Mix icon strip rendering (HTML + CSS within markdown)
- Matchup Outlook pill rendering (HTML within cell)
- HR Threat icon rendering (HTML character + CSS)
- Session state keys for TCC compact mode, section collapse state, active player

### 11.2 What Codex MAY NOT Modify

**Runtime-sensitive — do not touch:**
- `pipeline.py` — data pipeline; no UI dependencies
- `engine/probability.py` — model logic
- `engine/calibration.py` — calibration system
- `engine/filters.py` — 7-rule filter logic
- `output/ranker.py` — composite score calculation
- `filter_controls.py` — preset values (may ADD presets; may NOT remove existing)
- Any `session_state` key not explicitly scoped to TCC display state
- MAIN/JIG routing logic in `app.py`
- `navigation_continuity.py`
- `investigation_state.py` — investigation state ownership

### 11.3 Runtime-Sensitive Zones

```
ZONE 1: session_state key namespace
  ├─ Codex-owned TCC keys: tcc_compact_mode, tcc_section_[name]_collapsed
  ├─ Codex-owned table keys: table_active_player, table_active_player_row
  └─ PROTECTED keys: min_ev_pct, min_edge_pct, filter_* (owned by existing filter_controls.py)

ZONE 2: pipeline.py output schema
  └─ Batters Table reads these fields — any schema change breaks table rendering:
     model_prob, ev_pct, edge_pct, barrel_pct, hard_hit_pct, xslg, iso,
     pull_air_pct, hr_window_pct, exit_velo, launch_angle, sweet_spot_pct,
     hr_fb_pct, contact_shape_score, arsenal_matchup_score, hvy_modifier,
     matchup_grade, rank, score, confidence

ZONE 3: MAIN/JIG identity boundaries
  └─ TCC filter state must scope to MAIN engine only (not bleed into JIG session state)
  └─ JIG has its own filter_controls.py preset system — do not merge

ZONE 4: hydration and cache ownership
  └─ Batters Table renders from pre-computed data — no live API calls within table render
  └─ Table must not call pipeline.py directly — reads from session_state picks cache
```

### 11.4 Protected Architecture Boundaries

**NEVER cross these lines:**
1. Batters Table writes a filter value → violates TCC ownership
2. TCC renders a player row or stat cell → violates Batters Table ownership
3. Player Card opens on hover → violates click-only interaction doctrine
4. Visibility toggle alters formula or filter logic → violates visibility doctrine hard rule
5. Column reordering by operator in v1 → not in scope, creates state management complexity
6. Heatmap colors used outside of stat cells (e.g., on pill backgrounds or icon colors) → color system collision

---

## 12. UX Anti-Pattern List

### 12.1 Visual Anti-Patterns

| Anti-Pattern | Why Harmful |
|---|---|
| Neon glow on HR Threat icons | Cyberpunk aesthetic; destroys operational credibility |
| Gradient-filled escalation pills | Sportsbook aesthetic; implies decoration not signal |
| Emoji tier indicators (🔥⚡💥) | Fantasy sports register; incompatible with tactical doctrine |
| Looping animations on any icon | Visual noise; undermines trust in a calm system |
| Team color coding as primary escalation signal | Team colors carry no tactical meaning |
| HR Threat icons > 16px | Oversized; competes with stat value readability |
| More than 3 accent colors in any single row | Visual saturation; defeats hierarchy |
| Neon red (`#ff0000`) for Dangerous tier | Too alarming; tactical red (`#b84040`) correct |
| White backgrounds on dark UI | Shatters immersion; eye stress |
| Full-page modals for Player Card | Loses spatial context; use overlay |

### 12.2 Interaction Anti-Patterns

| Anti-Pattern | Why Harmful |
|---|---|
| Hover opens Player Card | Accidental trigger; player card should require deliberate intent |
| Separate "open player card" button | Redundant with player name click; wastes column width |
| Auto-sort on any TCC filter change | Disorienting during operator analysis |
| Filter changes trigger page scroll | Position loss; operator loses scan context |
| Table refresh with full re-render on filter | Visual disruption; use in-place filter |
| Tooltip opens immediately (0ms delay) | Triggers on scroll; use 200ms minimum |
| Column reordering in v1 | State management complexity; not operationally necessary |
| Multi-select rows | No operational use case in v1 |
| Double-click required for any action | Inconsistent with single-click doctrine |

### 12.3 Information Architecture Anti-Patterns

| Anti-Pattern | Why Harmful |
|---|---|
| TCC showing ranked player rows | Violates system split — TCC is control, not display |
| Batters Table showing a filter control | Violates system split — table is display, not control |
| HVY modifier wired into model_prob | Existing doctrine violation (already enforced) |
| League average shown in heatmap cell | Tooltip handles this — keep cell value clean |
| Matchup Outlook label changed at operator discretion | Static grade system; no operator-configured grade labels |
| Zero-state renders empty without diagnostic | Operator needs to know WHY the table is empty |
| "Showing top 12 of 12" when total is 12 | Unnecessary — only show "top 40 of N" when N > 40 |

### 12.4 Mobile Anti-Patterns

| Anti-Pattern | Why Harmful |
|---|---|
| Full 17-column table on mobile | Requires horizontal scroll that hides identity columns |
| Tooltips on touch | Touch hover unreliable across devices |
| TCC persistent sidebar on mobile | Consumes 40% viewport; incompatible with one-hand operation |
| Pitch Mix full icon strip on ≤ 480px | Too small to read at 12px icon size |

---

## 13. Runtime Contamination Risks

### 13.1 Session State Pollution

**Risk:** TCC writes a filter key that overlaps with an existing JIG or pipeline session_state key.  
**Mitigation:** All new TCC-specific display keys use prefix `tcc_` (e.g., `tcc_compact_mode`). All Batters Table interaction keys use prefix `table_` (e.g., `table_active_player`).  
**Protected:** Keys prefixed `tac_`, `jig_tac_`, `min_`, `filter_` are existing — do not repurpose.

### 13.2 Pipeline Dependency Contamination

**Risk:** Batters Table render logic calls a pipeline function directly instead of reading from cached session_state.  
**Mitigation:** Table renderer accepts only a `pd.DataFrame` argument (pre-filtered picks). No pipeline imports in table rendering code.

### 13.3 Filter Logic Contamination

**Risk:** Visibility toggle accidentally modifies a filter value (e.g., collapse section also sets min_barrel to 0).  
**Mitigation:** Section collapse is a display-only state change. No session_state filter key is written during collapse. Test: collapse Power & Contact, verify `tac_min_barrel` is unchanged.

### 13.4 Heatmap Color Collision

**Risk:** Heatmap tint colors bleed into icon or pill rendering when DOM structure is nested (parent div color affects child).  
**Mitigation:** Row-level heatmap tints applied as `background-color` on `<tr>`. Cell-level heatmap applied as `background-color` on individual `<td>`. Never apply heatmap tint to `<tbody>` — use row scope only.

### 13.5 Player Card State Leak

**Risk:** Opening a Player Card sets `session_state` values that affect filter or ranking on table close.  
**Mitigation:** Player Card is read-only. It reads pick data; it does NOT write to any filter, sort, or ranking key. `table_active_player` key is the only write from Player Card interaction.

### 13.6 MAIN/JIG Boundary Contamination

**Risk:** TCC filter state (written for MAIN engine) inadvertently applies to JIG engine picks on tab switch.  
**Mitigation:** MAIN TCC keys prefixed `tac_`. JIG TCC keys prefixed `jig_tac_`. Never read MAIN keys in JIG rendering path. Codex must verify tab-switch does not bleed filter state.

---

## 14. Mobile Degradation Expectations

### 14.1 Viewport Tiers

```
Desktop (≥1200px): Full 17-column table; full TCC sidebar; all tooltips
Tablet (768–1199px): 12-column table (Group D+E collapsed); TCC as drawer
Mobile (480–767px): 8-column table (Groups A+B only); TCC as full-screen drawer
Minimal (≤479px): 4-column table (Player, HR Threat, Matchup Outlook, Barrel%); TCC hidden
```

### 14.2 Column Priority at Mobile

Columns that survive at each breakpoint (ordered by priority):

**768px breakpoint (tablet):** Player, HR Threat, Matchup Outlook, Barrel %, Hard Hit %, xSLG, EV, HR Window %

**480px breakpoint (mobile):** Player, HR Threat, Matchup Outlook, Barrel %, Hard Hit %, xSLG, EV, HR Window %

**Removed from ≤768px:** Launch Angle, Sweet Spot %, HR/FB %, Contact Shape Score, Arsenal Matchup Score, Pitch Mix Analysis, Total HRs, ISO

**Removed from ≤479px:** Hard Hit %, xSLG, EV, HR Window % — minimum readable set only

### 14.3 TCC Behavior on Mobile

- TCC renders as a drawer (slides in from left on hamburger icon tap)
- Drawer covers 85% viewport width
- Preset bar visible at top of drawer (first item operator sees)
- Each section collapsible within the drawer
- Drawer dismisses by tapping outside or drawer close button
- TCC does NOT auto-dismiss when operator applies a filter — operator controls dismissal

### 14.4 Row Interaction on Mobile

- Player name tap opens Player Card (no hover state on touch)
- Player Card opens full-screen on ≤ 480px (not overlay — mobile viewport too narrow)
- Row tap-to-expand: not implemented in v1 (no expandable rows — flat table)
- Tooltips: not implemented on mobile

### 14.5 What Never Degrades

- Escalation tier color (left border on rows — scales with row height)
- HR Threat icon shape and color (16px bounding box maintained at all sizes)
- Matchup Outlook pill (scales with column width)
- Sort order (always composite score — never changed by mobile layout)

---

## 15. Final Tactical Hierarchy Summary

### 15.1 System Authority

```
PIPELINE (Codex owned)
  └─ Produces picks data (DataFrame)
       └─ TCC (Claude doctrine → Codex implementation)
            ├─ Consumes picks data
            ├─ Applies filter state to produce filtered_picks
            └─ Renders filter controls (does NOT render player rows)
                 └─ Batters Table (Claude doctrine → Codex implementation)
                      ├─ Consumes filtered_picks
                      ├─ Renders player rows with escalation tiers
                      ├─ Renders heatmap, icons, pills
                      └─ Player name click → Player Card
                               └─ Player Card (Codex owned, read-only)
                                    └─ Investigation depth display
```

### 15.2 Interaction Authority

```
OPERATOR ACTION HIERARCHY

Tier 1: Preset selection (TCC)         — broadest impact; instant results
Tier 2: Section filter adjustment (TCC) — targeted gate changes
Tier 3: Table scan + row identification  — reconnaissance
Tier 4: Player Card open               — investigation
Tier 5: (External) Deployment decision  — outside this doc scope
```

### 15.3 Signal Authority

```
SIGNAL HIERARCHY (Batters Table)

Primary:    HR Threat icon       — tier identity
Secondary:  Matchup Outlook pill — contextual grade
Tertiary:   Heatmap cells        — individual stat quality
Supplemental: Pitch Mix strip    — arsenal context (HVY only)
```

### 15.4 Escalation Authority

```
HR THREAT TIER ← pipeline.py score + barrel + matchup
MATCHUP OUTLOOK ← pitcher_factor + park_factor + platoon + weather
HEATMAP CELLS   ← individual stat vs league baseline thresholds
PITCH MIX       ← hvy_modifier (display-only, not in model_prob)
```

No UX element modifies escalation logic. Escalation is computed by the engine. UX displays it.

### 15.5 Visual Weight Hierarchy

```
WEIGHT 1 (max): Row surface tint + left border         (Elite, Dangerous only)
WEIGHT 2:       HR Threat icon shape + color           (all tiers)
WEIGHT 3:       Matchup Outlook pill color + label     (all grades)
WEIGHT 4:       Heatmap cell tint (green/red)          (Elite, Below only)
WEIGHT 5 (min): Typography contrast dimming            (secondary/tertiary columns)
```

No element at Weight N should visually overpower elements at Weight N-1. Hierarchy is enforced through opacity, saturation, and size — not through additional animation or motion.

### 15.6 Doctrine Conflict Resolution

If a future implementation decision creates apparent conflict between two doctrine rules:

1. System split (§1.3) takes priority over all other rules
2. Visibility-never-alters-logic (§3.1) takes priority over layout convenience
3. Click-only Player Card (§5.1) takes priority over any hover interaction desire
4. Runtime contamination risk (§13) takes priority over visual enhancement
5. Operator cognitive load reduction takes priority over visual richness

---

## Appendix A: Token Dictionary for Codex

All session_state keys scoped to this doctrine:

```python
# TCC Display State (new — safe to create)
"tcc_compact_mode"              # bool — TCC compact mode active
"tcc_section_power_collapsed"   # bool — Power & Contact section collapsed
"tcc_section_shape_collapsed"   # bool — Launch & Contact Shape collapsed
"tcc_section_matchup_collapsed" # bool — Matchup & Splits collapsed
"tcc_section_pitcher_collapsed" # bool — Pitcher Vulnerability collapsed
"tcc_section_env_collapsed"     # bool — Environment collapsed
"tcc_section_signals_collapsed" # bool — Advanced HR Signals collapsed
"tcc_section_momentum_collapsed"# bool — Momentum & Recency collapsed
"tcc_section_context_collapsed" # bool — Game Context collapsed

# Batters Table Interaction State (new — safe to create)
"table_active_player"           # str | None — player name with open Player Card
"table_active_player_row"       # int | None — row index of active player

# EXISTING — do not modify, do not repurpose
"tac_min_barrel"
"tac_min_hh"
"tac_min_xslg"
"tac_min_iso"
"tac_min_pull_air"
"tac_min_hr_window"
"tac_min_ev"
"tac_min_edge"
"tac_min_conf"
"tac_min_model_prob"
```

---

## Appendix B: HR Threat Classification Logic (Conceptual — Display Only)

```python
# Conceptual only — not to be implemented without Codex coordination
# Maps existing pipeline output fields to HR Threat display tier

def classify_hr_threat(batter: dict) -> str:
    barrel = batter.get("barrel_pct", 0.0)
    model  = batter.get("model_prob", 0.0) * 100
    ev_pct = batter.get("ev_pct", 0.0)

    if barrel >= 12.0 and model >= 20.0:
        return "Elite"
    if barrel >= 10.0 and ev_pct >= 2.0:
        return "Dangerous"
    if batter.get("qualifies", False) and ev_pct >= 0:
        return "Active"
    if barrel >= 8.0 or model >= 15.0:
        return "Elevated"
    return "Monitor"
```

Classification reads from pipeline output only. No new signals. No model changes.

---

*Planning document only. No runtime systems modified. No commits made.*  
*Codex ownership of runtime stabilization fully preserved.*  
*Next: Room 04 — Full Slate Command System.*
