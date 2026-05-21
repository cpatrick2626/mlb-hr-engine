# Phase 3 Controlled Expansion — Refinement Doctrine
**MLB HR Engine v4 | Post-MSP Era | 2026-05-20**

---

## Scope Declaration

This document covers runtime-aware UX refinement only. Architecture, orchestration, session_state ownership, hydration, and routing are closed. All recommendations are rollback-safe, restraint-oriented, and grounded in the platform as built through Session 44.

---

## 1. Runtime UX Friction Audit Doctrine

### What Counts as Friction

Friction is any interaction that forces a user to re-orient, repeat an action, or wait without feedback when the system has the information it needs.

**Audit categories:**

| Category | Friction Type | Example |
|---|---|---|
| Load friction | No progress signal during fetch | Blank tab while pipeline runs |
| State friction | Filter resets unexpectedly | TCC preset reverts on tab switch |
| Content friction | Empty state gives no guidance | Full Slate shows nothing, no explanation |
| Stale friction | Data shown without age signal | Pitch mix from prior cache, no indicator |
| Cognitive friction | Two signals say different things | Model says 18%, ELITE tab shows B-tier |
| Action friction | Irreversible action with no confirm | Clear Slip already addressed in Session 15 |

### Audit Protocol

Run this sequence before any refinement session:

1. Cold load — open app with no session_state. Note first screen the user sees.
2. Filter interaction — move one TCC control. Does everything that should update, update?
3. Empty states — reduce all filters until a tab empties. Is the empty state actionable?
4. Stale indicators — is data currency visible when it matters (lineup unconfirmed, pitch mix from prior year)?
5. Degraded load — disconnect Odds API key. Does the app degrade gracefully or error silently?
6. Optimizer flow — enable optimizer, switch presets. Does the badge update? Does rejected picks expander populate?

### Friction Threshold

Address any friction that requires more than one non-obvious user action to resolve. Do not address friction that exists because the underlying data genuinely isn't available.

---

## 2. Validation Observation Checklist

Use before accepting any UX change. "Passes" means no regression from pre-change baseline.

### Display Accuracy

- [ ] Barrel% shown in cards matches `sc_barrel` in the pick dict (spot-check 3 players)
- [ ] EV% tooltip shows .1f format (not truncated to integer)
- [ ] Model prob pill matches `model_prob` field (not calibrated_prob unless labeled as such)
- [ ] STEAM badge fires only when steam flag is active in the pick dict
- [ ] OPT badge fires only when pick is in `_display_pool` and optimizer is ON
- [ ] Game time shows "ET" suffix in FD Slip cards

### Tab Consistency

- [ ] `_n_elite` count matches actual Elite tab content (sources from `ranked`, not `_tac_ranked`)
- [ ] Full Slate "All Players" mode shows all batters regardless of TCC filter state
- [ ] JIG Full Slate tab label reflects `scored_all` count (full universe, not filtered)
- [ ] Matchup Edge: missing-context players sort to bottom (default modifier = 0.0)
- [ ] Portfolio tab: Input/Selected counts update when preset changes

### Data Currency

