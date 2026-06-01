# Design Spec — Pitch Mix Analysis Modal

Status: Design-locked · 2026-05-25
Risk class for implementation: MEDIUM
Renders as: Modal overlay (within Dynamic Tactical Viewport)
Opens from: Full Slate Matrix row → matchup quality pie click
Sibling modal: Batter Card

## Purpose

The Pitch Mix Analysis modal provides tactical pitcher arsenal analysis for a selected batter-pitcher matchup tonight. Primary use: understand which pitch types the pitcher throws, how the batter historically performs against each, and identify the exploit angle.

## Doctrine identity

JIG-flavored tactical surface that displays:
- Pitcher arsenal composition
- Batter historical performance per pitch type
- HVY signal (display-only, doctrine-compliant)
- Environment and handedness context
- Final tactical verdict

Per architectural invariant: HVY pitch-mix modifier is display-only on JIG side and must not be folded into MAIN model probability. This modal honors that explicitly with a visible "display only · does NOT modify MAIN" badge on the HVY panel.

## Layout

### Header
- Modal title: Pitch Mix Analysis
- Breadcrumb: Full Slate → Pitch Mix Analysis
- Close button (top-right)
- Batter name + team + handedness
- Pitcher name + team + handedness

### Section 1 — Matchup bar
Single horizontal bar showing batter-vs-pitcher matchup quality (model-derived). Tier badge: Elite / Strong / Avg / Weak / Danger.

### Section 2 — Pitcher arsenal donut
Donut chart showing pitch usage % per pitch type:
- 4-Seam Fastball
- Sinker
- Slider
- Changeup
- Curveball
- Additional types if pitcher throws them

Each slice colored by pitch type. Hover for usage %.

### Section 3 — Per-pitch row grid

For each pitch the pitcher throws, one row with:

| Field | Source |
|---|---|
| Pitch type | Pitcher arsenal |
| Usage % | Statcast |
| Velo (mph) | Statcast |
| Batter xwOBA vs this pitch | Statcast |
| Batter barrel% vs this pitch | Statcast |
| Batter whiff% vs this pitch | Statcast |
| Verdict pill | EXPLOIT / HUNT / NEUTRAL |

Verdict colors:
- EXPLOIT (green) — Batter punishes this pitch
- HUNT (amber) — Batter is hunting this pitch
- NEUTRAL (gray) — No edge either way

### Section 4 — HVY signal panel (display only)

JIG-side HVY pitch-mix score for this matchup. Clearly labeled:

"HVY signal · Display only — This signal is JIG-side and does NOT modify MAIN model probability per doctrine."

Includes:
- HVY composite score 0-10
- Top exploit pitches identified by HVY
- Confidence indicator

### Section 5 — Environment + Handedness context

Four small context cards in a 2x2 grid:
- Park HR factor with current value
- Wind + conditions for game-time
- Handedness edge (L vs R, R vs L, neutral)
- Pitcher fatigue (pitches thrown, days rest, decline curve)

### Section 6 — Final tactical verdict bar

Horizontal bar at bottom showing:
- Overall tactical verdict: DEPLOY / WATCHLIST / HOLD / SCRATCH
- Two action buttons on the right:
  - FanDuel button (open HR prop)
  - "Open Batter Card" button (switches to sibling modal)

## Data integrity

- All pitch data sourced from Statcast pitch-level data
- If pitcher hasn't faced this batter (or sample too small), row shows `--` with note
- HVY signal only displays if model confidence threshold met (per config.py)
- Never fabricate xwOBA or barrel% from insufficient sample
- Pitcher arsenal donut shows only confirmed pitch types from recent appearances

## MAIN/JIG separation

- HVY signal panel is JIG-side, labeled explicitly
- Pitch-by-pitch xwOBA/barrel/whiff are statcast data, source-neutral
- Verdict pills (EXPLOIT/HUNT/NEUTRAL) are JIG-tactical interpretations, marked as JIG output
- MAIN model probability and ranking are NOT modified by anything shown in this modal

## Tooltip coverage

- Every stat column header (definition + tier cutoffs)
- Every verdict pill (what it means tactically)
- HVY signal panel header (full doctrine reminder)
- Pitcher fatigue card (how the metric is calculated)
- Tactical verdict bar (how the verdict is derived)

## Interactions

| Element | Action |
|---|---|
| Close button | Returns to Full Slate Matrix |
| FanDuel button | Opens HR prop in new tab |
| Open Batter Card button | Switches to Batter Card modal for same player |
| Any pitch row | Highlights that pitch in the arsenal donut |
| Verdict pill | Shows tooltip explaining the tactical read |

## Implementation risks

- MEDIUM — Modal rendering (modal architecture is a closed surface — see CLAUDE.md)
- MEDIUM — Pitcher arsenal donut chart (pure visualization)
- MEDIUM — Per-pitch matchup computation (read-only data join)
- MEDIUM — HVY signal display (must not leak into MAIN code path)
- HIGH — Modal-to-modal navigation (Pitch Mix → Batter Card) touches modal architecture

## Cross-references

- DESIGN_FULL_SLATE_MATRIX.md — parent surface
- DESIGN_BATTER_CARD.md — sibling modal
- MASTER_TCC_DOCTRINE.md — MAIN/JIG separation rules
- DOCTRINE_RANKING_RULE.md — ranking source rule (HVY doesn't affect rank)
- pipeline.py — pitch-level data assembly
