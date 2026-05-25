# Design Spec — Full Slate Intelligence Matrix

Status: Design-locked · 2026-05-25
Risk class for implementation: MEDIUM
Renders in: Dynamic Tactical Viewport (Main room sub-room: Full Slate)
Parent surface: Master Dashboard Shell
Child surfaces: Pitch Mix Analysis (modal), Batter Card (modal)

## Purpose

The Full Slate Intelligence Matrix is the dense battlefield-style scan surface for tonight's MLB slate. It displays every batter eligible for HR prop analysis, grouped by game, with tier ranking driven by model HR probability. Primary use: fast tactical scan of the full slate to identify deployment-ready targets.

## Doctrine identity

Per FULL_SLATE_UX_DOCTRINE.md:
- Dense battlefield-style matrix
- Player threat rows
- Matchup quality indicators
- Heatmapped metrics
- Escalation color hierarchy
- Compact tactical scan UX
- Restrained glow
- Premium operational realism
- Rapid Full Slate intelligence scanning doctrine

## Layout

### Game grouping
Players grouped by game. Each game gets a header card showing:
- Park name
- Game time (ET)
- Weather pill (temp, wind, conditions)
- Optional environment tier badge

Under each game header: rows for every starting batter in that game.

### Column structure (18 columns)

| Pos | Column | Source | Notes |
|---|---|---|---|
| 1 | Tier icon | Model tier | Bolt/target/arrow/radar/shield |
| 2 | Player | Roster | Name + team color chip |
| 3 | Matchup quality | Model | Pie quadrant viz |
| 4 | PA | Season totals | Sample-size context |
| 5 | AVG | Season | Batting average |
| 6 | SLG | Season | Slugging % |
| 7 | BABIP | Season | Batting Avg Balls In Play |
| 8 | GB% | Statcast | Ground ball rate |
| 9 | HH% | Statcast | Hard-hit rate (95+ mph) |
| 10 | LD% | Statcast | Line-drive rate |
| 11 | Barrel% | Statcast | Optimal EV+LA combo |
| 12 | EV | Statcast | Avg exit velocity |
| 13 | LA degrees | Statcast | Avg launch angle |
| 14 | Pull% | Statcast | Pull-side rate |
| 15 | Cent% | Statcast | Center-field rate |
| 16 | Opp HR/9 | Pitcher stat | Opposing pitcher HR/9 |
| 17 | xwOBA | Statcast | Expected weighted on-base |
| 18 | HR/PA | Season | HR per plate appearance |
| 19 | FanDuel | Market | Display-only · per doctrine |

Column 19 (FanDuel) is display-only market data per DOCTRINE_RANKING_RULE.md. It does not affect tier or rank.

### Drag-to-reorder

Operator can drag column headers (columns 4-18, the stat columns) to reorder them. Tier icon, Player, and Matchup Quality columns are fixed in their positions. FanDuel column always stays as the rightmost column.

Column order persists per operator (requires session_state — HIGH risk for implementation).

## Tier system

5 tiers, model HR probability driven:

| Tier | Icon | Color | HR prob range (approx) | Operator interpretation |
|---|---|---|---|---|
| Critical | Bolt | Red #e63946 | Top ~5% | Highest threat, deploy candidates |
| Dangerous | Target | Amber #f59e0b | Next ~10% | Strong threats, watchlist |
| Strong | Arrow up-right | Green #1da750 | Mid tier | Above-average opportunity |
| Active | Radar | Blue #1da3e8 | Lower mid | Active but not standout |
| Quiet | Shield | Gray #6a6a6a | Bottom | Low threat, informational |

Exact thresholds live in config.py and are the single source of truth. Specs here describe the visual mapping, not the threshold values.

## Color heatmap

Numeric cells use a 5-color heat ramp:

| Bucket | Color | Hex |
|---|---|---|
| Elite (top 10%) | Bright green | #1da750 |
| Strong (10-25%) | Dark green | #0f5c2c |
| Average (25-75%) | Neutral dark | #1a1a1a |
| Weak (75-90%) | Dark red | #7a1f24 |
| Danger (bottom 10%) | Red | #e63946 |

Percentile cutoffs per metric live in config.py.

## Row interactions

| Interaction | Effect |
|---|---|
| Click tier icon | Opens FanDuel HR prop for that player |
| Click player name | Opens Batter Card modal for that player |
| Click matchup quality pie | Opens Pitch Mix Analysis modal |
| Click any heatmapped cell | Shows tooltip with full tier breakdown for that metric |
| Hover cell | Shows tier definition and cutoffs |
| Hover column header | Shows full stat definition + tier cutoffs |
| Hover tier legend | Shows all 5 tiers with definitions |

## Tooltip coverage

Every interactive element has a tooltip:
- Stat column headers (definition + tier cutoffs)
- Every heatmap cell (current value + tier classification)
- Tier icon column (tier definition)
- Tier legend (full tier system)
- Player name (sample preview before opening card)
- Matchup quality pie (preview before opening modal)
- FanDuel button (opens HR prop in new tab)

## View modes

Two view toggles (button group at top of matrix):

- Game view (default) — grouped by game card, batters under each game
- Player view — flat ranked list across all games, sorted by tier

Game view supports the SCAN workflow (understand each game's threat profile). Player view supports the DEPLOY workflow (identify top N targets regardless of game).

## Filter integration

The matrix consumes filters from:
- MAIN Command Center (filter panel) — same filter set
- TCC overlay (when active)

Filters affect which rows display, not which columns or how they're ranked.

## Data integrity

- All metrics sourced from Statcast / MLB Stats API
- If data unavailable for a row, cell displays `--`
- If pitcher not confirmed yet, Opp HR/9 column shows `--`
- If lineup unconfirmed, batter still listed but flagged with lineup state pill
- Never fabricate tier when model probability missing — row hidden until data arrives
- No synthetic percentiles or invented thresholds

## MAIN/JIG separation

- Full Slate Matrix is a MAIN surface
- Tier ranking driven by model probability per DOCTRINE_RANKING_RULE.md
- JIG signals (HVY, arsenal scoring) do NOT appear in this matrix
- Pitch Mix Analysis modal (opens from this matrix) displays JIG arsenal signals but marks them display-only

## Performance budget

- Renders 50-300 player rows per slate
- Drag-reorder must not trigger pipeline rerun (UI-only operation)
- Filter changes trigger pipeline recompute (MEDIUM risk for implementation)
- Heatmap calculation runs once per pipeline result, cached client-side

## Implementation risks

- MEDIUM — Drag-to-reorder column headers (UI state, no closed surfaces)
- MEDIUM — Game-view vs player-view toggle (display-mode toggle)
- HIGH — Filter persistence per operator (session_state ownership)
- HIGH — Cross-surface routing (click row → open Batter Card modal)
- MEDIUM — Heatmap calculation (pure computation, no closed surfaces)

## Cross-references

- FULL_SLATE_UX_DOCTRINE.md — full slate doctrine
- DOCTRINE_RANKING_RULE.md — ranking source rule
- DESIGN_PITCH_MIX_ANALYSIS.md — child modal
- DESIGN_BATTER_CARD.md — child modal
- DESIGN_MAIN_COMMAND_CENTER.md — filter panel (sibling)
- config.py — tier thresholds (single source of truth)
- pipeline.py — data assembly entrypoint
