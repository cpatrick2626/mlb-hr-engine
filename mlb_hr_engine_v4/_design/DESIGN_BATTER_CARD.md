# Design Spec — Modular Batter Card

Status: Design-locked · 2026-05-25
Risk class for implementation: MEDIUM (HIGH if layout persistence added)
Renders as: Modal overlay (within Dynamic Tactical Viewport)
Opens from: Full Slate Matrix row → player name click
Sibling modal: Pitch Mix Analysis

## Purpose

The Batter Card is the operator's deep-dive view on a single batter for tonight's slate. Primary use: qualify a player from SCAN to DEPLOY by reviewing all material signals (model output, Statcast profile, splits, recent form, environment, and tonight's matchup).

## Customization scope (locked)

Drag-to-reorder modules only. No add/remove. No resize. All 12 modules always visible.

Trade-offs accepted with operator:
- Less flexible than full modular dashboard, but simpler and faster to implement
- Reset order button restores default arrangement
- No layout persistence in v1 (would require session_state — HIGH risk)
- Future enhancement could add persistence, opt-in module hiding

## Layout

### Always-fixed top — Identity strip
Cannot be moved. Shows:
- Jersey number + position
- Player name (uppercase, bold)
- Team handedness (Bats L/R)
- Opponent handedness (vs LHP/RHP)
- Current tier pill
- Team logo (initials, no photo per likeness rules)
- Team name + record
- FanDuel button (top-right corner of identity strip) — opens HR prop

Identity strip uses a subtle team-color gradient (LAD blue, etc.) with restrained glow accent.

### Always-fixed bottom — System status footer
Cannot be moved. Shows:
- System operational status
- Data sync indicator (Live / Stale / Gap)
- Injury watch indicator
- Park indicator (favorable/neutral/unfavorable)
- Model confidence bar (percentage with progress bar)

### Customizable middle grid — 12 modules

Drag-reorderable via the drag handle on each module header. Default order:

| Pos | Module | Default size | Side |
|---|---|---|---|
| 1 | HR Threat | 1x1 | MAIN |
| 2 | HR Projection | 1x1 | MAIN |
| 3 | Statcast Metrics (16-tile sub-grid) | 2x2 | MAIN |
| 4 | xSLG Splits | 1x1 | MAIN |
| 5 | Pull Power | 1x1 | MAIN |
| 6 | Pitch Type Destruction | 2x1 | JIG display |
| 7 | Barrel Quality | 1x1 | MAIN |
| 8 | Contact Quality | 1x1 | MAIN |
| 9 | Plate Discipline | 1x1 | MAIN |
| 10 | HR Environment (tonight) | 2x1 | MAIN |
| 11 | Power vs RHP/LHP (last 20 games) | 2x1 | MAIN |
| 12 | Up Next (opposing pitcher card) | 2x1 | MAIN |

Module sizes are fixed (no resize). Sizes reflect data density.

### Module details

HR Threat (1x1)
- Single big number (0-100 threat score)
- Tier pill below
- Percentile context

HR Projection (1x1)
- Today's projected HR% (with up/down trend indicator)
- Season pace
- 1-year HR projection

Statcast Metrics (2x2 with 16 sub-tiles)
Sub-grid showing 16 Statcast metrics with percentiles: Max EV, Avg EV, Hard Hit %, Barrel %, Sweet Spot %, Barrels (tonight), Max Velo, Avg Distance, Launch Angle, Optimal LA%, Pull Air%, Pull LA%, ISO, wOBA, Chase %, Zone Contact %

xSLG Splits (1x1)
- xSLG vs RHP (horizontal bar)
- xSLG vs LHP (horizontal bar)
- Percentile context

Pull Power (1x1)
- 3-cell spray: Pull % / Center % / Oppo %
- Heat color per cell (hot/warm/cool)
- Percentile per direction

Pitch Type Destruction (2x1) — JIG display badge
- Per-pitch row grid (4-Seam, Sinker, Slider, Change, Curve)
- Each row: xwOBA vs that pitch, dmg bar, percentile
- Header badge: "JIG display"
- Tooltip: "Display only · does NOT modify MAIN"

Barrel Quality (1x1)
- Perfect / Solid / Total barrel breakdown
- Horizontal bars

Contact Quality (1x1)
- Squared up / Mid / Poor breakdown
- Color-coded (green for squared up, red for poor)

Plate Discipline (1x1)
- Z-swing % · BB rate · Zone contact %
- Color-coded by tier

HR Environment tonight (2x1)
- Big environment score (0-10) with favorable tag
- 5 context tiles: Temp / Wind / Humidity / Air density / Elevation
- Each tile has value + tier label

Power vs RHP/LHP last 20 games (2x1)
- 4 metric tiles: wOBA / xwOBA / ISO / HR rate
- Trend chart (20 bars showing daily output)
- Splits chosen based on tonight's opposing pitcher handedness

Up Next opposing pitcher (2x1)
- Pitcher team logo (initials chip)
- Pitcher name + team + handedness + jersey number
- Three quick stats: HR/9, Barrels%, xwOBA allowed
- Pitcher HR-risk pill (High/Med/Low)

## Interactions

| Element | Action |
|---|---|
| Drag module header | Reorder modules in the grid |
| Reset Order button | Restores default module order |
| FanDuel button | Opens HR prop in new tab |
| Up Next pitcher card click | Opens Pitch Mix Analysis modal for this matchup |
| Close button | Returns to Full Slate Matrix |
| Hover Pitch Type Destruction module | Shows JIG display doctrine reminder |

## Data integrity

- All metrics sourced from Statcast / MLB Stats API
- Missing metrics show `--` not zeros
- Percentile context only shown when sample size sufficient
- Trend chart hidden if fewer than 5 games played in window
- Team logos use initials (LAD, BOS, etc.) — never AI-generated player photos
- Identity strip never displays unconfirmed lineup data (uses `--` if pending)

## MAIN/JIG separation

- 11 of 12 modules are MAIN-side (quantitative model output and Statcast data)
- 1 module (Pitch Type Destruction) is JIG display-only, badged explicitly
- Pitch Type Destruction data informs the operator but does NOT contribute to ranking or HR threat score per DOCTRINE_RANKING_RULE.md

## Tooltip coverage

- Every metric tile (definition + tier cutoffs)
- Every module header (description + drag hint)
- Reset Order button (action description)
- FanDuel button (opens external)
- JIG display badge (full doctrine reminder)
- Trend chart bars (per-game breakdown on hover)

## Implementation risks

- MEDIUM — Modal rendering (closed surface — modal architecture)
- MEDIUM — Drag-to-reorder modules (UI state only)
- MEDIUM — Module rendering (12 modules, each is a small component)
- HIGH — Modal-to-modal navigation (Up Next click → Pitch Mix modal)
- HIGH — Layout persistence per operator (session_state ownership) — DEFERRED to future spec

## Cross-references

- DESIGN_FULL_SLATE_MATRIX.md — parent surface
- DESIGN_PITCH_MIX_ANALYSIS.md — sibling modal (opens from Up Next module)
- DOCTRINE_RANKING_RULE.md — ranking source rule
- MASTER_TCC_DOCTRINE.md — MAIN/JIG separation
- pipeline.py — batter data assembly
- config.py — tier thresholds
