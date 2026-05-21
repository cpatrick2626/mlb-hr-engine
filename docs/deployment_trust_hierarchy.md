# Deployment Trust Hierarchy
## MLB HR Engine — Trust-State Architecture & Confidence Degradation Rules

**Version:** 1.0  
**Date:** 2026-05-20  
**Phase:** Step 5/12 — Suppression Intelligence Contract & Deployment Workflow Stabilization  
**Author:** Claude (Visual Doctrine Authority)  
**Status:** Specification only. No runtime code modified.  
**Cross-reference:** `spec_suppression_score_contract_v1.md`, `spec_deployment_panel_architecture_v1.md`, `operator_override_doctrine.md`, `escalation_vs_suppression_doctrine.md`

---

## Overview

The deployment trust hierarchy defines how the quality and availability of underlying data sources affects operator deployment confidence. A suppression score computed from complete, fresh data means something different than a suppression score computed from degraded or partial sources. A batter escalation tier computed from full Statcast data means something different than one computed without it.

The trust hierarchy makes that difference visible and operational — not hidden in footnotes.

**Core principle:** The engine never silently degrades. When source quality drops, trust-state changes visibly. Operators deploy knowing the exact confidence level of the data they are acting on.

---

## A. TRUST-STATE LADDER

Four states. Assigned at session initialization and updated dynamically as source status changes.

| State | Meaning | Triggers |
|-------|---------|---------|
| FULL | All critical sources live and fresh | All sources reporting within freshness threshold |
| DEGRADED | One or more secondary sources stale or unavailable | Statcast stale, weather stale, pitch mix unavailable |
| RESTRICTED | One or more primary sources unavailable | Statcast unavailable, MLB API degraded |
| BLOCKED | Critical primary source failure or data integrity failure | MLB API unavailable, schedule data missing |

### FULL

All sources are live and within freshness thresholds. The engine is operating at full analytical capacity. Suppression scores are complete. Calibration is current. Deployment confidence is as stated.

**Source conditions for FULL:**
- MLB Stats API: live
- Statcast: fresh (data age < 24 hours for pitcher profile, < session-start for batter stats)
- Weather: fresh (data age < 90 minutes from game time)
- Pitch Mix: available (pitch mix computed for this matchup)
- Schedule/lineup: confirmed starters available

### DEGRADED

One or more secondary sources are stale or unavailable. The engine is operating at reduced analytical capacity. Suppression scores may be partial. Some signals may be missing. Escalation tier calculations may use prior-year or fallback data.

**Conditions that trigger DEGRADED (any one sufficient):**
- Statcast data age > 24 hours (stale but not absent)
- Weather data age > 90 minutes before game time
- Pitch mix unavailable for this matchup
- Prior-year Statcast being used for batter (current-year sample insufficient)
- Any source returning degraded-quality data rather than complete unavailability

**Deployment permissions:** Full deployment available. Operator informed of specific degradation.

### RESTRICTED

One or more primary sources are unavailable. The engine is missing data that materially affects escalation tier or suppression score calculation.

**Conditions that trigger RESTRICTED (any one sufficient):**
- Statcast completely unavailable (no barrel rate, exit velocity, or SwStr% for this pitcher or batter)
- MLB Stats API returning degraded responses (partial lineup data, missing pitcher stats)
- Weather completely unavailable for an outdoor game (dome status unknown, no fallback available)
- Lineup confirmation unavailable at session start

**Deployment permissions:** Deployment available but confidence label changes ("Deploy — restricted data"). LOCKDOWN override blocked when RESTRICTED.

### BLOCKED

Data integrity failure. The engine cannot confirm basic pick validity.

**Conditions that trigger BLOCKED (any one sufficient):**
- MLB Stats API completely unavailable (no schedule, no lineup, no stats)
- Schedule data missing (game existence unconfirmed)
- Lineup data completely unavailable (player starting status unknown)
- Data integrity check failure (duplicate picks detected, P&L calculation errors)

**Deployment permissions:** Deployment blocked. [Deploy] control disabled. Panel is informational only. Resolve data source first.

---

## B. ESCALATION DECAY RULES

When trust-state degrades, the displayed escalation tier does not change — the model output is what it is. Instead, the deployment confidence interpretation changes.

| Trust State | Displayed Tier | Deployment Interpretation |
|-------------|---------------|--------------------------|
| FULL | FIRE | "High confidence. Full model capacity. Deploy at stated size." |
| DEGRADED | FIRE | "High confidence. Note: [specific source] operating at reduced capacity. Confidence may be marginally affected." |
| RESTRICTED | FIRE | "Tier computed with incomplete data. Deploy with reduced confidence. Consider smaller position size." |
| BLOCKED | FIRE | "Tier cannot be confirmed. Deployment not available until data source resolves." |

**Rule:** The tier badge does not visually change. The Zone 6 confidence layer communicates the decay. The operator sees both: what the model computed and what confidence to place in that computation.

---

## C. SUPPRESSION AMPLIFICATION RULES

