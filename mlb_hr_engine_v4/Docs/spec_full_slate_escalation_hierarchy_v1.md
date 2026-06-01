# Full Slate Escalation Hierarchy & Battlefield Orchestration Doctrine
## MLB HR Engine v4 — Room 04 Full Slate Command System

**Phase:** 3A Step 02/10  
**Room:** 04 — Full Slate Command System  
**Date:** 2026-05-22  
**Status:** PLANNING / DOCTRINE ONLY — No runtime changes. No commits.  
**Cross-references:**
- `FULL_SLATE_UX_DOCTRINE.md` — Game card escalation levels, visual tokens, mobile doctrine
- `docs/full_slate_tactical_doctrine.md` — Operator workflow, threat clusters, alert philosophy
- `docs/escalation_tier_visual_spec.md` — Batter tier visual spec (FIRE/STRONG/WATCH/COLD/VOID)
- `docs/full_slate_parent_orchestrator_doctrine.md` — Orchestrator boundaries, ownership table
- `docs/spec_tcc_batters_table_doctrine_v1.md` — HR Threat icons (Elite/Dangerous/Active/Elevated/Monitor)

---

## Contents

1. [Three-Level Escalation Architecture](#1-three-level-escalation-architecture)
2. [Game Card Escalation Hierarchy](#2-game-card-escalation-hierarchy)
3. [Battlefield Scan Doctrine](#3-battlefield-scan-doctrine)
4. [Game Grouping Doctrine](#4-game-grouping-doctrine)
5. [Dangerous Game Isolation Doctrine](#5-dangerous-game-isolation-doctrine)
6. [Slate Compression Doctrine](#6-slate-compression-doctrine)
7. [Tactical Pacing Doctrine](#7-tactical-pacing-doctrine)
8. [Visibility Mode Doctrine](#8-visibility-mode-doctrine)
9. [Escalation Color & Icon Doctrine](#9-escalation-color--icon-doctrine)
10. [Validation Checklist](#10-validation-checklist)
11. [Codex Implementation Boundaries](#11-codex-implementation-boundaries)
12. [UX Anti-Patterns](#12-ux-anti-patterns)
13. [Runtime Contamination Risks](#13-runtime-contamination-risks)
14. [Final Orchestration Hierarchy Summary](#14-final-orchestration-hierarchy-summary)

---

---

# 1. Three-Level Escalation Architecture

## 1.1 The Problem

Three independent escalation hierarchies exist in the system. Each operates at a different scope. Mixing them is a contamination error. This section defines the boundaries precisely.

---

## 1.2 Level A — Game Card Escalation

**Scope:** Full Slate game card containers  
**Defined in:** `FULL_SLATE_UX_DOCTRINE.md`  
**Operating layer:** Game → game card → visual treatment

| Level | Label | Trigger |
|-------|-------|---------|
| A1 | CRITICAL | EV ≥25% AND Edge ≥12% AND Barrel ≥12% + favorable environment |
| A2 | DANGEROUS | EV ≥20% AND Edge ≥8% AND Barrel ≥10% |
| A3 | ELEVATED | EV ≥15% OR Edge ≥8% OR Barrel ≥10% OR Model ≥18% |
| A4 | ACTIVE | Qualified picks exist (pass all 7 filters). No extraordinary signal. |
| A5 | QUIET | No qualifying picks. Below all filter thresholds. |

**Derivation rule:** Game card escalation = highest batter escalation within that game.  
**Propagation direction:** Upward only. One CRITICAL batter elevates the game card. Neighboring games are unaffected.

---

## 1.3 Level B — Batter Card Tier

**Scope:** Individual batter cards in Full Slate expanded view  
**Defined in:** `docs/escalation_tier_visual_spec.md`  
**Operating layer:** Player → card → visual tier

| Tier | Label | Signal Condition |
|------|-------|-----------------|
| B1 | FIRE | Elite barrel in favorable context. All filters passed. EV ≥ threshold. Top deployment pick. |
| B2 | STRONG | Above-average power. All filters passed. Positive EV. High confidence below elite. |
| B3 | WATCH | Marginal EV. Caution flags. Approaching filter thresholds. Not recommended without review. |
| B4 | COLD | Failed one or more filters. Do not deploy. |
| B5 | VOID | Invalid. DNP, scratched, postponed, data unavailable. |

**Mapping to Level A:** B1 (FIRE) maps to A1/A2/A3 depending on EV/Edge magnitude. B2 (STRONG) maps to A3/A4. B3 (WATCH) maps to A4/A5. B4/B5 always map to A5.

---

## 1.4 Level C — HR Threat Icon

**Scope:** Batters Table columns, TCC display, compact row indicators  
**Defined in:** `docs/spec_tcc_batters_table_doctrine_v1.md`  
**Operating layer:** Batter row in tabular display

| Tier | Icon | Shape | Color | Barrel | Model Prob |
|------|------|-------|-------|--------|-----------|
| C1 | Elite | Diamond ◆ | Gold | ≥12% | ≥18% |
| C2 | Dangerous | Triangle ▲ | Red | ≥9% | ≥14% |
| C3 | Active | Filled circle ● | Blue | ≥6% | ≥10% |
| C4 | Elevated | Outline circle ○ | Amber | ≥4% | ≥7% |
| C5 | Monitor | Dash — | Gray | <4% | <7% |

---

## 1.5 Cross-Level Mapping

```
Level C (Icon)    →  Level B (Batter Card)  →  Level A (Game Card)
──────────────────────────────────────────────────────────────────
C1 Elite          →  B1 FIRE               →  A1/A2 CRITICAL/DANGEROUS
C2 Dangerous      →  B1/B2 FIRE/STRONG     →  A2/A3 DANGEROUS/ELEVATED
C3 Active         →  B2 STRONG             →  A3/A4 ELEVATED/ACTIVE
C4 Elevated       →  B3 WATCH              →  A4 ACTIVE
C5 Monitor        →  B3/B4 WATCH/COLD      →  A5 QUIET
```

**Non-contamination rule:** Level C icons NEVER replace Level A labels. Level A game card escalation NEVER drives Level C icon display. They are parallel systems serving different purposes at different scopes.

---

---

# 2. Game Card Escalation Hierarchy

Formally replaces any prior informal escalation ordering. All Full Slate implementations MUST respect this ordering.

## 2.1 Escalation Level Definitions

### CRITICAL (A1)

**Thresholds:** EV ≥25% AND Edge ≥12% AND Barrel ≥12% + favorable environment (park ≥1.05 OR weather ≥1.05)  
**Visual treatment:** Pinned to top of slate regardless of game start time. Full expanded state. Left-border `#b84040` + top-border `#b84040`. Surface `#1a0808`. PRIORITY badge in command strip.  
**Operator urgency:** Maximum. System interrupts passive scanning. Explicit deployment or dismissal required.  
**Collapse behavior:** Never auto-collapses. Sticky open.  
**Game sort order:** Position 1 (tied positions sorted by composite score of highest-ranked batter).

---

### DANGEROUS (A2)

**Thresholds:** EV ≥20% AND Edge ≥8% AND Barrel ≥10%  
**Visual treatment:** Expanded. Left-border `#b84040`. Background surface `#1c0e0e`. Batter rows with elevated text weight. Deployment zone visible.  
**Operator urgency:** High. Must review before session closes.  
**Collapse behavior:** Expanded by default. Operator can collapse manually; state is sticky.  
**Game sort order:** After all CRITICAL games.

---

### ELEVATED (A3)

**Thresholds:** EV ≥15% OR Edge ≥8% OR Barrel ≥10% OR Model ≥18% (any single condition)  
**Visual treatment:** Expanded by default. Left-border `#c8a035` (tactical amber). Background surface `#1e1a0e`. Batter row highlighted.  
**Operator urgency:** Medium. Review before session closes.  
**Collapse behavior:** Expanded by default. Collapsible.  
**Game sort order:** After all DANGEROUS games.

---

### ACTIVE (A4)

**Thresholds:** At least one batter passes all 7 filters. No extraordinary signal.  
**Visual treatment:** Default partially expanded (header + pitcher + top 1 batter visible). Subtle left-border accent `#4a7fa5` (steel blue). Normal text contrast.  
**Operator urgency:** Low. Review at leisure.  
**Collapse behavior:** Partially expanded by default. Full expand on click.  
**Game sort order:** After all ELEVATED games. Within ACTIVE, sort by game start time.

---

### QUIET (A5)

**Thresholds:** No qualifying picks in this game.  
**Visual treatment:** Collapsed (header only). Muted border `#3a3a3a` (dark gray). Text at 60% opacity. No accent color.  
**Operator urgency:** Zero.  
**Collapse behavior:** Fully collapsed by default. Operator must explicitly expand.  
**Game sort order:** Last. Hidden behind "Show X quiet games" toggle in default visibility mode.

---

## 2.2 Escalation Color Token System

These tokens are canonical. No deviation. Any implementation that uses colors outside this set is in violation of doctrine.

```css
--escalation-quiet:       #3a3a3a   /* Neutral dark gray */
--escalation-active:      #4a7fa5   /* Steel blue */
--escalation-elevated:    #c8a035   /* Tactical amber */
--escalation-dangerous:   #b84040   /* Tactical red (muted) */
--escalation-critical:    #8a0000   /* Deep red — border ring only */

--surface-quiet:          #141414
--surface-active:         #161820
--surface-elevated:       #1e1a0e
--surface-dangerous:      #1c0e0e
--surface-critical:       #1a0808

--text-primary:           #e8e8e8
--text-secondary:         #9a9a9a
--text-muted:             #5a5a5a
```

---

## 2.3 Animation Restraint Rules

- **One entry animation per card per session.** Not per scroll. Not per state change.
- **Entry animations are border-draws, not glows.** Border fills in 200–300ms. That's it.
- **Zero looping animations** at any escalation state, including CRITICAL.
- **Zero persistent pulsing** on any element visible for more than 5 seconds.
- **State transitions** (e.g., ACTIVE → ELEVATED on data refresh) are color swaps with a 150ms ease.

---

---

# 3. Battlefield Scan Doctrine

## 3.1 Operator Scan Sequence

The Full Slate is mission-control. Operators arrive with a finite decision window. The visual sequence enforces tactical priority.

```
[COMMAND STRIP]          ← Tier 1: Situational awareness in <1 second
        ↓
[ESCALATION SUMMARY]     ← "2 Critical · 3 Elevated · 7 Active" — one line
        ↓
[CRITICAL GAME CARDS]    ← Tier 2: Danger surfaced first — pinned, fully open
        ↓
[DANGEROUS GAME CARDS]   ← Tier 3: High-conviction plays — expanded
        ↓
[ELEVATED GAME CARDS]    ← Tier 4: Worth deployment consideration
        ↓
[ACTIVE GAME CARDS]      ← Tier 5: Qualified picks, no extraordinary signal
        ↓
[QUIET GAMES TOGGLE]     ← Hidden by default — "Show X quiet games" at bottom
```

**The command strip must answer these in under 1 second:**
- How many live/pre-game games are on the slate?
- Are any games in CRITICAL or DANGEROUS state?
- Active weather threats?
- Current pipeline freshness (last sync timestamp)?

---

## 3.2 Top-Down Scan Flow Rules

1. **Escalated games appear ABOVE the fold** on desktop at standard viewport sizes — always.
2. **No hero images, logos, or decoration above the fold** — every pixel conveys state.
3. **If zero escalations exist**, the operator sees this immediately — the slate FEELS quiet. No false urgency.
4. **Scan must complete in 90 seconds** for a 12-game slate. If not achievable, the slate is too noisy.

**90-Second Recon Standard:**
- 0–15s: Command strip reading
- 15–30s: CRITICAL/DANGEROUS card review (at most 2–3 cards)
- 30–60s: ELEVATED card scan
- 60–75s: ACTIVE card headers (peripheral)
- 75–90s: Deployment decision

---

## 3.3 Danger Cluster Surfacing

When multiple qualifying batters exist in one game, the game card surfaces a stack indicator:

```
  [TOP 2 VISIBLE]  ·  +3 more  ▼
```

Stack count is always truthful. Within stack, batters sort by composite score (EV×0.4 + Edge×0.35 + Confidence×0.25 — matching existing ranker logic). Best play first, always.

**Cluster types that propagate to command strip:**
- 3+ picks in same game → game card shows stack count
- Same pitcher targeted by 3+ picks → "targeted" indicator in expanded pitcher row
- Weather factor ≥1.08 with multiple picks → weather flag in command strip

---

---

# 4. Game Grouping Doctrine

## 4.1 Game Card Information Priority Order

Each game card presents information in strict hierarchy. Higher-priority fields CANNOT be displaced by lower-priority fields.

```
Priority 1: Game identity     — Teams, Time, Escalation badge
Priority 2: Pitcher danger    — SP name + handedness + pitcher_factor + fatigue
Priority 3: Top batter(s)     — Best 1-2 qualifying batters: EV%, rank, lineup spot
Priority 4: Environmental     — Park (extreme only) + weather (threat only)
Priority 5: Market context    — Best odds, implied probability delta
Priority 6: Expansion handle  — "See all X batters / pitcher detail / arsenal"
```

Priority 1–3 visible in collapsed state.  
Priority 4–6 appear on expand.

---

## 4.2 Collapse / Expand Defaults by Escalation Level

| Level | Default State | Expand Trigger | Auto-Collapse? |
|-------|---------------|----------------|----------------|
| CRITICAL | Fully open + pinned | N/A — always open | Never |
| DANGEROUS | Expanded + deployment zone | Already open | No — sticky |
| ELEVATED | Expanded (P1–P4 visible) | Already open | Operator only |
| ACTIVE | Partially expanded (P1–P3) | Click card body | No |
| QUIET | Collapsed (header only) | Explicit click | Yes — on refresh |

---

## 4.3 Game Separation Hierarchy

Games are grouped and separated as follows:

1. **Escalation tier dividers:** Thin 1px horizontal rule at 20% white opacity between tier groups (e.g., between last DANGEROUS card and first ELEVATED card).
2. **Within-tier separation:** 8px vertical gap between cards of same escalation level.
3. **QUIET separator:** A single "Show X quiet games ▾" toggle element separates active slate from quiet games.
4. **No team-color grouping** — team colors have no tactical meaning in this context.

---

## 4.4 Pitcher Attribution Clarity

From Session 39 doctrine — use `AWAY bats vs pitcher` not `AWAY → pitcher`. Directional arrow was ambiguous.

**Home batter rows:** face the away team's starting pitcher.  
**Away batter rows:** face the home team's starting pitcher.  
**TBD pitcher:** amber warning on that card. Card may still escalate based on batter profile alone.

---

## 4.5 Environmental Visibility Rules

Environmental signals are SUPPRESSED when neutral. Only render when:

- Park factor ≥1.08 → `HITTER PARK` badge (green)
- Park factor ≤0.93 → `PITCHER PARK` badge (red-muted)
- Wind ≥8mph toward CF → `WIND: 10mph IN` (amber)
- Wind ≥8mph away from CF → `WIND: 10mph OUT` (green)
- Temp ≤45°F → `COLD: 41°F` (blue-muted)
- Dome → render nothing. Dome teams have no weather exposure.

Do NOT show "Neutral environment." Do NOT show "Conditions nominal." The absence of an environmental badge means conditions are neutral — the operator does not need to be told nothing is happening.

---

---

# 5. Dangerous Game Isolation Doctrine

## 5.1 What Makes a Game Dangerous

A game achieves DANGEROUS or CRITICAL escalation when one or more of these stacking conditions are met:

**Primary triggers (any one sufficient for ELEVATED):**
- Top batter EV ≥15%
- Top batter Edge ≥8%
- Top batter Barrel ≥10%
- Model probability ≥18%

**Escalation stacks to DANGEROUS (require combination):**
- EV ≥20% AND Edge ≥8% AND Barrel ≥10%
- OR: stacked mutual pitcher vulnerability — pitcher_factor ≥1.25 with 2+ qualified batters

**Escalation stacks to CRITICAL (require convergence):**
- EV ≥25% AND Edge ≥12% AND Barrel ≥12%
- AND: favorable environment (park ≥1.05 OR weather factor ≥1.05)

---

## 5.2 Stacked HR Environment Definition

A "stacked HR environment" exists when three or more independent amplifying signals align in one game:

| Signal Layer | Escalation Condition |
|---|---|
| Batter power | Barrel ≥10% + FB% ≥28% |
| Pitcher vulnerability | pitcher_factor ≥1.20 |
| Park amplification | park_factor ≥1.06 |
| Weather amplification | weather_factor ≥1.05 |
| Line movement | Sharp-side money on Over |
| Lineup position | Batter in spots 2–5 |

**Two layers = ELEVATED. Three layers = DANGEROUS. Four+ layers = CRITICAL.**

This stacking philosophy prevents single-signal false escalations while surfacing genuinely convergent opportunities.

---

## 5.3 Mutual Pitcher Vulnerability

A game may escalate even without elite individual batter signals if the pitcher faces clustered vulnerability:

- Same pitcher targeted by 3+ qualified batters (not just visible in lineup — qualified through filters)
- Pitcher fatigue indicator (short rest ≤4 days)
- Pitcher K/GB suppressor at low level (GB-dominant pitcher typically suppresses HRs — absence of this = no suppression)

Mutual vulnerability is shown in expanded pitcher row only. It does NOT show on collapsed card.

---

## 5.4 Isolation Logic

CRITICAL and DANGEROUS games are visually isolated from the rest of the slate through:

1. **Positional isolation** — pinned to top of view (CRITICAL), above all time-ordered cards
2. **Surface isolation** — darker, warmer surface colors (#1a0808, #1c0e0e)
3. **Border isolation** — left-border color + glow (one slow pulse on arrival, then static)
4. **Density isolation** — more information visible at default state than lower-tier cards

CRITICAL games receive an additional **top-border** ring. This is the only card type with four-sided border treatment.

---

## 5.5 Escalation Stacking Visuals

The escalation badge on each card shows the GAME-level escalation. The batter rows within the card show individual batter-level FIRE/STRONG/WATCH/COLD tiers. These two systems coexist on the same card without conflict because they operate at different hierarchy levels.

**Example:** A DANGEROUS game card may contain:
- Row 1: B1 FIRE batter (the trigger batter)
- Row 2: B2 STRONG batter
- Row 3: B3 WATCH batter
- Game card = DANGEROUS (from the B1 trigger)

The DANGEROUS badge appears on the game card header. The FIRE/STRONG/WATCH badges appear on individual batter rows within the expanded card.

---

---

# 6. Slate Compression Doctrine

## 6.1 Purpose

A 15-game slate would produce 200+ batter rows if rendered fully. Compression is not optional — it is a core operational requirement.

## 6.2 Compression Hierarchy

Information compresses from lowest-priority to highest. QUIET games are the first casualty.

**Compression levels:**

| Mode | What's Visible | Trigger |
|---|---|---|
| Default | CRITICAL + DANGEROUS expanded, ELEVATED expanded, ACTIVE partially shown, QUIET hidden | Initial load |
| Escalation-only | CRITICAL + DANGEROUS only — all others hidden | Operator toggle or filter |
| All games | Full slate including QUIET | Explicit "Show all" action |

---

## 6.3 Compression Rules (Hard)

- **Avoid giant vertical walls.** No more than 5 consecutive cards of same escalation tier without a visual separator.
- **Avoid endless card repetition.** Each card must communicate its tier in the first 2–3 lines without repetition from the card above.
- **Avoid duplicate information.** If game time appears in the card header, it does not appear again in the body. If EV appears on the batter row, it does not appear again in the expansion handle.
- **Preserve tactical pacing.** QUIET games must not occupy vertical space proportional to their tactical irrelevance. They are compressed to a single toggle line at the bottom.
- **Badge restraint by state:**

| Card State | Max Badges |
|---|---|
| QUIET, collapsed | 0 |
| ACTIVE, collapsed | 1 (escalation badge only) |
| ELEVATED, collapsed | 2 (escalation + one signal) |
| DANGEROUS/CRITICAL, expanded | 3 (escalation + barrel tier + environmental) |
| Deployment briefing zone | Unlimited within zone |

---

## 6.4 Full Slate Mode Compression

The current app implements three visibility modes (from Session 37):

| Mode | Pool | Filter Behavior |
|---|---|---|
| All Players | `all_players` — full slate | Filters highlight, do NOT remove |
| Qualified | `_tac_ranked` — TCC-filtered | Filters remove. Only qualified picks visible. |
| Elite Targets | barrel ≥8% from `all_players` | Highlights + escalation ordering |

**In All Players mode:** Compression means row background signals importance (tac-qualified=#0f0f1a, sidebar-qual=#0a0a12, no-odds=#080808). Rows are not removed. The operator sees the full battlefield but escalation is encoded in background density.

**In Qualified mode:** Compression is achieved by the filter system. Only picks passing all 7 filters render.

**In Elite Targets mode:** Compression is achieved by barrel threshold + escalation ordering.

---

---

# 7. Tactical Pacing Doctrine

## 7.1 Visual Breathing Rhythm

The Full Slate must breathe. Dense → focused → dense is the rhythm of an operational briefing, not a data wall.

**Rhythm pattern:**
1. Command strip (high density — all summary info in one bar)
2. CRITICAL game card (focused — one game, deep detail)
3. DANGEROUS game card (medium density)
4. [visual separator — 1px rule]
5. ELEVATED game cards (medium density)
6. [visual separator]
7. ACTIVE game cards (lower density — top batter only visible)
8. [quiet games toggle line]

The separator lines at tier transitions are the "breath" — the pause between operational clusters.

---

## 7.2 Escalation Rhythm

Escalation is a crescendo. The operator should feel increasing urgency as they move down from QUIET to CRITICAL. This means:

- QUIET cards: minimum visual mass. Almost invisible.
- ACTIVE cards: clear but not demanding.
- ELEVATED cards: pulls the eye. Amber border is warm.
- DANGEROUS cards: commands attention. Red surface. Information-dense.
- CRITICAL cards: cannot be ignored. Pinned. Maximum visual weight.

The rhythm is: **whisper → speak → alert → command → demand**.

---

## 7.3 Investigation Pacing

When the operator drills into a game card, the pacing shifts:

- Card expand: 120–150ms ease-out. Not instant (would feel jarring). Not slow (would feel sluggish).
- Arsenal detail: expand-on-demand only. Never auto-expanded.
- Deployment briefing: requires explicit entry into Focus Mode. Cannot be accidentally triggered.

**Decision cycle target:** Operator should be able to make a confident deployment decision within 120 seconds of opening a pick.

---

## 7.4 Hierarchy Transitions

Between expansion levels (Slate → Game → Player → Arsenal → Deployment), visual transitions must:

- Always be directional (forward = expanding, back = compressing)
- Never lose prior context (game header persists at each level)
- Never teleport (always one level at a time, back-chevron available)

---

---

# 8. Visibility Mode Doctrine

## 8.1 Modes

Four operator-accessible visibility modes:

| Mode | What's Shown | Filter Effect | Access |
|---|---|---|---|
| Default | CRITICAL/DANGEROUS/ELEVATED expanded, ACTIVE partial, QUIET hidden | Escalation-ordered | Initial load |
| Dangerous Only | CRITICAL + DANGEROUS cards only | All others hidden | Command strip toggle |
| Elite Only | Games with barrel ≥10% batters | Others hidden | Command strip toggle |
| All Games | Full slate including QUIET | QUIET visible | "Show all games" action |

---

## 8.2 Compact Mode

Compact mode reduces each card to a single-line summary:

```
[ESCALATION DOT] AWAY @ HOME   TIME   [TOP BATTER: EV%]   [BADGE]
```

Compact mode is useful for rapid re-scan after deep investigation. Operator returns to compact to re-orient.

**Compact mode rules:**
- All cards same height (exception to normal tier-height hierarchy)
- Escalation dot (color-coded) left of team names — no text label, dot color sufficient
- Only top batter's EV% shown — no pitcher, no park, no weather
- One badge maximum (escalation level label)
- Click on compact row → expands to full card inline

---

## 8.3 Visibility Non-Contamination Rule

**Visibility changes NEVER alter underlying calculations.**  
**Visibility changes NEVER mutate tactical state.**

Specifically:
- Hiding a game card does NOT remove its batters from `ranked`, `all_players`, or any scoring pools.
- Filtering to "Elite Only" does NOT change composite scores or filter thresholds.
- Compact mode does NOT invalidate card HTML caches (fingerprints unchanged).
- Mode switches do NOT trigger pipeline re-runs.

This is the immutable visibility contract. Violating it is a runtime contamination event.

---

## 8.4 Mobile Visibility Hierarchy

On mobile (viewport ≤768px):

```
[COMMAND STRIP — sticky]
[ESCALATION SUMMARY — 1 line]
[CRITICAL CARDS — full width stacked]
[ELEVATED CARDS — full width stacked]
[ACTIVE CARDS — collapsed by default]
[Show X quiet games ▾]
```

Mobile cards use progressive disclosure (Level 1 → Level 2 → Level 3) via tap.  
Level 1: header + top batter only.  
Level 2: P1–P4 visible (pitcher + environment added).  
Level 3: full arsenal + deployment zone.

**Quiet games are hidden by default on mobile.** Accessible only via explicit toggle.

---

---

# 9. Escalation Color & Icon Doctrine

## 9.1 Icon Shape Hierarchy

Shape communicates before color. Operator peripheral vision reads shape in <100ms. Color alone requires focused attention.

**Full Slate game card icons (Level A):**

| Level | Shape | Behavior |
|---|---|---|
| CRITICAL | Solid red square ■ | Static after 1 entry pulse |
| DANGEROUS | Solid red triangle ▲ | Static after 1 entry animation |
| ELEVATED | Filled amber circle ● | Static |
| ACTIVE | Outline blue circle ○ | Static |
| QUIET | Dash — | Static, dim |

**Batter card tier icons (Level B):**

| Tier | Shape | Color |
|---|---|---|
| FIRE | ⚡ (optional) + capsule badge | Amber `#F5A623` |
| STRONG | Capsule badge only | Cyan `#00D4FF` |
| WATCH | Capsule badge only | White 60% |
| COLD | Dashed capsule | Steel blue 60% |
| VOID | None | — |

**Batters Table HR Threat icons (Level C — fixed from Session 05):**

| Tier | Shape | Color |
|---|---|---|
| Elite | Diamond ◆ | Gold |
| Dangerous | Triangle up ▲ | Red |
| Active | Filled circle ● | Blue |
| Elevated | Outline circle ○ | Amber |
| Monitor | Dash — | Gray |

---

## 9.2 Color Hierarchy Doctrine

**Primary signal colors (exclusive use — never for decoration):**
- Amber `#c8a035` / `#F5A623` → escalation (ELEVATED, FIRE)
- Tactical red `#b84040` → danger (DANGEROUS, CRITICAL)
- Steel blue `#4a7fa5` → active qualification
- Cyan `#00D4FF` → STRONG tier (player cards only)
- Gold / warm yellow → Elite tier (C1 icon only)

**Prohibited:**
- Gradient fills on card surfaces (no exceptions)
- Neon (lime green, electric blue, hot pink)
- More than 3 simultaneous accent colors in a single card
- Orange (too sportsbook — use amber only)
- Bright red (use tactical red `#b84040` only)

---

## 9.3 Glow Restraint

Glow is a signal, not a style choice.

**Permitted glow:**
- FIRE batter cards: 8px amber glow on badge border. 12px outer halo on card border.
- STRONG batter cards: 6px cyan glow on badge border. 8px outer halo.
- CRITICAL game cards: top-border ring. No additional glow.
- DANGEROUS game cards: left-border only. No halo.

**Prohibited glow:**
- Looping glow pulses on any element
- Inner glows on any surface
- Glow on WATCH, COLD, QUIET cards
- Glow on Level C (HR Threat) icons in Batters Table
- Simultaneous amber AND cyan glow on same view

**Glow restraint philosophy:** In a mixed-tier list, only amber is the active glow. Cyan appears only when no amber cards are present. A view where everything glows is a view where nothing glows.

---

## 9.4 Row Highlighting

**Game card row backgrounds (Full Slate compact rows):**
- Tac-qualified: `#0f0f1a`
- Sidebar-qual (secondary): `#0a0a12`
- No odds: `#080808`
- Not qualified: no background change

**Batter tier row highlighting (within expanded game card):**
- FIRE batter: left-margin vertical bar matching `#b84040`/`#c8a035` per escalation level
- STRONG batter: left-margin bar in steel blue `#4a7fa5`
- WATCH batter: muted contrast, no left-margin bar
- COLD batter: muted, no bar

---

---

# 10. Validation Checklist

## 10.1 Escalation Ordering

- [ ] CRITICAL games appear before DANGEROUS games regardless of start time
- [ ] DANGEROUS games appear before ELEVATED games regardless of start time
- [ ] ELEVATED games appear before ACTIVE games regardless of start time
- [ ] QUIET games are hidden by default (accessible via toggle only)
- [ ] Within same escalation tier, games sort by start time
- [ ] CRITICAL games are pinned (do not reorder on manual sort)
- [ ] Escalation level = highest batter escalation in game, not average

## 10.2 Game Card Grouping

- [ ] Tier-boundary dividers (1px rule) present between DANGEROUS→ELEVATED, ELEVATED→ACTIVE
- [ ] Game card shows escalation badge right-aligned in header row
- [ ] Pitcher attribution uses "bats vs pitcher" format, not arrow
- [ ] Environmental badges suppressed when neutral (no "Conditions nominal" text)
- [ ] TBD pitcher shows amber warning on that card

## 10.3 Collapse / Expand Behavior

- [ ] CRITICAL cards: always open, never auto-collapse
- [ ] DANGEROUS cards: expanded by default, manually collapsible
- [ ] ELEVATED cards: expanded by default
- [ ] ACTIVE cards: partially expanded (P1–P3 visible)
- [ ] QUIET cards: fully collapsed by default
- [ ] Collapse state is sticky (survives non-data rerenders)
- [ ] Cards do NOT auto-collapse on data refresh (only on full app reinitialize)

## 10.4 Dangerous Game Isolation

- [ ] DANGEROUS/CRITICAL cards use warmer surface colors (#1c0e0e / #1a0808)
- [ ] CRITICAL cards have top-border ring (four-sided border)
- [ ] DANGEROUS cards have left-border only (no top ring)
- [ ] Entry animation: one border pulse on arrival, then static — no loops
- [ ] Stacked HR environments (3+ signal layers) → DANGEROUS minimum

## 10.5 Visual Pacing

- [ ] Separator lines present at tier transitions
- [ ] Max 5 consecutive cards of same tier before separator
- [ ] Badge count enforced (0/1/2/3 max by state)
- [ ] QUIET toggle line at bottom (not spread throughout slate)

## 10.6 Readability

- [ ] Three typography levels only: Primary / Secondary / Tertiary
- [ ] No more than 3 type sizes per card
- [ ] Label compression applied (EV% not "Expected Value Percentage")
- [ ] Labels dim, values bright — operator reads values not labels
- [ ] Zero-redundancy rule: no data point appears twice in same card scope

## 10.7 Mobile Degradation

- [ ] Cards readable at viewport ≤768px without horizontal scroll
- [ ] Command strip compresses to single bar on mobile
- [ ] Escalation color survives reduced card height (header row tint)
- [ ] Quiet games hidden by default on mobile
- [ ] Progressive disclosure (3-tap expand) functional on mobile

## 10.8 Hover Behavior

- [ ] Hover brightens border (1px → 1.5px, opacity +10%) — no layout shift
- [ ] No panels expand on hover
- [ ] No data fetches triggered on hover
- [ ] Hover response <16ms (one frame)

## 10.9 Tactical Scan Flow

- [ ] First visible element: command strip
- [ ] Second visible element: first CRITICAL or DANGEROUS card
- [ ] Escalation badge right-aligned in every card header
- [ ] First batter EV% left-anchored after rank number
- [ ] 90-second recon achievable for 12-game slate
- [ ] No horizontal movement >20% of viewport required for primary scan path

---

---

# 11. Codex Implementation Boundaries

## 11.1 What Codex MAY Implement

Codex has safe implementation authority over:

- Full Slate game card ordering logic (escalation-first sort, by `classify_escalation()` output)
- `classify_escalation(batter: dict) -> str` helper function (CONCEPTUAL in `FULL_SLATE_UX_DOCTRINE.md` Appendix B — safe to implement as a NEW function)
- `classify_game_card(game_batters: list[dict]) -> str` helper function (same)
- Game card collapse/expand default state logic (read escalation level → set `expanded` bool)
- Escalation badge HTML rendering (color tokens, badge labels)
- Game card left-border and surface color from escalation level
- Batter row left-margin indicator bars
- Visibility mode radio selector (All Players / Qualified / Elite Targets already implemented in Session 37)
- Compact mode render path (single-line game rows)
- Tier-boundary divider HTML between escalation groups
- Environmental badge suppression logic (show only when threshold exceeded)
- Badge count enforcement (max 0/1/2/3 by card state)
- Command strip escalation summary counts

## 11.2 What Codex MAY NOT Touch

**PROTECTED — ABSOLUTE:**

| Zone | Module | Reason |
|---|---|---|
| Pipeline data flow | `pipeline.py` | Session 37 Codex boundary. Routing and hydration are frozen. |
| Session state routing | `app.py` tab routing | MAIN/JIG navigation continuity. Session 05 boundary. |
| Session state filter keys | `tcc_*` / `table_*` prefix | Session 05. Keys are fixed API. |
| Engine scoring | `engine/probability.py`, `engine/ev.py`, `engine/filters.py` | Scores and rankings are upstream. Display reflects them, never drives them. |
| Ranker output | `output/ranker.py` | `ranked` list order is sacred. Display never reorders the ranked list. |
| Portfolio optimizer | `portfolio/optimizer.py` | Session 27. Optimizer selection is display input, not display output. |
| Cache ownership | `@st.cache_data` functions | Invalidation logic is already fingerprinted. Do not add new cache keys without doctrine-level approval. |
| Hydration triggers | `_load_data()`, `pipeline.py` | Data loading is Codex-unsafe. |
| Pick tracking writes | `tracking/pick_tracker.py` | Deployment logging is an operational write — never triggered by display state changes. |
| HVY scoring | `clients/pitch_mix.py` | Display-only signal already. Never feed back into model_prob. |

**PROTECTED — DISPLAY SCOPE:**

| Restriction | Rule |
|---|---|
| No sorting of `ranked` list | Full Slate display may ORDER by escalation in the game-grouped view. It may NOT re-sort the underlying ranked list. |
| No filter mutation from visibility toggle | Toggling "Dangerous Only" view hides cards — it does NOT change `_tac_params` or filter thresholds. |
| No session_state writes from card HTML | Card HTML builders are pure render functions. Zero side effects. |
| No lazy-gate key collisions | New lazy-gate keys MUST include slate_ts anchor (pattern: `f"key_{player_id}_{slate_ts}"`) — per Session 44 Bug C |

---

## 11.3 Safe Implementation Zones

**New session_state keys allowed (must use these prefixes):**

| Prefix | Scope | Example |
|---|---|---|
| `fs_*` | Full Slate visibility state | `fs_mode_sel`, `fs_escalation_filter` |
| `_esc_*` | Escalation display state | `_esc_card_open_{game_pk}` |
| `_vis_*` | Visibility mode | `_vis_compact_active` |

**New helper functions allowed:**

- `classify_escalation(batter: dict) -> str` — pure function, no side effects, no session_state
- `classify_game_card(game_batters: list[dict]) -> str` — same
- `_game_escalation_sort_key(game: dict) -> tuple` — pure sort key function
- `_render_escalation_badge(level: str) -> str` — HTML string only, no state

---

---

# 12. UX Anti-Patterns

These patterns are explicitly prohibited. Any implementation exhibiting these patterns fails doctrine review.

## 12.1 Layout Anti-Patterns

| Anti-Pattern | Why Rejected | Correct Alternative |
|---|---|---|
| Spreadsheet rows with 12+ columns | Horizontal scroll breaks scan rhythm | Group signals by function, not by field name |
| All cards same height | Destroys visual priority differentiation | CRITICAL cards taller than QUIET cards |
| Infinite scroll for game cards | Operator loses position, misses games | Paginated groups by escalation tier |
| Tabs for Critical / Elevated / Active | Tabs hide content — cards surface it | Single scrolling slate with tier ordering |
| Giant whitespace between every card | Destroys tactical density | 8px gap within tier, 1px divider between tiers |
| Flat SaaS layout (equal weight everything) | No tactical differentiation | Apply escalation hierarchy rigorously |

## 12.2 Visual Anti-Patterns

| Anti-Pattern | Why Rejected |
|---|---|
| Continuous pulsing on any element | Operator reads the interface as broken |
| Looping glow on CRITICAL cards | One entry animation, then static |
| Team-color coding for escalation | Team colors have no tactical meaning |
| Emoji-based indicators (🔥 🔴) | Consumer sports app feel — not command center |
| HOT / TRENDING badges | Marketing language in operational context |
| Orange as a warning color | Sportsbook association — use amber only |
| Bright neon red (#FF0000) | Use tactical red #b84040 |
| Gradient fills on card surfaces | Decoration without signal value |

## 12.3 Interaction Anti-Patterns

| Anti-Pattern | Why Rejected |
|---|---|
| Modals for batter detail | Breaks context — use inline expansion |
| Pop-up overlays for environmental data | Tooltip-only data is mobile-hostile |
| Hover-triggered panel expansion | Accidental trigger risk |
| Auto-scroll to top on filter change | Operator loses position |
| Auto-collapse all cards on data refresh | Operator loses investigation state |
| Multi-step wizard for deployment | Single confirmation only — no wizard |

## 12.4 Data Anti-Patterns

| Anti-Pattern | Why Rejected |
|---|---|
| Showing "Neutral" for non-threatening signals | Adds noise; absence = neutral |
| Showing all stat columns in collapsed state | Priority 1–3 only; rest on expand |
| EV% and Edge% both visible in collapsed state | Edge summarizes the delta — show that alone |
| Displaying raw probability alongside calibrated | Show calibrated only; explanation on expand |
| "Loading..." placeholder cards | Uncertainty — use peripheral status only |

---

---

# 13. Runtime Contamination Risks

## 13.1 Definition

Runtime contamination occurs when a display-layer change mutates, interferes with, or bypasses a protected runtime system. The following patterns are the most common contamination vectors in Full Slate implementation.

---

## 13.2 Contamination Risk Catalog

### Risk 1: Escalation filter mutating `_tac_params`

**Description:** A "show only DANGEROUS+" visibility toggle inadvertently writes to `st.session_state["tac_min_ev"]` or other TCC filter keys.  
**Impact:** Changes the underlying filter thresholds for all tabs, not just Full Slate.  
**Prevention:** Visibility toggles write ONLY to `fs_*` or `_vis_*` prefixed keys. They never write to `tcc_*` or `table_*` keys.

---

### Risk 2: Game-card ordering resorting `ranked`

**Description:** Full Slate implements escalation-first ordering by mutating the `ranked` list.  
**Impact:** Breaks composite score ranking across all tabs. Elite tab, Quick View, and Portfolio all source from `ranked`.  
**Prevention:** Escalation ordering is applied to a COPY of the game-grouped view only. `ranked` list is read-only in all Full Slate code.

---

### Risk 3: Card HTML cache invalidated by visibility state

**Description:** `_CARD_CACHE` fingerprint includes visibility mode, causing HTML rebuilds on every mode switch.  
**Impact:** Defeats the card caching introduced in Session 41. 100+ HTML rebuilds on every mode toggle.  
**Prevention:** Card fingerprints are keyed on player data + slate_ts only. Visibility mode is NOT part of fingerprint.

---

### Risk 4: Lazy-gate keys without slate_ts anchor

**Description:** New pitch-mix or card lazy-gate keys lack `slate_ts` in their key name.  
**Impact:** Session 44 Bug C reoccurs — stale content served across date boundaries.  
**Prevention:** All new lazy-gate keys MUST include `slate_ts`. Pattern: `f"pm_loaded_{prefix}_{player_id}_{slate_ts}"`.

---

### Risk 5: Escalation badge writing to investigation_state

**Description:** Clicking an escalation badge inadvertently triggers a write to `investigation_state.py` or similar state tracking.  
**Impact:** Mutates operator investigation context without a deliberate drill-down action.  
**Prevention:** Escalation badge HTML is display-only. No Streamlit widget (no `st.button`, no `st.checkbox`) inside badge HTML. Badge click behavior is visual only.

---

### Risk 6: Mobile viewport detection triggering pipeline re-run

**Description:** A viewport-width JS hook triggers a Python callback that re-runs the data pipeline.  
**Impact:** Rate-limit burns, slow load, data inconsistency mid-session.  
**Prevention:** Viewport detection is CSS-only or JS-only. No Python callbacks attached to viewport events.

---

### Risk 7: Visibility mode persisting across dates

**Description:** `fs_mode_sel` session_state key retains yesterday's "Dangerous Only" mode when operator opens app on a new date.  
**Impact:** Operator cannot see today's slate because yesterday's filter is still active.  
**Prevention:** Visibility mode keys are reset on pipeline date change. Either re-initialize on `slate_ts` change, or prefix with date: `f"fs_mode_{slate_date}"`.

---

### Risk 8: HVY modifier fed into escalation level calculation

**Description:** `hvy_modifier` value influences escalation classification, bypassing the defined thresholds.  
**Impact:** HVY is display-only — it must NEVER feed back into model_prob or escalation classification.  
**Prevention:** `classify_escalation(batter)` reads only: `ev_pct`, `edge_pct`, `barrel_pct`, `model_prob`, `qualifies`. No other fields.

---

---

# 14. Final Orchestration Hierarchy Summary

## 14.1 The Full Slate Battlefield Map

```
FULL SLATE PARENT ORCHESTRATOR
│
├── COMMAND STRIP (always visible)
│   ├── Pipeline identity (version + run timestamp)
│   ├── Live game count
│   ├── Escalation summary (N Critical · N Elevated · N Active · N Quiet)
│   ├── Active environmental threats
│   └── Sync state (last refresh + freshness indicator)
│
├── VISIBILITY MODE SELECTOR
│   ├── Default (escalation-ordered, QUIET hidden)
│   ├── Dangerous Only (A1 + A2 cards only)
│   ├── Elite Only (barrel ≥10% games only)
│   └── All Games (full slate including QUIET)
│
├── GAME CARD LAYER (ordered by escalation, then start time)
│   │
│   ├── [CRITICAL GAMES] — pinned, fully open
│   │   ├── Game header (teams, time, CRITICAL badge)
│   │   ├── Pitcher danger row (factor, fatigue, DANGER label)
│   │   ├── Batter stack (ranked by composite score)
│   │   │   ├── B1 FIRE batter → left-margin bar (critical red)
│   │   │   └── B2 STRONG batter → left-margin bar (steel blue)
│   │   ├── Environmental row (if conditions active)
│   │   ├── Market context (best odds, edge)
│   │   └── Deployment briefing zone
│   │
│   ├── [DANGEROUS GAMES] — expanded, deployment zone visible
│   │   └── [same structure as CRITICAL, minus top-border ring]
│   │
│   ├── ─────── tier separator ───────
│   │
│   ├── [ELEVATED GAMES] — expanded by default
│   │   └── [P1–P4 visible, no deployment zone unless expanded further]
│   │
│   ├── ─────── tier separator ───────
│   │
│   ├── [ACTIVE GAMES] — partially expanded (P1–P3)
│   │   └── [Sorted by start time within tier]
│   │
│   └── [QUIET GAMES TOGGLE] — "Show X quiet games ▾"
│
└── INVESTIGATION / DEPLOYMENT LAYER (operator-driven)
    ├── Threat Cluster View (multi-pick game expansion)
    ├── Arsenal Breakdown (pitch mix, HVY detail — display only)
    └── Deployment Focus Mode (single pick, cognitive collapse)
```

---

## 14.2 Operational Doctrine in Three Rules

**Rule 1: SCAN THE FIELD → ISOLATE DANGER → ESCALATE TARGETS**

Every Full Slate design decision serves this loop. Escalation ordering is not aesthetic — it is operational necessity.

**Rule 2: DISPLAY REFLECTS SCORES. DISPLAY NEVER DRIVES SCORES.**

Visibility, filtering, escalation badges, and mode switches are read-only operations on the data layer. Nothing in the display layer writes to `ranked`, `_tac_params`, or any engine output.

**Rule 3: ONE ENTRY ANIMATION. THEN STATIC.**

The operator trusts a calm system. Every looping animation is a signal that the system is broken or panicking. CRITICAL cards earn attention through placement and information density — not through visual noise.

---

## 14.3 Implementation Sequence for Codex

Safe implementation order (do not parallelize — each step depends on prior):

1. Implement `classify_escalation(batter)` and `classify_game_card(batters)` as pure helper functions in `app.py` (no session_state, no side effects)
2. Add escalation-ordered game sort to `_render_full_slate_all_players()` — sort games by `classify_game_card()` output, then by start_time within tier
3. Add tier-boundary divider HTML between escalation groups
4. Add game card surface color and border color from escalation level (read from color token table)
5. Add escalation badge (right-aligned in game header row)
6. Add collapse/expand default behavior by escalation level
7. Add visibility mode toggles (Dangerous Only / Elite Only) — write to `fs_*` keys only
8. Add command strip escalation summary counts (read from classified game list)

**Each step is independently testable and independently rollback-safe.**

---

*Document Status: Planning and doctrine only. No runtime files modified. No commits made. Codex ownership of protected runtime systems fully preserved.*

*Room 04 Complete — Next: Room 06 Deployment, FD Slip & Tracking Systems*
