# Release Readiness Checklist v1
## MLB HR Engine — Master Stabilization

**Date:** 2026-05-20  
**Step:** 12 of 12  
**Owner:** Claude (doctrine)  
**Version:** v1.0 — Post-Stabilization Baseline

---

## Purpose

Defines the minimum criteria MLB HR ENGINE must satisfy before each release gate:
- Internal deployment (operator-only usage)
- Extended operator usage (daily operational use)
- Implementation expansion (new component development)
- Release candidate status (external deployment readiness)

---

## Gate Definitions

| Gate | Definition |
|---|---|
| **Internal Deployment** | Engine runs daily without runtime crashes; core pick flow operational |
| **Extended Operator Usage** | All validated systems stable; operator workflow uninterrupted across full slate |
| **Implementation Expansion** | Known-good baseline locked; isolation doctrine established; rollback paths confirmed |
| **Release Candidate** | All PASS criteria satisfied; no FAIL items open; known CONDITIONAL items documented |

---

## Checklist: Runtime Stability

### RS-01: Core Pipeline Execution

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| `pipeline.py` runs without uncaught exception | Zero exceptions on clean data | One non-critical warning logged | Any uncaught exception in main flow |
| Picks generated from full lineup slate | ≥ 80% of starters have model_prob | 60–80% coverage (API degradation) | < 60% coverage or zero picks generated |
| Session state initialized cleanly | All required keys present on first load | Non-critical key missing, auto-recovered | Required key missing causes crash |
| Config assertions pass on startup | `RECENT_WEIGHT + SEASON_WEIGHT == 1.0` assertion clears | — | Assertion fails; app does not start |
| HR rate cap enforced | All model_prob ≤ 0.29 in output | — | Any output exceeds MAX_GAME_HR_PROB |

### RS-02: Data Source Continuity

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| MLB Stats API reachable | Schedule + lineup + stats fetched | Partial fetch (stale cache used) | No schedule; zero lineups |
| Odds API connectivity | Live lines fetched for ≥ 2 books | Fallback to `manual_odds.csv` | No odds; all picks missing market data |
| Statcast (Baseball Savant) reachable | Barrel/EV data fetched for ≥ 90% of batters | Blended-year data used for remainder | Zero Statcast data; prior-year only for all |
| Weather (Open-Meteo) reachable | All games have temp/wind/humidity factors | Neutral weather factor applied (1.0) | Weather fetch blocks pipeline execution |

---

## Checklist: Rerun Validation

### RR-01: Rerun Loop Detection

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| Repeated data load does not trigger duplicate picks | Dedup confirms zero new rows on rerun | Dedup catches and discards duplicates | Duplicate picks logged to pick_tracker.csv |
| Cache TTL respected | `@st.cache_data` TTL prevents stale re-renders | TTL expired early; extra fetch performed | Cache bypassed; every render makes live API call |
| Auto-refresh does not cause session_state reset | All session_state keys persist across auto-refresh | One non-critical key reset; operator not affected | Operator filter state cleared on auto-refresh |
| Rerun loop threshold | No runaway rerun detected | 1 extra rerun per user action (acceptable) | > 2 consecutive reruns without user action |

---

## Checklist: Shell Continuity

### SC-01: Application Shell Integrity

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| Sidebar renders without exception | Full sidebar renders on first load | Sidebar renders after 1 retry | Sidebar blank or crashes |
| Tab navigation preserves state | Engine tab switch does not clear picks | Minor scroll reset on tab switch | Active player or filter state cleared on tab switch |
| TCC (filter controls) read correctly | All filter session_state keys resolve | One key uses fallback default | Required TCC key missing; filter crashes |
| Parent orchestration intact | MAIN and JIG are fully independent sections | Minor shared-key collision (logged) | MAIN state overwrites JIG state or vice versa |
| Card HTML builds without error | All card HTML strings complete without KeyError | One card falls back to empty section | Any card raises exception on render |

