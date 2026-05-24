# Card Hierarchy Specification
## MLB HR Engine — Visual Architecture

**Version:** 1.0  
**Date:** 2026-05-20  
**Phase:** Claude Step 2/12 — Visual Doctrine Stabilization  
**Status:** Specification only. No runtime code modified.

---

## Overview

The card hierarchy spec defines how every card type in the MLB HR Engine communicates priority, tier, and actionability through visual structure alone — before any label is read. The guiding sequence is:

```
SCAN → QUALIFY → DEPLOY
```

And for matchup-driven views:

```
MATCHUP → CONFIRM → EXPLOIT
```

Every card type must honor one of these two sequences. A card that forces an operator to read labels before knowing whether to act has failed.

---

## Card Priority Tiers

Five visual tiers govern all card types. Tier is determined by the engine's escalation logic, not by operator preference.

| Tier   | MLB HR Engine Label | Visual Voltage | Operator Expectation |
|--------|---------------------|----------------|----------------------|
| T1     | FIRE                | Maximum        | Deploy immediately. No hesitation signal. |
| T2     | STRONG              | High           | High-confidence pick. Deploy with confirmation. |
| T3     | WATCH               | Moderate       | Marginal edge. Requires context review before deploy. |
| T4     | COLD                | Subdued        | Suppressed. Do not deploy. Signal the reason. |
| T5     | VOID                | Minimal        | Invalid pick. DNP, scratch, lineup exclusion, filter failure. |

**Rule:** A FIRE card and a VOID card for the same player must look fundamentally different without reading any text. If tier ambiguity is possible at 2-second glance, the hierarchy is broken.

---

## Visual Dominance Rules

### Primary Dominant Element

Each card has exactly one primary dominant element — the element that wins the visual entry contest.

| Card Type            | Primary Dominant Element |
|----------------------|--------------------------|
| Player Threat Card   | HR Threat Score badge (number + tier word) |
| Matchup Card (H2H)   | Strike zone xSLG grid (color gradient) |
| Game Card            | Environment score + team matchup header |
| Deployment Card      | EV% badge + bet size |
| Pitch Mix Card       | Pitch usage bar chart (horizontal) |
| Escalation Module    | Tier badge + dominant metric (barrel or EV) |

**Rule:** Only one element may be primary dominant per card. If the player image, the badge, and a stat cluster are competing for first attention, the card has no primary dominant element and must be revised.

---

## Threat Escalation Hierarchy Within Cards

Within any single card, information must appear in descending signal weight. No exceptions.

### Player Threat Card Information Order

```
1. HR Threat Score + Tier Badge          ← SCAN target
2. HR Probability % (tonight)            ← QUALIFY gate 1
3. EV% + Edge%                           ← QUALIFY gate 2
4. Barrel% + Exit Velocity               ← QUALIFY gate 3
5. Park Factor + Pitcher Factor          ← QUALIFY gate 4
6. Bet Size + Sportsbook Target          ← DEPLOY signal
7. Pitch Mix Module (HVY modifier)       ← CONFIRM supplement
8. Environment Score                     ← Context only
```

Items 1–3 must be visible on the compact card state.  
Items 4–6 visible after first expand.  
Items 7–8 visible after second expand (deep context mode).

### Matchup Card (H2H) Information Order

```
1. Strike zone xSLG grid                 ← MATCHUP anchor
2. Matchup edge % + advantage direction  ← CONFIRM signal
3. EV + Confidence                       ← CONFIRM gate
4. Pitcher profile (suppressor signals)  ← CONFIRM gate
5. Batter power profile                  ← EXPLOIT confirmation
6. Career H2H block                      ← EXPLOIT supplement
7. Pitch mix tables                      ← EXPLOIT supplement
```

### Game Card Information Order

```
1. Teams + environment score             ← SCAN anchor
2. HR Opportunity score                  ← SCAN qualifier
3. Pitcher matchup (both suppressors)    ← QUALIFY gate
4. Top 3 HR threats in game             ← QUALIFY gate
5. Full lineup table (expandable)        ← DEPLOY context
```

---

## Expandable Depth Behavior

### Three Depth States

**COMPACT** — Default view in Full Slate and list contexts.
- Shows: Tier badge + player name + HR prob + EV%
- Height: 48–56px per card
- No player image
- Left-border accent in tier color only

**STANDARD** — Default in Main and JIG tabs. Default expand state in Full Slate.
- Shows: Tier badge + score + HR prob + EV + Barrel + Park + Pitcher signals
- Height: 180–220px
- Stat clusters (2–3 zones)
- Player image optional at T1/T2 only

**EXPANDED** — On-demand. One card expanded at a time.
- Shows: Full statcast profile + pitch mix + environment + deployment panel
- Height: full viewport or modal
- Player hero image active
- All signal layers visible

