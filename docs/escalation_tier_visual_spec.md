# Escalation Tier Visual Specification
## MLB HR Engine — Tactical Escalation Language

**Version:** 1.0  
**Date:** 2026-05-20  
**Phase:** Claude Step 2/12 — Visual Doctrine Stabilization  
**Status:** Specification only. No runtime code modified.

---

## Overview

The escalation tier system is the primary visual intelligence layer of the MLB HR Engine. It converts model probability output into an immediately readable signal that an operator can act on without reading labels.

**Design principle:** Escalation must feel tactical and believable. Not alarming. Not decorative. Not gamified. A professional analyst looking at a FIRE-tier pick should feel the same way they would looking at a "market inefficiency confirmed" signal in a trading terminal — elevated focus, not excitement.

**Five tiers:**

| Tier   | Word        | Color Family  | Emotional Register         |
|--------|-------------|---------------|---------------------------|
| T1     | FIRE        | Amber / Gold  | High-alert readiness       |
| T2     | STRONG      | Cyan / Ice    | Elevated confidence        |
| T3     | WATCH       | White / Muted | Neutral attention hold     |
| T4     | COLD        | Steel / Gray  | Suppressed, stand down     |
| T5     | VOID        | Deep Gray     | Invalid, no signal         |

---

## Tier Visual Rules

---

### T1 — FIRE

**Definition:** Elite barrel batter in favorable context. All filters passed. EV ≥ threshold. High confidence. Top-of-slate deployment pick.

**Glow Intensity:**  
- Badge border: 8px amber glow (`#F5A623`, 90% opacity, spread 8px, blur 16px)  
- Ambient behind score number: 40px radial amber glow, 25% opacity  
- Card border: 1px solid amber (`#F5A623`) + 12px outer glow at 40% opacity  
- No inner glow — glow is external only

**Border Behavior:**  
- 1px solid amber on all four sides  
- 12px outer glow halo  
- No dash, no animation on border itself  
- COMPACT state: left border only at 3px amber, no halo

**Typography Emphasis:**  
- Score number: 64px bold, white (`#FFFFFF`)  
- Tier word "FIRE": 18px uppercase tracking +0.15em, amber (`#F5A623`)  
- Stat values: 14px medium, white  
- Percentile labels: 10px uppercase, amber 60% opacity

**Animation Allowance:**  
- Score badge: 1-second slow pulse on initial card load only (fade in from 0 to 100% glow intensity)  
- No continuous pulse, no flash, no bounce  
- Live data refresh: subtle 0.3s border opacity pulse when data updates (40%→100%→70%)  
- Card enter animation: 0.2s fade-up from 8px below final position

**Density Adjustments:**  
- Full three-zone layout: hero | body | tail  
- Hero zone active: player action image rendered at full resolution  
- All stat clusters visible at STANDARD state (no hidden stats)

**Badge Treatment:**  
- Capsule shape, 24px height, amber fill at 15%, amber border 1px  
- Text: "FIRE" in amber, uppercase  
- Confidence number adjacent: "91" in white bold, 16px  
- Small lightning icon prefix: ⚡ (optional at T1 only)

**Background Treatment:**  
- Card surface: `#0D1525` (slight blue-tint near-black)  
- Hero zone background: radial amber gradient bleed behind player image (0% center, ambient edge)  
- No solid color fills for any zone  

**Interaction Behavior:**  
- COMPACT: click expands inline to STANDARD  
- STANDARD: amber expand-to-full icon at top-right corner  
- EXPANDED: modal with full-depth view  
- Hover: 0.15s border brightens to 100% opacity, cursor pointer

**Operator Attention Expectation:**  
Operator will notice T1 cards first in any list, even without intentional search. The amber glow creates a peripheral pull that draws the eye. T1 cards in a Full Slate list view must be distinguishable from 2 meters away.

---

### T2 — STRONG

**Definition:** Above-average power profile. All filters passed. Positive EV. High confidence but below elite tier.

