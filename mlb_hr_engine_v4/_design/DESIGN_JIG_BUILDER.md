# Design Spec — JIG Builder All-In-One

Status: Design-locked · 2026-05-25
Risk class for implementation: MEDIUM (HIGH for JIG grade computation and preset persistence)
Renders in: Dynamic Tactical Viewport (JIG room sub-room: JIG Builder)
Sibling sub-room: JIG WAY (JIG's filter command panel — not yet designed)
JIG identity: Amber/orange accent (distinct from MAIN red)

## Purpose

JIG Builder All-In-One is the integrated tactical surface that combines filter command + target table on a single page. Primary use: rapid MATCHUP to CONFIRM to EXPLOIT workflow without switching surfaces.

## Doctrine identity

- Integrated all-in-one JIG Builder interface
- Combines tactical filter command + battlefield intelligence matrix
- Aggressive HR exploitation workflow
- Compact dense operational layout
- Restrained glow HUD styling
- Modular tactical panels
- Live target intelligence table
- MATCHUP to CONFIRM to EXPLOIT doctrine

## JIG vs MAIN identity

Per architectural invariant: MAIN and JIG are separate intelligence layers.

| Aspect | MAIN | JIG |
|---|---|---|
| Identity color | Red #e63946 | Amber #f59e0b |
| Workflow | SCAN to QUALIFY to DEPLOY | MATCHUP to CONFIRM to EXPLOIT |
| Ranking driver | Model HR probability | Model probability + JIG tactical signals |
| HVY pitch-mix signal | Not included | Display + JIG-side scoring |
| Filter panel | MAIN Command Center | JIG WAY |
| Integrated surface | None | JIG Builder (this spec) |

The two layers must not be merged. JIG Builder is a JIG-side surface that may reference MAIN model probability but does not modify it.

## Layout — Two zones in one page

### Zone 1 — Matchup · Filter Command (top)

9 filter sections in auto-fit grid, similar to MAIN Command Center but JIG-flavored.

Differences from MAIN Command Center:
- Default filter values pre-populated with JIG-tactical thresholds (e.g. ISO 0.200, Barrel% 8.0)
- Color identity: amber accent instead of green
- Same drag-reorder behavior (section + filter level)
- Same tooltip coverage

JIG-side section structure:

| Num | Section | Filters |
|---|---|---|
| 1 | Batter Power & Contact | ISO, xSLG, Barrel%, Hard Hit%, Avg EV, HR/FB% |
| 2 | Launch & Contact Shape | Pull Air%, Launch Angle, HR Window%, Sweet Spot%, Fly Ball% |
| 3 | Matchup & Splits | vs RHP ISO, vs LHP ISO, Pitch Type Damage%, Min Matchup Modifier%, Min wRC+ |
| 4 | Pitcher Vulnerability | Total HR Allowed, HR/9, Barrel% Allowed, Hard Hit% Allowed, Fly Ball% Allowed, Pull Damage% |
| 5 | Environment | Park HR Factor, Wind, Wind Direction, Temperature, Humidity, Air Density |
| 6 | Advanced HR Signals | Contact Shape Score, Arsenal Matchup Score, Opposite Field Weakness%, Lifted Hard Hit%, EV Trend |
| 7 | Game Context | Exclude Started Games, Include Live Games, No Time Gate, Confirmed Lineups Only, Pre-Lineup Pool Toggle |
| 8 | Output Control | Min Projected HR%, Min Confidence%, Max Players |
| 9 | Sort & Order | Sort By, Sort Direction |

### Zone 2 — Confirm · Player Target Intelligence (bottom)

Player target table with ~292 player rows. Each row shows:

| Column | Notes |
|---|---|
| Rank | Tactical rank (model + JIG tactical) |
| Player | Name + team + position |
| Matchup Quality | 4-quadrant pie viz |
| PA | Plate appearances |
| AVG | Batting average |
| SLG | Slugging |
| BABIP | Batting Avg Balls In Play |
| GB% | Ground ball rate |
| HH% | Hard-hit rate |
| LD% | Line-drive rate |
| EV | Exit velocity |
| LA | Launch angle |
| Cent% | Center-field rate |
| Opp HR/9 | Pitcher HR/9 |
| xwOBA | Expected wOBA |
| HR/PA | HR per plate appearance |
| PROJ % | Projected HR % |
| CONF % | Model confidence |
| GRADE | JIG tactical grade (A+, A, A-, B, C) |

### Workflow zone labels

Explicit doctrine banner between Zone 1 and Zone 2:

"JIG Workflow: 1 MATCHUP · filter command → 2 CONFIRM · player target intel → 3 EXPLOIT · click to deploy"

Each zone has its label at the top:
- Zone 1: 1 MATCHUP · filter command
- Zone 2: 2 CONFIRM · player target intel

EXPLOIT is implicit in row interactions (click matchup pie → Pitch Mix Analysis, click name → Batter Card, click rank → FanDuel deploy).

## Target table interactions

| Element | Action |
|---|---|
| Drag column header | Reorder column in target table |
| Click matchup quality pie | Opens Pitch Mix Analysis modal |
| Click player name | Opens Batter Card modal |
| Click rank number | Opens FanDuel HR prop for that player |
| Hover any heatmap cell | Tier breakdown tooltip |
| Hover GRADE pill | JIG grade explanation |

## Heatmap on numeric cells

Same 5-color heat ramp as Full Slate Matrix:
- Elite (top 10%) — bright green #1da750
- Strong (10-25%) — dark green #0f5c2c
- Average (25-75%) — neutral dark #1a1a1a
- Weak (75-90%) — dark red #7a1f24
- Danger (bottom 10%) — red #e63946

Percentile cutoffs per metric live in config.py.

## JIG GRADE column

Final column shows JIG tactical grade derived from:
- Model HR probability (MAIN signal, weighted in)
- JIG arsenal exploit signal
- HVY pitch-mix signal (JIG side, doctrine-compliant)
- Recency / momentum factors
- Environment + matchup composite

JIG grade computation is HIGH risk for implementation because it requires a JIG scoring formula that must NOT blend into MAIN model probability. The formula lives in JIG-domain code; output is JIG-domain only.

Grade scale:
- A+ — Critical tactical opportunity
- A — Strong tactical opportunity
- A- — Solid tactical opportunity
- B — Marginal tactical opportunity
- C — Below tactical threshold

## Doctrine compliance — explicit notes

- MAIN/JIG separation: JIG Builder is a JIG surface; MAIN model probability is referenced but never modified
- JIG signals (Contact Shape, Arsenal Matchup, HVY) are JIG-domain and labeled
- Filter scope feeds JIG pipeline, not MAIN pipeline (separate pipelines per doctrine)
- JIG GRADE column is JIG-domain output; does not appear on MAIN surfaces
- Market data (FanDuel odds) is display-only, not in JIG GRADE calculation per DOCTRINE_RANKING_RULE.md

## Tooltip coverage

Same comprehensive coverage as MAIN Command Center for the filter zone, plus:
- Every target table column header (definition + tier cutoffs)
- Every heatmap cell (current value + tier breakdown)
- Every JIG GRADE pill (grade definition + composite breakdown)
- Workflow banner (MATCHUP to CONFIRM to EXPLOIT doctrine)
- Zone labels (doctrine references)
- Stat key/legend at top of target table

## Data integrity

- All stats sourced from Statcast / MLB Stats API
- Missing data shows `--` not zeros or invented values
- JIG GRADE only assigned when sufficient sample size per config.py
- No fabricated tier when model probability missing — row hidden
- Pitch Type damage data only shown when pitcher confirmed
- Pie quadrants only populated when all 4 matchup factors have data

## Implementation risks

- MEDIUM — Filter command grid (shared logic with MAIN Command Center)
- MEDIUM — Target table rendering (shared logic with Full Slate Matrix)
- MEDIUM — Workflow zone labels (static UI)
- HIGH — JIG GRADE computation (must not blend with MAIN model probability)
- MEDIUM — Section + filter + column drag-reorder
- HIGH — Preset persistence (session_state ownership)
- MEDIUM — Cross-surface routing (Pitch Mix + Batter Card modal navigation)
- HIGH — Separate JIG pipeline (must coexist with MAIN pipeline without contamination)

## Cross-references

- MASTER_TCC_DOCTRINE.md — MAIN/JIG separation rules
- DOCTRINE_RANKING_RULE.md — ranking source rule
- DESIGN_FULL_SLATE_MATRIX.md — MAIN target table sibling
- DESIGN_MAIN_COMMAND_CENTER.md — filter panel reference (mirror structure)
- DESIGN_PITCH_MIX_ANALYSIS.md — child modal
- DESIGN_BATTER_CARD.md — child modal
- config.py — single source of truth for thresholds
- pipeline.py — data assembly (JIG pipeline subroutines)