**Rule:** Expanding a card never navigates away from the current view. All depth is in-place.

---

## Tactical Information Ordering

The following ordering must be consistent across all card types and all depth states. Operators must build spatial memory — the barrel rate is always in the same position relative to the HR prob. Breaking this positional consistency forces re-reading on every card.

### Standard Stat Cluster Layout (2-column)

```
LEFT COLUMN               RIGHT COLUMN
HR PROB %                 EV %
Barrel %                  Edge %
Exit Velo                 Confidence
Park Factor               Pitcher Suppressor
```

### Percentile Label Format

```
[VALUE][UNIT]
P[XX] ← percentile in small caps below
```

Example: `21.4%` with `P99` below it.  
Do not use "94th NILE" — use "P94" for consistency and scan speed.

---

## Progressive Disclosure Rules

1. **COMPACT → STANDARD:** Triggered by click/tap on card. Single interaction. No hover states that reveal primary data.
2. **STANDARD → EXPANDED:** Triggered by explicit expand control (chevron icon or "expand" label). Second interaction.
3. **EXPANDED → COMPACT:** Triggered by close/collapse control or Escape. Returns to original list position.
4. **Only one EXPANDED card may exist at a time** in list views. Expanding a second card collapses the previous.
5. **Modal alternative:** EXPANDED state may open as an overlay modal rather than inline expansion, depending on view context. JIG tab uses modal. Main tab uses inline. Full Slate uses modal.

---

## Stat Visibility Doctrine

### Always Visible (T1/T2 COMPACT state)
- HR Probability %
- EV %
- Tier badge

### Visible at STANDARD state
- Barrel %
- Park Factor (numerical)
- Pitcher Suppressor factor
- Edge %
- Bet size (if configured)

### Visible at EXPANDED state only
- Full Statcast profile (xSLG, hard-hit%, sweet spot%, FB%, pull%, ISO)
- Pitch Mix HVY modifier breakdown
- Environment detail (temp, wind direction, humidity, air density)
- Calibration confidence flag
- Platoon split signal

### Never visible on card (link-out only)
- Raw Bayesian regression calculation
- Platt calibration internals
- Kelly fraction math
- API source metadata

---

## Hover and Expand Philosophy

**Desktop hover is supplementary, never primary.**  
Tooltips on hover may provide: percentile rank, definition of the stat, data source.  
Tooltips must NOT contain: the primary deployment signal, the tier determination, or the bet size.  
If a critical metric only becomes visible on hover, it must be promoted to visible state.

**Expand is the primary depth mechanism.**  
Every operator interaction that reveals meaningful data must be a click/tap, not a hover.  
Hover states are permitted for: row highlighting, tooltip definition, expand-button state change.

---

## Desktop vs Mobile Behavior

### Desktop (≥1280px)
- Full three-zone card layout (hero zone | body | tail)
- Multiple cards visible simultaneously in grid or column layout
- Right sidebar quick picks persistent
- Lineup tables with all stat columns

### Tablet (768–1279px)
- Two-zone card layout (body | tail — hero zone suppressed for T3 and below)
- Single-column card stack or 2-column compressed grid
- Right sidebar collapses to a drawer triggered by icon
- Lineup tables collapse to 5 priority columns (name | barrel | HR prob | EV | risk flag)

### Mobile (<768px)
- Single-zone card: tier badge | name | HR prob | EV — all on one row
- Expand reveals STANDARD state as a bottom sheet
- EXPANDED state is full-screen modal only
- No lineup tables — replaced by ordered threat list (batter name + tier badge + HR prob)
- Environment score visible as icon-only in game header

---

## Individual Card Type Specs

### Player Threat Card

**Purpose:** Display an individual batter's HR threat level and deployment readiness.

**COMPACT state:**
```
[TIER BADGE] [PLAYER NAME]          [HR PROB %] [EV %]
             [TEAM] [HAND] [LINEUP POS]
```

**STANDARD state:**
```
[HERO IMAGE — T1/T2 only]  [HR THREAT SCORE — large]
                            [TIER BADGE + WORD]
[STAT CLUSTER 1]            [STAT CLUSTER 2]
Barrel % | Exit Velo        EV % | Edge %
Park Factor                 Pitcher Suppressor
[HR ENVIRONMENT SCORE]
[UP NEXT MATCHUP — pitcher thumbnail]
```

**EXPANDED state:**
Full statcast profile + pitch mix module + deployment panel

**Tier differentiation:**
| Tier  | Hero Image | Score Number Size | Badge Glow | Card Border |
|-------|-----------|-------------------|------------|-------------|
| FIRE  | Yes, full  | 64px bold         | Amber glow | 1px amber + halo |
| STRONG| Yes, compressed | 48px bold    | Cyan glow  | 1px cyan + subtle halo |
| WATCH | No        | 36px medium       | No glow    | 1px white 30% opacity |
| COLD  | No        | 32px light        | No glow    | 1px white 20% opacity, dashed |
| VOID  | No        | —                 | No glow    | 1px red 20% opacity, dashed |

