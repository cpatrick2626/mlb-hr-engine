# Data Integrity, Trust States & Resiliency Doctrine
## MLB HR Engine v4 — Room 07 Governance Document

**Version:** 1.0
**Date:** 2026-05-22
**Phase:** Phase 3A — Step 04/10
**Room:** 07 — Data Integrity, Trust States & Resiliency
**Status:** Doctrine only. No runtime code modified. No Streamlit or Python execution path touched.
**Cross-references:** `deployment_trust_hierarchy.md`, `escalation_vs_suppression_doctrine.md`, `FULL_SLATE_UX_DOCTRINE.md`, `full_slate_parent_orchestrator_doctrine.md`, `operator_override_doctrine.md`

---

## Overview

This document formalizes the complete trust-state governance layer for MLB HR Engine v4. It extends and consolidates the foundational work in `deployment_trust_hierarchy.md` into a full resiliency doctrine covering source trust, degraded-state handling, fallback hierarchy, operator visibility, failure isolation, and runtime contamination prevention.

**Core doctrine:** `VERIFY → DEGRADE → SURVIVE → RECOVER`

The operator must never feel blindsided. The system must never pretend. Failure states are controlled, visible, and operational — not hidden, silent, or catastrophic.

---

## Contents

1. [Trust-State Hierarchy Doctrine](#1-trust-state-hierarchy-doctrine)
2. [Degraded-State Taxonomy](#2-degraded-state-taxonomy)
3. [Fallback Hierarchy Doctrine](#3-fallback-hierarchy-doctrine)
4. [Operator Visibility Doctrine](#4-operator-visibility-doctrine)
5. [Failure Isolation Doctrine](#5-failure-isolation-doctrine)
6. [Retry & Recovery Doctrine](#6-retry--recovery-doctrine)
7. [Trust-State UX Doctrine](#7-trust-state-ux-doctrine)
8. [Validation Checklist](#8-validation-checklist)
9. [Codex Implementation Boundaries](#9-codex-implementation-boundaries)
10. [Runtime Contamination Risks](#10-runtime-contamination-risks)
11. [UX Anti-Patterns](#11-ux-anti-patterns)
12. [Recovery Workflow Hierarchy](#12-recovery-workflow-hierarchy)
13. [Final Resiliency Orchestration Summary](#13-final-resiliency-orchestration-summary)

---

## 1. Trust-State Hierarchy Doctrine

### 1.1 The Eight Trust States

Trust state is a session-level label assigned at initialization and updated dynamically as source availability changes. It governs what the operator can do, what they see, and how confidence is communicated.

| State | Code | Meaning | Operator Impact |
|-------|------|---------|----------------|
| LIVE | `LIVE` | All sources live, fresh, validated. Full analytical capacity. | Full deployment. All controls active. No caveats. |
| FULL | `FULL` | All critical sources live. Minor signals may be stale. | Full deployment. Minor staleness noted in Zone 6. |
| PARTIAL | `PARTIAL` | All primary sources live. One or more secondary sources stale or unavailable. | Full deployment available. Operator informed of partial signal loss. |
| DEGRADED | `DEGRADED` | One or more secondary sources unavailable. Signal quality reduced. | Full deployment available. Confidence caveat displayed. Tier may understate risk. |
| STALE | `STALE` | Sources are available but data age exceeds freshness thresholds. | Deployment available. Staleness timestamp shown. Operator must acknowledge age. |
| FALLBACK | `FALLBACK` | Live source unavailable. Fallback (prior-year, cached, or manual) data active. | Deployment available with reduced confidence label. Fallback origin must be disclosed. |
| RESTRICTED | `RESTRICTED` | One or more primary sources unavailable. Material data gaps. LOCKDOWN override blocked. | Deployment available at reduced confidence. LOCKDOWN override blocked. |
| BLOCKED | `BLOCKED` | Critical primary source failed. Pick validity unconfirmable. | Deployment blocked. Panel is informational only. |

### 1.2 Trust State Precedence

When multiple conditions are active simultaneously, the most restrictive trust state governs the session.

```
BLOCKED > RESTRICTED > FALLBACK > STALE > DEGRADED > PARTIAL > FULL > LIVE
```

**Example:** Statcast unavailable (FALLBACK) + MLB Stats API partially degraded (RESTRICTED) → session trust state = RESTRICTED.

### 1.3 Trust State Transitions

Trust state transitions are driven by source status changes. They are not operator-controllable.

```
LIVE → FULL         (minor source staleness detected)
FULL → PARTIAL      (secondary source stale or unavailable)
PARTIAL → DEGRADED  (secondary source fully unavailable, signal material)
DEGRADED → STALE    (all sources available but data age exceeds thresholds)
DEGRADED → FALLBACK (live source replaced by cached/prior-year data)
FALLBACK → RESTRICTED (primary source unavailable, fallback only)
RESTRICTED → BLOCKED  (critical primary source failure)
```

Recovery transitions run in reverse order. A BLOCKED system does not skip directly to LIVE — it must recover through RESTRICTED, then FALLBACK or STALE, then DEGRADED, before returning to FULL.

### 1.4 Trust State Escalation Rules

**Escalation:** State moves toward BLOCKED when source quality drops.
**Decay:** State moves toward LIVE when sources recover and are validated.

State changes never happen silently. Every transition must:
1. Update the trust state indicator in the Command Strip (Zone 5).
2. Render an appropriate banner or badge at the view level.
3. Adjust the deployment panel confidence language (Zone 6).
4. Log the transition with timestamp and source cause.

### 1.5 Source Ownership Map

| Source | Module | Trust Tier | Category |
|--------|--------|------------|----------|
| MLB Stats API (schedule, lineup, pitcher stats) | `clients/mlb_stats.py` | T1 — Primary Critical | Blocks on failure |
| Statcast / Baseball Savant (barrel%, EV, SwStr%) | `clients/statcast.py` | T1 — Primary Critical | Falls back to prior-year |
| The Odds API (market lines) | `clients/odds_api.py` | T1 — Primary Critical | Falls back to `manual_odds.csv` |
| Open-Meteo (weather) | `clients/weather.py` | T2 — Secondary | Falls back to neutral factor 1.0 |
| Pitch Mix / HVY modifier | `clients/pitch_mix.py` | T2 — Secondary | Falls back to HVY = 1.0 (neutral) |
| Park factors (internal data) | `data/park_factors.py` | T3 — Internal | Never unavailable |
| Line snapshots (CLV) | `tracking/line_snapshots.py` | T3 — Operational | Non-blocking |
| Pick tracker (deployment log) | `tracking/pick_tracker.py` | T3 — Operational | Non-blocking |

---

## 2. Degraded-State Taxonomy

### 2.1 MLB Stats API Degradation

| Severity | Condition | Trust State | Operator Message | Fallback |
|----------|-----------|-------------|-----------------|----------|
| WARNING | Partial lineup returned (< all starters) | PARTIAL | "Lineup incomplete — [N] starters unconfirmed." | Show confirmed starters only; note gaps |
| WARNING | Pitcher stats partially missing | DEGRADED | "Pitcher stats incomplete — suppression score may be partial." | Use available signals; note missing |
| CRITICAL | Schedule data absent | BLOCKED | "Schedule unavailable — game existence unconfirmable." | No fallback. Deployment blocked. |
| CRITICAL | Full API unavailable | BLOCKED | "MLB Stats API offline — no picks available." | No fallback. Deployment blocked. |

**Suppression behavior:** Missing lineup fields suppress the affected batter's row in the picks table with a `DATA INCOMPLETE` indicator. Other batters are not affected.

### 2.2 Statcast Degradation

| Severity | Condition | Trust State | Operator Message | Fallback |
|----------|-----------|-------------|-----------------|----------|
| INFO | Data age 24–36 hours | FULL | "Statcast: [age] old." | Use existing data |
| WARNING | Data age > 36 hours | DEGRADED | "Statcast stale — barrel and velocity signals based on [timestamp]." | Use existing data with staleness note |
| WARNING | Current-year sample < 50 PA | PARTIAL | "Statcast: prior-year blend active — small current-year sample." | Prior-year + current blend per `PRIOR_YEAR_TRUST` |
| CRITICAL | Current-year unavailable, prior-year used | FALLBACK | "Statcast unavailable — power signals from prior-year data." | Prior-year Statcast at `PRIOR_YEAR_TRUST = 0.85` |
| CRITICAL | Both years unavailable | RESTRICTED | "Statcast offline — power assessment uses league baseline only." | League-average barrel/EV in `config.py` |

**Signal impact when FALLBACK:** Zeroed signals: VELO_SPIKE (requires fresh velocity), ELITE_PUT_AWAY (requires current SwStr%). Retained signals: GB_DOMINANT (from prior-year), BARREL_RATE (degraded), LOW_BARREL_ALLOWED (prior-year pitcher). Maximum achievable suppression score without Statcast: ~52 (from GB, handedness, pitch mix, weather).

### 2.3 Weather Degradation

| Severity | Condition | Trust State | Operator Message | Fallback |
|----------|-----------|-------------|-----------------|----------|
| INFO | Data age 60–90 minutes before first pitch | FULL | "Weather: [age] — conditions may have shifted." | Use existing data |
| WARNING | Data age > 90 minutes before first pitch | DEGRADED | "Weather stale — wind/temperature factors from [timestamp]." | Use existing data with staleness note |
| WARNING | API timeout on retry | DEGRADED | "Weather fetch timed out — prior conditions in use." | Last successful fetch |
| CRITICAL | Weather unavailable, outdoor game | RESTRICTED | "Weather offline — environmental signals cannot be evaluated." | Factor = 1.0 (neutral). Note dome status if applicable. |

**Dome exception:** For confirmed dome stadiums, weather source failure produces NO trust state change. Dome status is derived from `data/park_factors.py` (internal, always available). Environmental factor is always 1.0 for domes regardless of weather source state.

### 2.4 Odds / Market Degradation

| Severity | Condition | Trust State | Operator Message | Fallback |
|----------|-----------|-------------|-----------------|----------|
| WARNING | Partial odds returned (some markets missing) | PARTIAL | "Odds incomplete — [N] picks missing market lines." | Show picks with available lines; flag missing |
| WARNING | API rate limit hit | DEGRADED | "Odds API rate limited — market data from [timestamp]." | Cached odds if available |
| CRITICAL | Odds API unavailable, no cache | FALLBACK | "Odds offline — manual_odds.csv active." | `manual_odds.csv` fallback |
| CRITICAL | Odds API unavailable, no CSV | RESTRICTED | "No market data available — EV and edge cannot be computed." | EV/edge suppressed. Picks ranked by model_prob only. |

### 2.5 Pitch Mix / HVY Degradation

| Severity | Condition | Trust State | Operator Message | Fallback |
|----------|-----------|-------------|-----------------|----------|
| INFO | HVY unavailable for single matchup | FULL | HVY pill shows `N/A` on affected card | HVY = 1.0 (neutral) for that matchup |
| WARNING | HVY unavailable for > 25% of matchups | PARTIAL | "HVY signal unavailable for [N] games." | HVY = 1.0 (neutral) per unavailable matchup |
| WARNING | Pitch mix data age > 48 hours | DEGRADED | "Pitch mix data stale — HVY modifier from [timestamp]." | Use stale data with note |

**Hard rule:** HVY modifier failure never affects model_prob (HVY is display-only). Pitch mix degradation cannot trigger worse than PARTIAL trust state.

### 2.6 Lineup Confirmation Degradation

| Severity | Condition | Trust State | Operator Message | Fallback |
|----------|-----------|-------------|-----------------|----------|
| INFO | Lineups confirmed but > 2 hours old | FULL | "Lineups: confirmed [timestamp]." | Use confirmed lineups |
| WARNING | Lineup unconfirmed within 2 hours of first pitch | DEGRADED | "Lineup unconfirmed — batting order not posted." | Use probable starters; note uncertainty |
| CRITICAL | Lineup unconfirmed within 30 minutes of first pitch | RESTRICTED | "Lineup still TBD at [time] — starter status at risk." | Mark affected picks with `LINEUP RISK` indicator |
| CRITICAL | Starter scratched mid-session | RESTRICTED | "⚡ [Player] scratched — lineup updated." | Remove scratched player from active picks immediately |

---

## 3. Fallback Hierarchy Doctrine

### 3.1 Source Priority Ladder

For each data source, fallback activates in strict order. A higher-priority source is always preferred over a lower-priority source. Fallbacks must never pretend to be live data.

#### MLB Stats API

```
1. Live MLB Stats API (primary)
2. [No fallback] — BLOCKED state if unavailable
```

**Rule:** No synthetic schedule or lineup data. If MLB Stats API is unavailable, the session enters BLOCKED state. There is no acceptable fallback for schedule and lineup data.

#### Statcast

```
1. Live Statcast API (current-year, < 24h)
2. Stale Statcast (current-year, 24–72h) — STALE state
3. Prior-year Statcast blend (PRIOR_YEAR_TRUST = 0.85) — FALLBACK state
4. League-average Statcast constants (config.py) — RESTRICTED state
```

**Disclosure rule:** When prior-year Statcast is active, every affected pick displays: `"Power: prior-year data (current-year unavailable)"`. League-average fallback displays: `"Power: league baseline only — Statcast offline"`.

#### Odds / Market Lines

```
1. Live Odds API (< 2h before first pitch)
2. Cached Odds API response (same session) — STALE state
3. manual_odds.csv (operator-maintained) — FALLBACK state
4. No market data — RESTRICTED state (EV/edge suppressed, rank by model_prob)
```

**Disclosure rule:** When `manual_odds.csv` is active, the Command Strip displays: `"ODDS: MANUAL — Odds API offline"`. EV% and Edge% are labeled `(manual odds)` throughout.

#### Weather

```
1. Live Open-Meteo API (< 90 min before first pitch)
2. Cached Open-Meteo response (same session, < 3h) — STALE state
3. Neutral factor (1.0) — FALLBACK/RESTRICTED state for outdoor games
```

**Disclosure rule:** When neutral factor is applied due to weather unavailability, every affected outdoor game card displays: `"Weather: unavailable — environmental factor neutral"`. Dome games never require this disclosure.

#### Pitch Mix / HVY

```
1. Live pitch mix computation (current-season data)
2. Prior-season arsenal data — STALE state
3. HVY = 1.0 (neutral, no signal) — FALLBACK state
```

**Hard rule:** HVY fallback to 1.0 is silent at the card level (HVY is display-only). Trust state impact is limited to PARTIAL or less. No operator message required for single-matchup HVY failure.

### 3.2 Fallback Disclosure Standards

When any fallback is active:

1. **Source label is always shown.** "Statcast: prior-year blend" — never just "Statcast."
2. **Timestamp or age is shown.** "Odds: manual_odds.csv — last updated [date]" — never "Odds: manual."
3. **Confidence impact is stated.** "Power signals are from prior-year data. Current-year barrel performance is unconfirmed."
4. **The fallback is never presented as equivalent to live data.** The system does not smooth over the difference.

### 3.3 Stale-Cache Usage Rules

| Source | Stale Threshold | Max Stale Usage | Trust State |
|--------|-----------------|-----------------|-------------|
| Statcast | 24h | 72h | STALE → FALLBACK |
| Weather | 90min | 3h (session cache) | STALE → FALLBACK |
| Odds API | 2h | Same session only | STALE → FALLBACK |
| Pitch Mix | 48h | 7 days | STALE → DEGRADED |
| Lineup | 2h before game | 30min before game = RESTRICTED | PARTIAL → RESTRICTED |

**Hard rule:** No source is used beyond its max stale usage window without explicit operator acknowledgement. If a source has exceeded its max window, the deployment panel requires operator acknowledgement before picks from that source are visible.

### 3.4 Retry Suppression During Fallback

When fallback is active:
- **No automatic retry during active fallback period** — retry storms waste rate-limited API quota.
- **Retry window:** Source-specific cooldowns govern when retry is attempted (see Section 6).
- **Operator cannot force retry** during cooldown window. The retry button shows time remaining.
- **Fallback status does not change until retry succeeds and data is validated.**

---

## 4. Operator Visibility Doctrine

### 4.1 Visibility Hierarchy

Trust state governs where and how warnings appear. Higher severity = higher placement in the operator's scan path.

| Trust State | Primary Location | Secondary Location | Interaction Required |
|-------------|-----------------|-------------------|---------------------|
| LIVE | — | Zone 5 sync state (green) | None |
| FULL | Zone 5 sync state | — | None |
| PARTIAL | Zone 5 sync state (amber dot) | Affected card footer | None |
| DEGRADED | Zone 5 sync state (amber) + Zone 6 source table | Affected card footer note | None |
| STALE | Zone 5 sync state (amber, timestamp) | Zone 6 source table | None |
| FALLBACK | Command Strip banner (persistent) + Zone 6 | Every affected card (labeled) | None |
| RESTRICTED | Command Strip banner (persistent, orange) + Zone 6 | Zone 2 confidence layer | Deployment size guidance |
| BLOCKED | Command Strip banner (crimson) + Full panel | [Deploy] button disabled | Resolution required |

### 4.2 Command Strip Trust Indicator

Zone 5 of the Command Strip shows real-time trust state. This indicator is always visible.

```
[LIVE]       ●  green     #2d6a2d    No message
[FULL]       ●  green     #2d6a2d    "Data: current"
[PARTIAL]    ●  amber     #c8a035    "Partial: [source] stale"
[DEGRADED]   ●  amber     #c8a035    "Degraded: [source] unavailable"
[STALE]      ●  amber     #c8a035    "Stale: [source] — [age]"
[FALLBACK]   ●  orange    #d4620a    "Fallback: [source] offline"
[RESTRICTED] ●  orange    #d4620a    "Restricted: [source] failure"
[BLOCKED]    ●  crimson   #8a0000    "BLOCKED: [source] — resolve before deployment"
```

The indicator dot uses a single slow pulse (one cycle, 300ms) on trust state change to signal the transition. After the transition animation, it is static. No looping pulse.

### 4.3 Degraded Banners

For FALLBACK, RESTRICTED, and BLOCKED states, a persistent banner appears below the Command Strip.

**FALLBACK banner:**
```
⬦ FALLBACK ACTIVE — [Source]: [fallback type] — [specific disclosure]
```
Amber border, dark amber surface. Not dismissible until source recovers.

**RESTRICTED banner:**
```
⬦ RESTRICTED — [Source] unavailable — deployment confidence reduced
```
Orange border, dark orange surface. Not dismissible. Shows for entire session until source recovers.

**BLOCKED banner:**
```
⬦ BLOCKED — [Source] failure — resolve to restore deployment
   → [Specific resolution guidance]
```
Crimson border, dark surface. Occupies full Command Strip width. Not dismissible.

**Banner rules:**
- Maximum one banner visible at a time (most restrictive state wins).
- Banners never stack — the most severe single banner is shown.
- Banners display the specific source that triggered the state, not a generic message.
- Banners are not animated after initial appearance.

### 4.4 Card-Level Trust Indicators

Cards affected by degraded sources display a footer note — never a banner, never a disruption to the primary data hierarchy.

**PARTIAL / DEGRADED footer note:**
```
─────────────────────────────────────
⬦ Statcast: 31h old — power signals may not reflect recent trends
```
Tertiary text color (#9a9a9a). One line maximum.

**FALLBACK footer note:**
```
─────────────────────────────────────
⬦ Power: prior-year Statcast — current-year unavailable
```
Secondary amber text. One line maximum.

**RESTRICTED footer note:**
```
─────────────────────────────────────
⚠ Partial data — suppression score reflects available signals only
```
Orange text. One line maximum.

**Rules:**
- Footer notes never appear on QUIET cards (no picks = no data to qualify).
- Footer notes are never shown for HVY fallback to neutral (HVY = display-only).
- Footer notes do not repeat information already visible in Zone 6 of the deployment panel.

### 4.5 Stale Timestamp Standards

Timestamps in trust communication must be exact. Vague descriptions are rejected.

**Rejected:** "a couple days ago," "recently," "earlier today," "~30 hours"
**Required:** "31h 14m ago," "Updated 2026-05-21 14:22 ET," "Last fetch: 06:47 ET"

Timestamps are always in ET (Eastern Time, local game-day convention). All trust indicators with time references use this format:
- Within 24h: `"3h 14m ago"`
- Beyond 24h: `"Updated 2026-05-21 14:22 ET"`

### 4.6 Trust Overlay in Deployment Panel

Zone 6 of the deployment panel contains a source status table whenever trust state ≥ DEGRADED.

| Source | Status | Age / Note |
|--------|--------|-----------|
| MLB Stats API | ✓ Live | — |
| Statcast | ⬦ Stale | 31h 14m ago |
| Weather | ✓ Live | — |
| Odds API | ✓ Live | — |
| Pitch Mix | ⬦ Unavailable | HVY = 1.0 (neutral) |

This table never shows sources in FULL/LIVE state in detail — only sources with trust degradation are called out. A fully live session shows no source table in Zone 6 (only "Data: current" green indicator).

---

## 5. Failure Isolation Doctrine

### 5.1 Subsystem Isolation Rules

Each data source is an isolated subsystem. Failure of one subsystem must be contained. Cross-system contamination is the most dangerous failure mode.

**Isolation rules:**

| Failing Subsystem | What It May Affect | What It Must NOT Affect |
|-------------------|--------------------|------------------------|
| Weather client | Weather suppression signals, outdoor game environmental factor | Statcast signals, odds, lineup, Full Slate navigation |
| Pitch Mix / HVY | HVY display modifier on affected cards | model_prob, escalation tier, suppression score, other cards |
| Statcast client | barrel%, EV, SwStr% signals, power_mult | MLB Stats API, lineup data, odds, weather, navigation |
| Odds API | EV%, edge%, bet sizing | model_prob, escalation tier, Statcast signals, navigation |
| Pick tracker / CLV | Operational logging | All analytical systems; never blocks picks display |
| Line snapshots | CLV data | Never blocks picks, never affects model, never affects deployment panel |

### 5.2 Containment Rules

**Rule 1 — No cascade failures.** A source timeout must produce a handled exception, not an unhandled error that propagates up the call stack. Every client module (`clients/*.py`) must wrap API calls in try/except and return a structured result with a `status` field indicating `"live"`, `"stale"`, `"fallback"`, or `"unavailable"`.

**Rule 2 — No silent propagation.** If a subsystem returns `"unavailable"`, the consuming module (`engine/probability.py`, `engine/ev.py`, etc.) must acknowledge the missing input and apply the appropriate fallback or suppress the affected signal. It must not use a stale reference from a prior session call.

**Rule 3 — No cross-contamination.** A Statcast failure must not cause weather signals to be treated as unreliable. Trust states are source-specific at the subsystem level. Only the session-level trust state (Section 1) aggregates them into a single operator-facing label.

**Rule 4 — Full Slate cannot be blocked by secondary failures.** Weather client failure must not prevent the Full Slate view from loading. Pitch mix failure must not prevent the Batters Table from rendering. Only an MLB Stats API BLOCKED state may prevent the Full Slate view from showing picks.

**Rule 5 — Navigation is always available.** No data source failure may block tab navigation, page routing, or sidebar controls. The operator must always be able to navigate to any view, even in BLOCKED state. Blocked views show their data-unavailability state, not an error page.

### 5.3 Graceful Degradation Sequence

When a subsystem fails, the degradation sequence is:

```
1. Catch exception at the client boundary.
2. Return structured result: {status: "unavailable", data: None, fallback_used: bool, age: None}
3. Consuming module checks status field.
4. If unavailable: apply fallback (prior-year, neutral factor, or suppress signal).
5. Emit trust state event: {source: "statcast", state: "unavailable", timestamp: now()}
6. Session trust state updates to the most restrictive active state.
7. UI receives updated trust state and renders appropriate indicators.
8. Operator is informed via Command Strip + relevant banners.
```

Steps 1–4 are invisible to the operator. Steps 5–8 are the visible resiliency layer.

### 5.4 Restricted-Mode Operation

When trust state = RESTRICTED:

- Full Slate view renders all available picks. Missing-source picks are labeled.
- Batters Table renders with partial signal disclosure.
- Deployment panel shows restricted confidence label in Zone 6.
- LOCKDOWN override is blocked (operator cannot override into LOCKDOWN when data is materially incomplete).
- HIGH suppression override remains available with added restricted-data caveat.
- Picks from affected sources display `PARTIAL DATA` indicator in their card footer.
- The operator can still act. They are informed of the limitation. They choose.

---

## 6. Retry & Recovery Doctrine

### 6.1 Retry Suppression Rules

Automatic retries must be rate-limited to prevent storm conditions and API exhaustion.

| Source | First Failure | Retry Window | Max Retries Per Session | Cooldown After Max |
|--------|---------------|-------------|------------------------|-------------------|
| MLB Stats API | Immediate retry (1x) | 60s after failure | 3 | 5 min lockout, then manual only |
| Statcast | Wait 30s | 120s window | 2 | 10 min lockout |
| Odds API | Wait 60s | 120s window | 3 | Session lockout (rate limit protection) |
| Weather | Wait 30s | 90s window | 3 | 5 min lockout |
| Pitch Mix | Wait 60s | 180s window | 2 | No lockout (HVY = 1.0 fallback is stable) |

**Hard rule:** No retry storm. If a source has exceeded its max retries, the retry button shows countdown to next available retry window. The operator cannot bypass the cooldown via UI interaction.

### 6.2 Cooldown Hierarchy

Retry cooldowns escalate when multiple consecutive failures occur:

```
First failure: Automatic retry per source schedule above.
Second failure in session: Cooldown × 2.
Third failure in session: Cooldown × 4 + operator acknowledgement required before next retry.
Fourth+ failure in session: Manual retry only. No automatic retry for remainder of session.
```

**Rule:** A source that has failed 4+ times in a single session is treated as structurally unavailable for that session. The fallback is locked in. The operator is informed. Retries remain possible via manual trigger but have no automatic schedule.

### 6.3 Recovery Timing

When a source recovers (retry succeeds and data validates):

1. Trust state updates immediately to reflect the new source availability.
2. If recovery improves trust state (e.g., RESTRICTED → DEGRADED), Command Strip updates.
3. Affected picks are re-evaluated using recovered data. Model outputs are refreshed.
4. Stale fallback data is replaced by live data. Fallback labels are removed.
5. A brief recovery note appears in Zone 6: "Statcast: recovered at 14:22 ET — signals restored."
6. Recovery note auto-clears after 60 seconds. It is not persistent.

**Rule:** Recovery from BLOCKED to RESTRICTED requires explicit operator acknowledgement before deployment controls re-enable. Recovery from RESTRICTED to DEGRADED or better enables deployment controls automatically.

### 6.4 Recovery Escalation

If a source fails to recover within expected windows:

| Time Without Recovery | Action |
|----------------------|--------|
| 15 minutes | Cooldown message includes estimated resolution time if detectable |
| 30 minutes | Source labeled "Extended outage" in Zone 6 source table |
| 60 minutes | Session-level advisory: "Recommend restarting session if [source] critical to your deployment plan" |

The engine does not auto-restart. The operator decides. The advisory is informational.

### 6.5 Revalidation Sequencing

When multiple sources recover simultaneously:

```
Priority order for revalidation:
1. MLB Stats API (schedule + lineup) — revalidate first
2. Statcast — revalidate second (depends on lineup for player matching)
3. Odds API — revalidate third (depends on player list for matching)
4. Weather — revalidate fourth (independent but affects suppression context)
5. Pitch Mix / HVY — revalidate last (display-only, non-blocking)
```

Revalidation is sequential to prevent partial state where lineup is stale but Statcast is live. Each source validates successfully before the next begins revalidation.

---

## 7. Trust-State UX Doctrine

### 7.1 Trust Color Hierarchy

Trust state colors follow a restrained, operational palette. All colors are muted — no neon, no pure saturated primaries.

```
LIVE / FULL:      #2d6a2d    (tactical green — confirmation)
PARTIAL:          #c8a035    (tactical amber — attention)
DEGRADED:         #c8a035    (tactical amber — same as PARTIAL, severity via text)
STALE:            #c8a035    (tactical amber — same tier, staleness via timestamp)
FALLBACK:         #d4620a    (tactical orange — escalated concern)
RESTRICTED:       #d4620a    (tactical orange — same as FALLBACK, severity via text)
BLOCKED:          #8a0000    (tactical deep red — operational halt)
```

**Rule:** PARTIAL, DEGRADED, and STALE share the amber token. They are differentiated by text and specific source information — not by color. Color compression at the amber tier prevents warning inflation.

### 7.2 Shape Hierarchy

Trust state uses shape tokens to reinforce meaning independent of color (accessibility compliance):

```
●   Filled circle   — source live / FULL / LIVE state
◐   Half-filled     — PARTIAL / DEGRADED / STALE
⬦   Diamond         — FALLBACK / RESTRICTED
⚠   Warning         — RESTRICTED (high severity within tier)
✕   Blocked         — BLOCKED state
```

### 7.3 Glow Restraint

**No glow on trust state indicators.** Glow is used exclusively for FIRE-tier escalation badges. Trust state indicators communicate through color, shape, and text — not animation or luminance effects.

**Permitted:** Single-cycle pulse on trust state transition (300ms, then static).
**Forbidden:** Persistent pulse on any trust indicator. Glow on amber or orange indicators. Shadow bloom on degraded banners.

### 7.4 Degraded-State Visuals

When trust state = DEGRADED or STALE:

- Command Strip indicator: amber dot, static after 300ms transition pulse.
- Zone 6 source table: amber border, dark amber surface (`#1a1500`), white text.
- Affected card footer: one-line note in tertiary text color.
- No full-card color treatment. Cards are not tinted for data degradation.

**Rule:** The card visual treatment (amber for ELEVATED, red for DANGEROUS) communicates escalation tier — not trust state. These two systems never overlap in visual treatment.

### 7.5 Restricted-State Visuals

When trust state = RESTRICTED:

- Command Strip indicator: orange dot, persistent.
- Persistent banner below Command Strip: orange border, `#1a0d00` surface.
- Zone 6 source table: orange border treatment, orange indicator.
- Affected card footer: orange text `⚠ Partial data` note.
- Deployment panel Zone 9: button label changes from "[Deploy]" to "[Deploy — restricted data]".

### 7.6 Blocked-State Visuals

When trust state = BLOCKED:

- Command Strip indicator: crimson dot, persistent.
- Full-width banner below Command Strip: crimson border, `#0f0000` surface.
- Zone 6 source table: crimson border, resolution guidance.
- Deployment panel: Zone 9 button disabled, grayed. Zone 2 tier display grayed with "Unconfirmable" label.
- No pick cards are hidden — the Full Slate remains visible as informational context.

**Rule:** BLOCKED state does not clear the screen. The operator can still see all pick data. They simply cannot deploy. Maintaining visibility prevents re-investigation from scratch once the source recovers.

### 7.7 Visual Pacing Standards

Trust indicators are calm. They do not compete with escalation signals.

- Trust state badge and escalation tier badge must never appear in the same visual zone.
- Degraded banners appear below the Command Strip, above game cards — in the structural layer, not the content layer.
- Trust warnings never use exclamation marks in their primary label. Exclamation suggests panic. Trust communication is factual.
- Maximum one trust-related visual element per card in collapsed state.

---

## 8. Validation Checklist

### 8.1 Degraded-State Transition Validation

- [ ] When Statcast age exceeds 24h, trust state transitions to STALE automatically.
- [ ] When Statcast returns `unavailable`, trust state transitions to FALLBACK within one refresh cycle.
- [ ] When MLB Stats API is unavailable, trust state transitions to BLOCKED and [Deploy] button disables.
- [ ] When Weather is unavailable for outdoor game, trust state is RESTRICTED (not BLOCKED).
- [ ] When all sources recover, trust state transitions back toward FULL/LIVE.
- [ ] Trust state never skips levels on recovery (BLOCKED → FULL in one step is invalid).
- [ ] Trust state transition always generates a log entry with timestamp and source cause.

### 8.2 Stale-State Handling Validation

- [ ] Stale timestamps display exact age format ("31h 14m ago"), never vague descriptions.
- [ ] Stale data is labeled at point of use (Zone 6 source table, card footer note).
- [ ] Stale data does not prevent pick display (only affects confidence label).
- [ ] When stale threshold is exceeded for picks in deployment panel, Zone 6 shows timestamp.
- [ ] Stale lineup data triggers RESTRICTED, not BLOCKED, when within 30min of first pitch.

### 8.3 Fallback Activation Validation

- [ ] `manual_odds.csv` fallback activates when Odds API is unavailable.
- [ ] Command Strip shows "ODDS: MANUAL" label when `manual_odds.csv` is active.
- [ ] EV% and Edge% labels show "(manual odds)" suffix when manual odds are active.
- [ ] Prior-year Statcast fallback activates when current-year Statcast is unavailable.
- [ ] Prior-year fallback discloses "prior-year data" at every affected pick.
- [ ] Fallback never presents as equivalent to live data.
- [ ] HVY fallback to 1.0 is silent at the card level (HVY is display-only).

### 8.4 Retry Suppression Validation

- [ ] After max retries, retry button shows cooldown countdown — not a generic error.
- [ ] Cooldown multiplier escalates on consecutive failures (×1, ×2, ×4).
- [ ] No automatic retry occurs during active cooldown window.
- [ ] After 4th failure in a session, source is treated as structurally unavailable for the session.
- [ ] Retry storm protection: no source makes more than 3 automatic requests per 5-minute window.

### 8.5 Operator Visibility Validation

- [ ] Trust state indicator is visible in Command Strip Zone 5 at all trust states.
- [ ] Trust state transitions produce Command Strip update within one UI refresh cycle.
- [ ] FALLBACK and above states produce persistent banner below Command Strip.
- [ ] BLOCKED state disables [Deploy] button in Zone 9.
- [ ] Zone 6 source table appears when trust state ≥ DEGRADED.
- [ ] Source table shows exact timestamp for stale sources.
- [ ] Card footer notes appear only for DEGRADED, FALLBACK, RESTRICTED, BLOCKED.
- [ ] No trust-state visual elements appear at FULL or LIVE state (except green dot in Zone 5).

### 8.6 Restricted-Mode Operation Validation

- [ ] Picks display in RESTRICTED state (informational operation continues).
- [ ] LOCKDOWN override is blocked in RESTRICTED state.
- [ ] HIGH suppression override is available in RESTRICTED state with added caveat.
- [ ] Deployment panel Zone 9 button label changes to "[Deploy — restricted data]" in RESTRICTED.
- [ ] Navigation is always available regardless of trust state.
- [ ] Full Slate view renders in BLOCKED state (informational, no deployment).

### 8.7 Subsystem Isolation Validation

- [ ] Weather failure does not affect Statcast signal computation.
- [ ] Pitch mix failure does not affect model_prob or escalation tier.
- [ ] Statcast failure does not affect lineup display or odds computation.
- [ ] Pick tracker failure does not block picks display or deployment panel.
- [ ] Line snapshots failure does not affect any analytical system.
- [ ] No unhandled exception propagates from any client module to the Streamlit render layer.

### 8.8 Recovery Behavior Validation

- [ ] Source recovery updates Command Strip within one refresh cycle.
- [ ] Recovered source data replaces fallback data; fallback labels are removed.
- [ ] Zone 6 shows recovery note for 60 seconds, then clears.
- [ ] Recovery from BLOCKED requires operator acknowledgement before deployment re-enables.
- [ ] Recovery from RESTRICTED → DEGRADED or better auto-enables deployment controls.
- [ ] Revalidation follows the priority sequence (MLB Stats → Statcast → Odds → Weather → Pitch Mix).

### 8.9 Cache Behavior Validation

- [ ] Stale cache is used only within its max stale usage window (per source table in Section 3.3).
- [ ] Stale cache beyond max window requires operator acknowledgement before use.
- [ ] Cache staleness is computed against original fetch timestamp, not session start time.
- [ ] No cache is promoted from STALE to LIVE without a successful re-fetch.
- [ ] Empty cache (no prior fetch this session) does not silently substitute zero values.

---

## 9. Codex Implementation Boundaries

### 9.1 What Codex MAY Implement

Within trust-state and resiliency scope, Codex may safely implement:

- **Trust state indicator in Command Strip Zone 5** — reading from session_state trust_state key; rendering color/shape/text per this doctrine.
- **Degraded banners** — persistent banner component below Command Strip; reads trust_state; renders appropriate severity.
- **Zone 6 source table** — source status display within the deployment panel; reads source_status dict from session_state.
- **Card footer notes** — trust degradation disclosure below affected pick cards; reads per-pick source_status.
- **Stale timestamp formatting** — exact timestamp display logic; pure presentation layer.
- **Retry countdown UI** — display of cooldown remaining time; reads retry_state from session_state.
- **Recovery note display** — 60-second recovery acknowledgement in Zone 6; session_state flag.
- **LOCKDOWN override block in RESTRICTED** — gate on override control; reads trust_state.
- **[Deploy — restricted data] label change** — Zone 9 button label in RESTRICTED state.
- **[Deploy] button disable in BLOCKED** — Zone 9 button state in BLOCKED state.

### 9.2 What Codex MAY NOT Modify

These systems are protected. Trust-state feature work must not touch them.

| Protected System | Why Protected |
|-----------------|---------------|
| `pipeline.py` data loading | Owns cache and session hydration; trust state reads from pipeline, never writes to it |
| `session_state` key ownership | All `_display_pool`, `_tac_params`, `_hydration_*` keys are owned by existing modules |
| `engine/probability.py` model logic | Model outputs are read by trust state; trust state does not modify model behavior |
| `engine/calibration.py` | Calibration is post-model; trust state does not re-calibrate based on source state |
| `engine/ev.py`, `engine/market.py` | EV/edge computation; trust state labels the output but does not alter computation |
| `output/ranker.py` | Composite score and ranking are untouched; trust state may add visual labels, not re-rank |
| `clients/*.py` (return values) | Client return structures are fixed; trust state reads status field, does not rewrite data |
| Routing and tab navigation | Navigation must always be available; no trust state may block a tab |
| Full Slate orchestration | Parent orchestrator doctrine governs; trust state is a child concern |
| `tracking/pick_tracker.py` (log schema) | Schema is fixed; trust state may add a `trust_state_at_log` field via migration only |
| Deployment lifecycle (log → settle → CLV) | Trust state may label picks at log time; it does not alter settlement or CLV computation |

### 9.3 Protected Runtime Zones

The following runtime zones are closed to trust-state feature work:

- **Hydration sequence** — `@st.cache_data` pipeline fetch; runs before trust state is evaluated.
- **MAIN identity** — `main.py` orchestration; trust state is a UI layer concern.
- **JIG model** — if/when present; completely isolated from trust state concerns.
- **Backtest systems** — `backtest/` modules; trust state governs live session only.
- **Portfolio optimizer** — `portfolio/` modules; trust state may add optimizer-context label but does not modify selection logic.
- **ops_daily.py / monitoring_dashboard.py** — operational scripts; trust state is a runtime UI concern, not a batch-job concern.

### 9.4 Safe Resiliency Boundaries

Codex may safely add resiliency behaviors in these zones without consultation:

- **Any `clients/*.py` try/except wrapper** that returns structured `{status, data, fallback_used, age}` result.
- **Any fallback constant substitution** that uses values from `config.py` (league averages, neutral factors).
- **Any session_state flag** that records trust state: `st.session_state.trust_state`, `st.session_state.source_status`.
- **Any UI component** that reads from `session_state.trust_state` and renders per this doctrine without writing to any other session_state key.
- **`manual_odds.csv` CSV reader** as Odds API fallback — this path already exists in the codebase.

---

## 10. Runtime Contamination Risks

### 10.1 Stale-State Contamination

**Risk:** A prior session's stale data persists into a new session without detection.

**Mechanism:** `@st.cache_data` cache from a prior run is used in the new session. Statcast data fetched at session T is presented as fresh at session T+26h.

**Prevention:**
- Cache TTL must be enforced per source (`ttl` parameter in `@st.cache_data`).
- Session start always validates cache age against source-specific thresholds.
- Trust state is computed at session initialization, not assumed to carry from prior session.

**Containment:** If stale-state contamination is detected (timestamp check on cache hit), force a re-fetch. If re-fetch fails, apply STALE trust state immediately. Do not silently use the contaminated cache.

### 10.2 Fallback Poisoning

**Risk:** Prior-year Statcast fallback data becomes the de facto "live" source when it persists across multiple sessions without a live Statcast fetch succeeding.

**Mechanism:** Session 1 uses prior-year fallback (Statcast unavailable). Session 2 starts the next day — Statcast returns a 200 status but the response is empty (Baseball Savant partial outage). Prior-year data from Session 1 is promoted because it's "more recent than nothing."

**Prevention:**
- Prior-year fallback is never stored as a validated live source.
- Fallback trust state (FALLBACK) persists until a successful live-data fetch validates.
- An empty successful response is treated as UNAVAILABLE, not as validation.
- `fallback_used: true` flag is preserved through all cache layers.

**Containment:** Fallback label persists until live data validates. The operator always sees the fallback indicator — it cannot be automatically upgraded to FULL trust.

### 10.3 Trust Escalation Drift

**Risk:** Trust state progressively degrades across a long session without the operator noticing, because individual state changes are minor and the final trust state is far worse than the operator believes.

**Mechanism:** Session starts FULL. Weather becomes PARTIAL. Statcast becomes DEGRADED. HVY is unavailable. By the end of the session, effective trust is RESTRICTED — but no single change triggered a visible alert.

**Prevention:**
- Trust state is a session-level label, not a per-source label. The most restrictive state wins and governs the session banner.
- Compound degradation produces escalated trust state display immediately.
- Zone 6 source table always shows the full picture (all sources and their current status).

**Containment:** If trust state has degraded by two or more levels since session start, a compound-degradation note appears: "Multiple sources degraded since session start — review full source status before deployment."

### 10.4 Silent Restricted-Mode Failures

**Risk:** System enters RESTRICTED state but the operator does not realize it — they deploy thinking they have FULL trust.

**Mechanism:** RESTRICTED banner appears and operator dismisses it (or it is a subtle indicator they overlook). They proceed to deploy. The pick was computed from partial data.

**Prevention:**
- RESTRICTED banner is not dismissible. It persists for the entire session.
- Deployment panel Zone 9 button label changes — "[Deploy — restricted data]" is a persistent, visible difference from "[Deploy]".
- Pick log captures `trust_state_at_log` field so post-session review can identify restricted-mode deployments.

**Containment:** All picks logged during RESTRICTED state carry a flag. CLV and settlement analysis can segment by this flag to evaluate whether restricted-state deployments underperform.

### 10.5 Retry Storms

**Risk:** A source failure triggers rapid successive retries that exhaust API rate limits, causing all sources to fail.

**Mechanism:** Odds API rate limit is hit. System retries immediately. Rate limit re-fires. System retries again. Within 60 seconds, the API key is throttled for the session.

**Prevention:**
- Max retries per source per window are enforced (see Section 6.1).
- Cooldown escalation (×1, ×2, ×4) prevents storm conditions.
- Retry suppression applies to all auto-retries — no retry overrides the cooldown window.

**Containment:** If a source returns HTTP 429 (rate limited), the cooldown is immediately set to maximum (session-level lockout for Odds API). The operator is informed: "Odds API rate limited — manual_odds.csv active for session." Manual retry requires operator action after 10 minutes.

### 10.6 Degraded-Cache Corruption

**Risk:** A cached response from a degraded source is used without recognizing it as degraded — it appears valid but contains partial or incorrect data.

**Mechanism:** Weather API returns a 200 status with data, but the data is for the wrong zip code (geocoding error). The response validates successfully. Wind direction is inverted. Environmental suppression signals are wrong for the entire session.

**Prevention:**
- Source validation at the data level, not just at the HTTP level. Weather data must pass basic sanity checks (temperature within plausible range, wind direction 0–360°, dome detection check).
- If sanity check fails, the response is treated as UNAVAILABLE, not as live data.

**Containment:** Invalid response is logged with the specific sanity check failure. Trust state updates to FALLBACK or RESTRICTED per source. The invalid data is never stored in session cache.

### 10.7 Suppression Mismatch

**Risk:** Suppression score is computed from partial signals but displayed without indication that signals are missing — operator believes the score reflects full Statcast when it only reflects non-Statcast signals.

**Mechanism:** Statcast is in FALLBACK state. Suppression score computes from GB rate, handedness, and weather only. Score is 34 (LOW). With full Statcast, the score might be 75 (HIGH). Operator deploys on a FIRE pick facing a pitcher who would score HIGH or LOCKDOWN with full data.

**Prevention:**
- Suppression score display always includes signal completeness count: "Score: 34 (3 of 8 signals available)."
- When Statcast signals are unavailable, an amplification note appears: "Statcast unavailable — barrel and velocity signals not evaluated. Pitcher may present higher suppression than displayed."

**Containment:** The amplification note is surfaced at MODERATE or below suppression tier when Statcast is unavailable. At HIGH or LOCKDOWN, the note is unnecessary (available signals have flagged meaningful risk without Statcast).

### 10.8 Visibility Desync

**Risk:** Trust state indicator in the Command Strip shows FULL while individual cards show degraded-data warnings — operator sees contradictory signals.

**Mechanism:** Trust state is updated at session level on source failure, but the Command Strip renders before the session_state propagates to the card-level trust flags.

**Prevention:**
- Trust state is a single source of truth in `session_state.trust_state`.
- Command Strip and card-level indicators both read from the same session_state key.
- No card-level trust flag is computed independently of the session-level trust_state.

**Containment:** If desync is detected (card shows DEGRADED footer while strip shows FULL), the session_state trust_state is treated as the authoritative value. Card-level indicators are derived from it — they cannot contradict it.

---

## 11. UX Anti-Patterns

### 11.1 Warning Overload

**Anti-pattern:** Showing trust warnings on every card, every section, and every panel simultaneously.

**Why harmful:** Warning fatigue — operator learns to ignore all warnings, including critical ones. Signal-to-noise collapses.

**Doctrine response:** Trust warnings appear in one primary location (Command Strip) and one contextual location (Zone 6 or card footer). They do not appear simultaneously in both the card header and the card footer. They never appear in the pick rank or score display.

### 11.2 Fake Confidence

**Anti-pattern:** Showing FULL trust indicators when one or more sources are stale.

**Why harmful:** Operator acts on data they believe is current when it is not. Silent degradation is the most dangerous failure mode.

**Doctrine response:** Any source beyond its staleness threshold immediately triggers a trust state change (FULL → PARTIAL or DEGRADED). No grace period. No softening. The operator knows immediately.

### 11.3 Panic Aesthetics

**Anti-pattern:** Flashing red alerts, pulsing banners, full-screen error overlays for recoverable degradations.

**Why harmful:** Operator stress increases. Decision quality degrades. Recoverable degradations feel like emergencies.

**Doctrine response:** Only BLOCKED state uses a crimson indicator. All other states use amber or orange — controlled colors, not alarm colors. No element pulses persistently. Degradation is communicated calmly.

### 11.4 Blocking Navigation on Data Failure

**Anti-pattern:** Preventing tab switches or view navigation when a source is unavailable.

**Why harmful:** The operator cannot investigate, cannot find alternative picks, cannot access operational tools. The system becomes unusable precisely when they need flexibility.

**Doctrine response:** Navigation is always available regardless of trust state. BLOCKED state limits deployment — not exploration.

### 11.5 Collapsing Two Signals Into One

**Anti-pattern:** Combining trust state and escalation tier into a single composite indicator ("FIRE — Restricted").

**Why harmful:** Two independent dimensions are collapsed. Operator cannot independently assess model confidence (escalation) and data quality (trust state). See `escalation_vs_suppression_doctrine.md` Section A.

**Doctrine response:** Escalation tier and trust state never share a badge, a label, or a visual zone. They appear in separate structural positions.

### 11.6 Silent Fallback

**Anti-pattern:** Activating `manual_odds.csv` or prior-year Statcast without any operator notification.

**Why harmful:** The operator believes they are acting on live data. The fallback is structurally different from live data in ways that may materially affect deployment decisions.

**Doctrine response:** All fallback activations produce an immediate, persistent indicator. Fallbacks are never silent.

### 11.7 Vague Error Messages

**Anti-pattern:** "Data unavailable — try again later." "Source error." "Unable to load."

**Why harmful:** The operator cannot diagnose the issue, cannot estimate recovery time, cannot decide whether to wait or use a different approach.

**Doctrine response:** Every trust state change includes: the specific source, the specific failure type, the fallback in use (if any), and the retry status or resolution guidance.

### 11.8 Trust Confusion at Pick Log Time

**Anti-pattern:** Logging a pick without capturing the trust state at the time of deployment.

**Why harmful:** Post-session analysis cannot determine whether a losing pick was made with FULL or RESTRICTED data. Calibration drift analysis misses an important segmentation dimension.

**Doctrine response:** `trust_state_at_log` is captured for every pick at deployment time. This field is added to `tracking/pick_tracker.py` schema. It enables post-session segmentation of full-trust vs restricted-trust deployments.

---

## 12. Recovery Workflow Hierarchy

### 12.1 BLOCKED → RESTRICTED Recovery

**Trigger:** MLB Stats API recovers. Schedule and lineup data re-validate.

**Sequence:**
1. MLB Stats API returns valid schedule response.
2. Lineup data validates (expected starter count for all games).
3. Trust state transitions BLOCKED → RESTRICTED (if other sources still degraded) or BLOCKED → DEGRADED (if MLB Stats is the only failure).
4. Command Strip indicator updates. BLOCKED banner replaced by appropriate RESTRICTED or DEGRADED banner.
5. **Operator acknowledgement required** before [Deploy] button re-enables.
6. Zone 6 shows: "MLB Stats API: recovered at [timestamp]. Review pick list for updated lineup data."

**Operator acknowledgement:** A confirmation modal or acknowledgement strip: "MLB Stats API has recovered. Pick list has been refreshed. Review before deploying." Single-click acknowledgement. Not dismissible by scroll.

### 12.2 RESTRICTED → FALLBACK / DEGRADED Recovery

**Trigger:** A primary source (Statcast, Odds API) recovers but secondary sources remain degraded.

**Sequence:**
1. Source returns valid response and passes sanity checks.
2. Trust state transitions toward FALLBACK or DEGRADED per source hierarchy.
3. Command Strip indicator updates. RESTRICTED banner updates to DEGRADED banner.
4. **No operator acknowledgement required** for this transition — non-blocking.
5. Affected picks are re-evaluated with recovered data. Model outputs refresh.
6. Zone 6 recovery note: "[Source]: recovered at [timestamp] — signals restored."
7. Recovery note clears after 60 seconds.

### 12.3 FALLBACK / DEGRADED → FULL Recovery

**Trigger:** All degraded sources recover and validate.

**Sequence:**
1. Last degraded source returns valid response.
2. Trust state transitions to FULL (or LIVE if all conditions met).
3. Command Strip indicator transitions to green.
4. All degraded banners clear.
5. All card footer notes clear.
6. Zone 6 source table shows all sources as live — then Zone 6 reverts to minimal "Data: current" display.

**No acknowledgement required.** Full recovery is the positive case. Operator does not need to confirm good news.

### 12.4 Manual Recovery Actions

When automatic recovery fails, the operator may trigger:

- **Manual retry:** Available after cooldown window. Refreshes the specific failed source.
- **Manual odds CSV upload:** Available when Odds API is unavailable. Operator loads `manual_odds.csv` via sidebar control.
- **Session restart:** Available at any time. Clears all session state and begins fresh hydration sequence.
- **Ignore and continue:** Operator acknowledges restricted trust state and continues operating with disclosed limitations.

Manual recovery actions never require operator to exit the current view. All recovery UI is accessible from the sidebar or Command Strip.

---

## 13. Final Resiliency Orchestration Summary

### 13.1 Orchestration Principle

The resiliency layer is a governance wrapper around the analytical layer. It reads source status, evaluates trust state, communicates degradation to the operator, and enforces deployment controls — without modifying any model output, any analytical signal, or any pick ranking.

The analytical layer (engine, calibration, ranking, sizing) is unchanged by trust state. The operator receives the model's best output with a clear, accurate communication of what that output was computed from.

### 13.2 The Three Guarantees

**Guarantee 1 — No silent degradation.** Every source failure produces a visible trust state change within one UI refresh cycle. No degradation is hidden from the operator.

**Guarantee 2 — No fake confidence.** No fallback data is presented as live data. No stale data is presented as fresh. Every trust indicator reflects the actual quality of the underlying data.

**Guarantee 3 — Operational continuity.** Degraded and even BLOCKED states preserve operational access. The operator can always view the slate, navigate the system, and access prior picks. Deployment is the only controlled activity.

### 13.3 The Fallback Chain

```
Live source → Stale cache → Prior-year / neutral fallback → League baseline → [Signal suppressed]
```

Each step in the chain is disclosed. No step is silent. Each step has a defined trust state.

### 13.4 The Operator Experience

The operator should feel:

- **Informed** — they know what the system is working from.
- **Protected** — they cannot accidentally deploy on silently corrupted data.
- **Operationally aware** — they can see exactly which sources are live and which are not.
- **In control** — degraded states are not emergencies; they are managed conditions.
- **Never blindsided** — every failure is visible before it affects a deployment decision.

The system that communicates its limitations earns more trust than the system that conceals them. A DEGRADED trust state that is clearly communicated is operationally safer than a false FULL trust state.

### 13.5 Room 07 Status

This document establishes the complete trust-state, degraded-state, and resiliency governance layer for MLB HR Engine v4. It extends and formalizes `deployment_trust_hierarchy.md` into a full operational doctrine.

**Cross-system coverage:**
- `deployment_trust_hierarchy.md` — foundational trust ladder (FULL/DEGRADED/RESTRICTED/BLOCKED): extended to 8-state hierarchy here.
- `escalation_vs_suppression_doctrine.md` — escalation/suppression coexistence: trust state adds a third independent dimension.
- `FULL_SLATE_UX_DOCTRINE.md` — Command Strip Zone 5 trust indicator: aligned with Section 4.2 here.
- `full_slate_parent_orchestrator_doctrine.md` — orchestration boundaries: trust state is a child concern of the parent orchestrator.
- `operator_override_doctrine.md` — LOCKDOWN override blocks in RESTRICTED state: confirmed and documented in Section 5.4 here.

**Next room:** 08 — AI Workforce & Orchestration.

---

*Document end. Doctrine only. No runtime files modified. No Streamlit or Python execution path touched. No commits made.*
