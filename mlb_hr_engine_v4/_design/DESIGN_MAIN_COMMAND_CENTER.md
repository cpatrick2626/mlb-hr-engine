# Design Spec — MAIN Command Center

Status: Design-locked · 2026-05-25
Risk class for implementation: MEDIUM (HIGH for preset persistence)
Renders in: Dynamic Tactical Viewport (Main room sub-room: Command Center)
Also serves as: TCC pull-out overlay for the Main room
Sibling surface: JIG WAY (JIG's mirror of this — not yet designed)

## Purpose

The MAIN Command Center is the filter command panel that drives what shows in Full Slate Matrix and other MAIN-side surfaces. Primary use: tactical filter configuration to scope the slate from "all batters" down to deployment-ready candidates.

## Doctrine identity

- TCC orchestrates; it does not compute
- 9 grouped filter sections
- ~45 individual filter inputs
- Compact tactical control panel design
- Restrained glow HUD styling
- Battlefield filter architecture
- Premium command-center realism

## Customization scope (locked)

Option C — Both levels of customization:
- Drag section headers to reorder entire sections
- Drag individual filters to reorder within section
- Drag filters across sections (with type-safety: toggle filters only swap with toggle filters)

## Layout

### Top brand bar
- Logo + "MLB HR Engine · Tactical Command Center" title
- Subtitle: "Master project HR layout"
- Status strip on the right: Live status, Active slate (N games), System load, Current preset

### Preset bar
- Active filter count chip (live counter)
- Save Preset button
- Load Preset button (built-in: Default tactical, Aggressive, Conservative, Pre-lock)
- Reset All Filters button (red destructive variant)

### Filter section grid
Auto-fit responsive grid using minmax(360px, 1fr). Each section is a card with header + filter grid inside.

At 1400px+ viewport: 3-4 sections per row
At 1100px viewport: 2-3 sections per row
At 720px viewport: 2 sections per row
At 380px viewport: 1 section per row

### 9 sections

| Num | Section | Color | Filters |
|---|---|---|---|
| 1 | Batter Power & Contact | Red | ISO, xSLG, Barrel%, Hard Hit%, Avg Exit Velo, HR/FB% |
| 2 | Launch & Contact Shape | Green | Pull Air%, Launch Angle, HR Window%, Sweet Spot%, Fly Ball% |
| 3 | Matchup & Splits | Amber | vs RHP ISO, vs LHP ISO, Pitch Type Damage%, Min Matchup Modifier%, Min wRC+ |
| 4 | Pitcher Vulnerability | Red | Total HR Allowed, HR/9, Barrel% Allowed, Hard Hit% Allowed, Fly Ball% Allowed, Pull Damage% |
| 5 | Environment | Green | Park HR Factor, Wind, Wind Direction, Temperature, Humidity, Air Density |
| 6 | Advanced HR Signals | Red | Contact Shape Score (JIG display), Arsenal Matchup Score (JIG display), Opposite Field Weakness%, Lifted Hard Hit%, EV Trend |
| 7 | Momentum & Recency | Red | Recent HRs (7G), Recent Hard Hit%, Recent Barrel%, Hot Streak Indicator, Recent EV Trend, Launch Angle Trend |
| 8 | Game Context | Red | Exclude Started Games, Include Live Games, No Time Gate, Confirmed Lineups Only, Pre-Lineup Pool Toggle (toggles) |
| 9 | Output Control | Red | Min Projected HR%, Min Confidence%, Max Players, Sort By, Sort Direction |

Color category indicates section identity:
- Red border-top — MAIN-side quantitative sections
- Green border-top — Favorable conditions sections (Launch, Environment)
- Amber border-top — Threshold/calibration territory (Matchup & Splits)

### Bottom visibility toolbar
- Hide Sections button
- Link Tier Mode button (links to Full Slate Matrix tier scope)
- Compact Mode button
- Expanded Mode button (default active)
- Tactical Presets button (quick mode shortcuts)
- Save Layout Density button

### Footer
System status indicators: Command system status, Data status, Update timer, Operational status, Active filters count, Tactical mode (Engaged), Source (MLB Stats API).

## Filter input types

| Type | Visual | Source |
|---|---|---|
| Numeric stepper | Number value + up/down stepper | All numeric filters |
| Threshold | Same as numeric but amber-colored | Min Matchup Modifier%, Min wRC+ |
| Select dropdown | Value + chevron down | Wind Direction, Air Density, Sort By, Sort Direction |
| Toggle | On/off switch | Game Context section only |

## Customization — drag system

Section reorder
- Drag section header (contains grip icon + section number + name)
- Other sections highlight green on hover-during-drag
- Drop on another section → swap positions
- Whole filter grid stays intact with the section

Filter reorder (within section)
- Drag filter card body
- Other filters in same section highlight on hover
- Drop on another filter → swap positions
- Section structure preserved

Filter reorder (across sections)
- Drag filter from section A
- Drop on filter in section B
- Type-safety guard: toggle filters can only swap with toggle filters
- Non-toggle filters can only swap with non-toggle filters
- Cross-section move preserved across renders

## Preset system

- Save Preset — Captures current section order, filter order, and all filter values as named preset
- Load Preset — Restores section order, filter order, and values from saved preset
- Reset All Filters — Restores defaults (does NOT restore default order)
- Built-in presets — Default Tactical, Aggressive, Conservative, Pre-lock

Preset persistence requires session_state writes — HIGH risk for implementation.

## Tooltip coverage

Every interactive element has a tooltip:
- 4 status strip items (Live status, Slate, System Load, Current preset)
- Filter count chip
- 3 preset buttons (Save, Load, Reset)
- Every info icon on every filter (~45 filters)
- Every section header (description + drag hints + filter count)
- Section collapse + hide buttons
- All 6 visibility toolbar buttons
- Every footer status item

## Data integrity

- Default filter values are 0 / 0.0 / 0.000 (no fabricated thresholds)
- Min Matchup Modifier% defaults to 75 (operator standard from config.py)
- All filter values map to single source of truth in config.py
- Filter outputs do not modify model probability — they only scope which rows show
- No fabricated "match quality" — actual model output drives matchup quality

## MAIN/JIG separation

- Two filters in Section 6 (Advanced HR Signals) are JIG-domain: Contact Shape Score, Arsenal Matchup Score
- Both tooltips explicitly note "Display only · does NOT modify MAIN"
- These filters can scope which rows show but don't affect model probability
- MAIN Command Center is the MAIN-side filter panel — JIG WAY is the JIG-side mirror

## Interactions

| Action | Trigger |
|---|---|
| Adjust filter value | Click stepper or type in field |
| Save current config as preset | Save Preset button |
| Load saved preset | Load Preset button → pick from list |
| Reset all filters | Reset All Filters button |
| Reorder sections | Drag section header |
| Reorder filters within section | Drag filter card |
| Move filter across sections | Drag filter card to another section's filter |
| Hide a section | Section header → hide button (eye icon) |
| Collapse a section | Section header → collapse button (chevron up) |
| Read filter definition | Hover info icon |

## Filter scoping for Full Slate Matrix

When the operator adjusts a filter:
1. The filter scope is captured in client state
2. On commit, the scope is passed to pipeline.py
3. pipeline.py filters the slate
4. Full Slate Matrix re-renders with filtered rows
5. Active filter count updates in the preset bar
6. Other MAIN surfaces also re-scope

## Implementation risks

- MEDIUM — Static layout (9 sections + ~45 filters)
- MEDIUM — Drag-to-reorder sections (UI state)
- MEDIUM — Drag-to-reorder filters (UI state + type-safety guards)
- MEDIUM — Filter input editing (state binding)
- HIGH — Filter scope → pipeline.py routing (touches data assembly)
- HIGH — Preset Save/Load persistence (session_state ownership)
- HIGH — "Hide Sections" persistence (session_state)
- HIGH — "Link Tier Mode" cross-surface link (routing + multi-surface state)

## Cross-references

- MASTER_TCC_DOCTRINE.md — TCC orchestration rules
- DOCTRINE_RANKING_RULE.md — ranking source rule
- DESIGN_FULL_SLATE_MATRIX.md — primary consumer of filter scope
- DESIGN_JIG_BUILDER.md — has its own integrated filter section (mirrors this)
- config.py — single source of truth for thresholds, weights, calibration
- pipeline.py — canonical data assembly entrypoint