---

### Matchup Card (H2H)

**Purpose:** Confirm specific batter vs. pitcher exploit opportunity.

**Always opens at STANDARD state** — there is no meaningful COMPACT state for a H2H matchup.

**STANDARD state layout:**
```
[PITCHER PROFILE — left 30%]     [STRIKE ZONE GRID — center 40%]    [BATTER PROFILE — right 30%]
  Name, hand, ERA/FIP/HR9          xSLG by zone (3×3 color grid)       Name, hand, Barrel/xSLG
  Pitch mix mini                   MATCHUP EDGE % + direction           Season stats
  Suppressor signal                Confidence badge + EV                Career H2H

[PITCH MIX TABLE — left 50%]                [BATTER HIT PROFILE TABLE — right 50%]
```

**Tier differentiation:**
- Batter Advantage ≥15%: amber glow on center zone + "BATTER ADV" badge
- Neutral (±10%): no glow + "NEUTRAL" badge
- Pitcher Advantage ≥15%: red-tint on center zone + "PITCHER ADV" warning badge

---

### Game Card

**Purpose:** Summarize a game's HR opportunity landscape for Full Slate scanning.

**COMPACT state:**
```
[AWAY TEAM] @ [HOME TEAM]         [ENV SCORE /10]    [OPPORTUNITY BADGE]
[PITCHER A] vs [PITCHER B]        [Weather summary]  [Top threat: PLAYER NAME XX%]
```

**STANDARD state (expanded game):**
Full lineup table with per-row tier flags + matchup intel panel

**Tier differentiation:**
- Environment score ≥8.0: amber outline on game card
- Environment score ≤5.0: cold-blue tint on game card border
- No qualifying picks in game: VOID game card state (greyed, no opportunity badge)

---

### Deployment Card

**Purpose:** Convert a qualified pick into a configured bet action.

**Always modal.** Never inline.

**Layout:**
```
[PLAYER NAME] — [TEAM] — [TIER BADGE]
HR PROBABILITY: XX%       ENGINE CONFIDENCE: XX%
MARKET ODDS: [BOOK NAME] +XXX (implied: XX%)
EV: +XX.X%                EDGE: +XX.X%
BET SIZE: $XX             KELLY FRACTION: 0.25x

[SPORTSBOOK: ___________]  [ODDS CONFIRMED: +XXX]

[DEPLOY] [CANCEL]
```

**Friction requirement:** The DEPLOY action must be a second deliberate click. First click previews the deployment. Second click confirms. No single-tap deploy.

---

### Pitch Mix Card

**Purpose:** Display pitch arsenal matchup signal (HVY modifier) for a specific batter vs pitcher.

**Used inside:** H2H expanded state and Player Threat Card expanded state.

**Layout:**
```
[HVY MODIFIER VALUE: X.XX]        [SIGNAL DIRECTION: FAVORABLE / NEUTRAL / UNFAVORABLE]

PITCH TYPE     USAGE%   BATTER xSLG   BATTER ISO   K%
4-Seam FB      XX%      .XXX          .XXX          XX%
Slider         XX%      .XXX          .XXX          XX%
...
```

**Visual differentiation:**
- HVY > 1.15: amber badge "FAVORABLE"
- HVY 0.90–1.15: neutral badge "NEUTRAL"
- HVY < 0.90: cold-blue badge "UNFAVORABLE"

**Rule:** HVY modifier is display-only — it is NOT fed into model probability. This must be visually communicated. Use a subtle separator or label: "MATCHUP SIGNAL — NOT MODELED."

---

### Escalation Module

**Purpose:** Standalone escalation state indicator used in sidebar, header, or summary rows.

**Format:**
```
[TIER ICON] [TIER WORD]    [DOMINANT METRIC]
            [SECONDARY]
```

Examples:
```
🔥 FIRE        Barrel 21.4%
               EV +18.6%

❄️ COLD        Suppressed: 0.73× Park
               Pitcher: K/GB Suppressor Active
```

**Rule:** Escalation modules must work at 32px height and 160px width. They are designed for dense list contexts.

---

## Validation Checklist

- [x] All card types defined with COMPACT / STANDARD / EXPANDED states
- [x] Tier visual differentiation specified for each card type
- [x] Information ordering established per card type
- [x] Hover vs expand philosophy documented
- [x] Mobile behavior specified
- [x] Progressive disclosure rules defined
- [x] SCAN → QUALIFY → DEPLOY and MATCHUP → CONFIRM → EXPLOIT sequences honored

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