**Glow Intensity:**  
- Badge border: 6px cyan glow (`#00D4FF`, 70% opacity, spread 6px, blur 12px)  
- Ambient behind score: 30px radial cyan glow, 15% opacity  
- Card border: 1px solid cyan (`#00D4FF` at 60%) + 8px outer glow at 25% opacity

**Border Behavior:**  
- 1px solid cyan at 60% opacity on all four sides  
- 8px subtle outer glow  
- COMPACT state: left border at 2px cyan, no halo

**Typography Emphasis:**  
- Score number: 48px bold, white  
- Tier word "STRONG": 16px uppercase tracking +0.12em, cyan (`#00D4FF`)  
- Stat values: 14px medium, white  
- Percentile labels: 10px uppercase, cyan 50% opacity

**Animation Allowance:**  
- Card load: 0.2s fade-up, no glow pulse  
- Live refresh: 0.2s border opacity pulse (30%→80%→50%)  
- No continuous animation

**Density Adjustments:**  
- Standard three-zone layout  
- Hero zone: player image at 80% scale (slightly compressed vs T1)  
- All stat clusters at STANDARD state  

**Badge Treatment:**  
- Capsule shape, 22px height, cyan fill 10%, cyan border 1px  
- Text: "STRONG" in cyan, uppercase  
- Confidence adjacent: white bold 15px

**Background Treatment:**  
- Card surface: `#0D1525`  
- Hero zone background: subtle cyan radial bleed, 8% opacity  

**Interaction Behavior:**  
- Same expand pattern as T1  
- Hover: 0.15s border brightens

**Operator Attention Expectation:**  
T2 cards are the workhorse tier — the majority of daily picks. Operator identifies them quickly but T1 cards will always pull first. T2 must be clearly distinguishable from T3 at a glance without reading the tier word.

---

### T3 — WATCH

**Definition:** Marginal EV. Caution flags present (approaching filter thresholds, borderline park factor, moderate pitcher suppressor). Not recommended for deployment without review.

**Glow Intensity:**  
- No badge glow  
- No card border glow  
- Card border: 1px solid white at 25% opacity

**Border Behavior:**  
- 1px solid white at 25% opacity  
- COMPACT: left border 2px white at 25%, no halo  
- No glow, no pulse

**Typography Emphasis:**  
- Score number: 36px medium weight, white at 80% opacity  
- Tier word "WATCH": 14px uppercase, white at 60% opacity  
- Stat values: 13px medium, white at 80%  
- Percentile labels: 10px, white at 40%

**Animation Allowance:**  
- No animation  
- Card load: 0.15s simple fade-in  
- No refresh pulse

**Density Adjustments:**  
- Two-zone layout only: body | tail (no hero image)  
- Hero zone suppressed by default  
- Only priority stats visible at STANDARD: HR prob, EV, barrel, pitcher signal  
- Caution flags visible as text badges: "MARGINAL EV", "APPROACHING THRESHOLD"

**Badge Treatment:**  
- Capsule shape, 20px height, no fill, white border 1px at 40%  
- Text: "WATCH" in white at 60%, uppercase  
- Confidence: white at 50%, 14px  
- Caution flag badge: amber at 40% fill, amber border, text "⚠ CAUTION FLAG"

**Background Treatment:**  
- Card surface: `#0D1525` (same as other tiers — no distinct background)  
- No gradient bleed

**Interaction Behavior:**  
- Expandable same as T1/T2 but expand icon in white at 40% opacity  
- EXPANDED state shows caution reason in explicit text block: "FILTER CAUTION: Park factor at threshold (0.88 vs 0.87 floor)"

**Operator Attention Expectation:**  
T3 cards should recede visually. In a mixed-tier list, operator's eye should not land on WATCH cards before FIRE or STRONG cards. T3 is a peripheral layer — visible but not demanding.

---

### T4 — COLD

**Definition:** Suppressed pick. Failed one or more filters: park penalty, pitcher K/GB suppressor, weather threshold, below PA minimum, weak power profile. Do not deploy.

**Glow Intensity:**  
- No glow anywhere  
- Negative signal: all surfaces at reduced luminance

