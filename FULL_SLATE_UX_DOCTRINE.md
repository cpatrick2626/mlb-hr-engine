# Full Slate Battlefield UX Doctrine
## MLB HR Engine v4 — Command-Center Intelligence Layer

**Document Status:** Planning & Architecture Only  
**Runtime Systems:** FROZEN (Codex ownership)  
**This document:** UX doctrine, escalation hierarchy, interaction architecture — NON-IMPLEMENTED  
**Date:** 2026-05-20

---

## Table of Contents

1. [Full Slate Battlefield Scan Doctrine](#1-full-slate-battlefield-scan-doctrine)
2. [Escalation Hierarchy System](#2-escalation-hierarchy-system)
3. [Game Card Battlefield Doctrine](#3-game-card-battlefield-doctrine)
4. [Mobile Compression Doctrine](#4-mobile-compression-doctrine)
5. [Full Slate Command Strip Doctrine](#5-full-slate-command-strip-doctrine)
6. [Expansion Flow Architecture](#6-expansion-flow-architecture)
7. [Cognitive Load Reduction](#7-cognitive-load-reduction)
8. [Visual Restraint Guidelines](#8-visual-restraint-guidelines)
9. [Tactical Readability Recommendations](#9-tactical-readability-recommendations)
10. [Future Enhancement Opportunities](#10-future-enhancement-opportunities)

---

## 1. Full Slate Battlefield Scan Doctrine

### 1.1 Operator Scan Sequence

The Full Slate view is the mission-control layer. An operator arriving at this view has a finite decision window — games lock, lineups post, and odds shift. Every pixel must earn its place.

**Primary scan sequence (left-to-right, top-to-bottom gravity):**

```
[COMMAND STRIP]         ← Tier 1: Situational awareness in <1 second
    ↓
[GAME COUNT / STATUS]   ← Tier 2: Slate geometry (how many games, what inning state)
    ↓
[ESCALATED GAME CARDS]  ← Tier 3: Danger surfaced first (Critical → Dangerous → Elevated)
    ↓
[ACTIVE GAME CARDS]     ← Tier 4: Qualified picks with no escalation
    ↓
[QUIET GAME CARDS]      ← Tier 5: No actionable plays — compressed, skippable
```

### 1.2 What the Operator Sees First

The operator's eye must land on the command strip within 300ms of view load. The command strip must answer:

- How many live games are in the slate?
- Are any games in a Critical or Dangerous escalation state?
- What is the active weather threat level?
- What is the current pipeline freshness (last sync timestamp)?

**First-visible zone rules:**

- No hero images, logos, or decorative elements above the fold
- No full-width banners that consume vertical space without conveying state
- Escalated game cards appear ABOVE the fold on desktop at all standard viewport sizes
- If zero escalations exist, the operator should see this immediately — the slate should feel "quiet" at a glance

### 1.3 What Escalates Visually

Escalation signals must propagate from player-level data upward to game-card level, then to the command strip.

**Escalation triggers (from existing data model):**

| Signal | Source Field | Escalation Threshold |
|---|---|---|
| EV% | `ev_pct` | ≥15% → Elevated; ≥20% → Dangerous; ≥25% → Critical |
| Edge% | `edge_pct` | ≥8% → Elevated; ≥12% → Dangerous |
| Barrel tier | `barrel_pct` | ≥10% → Elevated; ≥12% → Dangerous |
| Model probability | `model_prob` | ≥18% → Elevated; ≥22% → Dangerous |
| Weather threat | `weather_factor` | ≤0.88 or ≥1.12 → Active |
| Pitcher danger | `pitcher_factor` | ≥1.25 (hittable) → Elevated on card |
| Line movement | `line_movement` | Sharp-side movement → flag |

A game card's escalation level = the highest-escalation player within that game.

### 1.4 Danger Visual Propagation

Danger propagates upward, not laterally. A single Critical-tier player in Game 7 should make Game 7's card surface at the top of the slate — it does not spread to neighboring cards.

**Propagation rules:**
- Each game card renders at its highest player escalation state
- The command strip's alert count = number of Elevated-or-above cards
- Quiet games sink to the bottom — they never displace escalated games from the scan path
- Escalation state updates dynamically (tied to pipeline freshness timer, not user interaction)

### 1.5 Scan Rhythm Design

The operator should be able to complete a full-slate reconnaissance in under 90 seconds for a 12-game slate. This requires:

- **Vertical density:** Each card must communicate its tier in the first 2-3 lines of content
- **Horizontal grouping:** Related signals (pitcher + park + weather) cluster on one row — not spread across 8 columns
- **Color before text:** The operator's peripheral vision reads color before they read labels
- **Badge restraint:** Maximum 3 visible badges per card in collapsed state — not a badge farm

---

## 2. Escalation Hierarchy System

### 2.1 The Five Levels

#### QUIET
*No actionable plays in this game. Below filter thresholds. No threat signals.*

- **Visual behavior:** Collapsed state by default. Muted border (neutral gray). No accent color. 50% opacity on game header text.
- **Information density:** Team names, inning state, one-line matchup summary only.
- **Escalation indicators:** None rendered.
- **Interaction expectations:** Operator does not need to interact. Collapse is default and sticky.
- **Operator urgency:** Zero. Peripheral scan only.
- **Animation:** None. Static render.
- **Color doctrine:** `--color-quiet: #3a3a3a` (dark gray surface). Text at 60% opacity. No borders with color.

---

#### ACTIVE
*Qualified picks exist. EV and edge pass filters. No extraordinary signals.*

- **Visual behavior:** Default expanded (2-3 lines visible). Subtle left-border accent `#4a7fa5` (steel blue). Normal text contrast.
- **Information density:** Team matchup, starting pitcher, top 2 qualified batters with rank + EV%, lineup spots.
- **Escalation indicators:** Green EV% pill on top batter. Lineup spot shown. Pitcher risk indicator neutral.
- **Interaction expectations:** Operator will expand to review. Card tappable/clickable for full detail.
- **Operator urgency:** Low. Review at leisure during session.
- **Animation:** None on card. Subtle fade-in on initial load only.
- **Color doctrine:** Steel blue border `#4a7fa5`. EV pill: `#2d6a2d` (dark green on dark surface). Text: full opacity.

---

#### ELEVATED
*Strong play exists. EV ≥15% OR Edge ≥8% OR Barrel ≥10%. Worth deployment consideration.*

- **Visual behavior:** Expanded by default. Left-border accent `#c8a035` (amber). Background surface subtly warmer `#1e1a0e`. Batter row highlighted.
- **Information density:** All ACTIVE fields + pitcher factor displayed, park factor rendered, 1 environmental signal visible.
- **Escalation indicators:** Amber EV% pill. "ELEVATED" label in small caps near top-right corner. Barrel% shown prominently for qualifying batters.
- **Interaction expectations:** Operator is expected to review before session closes. Card persists in view.
- **Operator urgency:** Medium. Do not miss this card.
- **Animation:** Left-border renders with a 200ms slow-fill animation on page load — draws eye without flashiness. No pulse, no glow loop.
- **Color doctrine:** Amber `#c8a035`. No orange (too sportsbook). Muted warm tones only. EV pill readable at arm's length.

---

#### DANGEROUS
*High-conviction play. EV ≥20% AND Edge ≥8% AND Barrel ≥10%. Clear deployment candidate.*

- **Visual behavior:** Expanded. Left-border `#b84040` (tactical red). Background surface `#1c0e0e`. Top batter row uses elevated text weight and warm red-adjacent accent.
- **Information density:** All ELEVATED fields + HVY pitch mix modifier shown, open vs model probability delta, bet sizing surfaced, correlation cluster if multi-pick game.
- **Escalation indicators:** Red EV% pill. "DANGEROUS" label. Barrel tier badge (e.g., "BARREL 12+"). Pitcher danger score visible.
- **Interaction expectations:** Operator must actively review and make a deployment decision. Interaction prompt subtly rendered ("Review Deployment").
- **Operator urgency:** High. This card should never leave the operator's scroll window without action.
- **Animation:** Border animates with a single slow pulse on arrival (one cycle, then static). Not looping. Not glowing. One pulse = presence confirmed.
- **Color doctrine:** Tactical red `#b84040`. No neon red. No glowing shadow. Surface warms subtly. White text only at full opacity.

---

#### CRITICAL
*Maximum signal convergence. EV ≥25% + Edge ≥12% + Barrel ≥12% + favorable environment.*

- **Visual behavior:** Pinned to top of slate regardless of game order. Full expanded state. Left-border `#b84040` + top-border `#b84040`. Surface `#1a0808`. "PRIORITY" badge in command strip.
- **Information density:** All DANGEROUS fields + full deployment briefing: best odds, suggested bet size, Kelly fraction, correlation exposure alert if applicable. Environmental summary in one line.
- **Escalation indicators:** "CRITICAL" label. PRIORITY badge in command strip increments. All factor scores shown. Deployment action available.
- **Interaction expectations:** Operator is expected to execute or explicitly dismiss. No passive scroll-past.
- **Operator urgency:** Maximum. System interrupts passive scanning.
- **Animation:** On arrival: one 300ms top-border fill animation. Then static. No loops, no shimmer, no ongoing glow. The card earns attention through placement and density, not animation noise.
- **Color doctrine:** All DANGEROUS rules apply plus top-border ring. No neon. No bright red fills. Dark red surfaces only. The system should feel serious, not alarming.

### 2.2 Escalation Color Token System

```
--escalation-quiet:     #3a3a3a   (neutral gray)
--escalation-active:    #4a7fa5   (steel blue)
--escalation-elevated:  #c8a035   (tactical amber)
--escalation-dangerous: #b84040   (tactical red — muted)
--escalation-critical:  #8a0000   (deep red — reserved for border ring)

--surface-quiet:        #141414
--surface-active:       #161820
--surface-elevated:     #1e1a0e
--surface-dangerous:    #1c0e0e
--surface-critical:     #1a0808

--text-primary:         #e8e8e8
--text-secondary:       #9a9a9a
--text-muted:           #5a5a5a
```

### 2.3 Animation Restraint Philosophy

- **One entry animation per card per session.** Not per scroll. Not per state change.
- **Entry animations are border-draws, not glows.** A border fills in 200–300ms. That's it.
- **Zero looping animations** on any escalation state, including Critical.
- **Zero persistent pulsing** on any element that has been on screen for more than 5 seconds.
- **State transitions** (Quiet → Active, Active → Elevated, etc.) are color swaps with a 150ms ease — not animated sequences.
- **The operator trusts a system that is calm.** Constant motion = noise. Noise = ignored.

---

## 3. Game Card Battlefield Doctrine

### 3.1 Information Priority Order

Each game card presents information in this strict hierarchy. Higher-priority information cannot be displaced by lower-priority information.

```
Priority 1: Game identity      — Teams, Time, Escalation state
Priority 2: Pitcher danger     — Starting pitcher, pitcher_factor, fatigue, pitch profile
Priority 3: Top batter(s)      — Best 1-2 qualifying batters, EV%, rank
Priority 4: Environmental risk  — Park factor (extreme only), weather (threat only)
Priority 5: Market context     — Best odds available, implied probability delta
Priority 6: Expansion handle   — "See all X batters / pitcher detail / arsenal"
```

Priority 1–3 must be visible in collapsed state.  
Priority 4–6 appear on single-tap expand.

### 3.2 Tactical Grouping Behavior

Signals are grouped by function, not by field name. An operator doesn't think in field names — they think in questions:

- "Is this pitcher hittable?" → `pitcher_factor` + `fatigue` + `arsenal type` = one group
- "Is this batter live?" → `model_prob` + `barrel_pct` + `lineup_spot` + `ev_pct` = one group
- "Is the environment supporting?" → `park_factor` + `weather` = one group
- "What's the market offering?" → `best_american` + `edge_pct` = one group

**Layout example (collapsed Active card):**

```
┌──────────────────────────────────────────────────────────────────┐
│  NYY @ BOS  7:10 PM ET                           [ACTIVE]        │
│  SP: Cole (RHP)  ·  Factor 1.08  ·  Rested                      │
│  ─────────────────────────────────────────────────────────────── │
│  #1  J. Devers   3B  │  Model 18.2%  │  EV +14.7%  │  Spot: 4  │
│  #2  C. Bellinger 1B │  Model 14.9%  │  EV +9.1%   │  Spot: 3  │
│  ─────────────────────────────────────────────────────────────── │
│  ▼ See 3 more batters / Expand arsenal / Weather: Neutral         │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 Visual Hierarchy

- **Game header row:** Maximum contrast. Team abbreviations bold. Time dim. Escalation badge right-aligned.
- **Pitcher row:** One line. Name + handedness + factor score + rest state. No paragraph.
- **Batter rows:** Rank number left-anchored (leftmost gravity). Name + position. Model probability. EV%. Lineup spot. All on one line.
- **Environmental row:** Renders ONLY if park factor ≤0.93 or ≥1.08 OR weather factor ≤0.92 or ≥1.08. Otherwise this row is suppressed. Do not show "Neutral" environment — the operator doesn't need to be told nothing is happening.
- **Expansion handle:** Always last. Renders count of suppressed batters. Expandable inline — no page navigation.

### 3.4 Collapse / Expand Flow

- **Default state** is determined by escalation level:
  - Quiet → Collapsed (header only)
  - Active → Collapsed (header + pitcher + top 1 batter visible)
  - Elevated → Expanded (all Priority 1–4 visible)
  - Dangerous → Expanded + deployment zone visible
  - Critical → Pinned + fully open + deployment zone

- **Expand interaction:** Single tap/click anywhere on card body (not just expand handle). Expand is fast — <100ms. No accordion animation longer than 150ms.

- **Collapse interaction:** Tap header row to collapse. Collapsed state is remembered per session. Cards do not auto-collapse on external data refresh.

### 3.5 Stack Visibility

When multiple qualifying batters exist in one game, the card shows a stack indicator:

```
  [TOP 2 VISIBLE]  ·  +3 more  ▼
```

Stack count is always truthful. If 5 batters qualify, show "Top 2" + "+3 more". Do not collapse it to just "See all."

Stacked batters are sorted by composite score (EV×0.4 + Edge×0.35 + Confidence×0.25 — matching the existing ranker logic). The operator should see the best play first, always.

### 3.6 Pitcher Danger Presentation

Pitcher danger is a two-signal display:

1. **Pitcher factor numeric** — always shown (e.g., `1.24`)
2. **Qualitative label** — rendered in small caps, derived from `pitcher_factor`:
   - `≤0.85` → `SUPPRESSOR` (dim, not a threat)
   - `0.86–1.05` → `NEUTRAL` (shown only on expand — never on collapsed card)
   - `1.06–1.20` → `HITTABLE`
   - `≥1.21` → `DANGER` (amber on Elevated cards, red on Dangerous/Critical)

Pitch mix (HVY modifier) is a supplemental signal that appears only on expand. It is NEVER the lead signal on a collapsed card — it is context, not headline.

### 3.7 Deployable Batter Surfacing

A "deployable" batter is defined as: `ev_pct >= MIN_EV_PCT AND edge_pct >= MIN_EDGE_PCT AND all 7 filters passed`. These are the picks the operator can act on.

- Deployable batters always render above non-deployable batters in the stack
- The word "DEPLOYABLE" is never shown — instead, the batter row uses a left-margin indicator mark (a thin vertical colored bar matching escalation color)
- Non-qualified batters (below filter) are shown in the expanded state with muted contrast and no indicator bar

### 3.8 Inning / Game State Positioning

Game state (inning, score) appears only in live/in-progress game contexts. For pre-game views:

- Show game time prominently
- Show pitcher confirmed/TBD status prominently (`TBD` pitcher = amber warning on that card)
- Do not render a simulated score or score placeholder

For live game contexts (future build):

- Score renders in the header row, right of team names
- Inning shown as `T6` / `B7` (half-inning abbreviated)
- Completed games render with `FINAL` badge and the card collapses to quiet

### 3.9 Environmental Visibility

Environmental signals are suppressed when neutral (see Section 3.3). When active:

- **Park factor ≥1.08:** `HITTER PARK` badge (green)
- **Park factor ≤0.93:** `PITCHER PARK` badge (red-muted)
- **Wind ≥8mph toward CF:** `WIND: 10mph IN` (amber)
- **Wind ≥8mph away from CF:** `WIND: 10mph OUT` (green)
- **Temp ≤45°F:** `COLD: 41°F` (blue-muted)
- **Humidity extreme:** rarely shown, only if factor diverges >5% from baseline
- **Dome:** render nothing — dome teams have no weather exposure

Environmental badges always appear on the same row, grouped together. Never interleaved with batter data.

---

## 4. Mobile Compression Doctrine

### 4.1 Mobile Tactical Hierarchy

On mobile (viewport ≤768px), the operator is typically in a time-constrained, one-hand mode. The entire slate must communicate its status without requiring horizontal scroll.

**Mobile hierarchy reorder:**

```
[COMMAND STRIP] — Always visible, sticky top
[ESCALATION SUMMARY] — "2 Critical · 3 Elevated · 7 Active" one line
[CRITICAL CARDS] — Full width, stacked
[ELEVATED CARDS] — Full width, stacked
[ACTIVE CARDS] — Full width, collapsed by default on mobile
[QUIET CARDS] — Hidden behind "Show X quiet games" toggle
```

### 4.2 Progressive Disclosure Behavior

Mobile cards use three disclosure levels:

**Level 1 (default on mobile):**
- Game header (teams + time + escalation badge)
- Top 1 batter only (name + EV% + lineup spot)
- Tap anywhere to advance

**Level 2 (first tap):**
- All Priority 1–4 fields
- Top 3 batters
- Environmental summary (if active)
- Pitcher danger

**Level 3 (second tap / expand all):**
- Full batter stack
- Arsenal/pitch mix
- Deployment briefing
- Bet sizing

**Rules:**
- Level 1 → Level 2 transition: 120ms slide expand, no bounce
- Level 2 → Level 3: same
- Back-chevron or tap-header collapses one level at a time
- Level 3 is sticky for Dangerous/Critical cards (doesn't auto-collapse)

### 4.3 Scroll Reduction Strategies

- Quiet games are hidden by default on mobile. Accessible via `Show all games (X quiet)` at bottom of list.
- Cards do not repeat information the command strip already shows (no redundant "3 Critical picks on slate" copy inside a card that's already escalation-colored)
- Long batter stacks use "Show 3 more" inside the expanded card rather than extending card height
- Environmental information is one-line maximum on mobile — never a multi-line block
- Pitcher arsenal detail is never visible at Level 1 or Level 2 on mobile

### 4.4 Compact Escalation Visibility

On mobile, escalation color must survive reduced card height. Color load shifts from borders (which may be too thin on mobile) to:

- Full-width background tint on the game header row (1 row = ~44px) matching escalation surface color
- Escalation label rendered as a small chip, not a full badge
- EV% pill remains on first batter row even at Level 1

Example Level 1 mobile card (Dangerous):

```
┌────────────────────────────────────────┐  ← #b84040 header tint
│  NYY @ BOS   7:10 PM   [DANGEROUS]    │
├────────────────────────────────────────┤
│  #1 Devers · EV +21.4% · Spot 4       │
│  ▼ Tap to expand (4 more batters)      │
└────────────────────────────────────────┘
```

### 4.5 Command Strip Mobile Behavior

On mobile, the command strip compresses to a single bar:

```
[●3 Critical] [●5 Elevated] [12 Active] [Synced 4m ago] [≡]
```

- Dot indicators replace word "alerts" — color-coded to escalation tokens
- Tap on `≡` opens a slide-over with full command strip content
- Strip never wraps to two lines — it scrolls horizontally if more than 4 segments
- Sync timestamp always visible — operator trust depends on freshness signal

---

## 5. Full Slate Command Strip Doctrine

### 5.1 Purpose

The command strip is the always-visible operations dashboard. It is never scrolled away from. It answers in under 1 second: "What is the state of the slate right now?"

### 5.2 Structural Zones

The command strip has five zones, left to right:

```
[ZONE 1: PIPELINE]  [ZONE 2: LIVE GAME COUNT]  [ZONE 3: ESCALATION SUMMARY]  [ZONE 4: ENVIRONMENT]  [ZONE 5: SYNC STATE]
```

**Zone 1 — Pipeline identity:**
- Engine version (`v4.2`) and run timestamp (`Run: 7:04 AM`)
- Clicking this zone opens a pipeline history / run log drawer
- If pipeline is stale (>2 hours old), this zone renders in amber with a `STALE` label

**Zone 2 — Live game count:**
- `14 Games · 8 Locked · 6 Live` (future state with live game data)
- Pre-game: `14 Games · All Pre-Game`
- Games with TBD pitchers: `2 TBD` shown as amber count
- Clicking opens a game-status sidebar

**Zone 3 — Escalation summary:**
- `3 Critical · 5 Elevated · 9 Active · 4 Quiet`
- Counts link to filtered views (tap "3 Critical" → slate filters to show only Critical cards)
- Zero counts are hidden entirely — if no Critical games, "Critical" is not shown
- Numbers update when pipeline refreshes — transition is a number swap, not a flash

**Zone 4 — Environment:**
- Shows only active environmental threats: `Wind ↑ 12mph · Cold: 44°F`
- If environment is fully neutral across all games: this zone is suppressed (empty)
- Never shows "Conditions nominal" or similar filler text

**Zone 5 — Sync state:**
- `Synced 3m ago` — always present
- `Refreshing...` with a subtle spinner during active refresh — not a progress bar, not an overlay
- If sync fails: `Sync failed — 14m ago` in amber
- Clicking opens a manual refresh trigger (UX action, not a Codex-owned system call)

### 5.3 Tactical Notifications

The command strip can surface tactical notifications — events that require operator attention but don't warrant a card escalation.

**Notification types:**

- Line movement alert: `↑ Devers line moved +20 pts (sharp side)`
- Lineup change: `⚡ Juan Soto scratched — BOS lineup pending`
- Pitcher change: `⚠ Cole scratched — TBD pitcher for NYY`
- Weather escalation: `🌬 Wind 14mph OUT at Fenway — recalculate`

**Notification rules:**
- Maximum 2 notifications visible at once in the strip
- Notifications are dismissible (single-tap × on each)
- If 3+ notifications exist, strip shows "2 alerts +" — tap to open notification drawer
- Notifications do not auto-dismiss (they're operational signals, not transient toasts)
- No notification icons that pulse, flash, or animate after 3 seconds on screen

### 5.4 Live Game Indicators

For live in-progress games (future state):

- Strip shows `● LIVE` in green with count of in-progress games
- Live games sort to the top of the slate view
- In-progress game cards show inning state updated at appropriate cadence
- The command strip does not show play-by-play or score feeds — that is a different product surface

### 5.5 Battlefield Notifications Architecture

Notifications follow a priority queue:

```
P1: Lineup scratches (pitcher or top qualifier)
P2: Significant line movement on qualified plays
P3: Weather changes affecting qualified plays
P4: Pipeline staleness beyond threshold
P5: Sync failure
```

P1 and P2 surface in the command strip itself.  
P3–P5 surface in the sync-state zone.  
All others route to the notification drawer only.

---

## 6. Expansion Flow Architecture

### 6.1 The Tactical Expansion Hierarchy

```
SLATE VIEW
    ↓ tap game card
GAME DETAIL
    ↓ tap batter row
THREAT CLUSTER VIEW
    ↓ tap "Arsenal / Pitch Mix" section
ARSENAL BREAKDOWN
    ↓ tap "Deploy" or "Evaluate"
DEPLOYMENT BRIEFING
```

### 6.2 Information at Each Stage

#### Slate View
- Game card collapsed/expanded per escalation defaults
- No per-player deep data visible
- Persistent: Command Strip, escalation states, game count

#### Game Detail
- All batters for this game (qualified + non-qualified, clearly separated)
- Pitcher full profile: handedness, factor, fatigue, pitch mix overview, K/GB tendency
- Park profile: factor score, HR tendency by batter hand
- Weather summary: temp, wind direction/speed, humidity if extreme, dome status
- Parlay eligibility: "2 batters qualify for same-game stack" (if applicable)
- Persistent: Command Strip, game header with escalation state

#### Threat Cluster View
- All correlated picks in this game displayed together (same lineup = same correlation cluster)
- Correlation warning if deploying 2+ from same lineup: `ρ = 0.40 — variance elevated`
- Exposure alert: if this game already represents >35% of slate exposure
- Persistent: Game header, command strip

#### Arsenal / Pitch Mix
- HVY modifier breakdown: all 5 signal components with individual values
- Pitcher arsenal: FB%, slider%, CH% — how it plays against batter hand
- Career H2H OPS (if available)
- This view is supplemental intelligence — it never replaces model_prob as the lead signal
- Label clearly: `[DISPLAY ONLY — Not fed into model probability]`
- Persistent: Game header, batter summary row

#### Deployment Decision
- Final deployment briefing:
  - Batter name, rank, model probability (calibrated)
  - Best odds available (source sportsbook)
  - Suggested bet size (quarter-Kelly output)
  - EV%, Edge%, Confidence score
  - One-line risk summary: "Elevated barrel — favorable park — hittable pitcher"
  - Quick-add to session tracker (logs pick without leaving view)
- Persistent: Everything above

### 6.3 Persistence Rules

Elements that persist through all expansion levels:

- Command Strip (always)
- Game header with escalation state (from Game Detail downward)
- Back navigation chevron (one level at a time, no teleport-to-slate)

Elements that intentionally reduce on expansion:

- Slate-level game count and escalation summary (Command Strip retains this — card removes it to reduce noise)
- Quiet game cards (collapse further when operator drills into another game)

### 6.4 Where Cognitive Load Intentionally Reduces

**As the operator expands deeper, the viewport narrows focus.** This is deliberate:

- At Deployment Briefing level: only one batter's information is visible. All other games are hidden. The operator is making one decision.
- Arsenal detail appears ONLY when the operator requests it. It is never surfaced automatically.
- Bet sizing appears at the final level only — never on the game card. This prevents premature sizing decisions before full context is reviewed.
- Escalation state from other games does not intrude at deployment level — the operator is focused.

---

## 7. Cognitive Load Reduction

### 7.1 The Zero-Redundancy Rule

Every data point should appear once in the operator's current view. If a value is visible in the command strip, it does not appear on the card. If it appears on the card header, it does not appear on the batter row.

**Violations to eliminate:**
- Showing "14 total games" both in the command strip AND as text on the first card
- Showing EV% on both the collapsed card AND the command strip escalation count (the count is sufficient)
- Repeating the game time in both the header row and the expansion panel
- Showing both `model_prob` and `market_no_vig_prob` and `edge_pct` in collapsed state (edge_pct summarizes the delta — show that alone)

### 7.2 Suppression Rules

Information is suppressed unless it is actionable:

| Field | Show condition |
|---|---|
| `park_factor` | Only if ≤0.93 or ≥1.08 |
| `weather_factor` | Only if ≤0.92 or ≥1.08 |
| `pitcher_factor` label | "NEUTRAL" label never shown; only HITTABLE or DANGER |
| `lineup_spot` | Show only if ≤5 (top-5 only, per filter logic) |
| `pitcher_fatigue` | Only if short-rest (≤4 days) |
| `market_no_vig_prob` | Only in Game Detail, not on card |
| `soft_flags` | Only in expanded state — never on collapsed card |
| `HVY modifier` | Only in Arsenal view, never on card |
| `correlation ρ` | Only when deploying 2+ picks from same lineup |

### 7.3 Label Compression Standards

| Verbose (avoid) | Compressed (use) |
|---|---|
| "Expected Value Percentage" | `EV%` |
| "Market No-Vig Probability" | `Mkt%` |
| "Composite Confidence Score" | `Conf` |
| "Batter Lineup Position" | `Spot` |
| "Quarter-Kelly Bet Size" | `Bet $` |
| "Pitcher Danger Factor" | `Ptch` |
| "Park Home Run Factor" | `Park` |
| "Statcast Power Multiplier" | `Pwr` |
| "Barrel Percentage" | `Brl%` |

Labels are dim — values are bright. The operator reads values, not labels.

### 7.4 Decision Fatigue Prevention

- Sort order is fixed by the engine (composite score). Operator does not need to sort columns manually.
- Filtering is limited to escalation-level filter (Critical / Elevated / Active / All). No multi-column sort UI.
- Bet size is pre-calculated and displayed as a dollar amount — the operator does not compute Kelly fractions in their head.
- The engine does not surface picks below filter thresholds in the primary view. Those exist only in the "All players" expansion, accessed explicitly.

---

## 8. Visual Restraint Guidelines

### 8.1 Color Philosophy

This system uses color as signal, not decoration. Every color element must carry meaning.

**Prohibited:**
- Gradient fills on card surfaces
- Neon accent colors (lime green, electric blue, hot pink)
- Background gradients that don't encode information
- Color used purely for "premium" aesthetics without conveying state
- More than 3 simultaneous accent colors in any single card

**Permitted:**
- Escalation token colors (5 defined, never deviated from)
- EV% pill: green spectrum only (`#2d6a2d` → `#1a4a1a` as intensity increases)
- Edge% display: same green spectrum
- Warning states: amber only (`#c8a035`), never orange
- Error states: tactical red (`#b84040`), never bright red

### 8.2 Typography Hierarchy

Three levels only:

1. **Primary** — Player names, EV%, team names, escalation labels. Full weight. Full contrast.
2. **Secondary** — Pitcher names, park identifiers, time. 80% contrast. Normal weight.
3. **Tertiary** — Labels, timestamps, quiet game content, non-active information. 50–60% contrast. Reduced weight.

No more than three type sizes in any single card. Headline (game teams), body (batter data), caption (labels and timestamps).

### 8.3 Density vs. Breathing Room

The system is information-dense but not crowded. Rules:

- 8px internal padding minimum on all card sides
- 4px vertical gap between batter rows
- 12px gap between the pitcher zone and batter zone within a card
- Separator lines between zones: 1px at 15% opacity — visible but not structural
- Never use zero-padding tables — the eye needs rhythm breaks

### 8.4 Badge Restraint

Maximum badges per card state:

| State | Max badges |
|---|---|
| Collapsed (Quiet) | 0 |
| Collapsed (Active) | 1 (escalation level only) |
| Collapsed (Elevated) | 2 (escalation + one signal) |
| Expanded | 3 (escalation + barrel tier + one environmental) |
| Deployment briefing | Unlimited within deployment zone |

Badges that are never used:
- "HOT" badges
- "🔥" or emoji-based indicators
- Animated count badges
- Blinking or attention-seeking indicators

---

## 9. Tactical Readability Recommendations

### 9.1 The 90-Second Recon Standard

A well-designed slate should allow a trained operator to complete reconnaissance in:

- 15 seconds: Command strip reading (slate status, escalation counts, sync state)
- 30 seconds: Critical and Dangerous card review (2–3 cards maximum at these tiers)
- 30 seconds: Elevated card scan (3–5 cards)
- 15 seconds: Active card headers (peripheral awareness only)

If this can't be completed in 90 seconds, the slate is too noisy or escalation signals are not distinct enough.

### 9.2 Scan Path Anchors

The operator's eye should anchor naturally at:

1. Top-left of command strip on page load
2. First Critical or Dangerous card (if any)
3. Escalation badge on each card (right-aligned header)
4. First batter EV% in each card (leftmost data after rank)

These four anchor points should be reachable without horizontal movement of more than 20% of viewport width.

### 9.3 Anti-Patterns to Avoid

| Pattern | Why harmful |
|---|---|
| Spreadsheet rows with 12+ columns | Horizontal scroll breaks scan rhythm |
| All cards same height | No visual priority differentiation |
| Color-coded only by team | Team colors have no tactical meaning |
| Pop-up modals for batter detail | Breaks context — use inline expansion |
| "Loading..." placeholder cards | Introduces uncertainty, breaks rhythm |
| Infinite scroll for game cards | Operator loses position, misses games |
| Tabs for Critical / Elevated / Active | Tabs hide content — cards surface it |
| Tooltip-only data | Mobile hostile, defeats rapid scan |

### 9.4 Cinematic Realism Standard

The system should feel like an intelligence dashboard used by professionals, not a consumer sports app.

**Achieving this through:**
- Dark surfaces with intentional contrast (not pure black, not light gray)
- Typographic consistency — no font mixing
- Data presented as operational signals, not entertainment metrics
- Labels are functional identifiers, not marketing language
- The absence of decoration is a design choice, not an oversight

**Avoiding:**
- Sportsbook UI patterns (odds-farm layouts, team-color hero banners)
- Stat-aggregator density (Baseball-Reference row-per-player spreadsheet)
- Fantasy sports dashboard patterns (player headshots, team logos dominating space)
- News/blog UX (cards with images, excerpts, timestamps as primary content)

---

## 10. Future Enhancement Opportunities

These represent aspirational capabilities — none are blocking the current build. All marked [NON-IMPLEMENTED CONCEPT].

### 10.1 Slate Heat Map [NON-IMPLEMENTED CONCEPT]

A top-of-slate visual grid: one cell per game, colored by escalation tier. Allows instant 2-second full-slate orientation before reading any card. Similar to a threat board in security operations.

```
[●] [●] [ ] [●] [ ] [●●] [ ] [ ] [●] [ ] [●] [ ]
 CR  EL  QT  EL  AC  DA   QT  AC  EL  QT  AC  EL
```

### 10.2 Correlation Cluster Visualization [NON-IMPLEMENTED CONCEPT]

In the Threat Cluster view, a visual diagram showing same-lineup batters as connected nodes. Strength of line = correlation factor. Operator can see at a glance if their portfolio is over-exposed to a single lineup.

### 10.3 Dynamic Escalation History [NON-IMPLEMENTED CONCEPT]

A mini timeline on each card showing how the pick's escalation level has changed since opening line. Did EV% rise as the market moved? Did it fall? This encodes line-movement intelligence visually without requiring the operator to read movement logs.

### 10.4 Deployment Session State [NON-IMPLEMENTED CONCEPT]

A persistent session-level tracker in the command strip: "Session: 3 deployed · $340 committed · 2 Critical · 1 Elevated." The operator has a running account of the current session's state without leaving the slate view.

### 10.5 Operator Dismissal Flow [NON-IMPLEMENTED CONCEPT]

For Critical and Dangerous cards: a deliberate dismissal action ("Skip this game — logged") rather than silent scroll-past. Creates an audit trail of intentional non-deployment decisions, which is operationally valuable for retrospective analysis.

### 10.6 Arsenal Fingerprint Badge [NON-IMPLEMENTED CONCEPT]

A 5-pixel-wide horizontal bar below the pitcher name showing pitch-mix danger profile — not a chart, just a colored band: `[FB%][SL%][CH%][CB%][CT%]` where each segment's saturation encodes the HVY modifier component. Completely optional supplemental signal, never replacing the factor score.

### 10.7 Predictive Escalation Indicator [NON-IMPLEMENTED CONCEPT]

For games where lineup is TBD: a "potential escalation" state — shown in a different visual treatment (dashed border rather than solid) — indicating the card could escalate once the lineup confirms. Prevents operator from deprioritizing a game prematurely.

### 10.8 Portfolio Exposure Overlay [NON-IMPLEMENTED CONCEPT]

An overlay mode on the slate (toggle in command strip) that dims cards based on current session exposure. If the operator has already deployed heavily on NYY batters, the NYY card dims slightly — visual budget management without math.

---

## Appendix A: Data Model Alignment

The following existing v4 fields map to UX elements in this doctrine:

| UX Element | Source Field | Module |
|---|---|---|
| Model probability | `model_prob` | `engine/probability.py` |
| EV% pill | `ev_pct` | `engine/ev.py` |
| Edge% | `edge_pct` | `engine/ev.py` |
| Rank number | `rank` | `output/ranker.py` |
| Lineup spot | `lineup_spot` | `clients/mlb_stats.py` |
| Pitcher factor | `pitcher_factor` | `engine/probability.py` |
| Park factor | `park_factor` | `data/park_factors.py` |
| Barrel % | `barrel_pct` | `clients/statcast.py` |
| Power multiplier | `statcast_power_mult` | `engine/probability.py` |
| Bet size | `bet_dollars` | `engine/sizing.py` |
| Confidence | `confidence` | `output/ranker.py` |
| Soft flags | `soft_flags` | `engine/filters.py` |
| HVY modifier | `hvy_modifier` | `clients/pitch_mix.py` |
| Best odds | `best_american` | `clients/odds_api.py` |
| Market prob | `market_no_vig_prob` | `engine/market.py` |
| Composite score | `score` | `output/ranker.py` |

---

## Appendix B: Escalation Classification Logic (Conceptual)

**[NON-IMPLEMENTED — Conceptual reference only]**

```python
# Conceptual only — not to be implemented without Codex coordination

def classify_escalation(batter: dict) -> str:
    ev = batter.get("ev_pct", 0)
    edge = batter.get("edge_pct", 0)
    barrel = batter.get("barrel_pct", 0) * 100  # normalize
    model = batter.get("model_prob", 0) * 100

    if ev >= 25 and edge >= 12 and barrel >= 12:
        return "CRITICAL"
    if ev >= 20 and edge >= 8 and barrel >= 10:
        return "DANGEROUS"
    if ev >= 15 or edge >= 8 or barrel >= 10 or model >= 18:
        return "ELEVATED"
    if batter.get("qualifies", False):
        return "ACTIVE"
    return "QUIET"

def classify_game_card(game_batters: list[dict]) -> str:
    # Game card escalation = highest batter escalation in game
    hierarchy = ["CRITICAL", "DANGEROUS", "ELEVATED", "ACTIVE", "QUIET"]
    levels = [classify_escalation(b) for b in game_batters]
    for level in hierarchy:
        if level in levels:
            return level
    return "QUIET"
```

---

*Document produced for planning purposes only. No runtime systems modified. No commits made. Codex ownership of runtime stabilization systems fully preserved.*
