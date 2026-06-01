# Loading, Skeleton & Hydration Philosophy v1
## MLB HR ENGINE — Trust-State Visibility During Data Load

**Owner:** Claude (UX Doctrine)
**Codex:** Implementation
**Status:** Documentation Only — No Runtime Code

---

## 1. Core Principle

**The operator must always know exactly what they are looking at and how fresh it is.**

Blank screens, silent stale data, and fake loading certainty are worse than visible failures. An operator who acts on stale or incomplete data due to a hidden system state is the worst outcome. Trust-state transparency is non-negotiable.

---

## 2. Loading State Hierarchy

States in order from cleanest to most degraded:

```
LEVEL 0: FRESH       — Data loaded from live source, within session freshness window
LEVEL 1: WARM        — Data from this session's last refresh, >5 min but <60 min old
LEVEL 2: STALE       — Data from a previous session or >60 min old current session
LEVEL 3: PARTIAL     — At least one data source failed; others loaded normally
LEVEL 4: DEGRADED    — Critical source failed; model output may be materially affected
LEVEL 5: NO DATA     — No data loaded at all; engine cannot run
```

**Rule:** The current state MUST be visible in the command strip at all times via a status indicator. Never hide the state level.

---

## 3. Skeleton Card Behavior

**When to show skeleton cards:** Between data load trigger and first render-ready payload.

**Skeleton card rules:**
- Skeleton cards render in the same layout position as real cards (same width, estimated height)
- Skeleton shows player name placeholder (gray animated shimmer bar), 2 stat pill placeholders, badge placeholder
- Skeleton never shows fake numbers. Gray shimmer only.
- Skeleton count matches last known card count from previous session if available; otherwise default 12 skeleton cards in Quick View
- Skeleton duration: as long as data is loading. No timeout fake-complete.

**What skeleton is not:**
- Skeleton is not a spinner in the center of the screen blocking all content
- Skeleton is not a blank white rectangle
- Skeleton is not a progress bar counting to 100% on a fake timeline

**After load completes:** Skeleton transitions to real card. No layout jump. Skeleton height was sized to match real card height.

---

## 4. Degraded-Data Placeholders

**Definition:** A specific data source failed but the engine ran with available data.

**Display rule:** A degraded-data card renders normally but carries a data-quality badge:

| Badge | Condition |
|---|---|
| `[SC MISS]` gray | Statcast data unavailable for this batter; model used prior-year or fallback |
| `[NO ODDS]` gray | No market odds loaded; EV/edge cannot be computed |
| `[PITCH N/A]` gray | Pitcher Savant fetch failed; HVY modifier may be neutral |
| `[LINEUP ?]` gray | Lineup not yet confirmed; batting order unknown |

**Placement:** Top-right corner of card, small gray pill. Never colored red/orange (those are reserved for edge and alert states). Never blinks or animates.

**Cards with degraded data are not hidden.** They appear in ranked order but the degraded badge alerts the operator to use caution on that pick.

---

## 5. Stale-Data Markers

**Definition:** Data was loaded but is now older than the freshness window.

**Freshness windows:**

| Source | Fresh | Warm | Stale |
|---|---|---|---|
| Odds (live market) | <5 min | 5–30 min | >30 min |
| Lineups | <10 min | 10–60 min | >60 min |
| Statcast | <24 hours | 24–72 hours | >72 hours |
| Weather | <30 min | 30–90 min | >90 min |
| Pitcher HVY context | <60 min | 60–180 min | >180 min |

**Stale indicator:** Small clock icon + time-since-load in command strip. Format: "ODDS 45m ago" in amber when warm, red when stale.

**Card-level stale indicator:** Not shown per-card (too noisy). Stale is shown at source level in command strip only.

---

## 6. Hydration Progress Language

**During data load, command strip shows progress in plain language:**

| State | Command Strip Text |
|---|---|
| Idle (no load triggered) | "No slate loaded · Click Load" |
| Schedule loading | "Loading schedule…" |
| Odds loading | "Fetching odds… N games" |
| Lineup loading | "Loading lineups…" |
| Statcast loading | "Loading Statcast… N batters" |
| HVY contexts loading | "Building pitch context…" |
| Calibration applying | "Applying calibration…" |
| Complete | "✓ Slate ready · N picks · Updated HH:MM ET" |
| Partial failure | "⚠ Partial load · ODDS unavailable · N picks" |
| Full failure | "✗ Load failed · Check connection" |