Trust-state degradation can interact with suppression tier in specific ways.

### Degraded-Source Suppression Amplification

When suppression score is computed from partial sources, the available signals may understate the true suppression level.

**Suppression amplification rule:** When Statcast is UNAVAILABLE and the displayed suppression tier = LOW or NONE, a note is added to Zone 3 of the deployment panel:

> "Statcast unavailable — barrel and velocity signals cannot be evaluated. Pitcher may present higher suppression than currently displayed."

This note does not change the displayed tier. It warns the operator that the tier may be understated.

**When NOT to amplify:** If Statcast is UNAVAILABLE and the non-Statcast signals alone produce MODERATE or higher suppression, no amplification note is needed. The available signals have already flagged meaningful risk.

### Compounding Suppression + Trust Degradation

When both suppression tier ≥ HIGH and trust-state ≥ DEGRADED are active simultaneously:

- Both signals render independently (Zone 3 and Zone 6)
- No combined signal collapse
- Override controls remain active (unless RESTRICTED + LOCKDOWN — blocked per operator override doctrine)
- The operator receives both signals: "This pitcher is a high suppressor, AND your data confidence is reduced"

---

## D. DEGRADED-SOURCE PENALTIES

Specific source unavailability impacts displayed confidence language in Zone 6 of the deployment panel.

| Source | Status | Confidence Penalty Label |
|--------|--------|--------------------------|
| Statcast | STALE (>24h) | "Barrel and velocity signals based on data from [age]. May not reflect recent trends." |
| Statcast | UNAVAILABLE | "Barrel, exit velocity, and swing-miss signals unavailable. Power assessment is partially blind." |
| Weather | STALE (>90min) | "Weather data may be outdated. Wind and temperature factors reflect conditions from [timestamp]." |
| Weather | UNAVAILABLE | "Weather data unavailable. Environmental suppression signals cannot be evaluated for outdoor game." |
| Pitch Mix | UNAVAILABLE | "HVY modifier unavailable. Pitch mix mismatch signal cannot be evaluated for this matchup." |
| MLB Stats API | DEGRADED | "Pitcher and lineup data may be incomplete. Stats-based suppression signals reduced." |

---

## E. UNAVAILABLE-SOURCE PENALTIES

When a source transitions from DEGRADED to UNAVAILABLE:

**Statcast UNAVAILABLE impact on escalation tier:**
- Batter `power_mult` computed without Statcast barrel/EV signals
- Falls back to prior-year data if available, or league-average blend
- Displayed tier may be lower than with full Statcast (conservative)
- Zone 6 label: "Batter power assessment uses prior-year or baseline data — current-year barrel performance unconfirmed."

**Statcast UNAVAILABLE impact on suppression score:**
- Signals zeroed: WEAK CONTACT ELITE, LOW BARREL ALLOWED, VELO SPIKE, ELITE PUT-AWAY (SwStr%)
- Maximum score achievable from remaining signals: ~52 (GB DOMINANT + PITCH MIX MISMATCH + HANDEDNESS + WEATHER)
- A pitcher who would score 80+ (LOCKDOWN) with full Statcast might score only 40–55 (MODERATE) without it
- The suppression tier may genuinely understate the pitcher's quality — and the operator is warned

**MLB Stats API UNAVAILABLE impact:**
- Escalation tier cannot be computed — BLOCKED trust-state triggers
- Deployment panel closes to information-only mode
- No deployment action available

---

## F. STALE-DATA HANDLING

Stale data is data that exists but is outdated beyond an acceptable threshold.

### Staleness Thresholds

| Source | Stale Threshold | Trust-State Impact |
|--------|-----------------|-------------------|
| Statcast (pitcher profile) | > 24 hours | DEGRADED |
| Statcast (batter season) | > 48 hours | DEGRADED |
| Weather | > 90 minutes before game time | DEGRADED |
| Pitcher stats (MLB API) | > 48 hours | DEGRADED |
| Lineup confirmation | > 2 hours before game time | DEGRADED |
| Lineup confirmation | > 30 minutes before game time | RESTRICTED |

### Staleness Display

Stale data is displayed in Zone 6 with timestamp:

> "Statcast data: stale (last updated 31 hours ago)"

The timestamp is always displayed when staleness threshold is exceeded. "Approximate" or vague age descriptions ("a couple days ago") are rejected. Exact timestamps are required.

---

## G. DEPLOYMENT VISIBILITY RULES

Trust-state governs what the operator sees in the deployment panel. This table summarizes the complete panel behavior by state.