---

## Checklist: Escalation Continuity

### EC-01: Escalation System Integrity

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| Steam alerts detected and displayed | STEAM badge renders when steam move detected | Steam badge absent; indicator shows in log | Steam detection crashes or corrupts pick list |
| Escalation tier labels correct | ELITE MISMATCH / FAVORABLE / NEUTRAL / UNFAVORABLE / AVOID correct | — | Any label mismatch vs underlying modifier value |
| Escalation surfaces in tray (doctrine) | No escalation replaces main engine view | — | Escalation triggers full-page reroute |
| CRITICAL interruption containment | CRITICAL events shown as persistent banner only | — | CRITICAL event clears player selection or collapses Full Slate |

---

## Checklist: Deployment Continuity

### DC-01: Deployment Queue Integrity

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| Pick logging writes to CSV atomically | `_atomic_write()` used; no partial writes | Retry on lock; write succeeds | Partial write or corruption of pick_tracker.csv |
| FD Slip game time cards show ET timezone | "ET" suffix present on all time cards | — | Game times shown in UTC or timezone unspecified |
| Clear Slip two-step confirmation active | Requires confirmation before clearing | — | Single click clears slip without confirmation |
| Settle Yesterday contextual button present | Shows in Performance tab with pending count banner | — | Button absent; operator cannot settle from app |

---

## Checklist: Full Slate Continuity

### FS-01: Full Slate Operational Integrity

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| All Players mode shows all batters | Full game-organized view with all starters | One game missing (schedule gap) | Full Slate shows empty or fewer than half of games |
| Qualified mode matches TCC filter state | `_tac_ranked` list matches active TCC params | Minor count mismatch (< 3 picks) | Qualified mode shows unfiltered picks |
| Elite Targets mode filters barrel≥8% | All displayed players have barrel_pct ≥ 0.08 | — | Sub-elite barrels appear in Elite Targets mode |
| Full Slate exempt from TCC in All Players mode | All players visible regardless of TCC filter | — | TCC filters remove players from All Players mode |
| Collapse restores scroll position | Pre-expansion anchor restored on collapse | Approximate position (within 1 card) | Scroll resets to top on collapse |

---

## Checklist: Lazy Gate Validation

### LG-01: Lazy Load System Integrity

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| Pitch mix expanders load on demand | Collapsed state costs ≤ 2 widget registrations | 3–5 widget registrations in collapsed state | Full pitch mix built unconditionally every render |
| JIG Power Profiles lazy gated | "Load Power Profiles" button required before HVY cards render | — | All 25 HVY cards render on every rerender |
| JIG Full Tactical lazy gated | "Load Full Tactical" button required | — | Full tactical renders unconditionally |
| Card HTML cache active | `_CARD_CACHE` prevents rebuild on stable fingerprint | Cache miss rate > 20% (within acceptable) | No caching; full card rebuild every rerender |
| Lazy gate keys anchored to slate_ts | Gate keys include `slate_ts` suffix | — | Stale pitch data persists across date change |

---

## Checklist: Trust-State Validation

### TS-01: Trust and Data Quality Signals

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| Blended-source indicator displayed | Prior-year Statcast players visibly marked | Indicator in log only | Blended players shown without distinction |
| Calibration drift monitor active | `monitoring_dashboard.py Phase 4` runs without error | Partial alert detection | Drift monitor crashes or produces no output |
| Odds API key validation enforced | 32-hex-char regex validates key on load | Warning logged; non-conforming key rejected | Non-conforming key accepted; silent bad requests |
| American odds range validation active | Prices in (−100, 100) rejected with log | — | Invalid odds accepted into model |

---

## Checklist: Mobile Sanity