**Border Behavior:**  
- 1px dashed, white at 15% opacity  
- COMPACT: left border 2px dashed, white at 15%  
- Dashed border is the deliberate Cold signal — dashed = discontinuous = suppressed

**Typography Emphasis:**  
- Score number: 30px light weight, white at 50% opacity  
- Tier word "COLD": 13px uppercase, white at 40% opacity — or use steel-blue `#7A8FA6`  
- Stat values: 13px, white at 60%  
- Suppressor reason: prominently labeled in text, not buried

**Animation Allowance:**  
- No animation whatsoever  
- Card load: simple appear, no transition

**Density Adjustments:**  
- Minimal layout: COMPACT state only by default  
- No hero image  
- No full stat clusters  
- Primary visible content: player name + "SUPPRESSED BY: [reason]" block  
- Expand available but defaults to collapsed

**Badge Treatment:**  
- Capsule shape, 18px height, no fill, white border 1px at 20%  
- Text: "COLD" in steel-blue at 60%, uppercase  
- Suppressor badge: red-orange at 20% fill, border 1px, text label: "PARK PENALTY" / "K/GB SUPPRESSOR" / "WEATHER CAP" / etc.

**Background Treatment:**  
- Card surface: `#0A0C14` (slightly darker than standard — negative signal)  
- No gradient, no glow, no image

**Interaction Behavior:**  
- Click expands to show suppressor reason in detail  
- No EXPANDED state / no full modal  
- No quick pick action available on COLD cards

**Operator Attention Expectation:**  
COLD cards must be visually subordinate to all other tiers. In a long Full Slate list, COLD cards should be filterable but visible (so operator knows why a player is excluded). The dashed border is the key signal — it communicates "this line is inactive" without requiring any label to be read.

---

### T5 — VOID

**Definition:** Invalid card state. Player did not start (DNP), lineup scratched, game postponed, filter hard failure, data unavailable.

**Glow Intensity:**  
- None

**Border Behavior:**  
- 1px dashed, white at 10% opacity (near-invisible)  
- Or: no border at all (flat rectangle)

**Typography Emphasis:**  
- Player name: white at 30% opacity (ghost text)  
- Tier word "VOID": 12px, white at 25% opacity  
- Reason text: "DNP — NOT IN LINEUP" / "POSTPONED" / "DATA UNAVAILABLE" in 11px white at 35%

**Animation Allowance:**  
- No animation  
- No load transition

**Density Adjustments:**  
- Minimum viable state: player name + void reason on a single line  
- No stats shown  
- No expand affordance  
- COMPACT only

**Badge Treatment:**  
- No badge, or single flat "VOID" label in minimal gray text

**Background Treatment:**  
- Card surface: `#090B12` (darkest surface level — recedes into page background)  
- Optionally: very subtle strikethrough pattern on surface (1px lines at 5% opacity)

**Interaction Behavior:**  
- No interaction  
- No hover state  
- No click target  
- VOID cards are informational tombstones only

**Operator Attention Expectation:**  
VOID cards must be visually invisible from 3+ feet away. An operator scanning the screen for deployment picks should not notice VOID cards at all — only if they specifically look for a missing player.

---

## Cross-Tier Summary Table

| Property              | FIRE (T1)            | STRONG (T2)          | WATCH (T3)           | COLD (T4)            | VOID (T5)            |
|-----------------------|----------------------|----------------------|----------------------|----------------------|----------------------|
| Badge glow            | 8px amber            | 6px cyan             | None                 | None                 | None                 |
| Card border           | 1px amber + halo     | 1px cyan + halo      | 1px white 25%        | 1px dashed white 15% | 1px dashed white 10% |
| Score size            | 64px bold            | 48px bold            | 36px medium          | 30px light           | —                    |
| Tier word color       | Amber #F5A623        | Cyan #00D4FF         | White 60%            | Steel blue 60%       | White 25%            |
| Hero image            | Yes, full            | Yes, 80%             | No                   | No                   | No                   |
| Animation             | Load pulse (1s)      | Fade-up              | Simple fade          | None                 | None                 |
| Default state         | STANDARD             | STANDARD             | COMPACT              | COMPACT              | COMPACT (read-only)  |
| Expand available      | Yes, full depth      | Yes, full depth      | Yes, caution detail  | Yes, reason only     | No                   |
| Background            | #0D1525 + amber bleed| #0D1525 + cyan bleed | #0D1525              | #0A0C14              | #090B12              |
| Peripheral visibility | High (immediate)     | Moderate-high        | Low                  | Very low             | None                 |