- [ ] Prior-year Statcast indicator visible on pitcher label when data is from prior season
- [ ] Pitch mix "Load Full Analysis" gate resets on new slate_ts (not stale from prior day)
- [ ] Card HTML cache invalidates on new `slate_ts` (not serving yesterday's cards)
- [ ] JIG Refresh clears both `_hvy_ck` and `picks_pm_ctx_*` keys

### Performance Checks

- [ ] Slider/number_input interaction does not trigger full pipeline re-run
- [ ] JIG Power Profiles and Full Tactical show lazy gate on first load (not pre-rendered)
- [ ] Pitch mix expanders default collapsed; content not built until user clicks Load
- [ ] P&L sidebar reads from cache (not CSV on every interaction)

---

## 3. Tactical Readability Refinement Standards

### Card Hierarchy Principles (Established — Do Not Deviate)

All 4 card types share a fixed anatomy. Refinements must preserve this skeleton:

```
[top accent hairline — grade color, 0.55-0.60 opacity]
[rank badge / player name / photo]
[game urgency countdown / badges: STEAM / OPT / barrel tier]
[PRIMARY stat pills: MDL / EV / EDGE — 13-14px, bg #0c0c22, label #4a4a70]
[SECONDARY stat pills: BRL / ENV — 10-12px, bg #0a0a18]
[border-right separator on EDGE pill]
[HVY bar at bottom]
[weather fragment — only when |wf-1.0| >= 0.04]
```

### Signal Priority Order

Reading order must match betting decision order:

1. **Market signals first** (EV, EDGE, ODDS) — the bet viability question
2. **Quality signals second** (MDL, BRL, tier badge) — the confidence question
3. **Context signals third** (HVY, weather, park) — the situational question

Do not reorder this hierarchy for visual aesthetics.

### Typography Budget

| Element | Size | Weight | Color |
|---|---|---|---|
| Player name | 14-15px | 700 | #e0e0f0 |
| Primary stat label | 8-9px | 400 | #4a4a70 |
| Primary stat value | 13-14px | 700 | white/tier color |
| Secondary stat label | 7-8px | 400 | #444-#555 |
| Secondary stat value | 11-12px | 600 | #aaa |
| Micro labels (ARSENAL, etc.) | 7-9px | 400 | #555-#666 |

Do not go below 7px for any visible label. Do not go above 15px for stat values.

### Grade Label Standards

| Tier | Label | When | Color |
|---|---|---|---|
| S | GOAT / ELITE MISMATCH | barrel≥12% or HVY=elite | #f59e0b amber |
| A | ELITE / FAVORABLE | barrel 10-12% or HVY=favorable | #818cf8 violet |
| B | SOLID / NEUTRAL | barrel 8-10% | #4ade80 green |
| C | CONTACT / UNFAVORABLE | barrel 5-8% | #60a5fa blue |
| D | — / AVOID | barrel<5% | #ef4444 red |

Matchup grade labels must read "MATCHUP: [LABEL]" in the JIG and Matchup Edge contexts to prevent confusion with QUANT tier.

### Density Calibration

Minimum card height: sufficient to show all primary stats without scrolling within the card.
Maximum card density: 3 stat rows before content becomes unreadable on a 1080p screen.
Quick View alpha grid: 2 columns. Never 3 — the stat pills become unreadable.

---

## 4. Deployment Tray Polish Standards

### Sidebar Tray Definition

The sidebar contains operational controls only. It is not an analytics panel.

**Current tray inventory (in display order):**
1. API key input + validation status
2. Auto-refresh toggle + countdown
3. Load data button + last-load timestamp
4. Slate status pill (CONFIRMED / MIXED / PROJECTED)
5. Portfolio Optimizer toggle + preset selector
6. 📸 Capture Closing Lines (CLV)
7. Update Yesterday's Results / Settle Yesterday
8. P&L summary (cached 5 min)
9. Coverage expander

### Tray Polish Rules

**Labels:** All sidebar buttons use plain operational English. No jargon. No marketing language.
- Correct: "Save for Results Tracking"
- Wrong: "Log Pick to CLV-Enabled Atomic Tracker"

**State feedback:** Every button that triggers a background operation shows a spinner or status message. No silent executions.

**Grouping:** Controls that belong to the same workflow phase are visually grouped:
- Data acquisition (API key, Load, Auto-refresh)
- Intelligence layer (Optimizer, CLV Capture)
- Settlement & tracking (Results, P&L)
- Coverage info (Coverage expander)

Do not interleave groups.

**Pending counts:** When pending items exist (unsettled picks, unconfirmed lineups), the relevant button shows a count badge. Example: "Update Yesterday's Results (7 pending)". Already implemented for Settle Yesterday — apply same pattern to CLV Capture when open_implied_pct is blank.

**Error states in sidebar:** If data load fails, sidebar shows categorized error (Odds API key invalid / MLB connectivity / generic) rather than full traceback. Already enforced — do not regress this.

### Tray Anti-Patterns

- Do not put analytics content (calibration drift, signal rankings) in the sidebar.
- Do not put filter controls in the sidebar (they belong in TCC).
- Do not show raw Python exception text in the sidebar ever.
- Do not add controls that duplicate tab-level functionality.

---

## 5. Sidebar Operational Hierarchy Refinement Rules

### Hierarchy Levels

The sidebar has three authority levels. Controls must not cross levels.

**Level 1 — Platform controls** (always visible, always functional):
- API key input
- Load data button
- Auto-refresh toggle

**Level 2 — Session intelligence** (visible after data loads):
- Optimizer toggle + preset
- CLV Capture button
- Slate status pill

**Level 3 — Retrospective tracking** (operational but lower urgency):
- Settle Yesterday
- P&L summary
- Coverage expander

### Ordering Rule

Level 1 → Level 2 → Level 3 top to bottom. No exceptions. The user's eye path is: "Can I load? → What intelligence layer is active? → What do I track afterward?"

### Visual Separation

Use `st.divider()` between Level 1 and Level 2, and between Level 2 and Level 3. No decorative headers needed — dividers are sufficient.

### P&L Summary Standards

P&L summary is Level 3. It is informational, not actionable. Display rules:
- Show: ROI%, win rate, n settled, n void
- Show only when n_settled > 0
- Do not show when n_settled = 0 (suppress entirely, do not show zeroes)
- Cache at 5 min (already implemented — maintain this)
- No micro-calibration alerts in sidebar — those belong in monitoring_dashboard.py

---

## 6. Mobile Tactical Shell Expectations

### Platform Reality

Streamlit is not a mobile-native framework. The app targets desktop operational use (1920×1080 or 1440×900). Mobile is a degraded access mode, not a primary target.

### Acceptable Mobile Behavior

The following behaviors are acceptable on mobile without remediation:
- Single-column card layout (Streamlit auto-collapses)
- Truncated stat pills (small screen, expected)
- Horizontal scroll on Full Slate table
- Sidebar collapsed by default (Streamlit default)
- Slower load times (network, not app)

### Unacceptable Mobile Behavior

These must not break on mobile even if they look different:
- Load data button must be reachable (sidebar must expand)
- API key input must be functional
- Quick View top picks must render (even if 1-column)
- Pick logging must work (Save for Results Tracking button)
- Settlement must work (Update Yesterday's Results)

### Mobile Non-Goals

Do not invest in:
- Custom mobile layouts or breakpoint detection
- Touch-optimized controls
- Swipe gestures
- Progressive Web App configuration
- Mobile-specific CSS overrides

If a user requests mobile optimization, the correct answer is: use the desktop browser or wait for a native mobile client that doesn't exist on this roadmap.

---

## 7. Degraded-State Visual Handling Refinement

### Degraded State Taxonomy

| State | Cause | User Impact |
|---|---|---|
| No odds | Odds API failure or key invalid | Model runs but no EV/EDGE; most picks filtered out |
| No lineup | Lineup not yet confirmed | game_urgency = PROJECTED; platoon split unreliable |
| No Statcast | Player has <300 PA or rookie | Falls back to blended/prior; labeled with indicator |
| Prior-year pitch data | Current season unavailable | Pitcher label shows "(PRIOR YEAR)" |
| No pitch context | `load_hvy_context()` returned None | Matchup Edge card shows "No pitch data" |
| Stale API cache | Schedule fetch returns old games | game date validation warns/skips (Session 15) |
| Void pick | >7 days unresolved | Excluded from P&L summary automatically |

### Visual Rules per State

**No odds:** Card renders in muted style (`opacity: 0.6`). ODDS pill shows "—". EV/EDGE pills show "—". Card does not disappear — it shows as dimmed, indicating a model-only candidate. Badge: `no odds` in gray.

**No lineup:** Urgency pill shows "🔵 PROJECTED" in blue. Platoon-dependent display fields (platoon multiplier) show as estimated, not confirmed. Do not hide the pick.

**No Statcast:** Power badge shows "BLENDED" or "PRIOR" in amber. Full Slate compact row: BRL shows in muted color. Tooltip (if implemented) explains the source.

**No pitch context:** Pitch mix expander shows "No pitch data available for this matchup." Do not show an empty expander body. Do not show a spinner indefinitely.

**Degraded load (Odds API down):** Sidebar shows: "Odds unavailable — model output only. Check API key or service status." Full picks tab still renders with model signals intact.

### Degraded State Anti-Patterns

- Do not remove cards from display solely because they lack one data source.
- Do not show Python exception text anywhere in the UI.
- Do not show "None" or "nan" as a displayed value — coerce to "—" at render time.
- Do not show a spinner that never resolves. Gate with lazy load (Session 40 pattern) or show error.

### Degraded State Priority

Fix degraded states in this order:
1. Data that is visually broken (None/nan showing as text) — highest priority
2. Loading states with no resolution path — high priority
3. Missing context labels (BLENDED/PRIOR indicators) — medium priority
4. Opacity/muting for unavailable market data — low priority, aesthetic only

---

## 8. Full Slate Readability Optimization Guidance

### Current Architecture (Session 37)

Three modes: All Players | Qualified | Elite Targets. All Players uses `_render_full_slate_all_players()` — game-organized, filters highlight not remove, 1 markdown call per game.

### Readability Rules

**Game header:** Must show: `AWAY @ HOME · time ET · urgency color · park factor (bolded) · qual count`.
- Park factor color: green if ≥1.05, red if ≤0.95, neutral otherwise.
- Qual count color: green at n≥3 (strong game), neutral otherwise.
- Do not add more than 2 data points to the game header — it becomes unreadable.

**Batter row density:** Compact format. 8 data points per row maximum:
`spot · name · team · BRL · MDL · EV · EDG · CNF + badges`
Do not add columns without removing one. Density is a constraint, not a target.

**Row background hierarchy:**
- TCC-qualified (EV + edge pass): `#0f0f1a` — slightly elevated
- Sidebar-qualified only: `#0a0a12` — baseline
- No odds: `#080808` — dimmed
Do not invent new background tiers.

**Badges in All Players mode:** STEAM, ★ELITE, ✓QUAL, ODDS badges operate as-defined. Do not add new badges to All Players compact rows — the format is too compressed.

**Pitcher attribution line:** `AWAY bats vs [pitcher name]` — already corrected in Session 39. Do not revert to arrow notation.

### Readability Anti-Patterns

- Do not use color as the only indicator of a meaningful state. Always pair with a label or symbol.
- Do not show fractional barrel rates (show `8.5%` not `0.085`).
- Do not truncate player names below 12 characters in compact rows.
- Do not sort All Players mode by anything other than batting order within a game. Sorting destroys game context.

### Full Slate Mode Selector

Radio selector placement: above the content, below the tab. Label should read: `View: All Players | Qualified | Elite Targets`.
- Do not rename modes without updating both the selector and the mode-specific lazy gate keys.
- Qualified mode renders `_render_qualified_table` — do not duplicate its logic in Full Slate.

---

## 9. Runtime Polish Acceptance Criteria

A refinement is accepted when it passes all applicable criteria. Criteria marked [BLOCKER] must pass before merge. Others are advisory.

### Functional Correctness [BLOCKER]

- [ ] No new `None` or `nan` values rendered as visible text
- [ ] No filter state reset unexpectedly on tab switch
- [ ] No card HTML cache collision (fingerprints are unique per pick + state combination)
- [ ] No lazy gate key collision across tabs (keys include `key_prefix` + `player_id` + `slate_ts`)
- [ ] Session_state keys unchanged from pre-change baseline (backward compatibility)

### Data Integrity [BLOCKER]

- [ ] `_n_elite` sources from `ranked` (not `_tac_ranked`)
- [ ] Missing-context picks default modifier = 0.0 (not 1.0)
- [ ] Elite secondary sort uses `score` (not barrel alone)
- [ ] Strategy candidates have positive EV gate applied

### Performance [ADVISORY]

- [ ] No new unconditional render loops added (all heavy loops behind lazy gate or cache)
- [ ] No new CSV reads on slider interaction (read operations cached or deferred)
- [ ] Card HTML not rebuilt when fingerprint is stable

### Visual Consistency [ADVISORY]

- [ ] New card elements follow PRIMARY/SECONDARY pill size hierarchy
- [ ] New grade labels follow established grade color table
- [ ] Separator (`border-right:1px solid #1e1e35`) present on EDGE pill in all card types
- [ ] Weather fragment renders only when |wf−1.0| ≥ 0.04
- [ ] All 4 card types retain top accent hairline

### Rollback Safety [BLOCKER]

- [ ] Feature can be disabled via config flag or session_state toggle without code change
- [ ] No new session_state keys that conflict with existing keys
- [ ] No structural change to any tracking CSV schema without migration guard

---

## 10. Post-MSP Refinement Governance Recommendations

### What "Governance" Means Here

Not a process bureaucracy. A set of defaults to prevent scope creep from reopening closed architectural questions disguised as UX refinements.

### The Three Questions

Before starting any refinement session, answer:

1. **Does this touch model_prob, calibration, or signal weights?** → If yes, it is not a UX refinement. It is a model change. Treat it as one: run validate_2025.py and analyze_calibration.py before and after.

2. **Does this add a new session_state key, a new CSV column, or a new config flag?** → If yes, document the key/flag in this file before merging. Undocumented keys become hidden state that breaks across sessions.

3. **Does this change the scoring or ranking of picks?** → If yes, verify Spearman ρ against pre-change ranking. Changes that reshuffle the top-50 without calibration justification are rejected.

### Refinement Session Budget

Each refinement session should close with exactly one of:
- A committed, documented UX change
- A documented decision NOT to change (and why)
- A confirmed bug fix with regression verification

Sessions that end with "we explored some things" and no committed output are wasted sessions. Document the decision even when the decision is "no change."

### Config Flag Lifecycle

Every config flag added since Session 19 has a rollback path. Maintain this:

| Flag | Module | Rollback Value | Effect |
|---|---|---|---|
| CALIBRATION_ENABLED | config.py | False | Disables Platt calibration |
| ELITE_REG_TARGET_ENABLED | config.py | False | Disables regression ceiling for barrel≥8% |
| ELITE_PLATT_ENABLED | config.py | False | Disables tier Platt for barrel≥10% |
| CONTEXT_MODERATION_ENABLED | config.py | False | Disables low-power context cap |
| DYNAMIC_VIG_ENABLED | config.py | False | Falls back to VIG_FACTOR=7.5% fixed |
| PITCHER_FACTOR_SCALE | config.py | 1.0 | Removes pitcher factor attenuation |
| FB_QUALITY_GATE_ENABLED | config.py | False | Disables FB% quality gate |

Any new refinement session that adds a config flag must add it to this table.

### Calibration Recheck Triggers

Re-run `analyze_calibration.py` (Session 21 script) when any of these occur:
- n settled picks crosses 500 (next milestone from current 262)
- 12-15% calibration bucket bias exceeds +4pp at n≥50
- Any signal weight change (even 1pp redistribution)
- Session 23 regression ceiling has been live for ≥100 new real picks

Do not re-calibrate Platt parameters (a, b) without a new CV-fitted run on current data.

### Deferred Work Queue (Ordered by Priority)

The following work is confirmed deferred — do not reopen prematurely:

1. **tab_advanced_strategies + tab_hits lazy gates** — straightforward, Session 41 pattern, no model risk
2. **JIG Phase 2B: game-command module + tactical tag system** — scoped but larger; requires dedicated session
3. **Platt re-calibration after Session 23 regression ceiling stabilizes** — needs n≥100 new real picks first
4. **Pitcher signal coefficient reduction** — rank #17/21, negligible aggregate; low ROI refinement
5. **Velo decline wiring into pipeline.py** — data plumbing done (Session 36); integration is a model change
6. **Archetype scoring bonus in ranker.py for barrel≥10% + power≥1.15** — Session 24 finding; validate at n≥200 first
7. **Optimizer EV/edge threshold tuning** — do not touch until n≥200 settled optimized picks with CLV data

### Anti-Scope-Creep Rules

These are hard stops. If a proposed refinement touches any of these, it is out of scope for Phase 3:

- Redesigning session_state ownership or hydration flow
- Adding a new routing layer or page structure
- Rewriting `pipeline.py` orchestration
- Redesigning the backtest runner
- Introducing a new primary signal without full backtest validation
- Changing the portfolio optimizer's composite score formula without n≥500 settled picks

### Operational Cadence

**Daily:** `ops_daily.py` → `capture_closing_lines.py` (~30min before first pitch) → `optimize_daily.py`

**Weekly:** `monitoring_dashboard.py` Phase 4 — check 12-15% calibration bucket drift

**Monthly:** Review this document. Remove items from Deferred Work Queue that have been completed. Add any new confirmed deferrals. Update the calibration state table in project memory.

---

*Document authority: Phase 3 Controlled Expansion. Supersedes no prior architecture documents. Supplements SESSION memory entries. Do not commit architecture changes citing this document as justification.*