| Zone | FULL | DEGRADED | RESTRICTED | BLOCKED |
|------|------|----------|------------|---------|
| Zone 1 (Header) | Normal | Normal | Normal | Normal + blocked banner |
| Zone 2 (Escalation) | Normal | Normal + note | "Partial data" label | Grayed — tier unconfirmed |
| Zone 3 (Suppression) | Normal | Normal + staleness note | "Partial signal data" label | Hidden — data unavailable |
| Zone 4 (Tactical) | Normal | Normal | Collapsed by default | Hidden |
| Zone 5 (Risk Factors) | Normal | + source-specific warnings | + source failure warning | Simplified — data limited |
| Zone 6 (Confidence) | "Data: Current" green | Amber indicator + source table | Orange-red indicator + source table | Crimson indicator + resolution guidance |
| Zone 7 (Override) | Per suppression tier | Per suppression tier + staleness note | Available (HIGH) / Blocked (LOCKDOWN) | Hidden |
| Zone 8 (Exposure) | Normal | Normal | Simplified | Hidden |
| Zone 9 (Action) | [Deploy] active | [Deploy] active | [Deploy — restricted data] active | [Deploy] blocked |

---

## H. COMPOUND STATE EXAMPLES

### Example 1: FIRE Hitter + Degraded Weather

**Situation:** FIRE escalation tier. Suppression = LOW. Weather data is 3 hours stale.

**Trust-state:** DEGRADED (weather stale threshold exceeded)

**Zone 2 display:** "FIRE tier. High confidence. Weather data from 3 hours ago — environmental factors may have shifted."

**Zone 3 display:** LOW suppression. Tier and score visible. Weather suppression signal shows "Weather: stale — WEATHER SUPPRESSION signal based on outdated data."

**Zone 6 display:** Amber indicator. "Weather: stale (3h 12m ago). All other sources current."

**Override required:** No (LOW suppression, no override threshold). Operator is informed of weather staleness but deploys normally.

**Deployment stance:** FIRE confidence with weather caveat. Operator should check current conditions independently if wind is a meaningful factor for this park.

---

### Example 2: STRONG Matchup + Stale Statcast

**Situation:** STRONG escalation tier. Suppression = MODERATE. Statcast data is 30 hours old.

**Trust-state:** DEGRADED (Statcast stale >24h)

**Zone 2 display:** "STRONG tier. High confidence. Statcast power signals based on data 30 hours old."

**Zone 3 display:** MODERATE suppression. Amber border. "Note: Barrel and velocity signals use data from 30 hours ago. Suppression tier may understate current pitcher profile."

**Zone 6 display:** Amber indicator. "Statcast: stale (30 hours). Weather: current. MLB API: current."

**Override required:** No (MODERATE suppression). But DEGRADED trust adds context — the suppression tier might be understated.

**Deployment stance:** STRONG confidence, MODERATE suppression, with acknowledgement that suppression signals are working from day-old data. Operator may choose to reduce position size marginally.

---

### Example 3: WATCH Hitter + Blocked Source

**Situation:** WATCH escalation tier. Suppression = HIGH. MLB Stats API partially degraded (pitcher stats not fully returned).

**Trust-state:** RESTRICTED (MLB Stats API degraded — pitcher stats partial)

**Zone 2 display:** "WATCH tier. Marginal edge — review before deployment. Pitcher stats partially unavailable."

**Zone 3 display:** HIGH suppression. Zone 3 header shows "Partial signal data — pitcher stats incomplete." Visible signals: those computable from available data (weather, HVY, handedness). Missing: GB-based signals, K%.

**Zone 6 display:** Orange-red indicator. "MLB Stats API: degraded. Pitcher groundball rate and strikeout data unavailable."

**Zone 7 display:** Override controls visible (HIGH suppression). Added note: "Source restriction: override available but suppress score reflects partial data."

**Override required:** Yes (HIGH suppression). LOCKDOWN override would be blocked in RESTRICTED state.

**Deployment stance:** WATCH tier already marginal. HIGH suppression (partial score). RESTRICTED data. Strong caution — operator should consider abandoning this pick rather than deploying under compounded uncertainty.

---

### Example 4: LOCKDOWN Suppression + Missing Pitch Mix

**Situation:** FIRE escalation tier. Suppression = LOCKDOWN (score 82 from Statcast signals + GB + K%). Pitch Mix unavailable (HVY modifier not computed).

**Trust-state:** DEGRADED (pitch mix unavailable)

**Zone 2 display:** "FIRE tier. High confidence."

**Zone 3 display:** LOCKDOWN suppression (crimson, 3px left border, score 82). "Note: HVY modifier unavailable — pitch mix signal not evaluated. Suppression score from barrel, GB, and put-away signals."

**Zone 6 display:** Amber indicator. "Pitch mix: unavailable for this matchup. Score reflects 5 of 8 possible signals."

**Zone 7 display:** LOCKDOWN override controls (two-step). "Override reflects partial suppression evaluation — pitch mix signal is missing."

**Override required:** Yes (LOCKDOWN). LOCKDOWN override available because trust-state = DEGRADED (not RESTRICTED).

**Deployment stance:** LOCKDOWN is LOCKDOWN even without pitch mix. The available signals (barrel allowed, GB rate, elite put-away) are sufficient to establish LOCKDOWN tier independently. Missing pitch mix might mean the true score is even higher. This pick requires deliberate override. Operator should consider that suppression may be understated.

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