**Rules:**
- Language is declarative, not cheerful. "Loading schedule…" not "Hang tight, getting your data!"
- Never show percentage complete unless the value is real (computed from actual steps)
- Never show "Done!" followed immediately by another loading state
- Never hide partial failure behind a success message

---

## 7. Trust-State Visibility During Load

**The operator must be able to answer three questions at any moment:**

1. **Is this data current?** → Answered by: command strip time-since-load + stale markers
2. **Is any source missing?** → Answered by: partial-load warning badge in command strip + `[SC MISS]`/`[NO ODDS]` card badges
3. **Is the engine running correctly?** → Answered by: pick count in command strip + slate status pill

**Never leave these questions unanswered.**

---

## 8. Partial-Data Display Rules

**Rule:** Show what is available. Do not wait for all sources to load before showing any cards.

**Load order priority:**
1. Schedule (game structure must load first)
2. Odds (market context; show EV/edge immediately once loaded)
3. Lineups (batting order)
4. Statcast (power profiles; show partial card without SC if SC fails)
5. HVY contexts (pitch mix; lazy-loaded, never blocks card render)

**Partial display example:**
- Odds loaded, Statcast not yet loaded → Show card with `[SC MISS]` badge, MDL computed from prior-year Statcast, EV/Edge computed from available odds
- Cards are live and ranked; operator can start scanning before full load completes

**Cards never held back because one of N sources is still loading.** The card renders with available data + appropriate degraded badge.

---

## 9. Failed-Source Display Rules

**Odds API failure:**
- Cards render without EV/Edge columns (columns hidden, not empty)
- Banner at top of Quick View tab: "⚠ Odds unavailable — EV and Edge cannot be computed. Model probabilities shown only."
- Picks can still be viewed/ranked by model prob, but cannot be deployed with EV context

**Statcast failure (full):**
- Banner: "⚠ Statcast unavailable — Power multipliers using prior-season data."
- All cards show `[SC MISS]` badge
- Model continues running with prior-year Statcast (this is the existing fallback)

**Schedule failure:**
- Engine cannot run. Full error state.
- Command strip: "✗ Schedule unavailable — Cannot load today's slate."
- Suggest retry action

**MLB Stats API failure (lineups):**
- Cards render without lineup confirmation data
- `[LINEUP ?]` badge on all cards
- Batting order shown as unknown

**Weather API failure:**
- weather_factor silently defaults to 1.0 (no weather adjustment)
- No per-card badge needed — weather is a small adjustment and the fallback is neutral
- Command strip shows "Weather: unavailable" in data sources row if operator expands source details

---

## 10. Forbidden Loading Patterns

| Forbidden | Reason |
|---|---|
| Blank screen while loading | Operator has no information; cannot assess wait time |
| Fake loading certainty ("Done!" when partial) | Trust violation — operator may act on incomplete data |
| Hidden failures (silent fallback with no indicator) | Worst pattern — operator doesn't know data is degraded |
| Silent stale data (no timestamp visible) | Operator cannot judge data freshness |
| Layout jumping (skeleton height differs from card height) | Visual instability, disorienting under time pressure |
| Misleading confidence ("100% confirmed" when lineup is projected) | False certainty is worse than honest uncertainty |
| Loading spinner with no progress information (indefinite) | Operators need to know if something is hung |
| Auto-reloading without operator awareness | Silent data changes can affect decisions mid-analysis |
| Showing prior slate data as current without explicit stale marker | Trust violation |

---

## 11. Layout Stability Rules

**Skeleton cards must match real card height.** If real card height varies (e.g., weather strip shows only conditionally), skeleton uses the maximum expected height to prevent layout jump.

**Progressive content load within a card** (e.g., pitch badges loading after main stats): Use a reserved height for the badge strip. If pitch data doesn't arrive, the reserved space collapses cleanly with no layout shift in surrounding cards.

**Table columns do not shift** when data partially loads. Columns are defined at render start. Empty cells show `—` (em-dash), not empty string (avoids column width reflow).

---

*Documentation only. No implementation. No app.py changes. No session_state changes.*