### MS-01: Mobile Layout Integrity

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| App renders at ≤ 768px viewport | No horizontal overflow; all cards visible | Minor overflow on one card section | App unusable at mobile viewport width |
| Card font sizes legible at mobile | All pill labels ≥ 10px | Primary labels at 10px (borderline) | Any label < 9px at 375px width |
| Scroll anchoring uses GAME_ROW targets | Mobile scroll restores to nearest game row | Approximate row anchor | Scroll resets to page top on mobile return |

---

## Checklist: Degraded-Data Behavior

### DD-01: Partial Data Resilience

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| No Statcast data: fallback behavior | Prior-year blended data applied; player labeled as blended | Neutral power_mult (1.0) applied; no crash | App crashes or player omitted |
| Missing pitcher arsenal: HVY modifier neutral | `hvy_modifier = 1.0` (neutral) applied; sorted to bottom | — | Missing context player ranked as if NEUTRAL (middle-sorted) |
| No lineup confirmed: projected lineup used | Lineup shown with PROJECTED slate indicator | — | App waits for confirmed lineup; no picks shown |
| Odds missing for player: player excluded from deployment | Player shown in All Picks but excluded from FD Slip | — | Player with no odds enters FD Slip |
| Weather API failure: neutral weather applied | All weather factors = 1.0; no exception | — | Weather failure cascades to pipeline crash |

---

## Checklist: Recovery Prompt Validation

### RP-01: Operator Recovery Experience

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| Recovery prompt offered after interruption | Restoration prompt shows after CRITICAL escalation resolves | Prompt delayed > 5 sec | No prompt; operator left in interrupted state |
| Quick View empty state provides guidance | Actual filter values shown with actionable fix guidance | Generic empty state shown | Empty state shows no guidance |
| Load error messages categorized | Odds API key error vs MLB connectivity vs generic each display distinct message | Combined error message shown | No error message; silent failure |
| Auto-refresh toast message present | Toast confirms successful refresh with timestamp | Toast absent but refresh succeeds | No indication of refresh; operator cannot tell if data is fresh |

---

## Checklist: Restoration Stack Validation

### SS-01: Context Restoration Stack

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| Restoration stack depth ≤ 10 | Stack prunes FIFO at overflow | Stack grows unbounded (memory risk) | Stack errors on push when full |
| Session-scoped only | Stack cleared on session end | — | Stack persists across sessions (stale tactical data) |
| Partial restoration preferred over failure | Partial restore delivers available context | — | Full restore failure delivers nothing |
| Fast-return (< 5 min): full context restored | Engine + game + player + JIG state + scroll | Engine + game + player only | Engine only |

---

## Checklist: Performance Sanity Thresholds

### PS-01: Render Performance

| Criterion | PASS | CONDITIONAL | FAIL |
|---|---|---|---|
| Initial load time (data fetch + render) | ≤ 15 seconds on warm cache | 15–30 seconds | > 30 seconds or timeout |
| Rerender on filter change | ≤ 2 seconds | 2–5 seconds | > 5 seconds; user perceives stutter |
| Card HTML build time (100 cards) | Negligible on cache hit; ≤ 1s on cold build | 1–3s cold build | > 3s cold build every rerender |
| `_tac_filter_fp` cache hit on stable filter | Filter loop skipped on fingerprint match | — | Filter loop runs on every slider interaction |
| Steam cache TTL (120s) | Steam detection reads disk at most once per 2 minutes | — | Steam detection reads disk every render |

---

## Release Gate Summary

| Gate | Required Criteria |
|---|---|
| **Internal Deployment** | RS-01, RS-02, SC-01 all PASS or CONDITIONAL |
| **Extended Operator Usage** | All checklists PASS or CONDITIONAL; no FAIL items in RS, SC, EC, DC, FS |
| **Implementation Expansion** | All checklists at PASS or CONDITIONAL; known-good baseline locked per `known_good_baseline_definition.md` |
| **Release Candidate** | All checklists PASS; all CONDITIONAL items documented with mitigations; no FAIL items open |

---

*Created: 2026-05-20 — Step 12 Final Stabilization Closeout*