---

## Anti-Pattern Rejection List

These patterns are explicitly forbidden across all tiers and all views. They break the tactical believability requirement.

**REJECTED: Continuous flashing or pulsing on live data**  
Signal: every data update causes a visible flash on the affected number.  
Why rejected: looks like a consumer alert system. An operator watching 30 picks cannot track which stat changed. Use subtle border pulse on card-level update only.

**REJECTED: Full neon palette (pure #00FF00, #FF00FF, pure #0000FF)**  
Signal: bright saturated primaries for status colors.  
Why rejected: associate with gaming UI, not command centers. All glow colors must be desaturated by 20–30% from pure primary. Amber `#F5A623` not `#FFFF00`. Cyan `#00D4FF` not `#00FFFF`.

**REJECTED: More than two active glow colors in a single view**  
Signal: amber FIRE picks AND cyan STRONG picks AND green FAVORABLE environment AND red COLD picks all glowing simultaneously.  
Why rejected: glow loses signal value when everything glows. One primary glow color per view state. In a mixed-tier list: amber is the active glow. Cyan appears only when no amber cards are present.

**REJECTED: Score number larger than 72px**  
Signal: extremely large hero numbers that push other content off-screen.  
Why rejected: the number must fit within the card zone without scrolling. 64px is the maximum for T1 at STANDARD state.

**REJECTED: Equal visual weight across tiers in list view**  
Signal: uniform card height, uniform badge size, uniform opacity for all five tiers.  
Why rejected: the entire purpose of the tier system is destroyed. Tiers must have different visual weights in list views. FIRE cards must be taller than COLD cards.

**REJECTED: Animated tier transitions when a player's tier changes during a session**  
Signal: a WATCH pick gets promoted to STRONG mid-session with a glowing animation effect.  
Why rejected: mid-session tier changes should be subtle (border refresh pulse) not celebratory. Treat data refreshes as operational updates, not events.

**REJECTED: Negative space as a danger signal**  
Signal: empty white/black zones to indicate suppressed picks.  
Why rejected: empty space is ambiguous — could mean "loading" or "no data" rather than "suppressed." Suppression must be explicitly labeled with a word + reason.

---

## Escalation in Context: Full Slate View

In Full Slate, all five tiers may appear simultaneously in a single scrolling list. The tier system must work in this compound view without breaking.

**Ordering rule:** FIRE → STRONG → WATCH → COLD → VOID (within each game container, and in the overall slate-level sort).

**Visual separation rule:** A visual divider (1px horizontal rule at 20% white opacity) must separate tier groups within a game container. FIRE and STRONG cards above the divider. WATCH, COLD, VOID below.

**Game container escalation:** The game card itself escalates when FIRE picks are inside it. A game with zero FIRE picks but 3 STRONG picks uses cyan card border. A game with no qualifying picks uses COLD game card treatment.

**Batch filter UI:** Operator must be able to filter Full Slate to show only T1+T2 (FIRE + STRONG). This removes WATCH/COLD/VOID entirely. Filter state is persistent for the session.

---

## Escalation in Context: Header Threat Ticker

The inning/live header bar (top of all views) shows the top 3 threats as a horizontal ticker:

```
[FIRE BADGE] OHTANI — LAD    [STRONG BADGE] JUDGE — NYY    [STRONG BADGE] DEVERS — BOS
```

- Badge size: 16px height, compact capsule
- Player name: 12px white bold
- Team: 10px gray
- Only T1 and T2 picks appear in ticker — T3 and below never surface here
- Ticker updates on live data refresh with 0.3s cross-fade

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
