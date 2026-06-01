# SPEC: Suppression Score Data Contract v1
**Document Type:** Data Contract  
**Spec Version:** v1  
**Status:** SPECIFICATION ONLY — no runtime code modified  
**Author:** Claude (Visual Doctrine Authority)  
**Created:** 2026-05-20  
**Phase:** Step 5/12 — Suppression Intelligence Contract & Deployment Workflow Stabilization  
**Cross-reference:** `spec_pitcher_suppression_card_v1.md`, `escalation_vs_suppression_doctrine.md`, `deployment_trust_hierarchy.md`

---

## A. CONTRACT PURPOSE

### Why Suppression Exists

The MLB HR Engine can produce a FIRE escalation tier for a batter whose underlying power metrics are genuinely strong — while that batter faces a pitcher whose profile structurally limits HR outcomes. Without a suppression layer, these two conflicting signals collapse into a single optimistic verdict. The operator deploys with false confidence.

Suppression intelligence exists to prevent that collapse. It surfaces pitcher-side risk independently of batter-side quality, giving operators both signals simultaneously so they can apply informed judgment before deployment.

### What Systems Consume Suppression

The suppression score is computed once per pitcher per session and consumed by:

1. **Pitcher Suppression Card** (`pitcher_suppression_card`) — renders tier badge, score value, signal pills, caution explanation
2. **Deployment Panel** (`deployment_panel`) — gates override controls, presents consolidated caution context
3. **Escalation vs Suppression Conflict Logic** — determines compound state display and override requirement level
4. **Full Slate View** — renders suppression tier badge adjacent to escalation badge in table rows

The suppression score is computed upstream by the data pipeline. It is passed as a pre-computed prop to all consuming components. No consuming component recalculates or modifies the score.

### Operational Trust Goals

- Operators trust suppression signals because they are consistent, legible, and deterministic
- Operators are never surprised by hidden weighting or unexplained tier promotions
- Suppression signals do not collapse batter-side confidence — they augment it with additional risk context
- The engine presents both signals. The operator adjudicates. The system does not collapse them.

### False-Positive Prevention Philosophy

The suppression system exists to flag pitchers who are structurally likely to suppress HR outcomes for any batter — not to flag pitchers who had a bad game or a small sample streak. Signal sources use rolling thresholds calibrated against MLB-wide distributions. Surface-level stats (ERA, WHIP) are excluded. Only contact-quality and batted-ball profile signals qualify.

---

## B. INPUT OWNERSHIP

All suppression inputs are owned and computed by the data pipeline (`pipeline.py`). Suppression card components receive pre-computed data only. No UI component calculates or modifies input values.

### Input Source Registry

| Signal | Owner | Source Module | Expected Format | Expected Range |
|--------|-------|---------------|-----------------|----------------|
| barrel_allowed_rate | pipeline | `clients/statcast.py` | float | 0.00–0.20 |
| gb_rate | pipeline | `clients/mlb_stats.py` | float | 0.30–0.70 |
| k_pct | pipeline | `clients/mlb_stats.py` | float | 0.10–0.45 |
| swstr_pct | pipeline | `clients/statcast.py` | float | 0.05–0.25 |
| fastball_velo_current | pipeline | `clients/statcast.py` | float (mph) | 85.0–102.0 |
| fastball_velo_season_avg | pipeline | `clients/statcast.py` | float (mph) | 85.0–102.0 |
| hvy_modifier | pipeline | `clients/pitch_mix.py` | float | 0.70–1.40 |
| platoon_iso_reduction | pipeline | `engine/probability.py` | float | 0.00–0.40 |
| wind_mph | pipeline | `clients/weather.py` | float | 0.0–40.0 |
| wind_direction | pipeline | `clients/weather.py` | str (FROM direction) | cardinal/degrees |
| pitcher_hand | pipeline | `clients/mlb_stats.py` | str | "L" or "R" |
| batter_hand | pipeline | `clients/mlb_stats.py` | str | "L" or "R" |
| pitcher_role | pipeline | `clients/mlb_stats.py` | str | "STARTER" / "OPENER" / "BULK" |
| data_source_status | pipeline | multiple clients | dict[str, str] | see Section E |

### Signal Definitions

#### Barrel Allowed Rate
- **Owner:** pipeline via `clients/statcast.py`
- **Format:** float, expressed as proportion (e.g., 0.042 = 4.2%)
- **Range:** 0.00–0.20 (league context: `LEAGUE_AVG_BARREL_RATE = 0.055`)
- **Fallback:** If Statcast unavailable, set to `None`. Score contribution for this signal = 0 (not imputed).
- **Missing-data handling:** `data_source_status["statcast"] = "UNAVAILABLE"` — trust-state downgrades to DEGRADED

#### Groundball Rate
- **Owner:** pipeline via `clients/mlb_stats.py`
- **Format:** float, expressed as proportion (e.g., 0.52 = 52%)
- **Range:** 0.30–0.70 (typical; cap at 0.70 for extreme values)
- **Fallback:** If GB rate unavailable, set to `None`. Signal score = 0.
- **Missing-data handling:** no trust-state downgrade (non-Statcast source)

#### Strikeout and SwStr Rates
- **Owner:** pipeline via `clients/mlb_stats.py` (K%) and `clients/statcast.py` (SwStr%)
- **Format:** float proportions (e.g., 0.28 = 28%)
- **K% Range:** 0.10–0.45; **SwStr% Range:** 0.05–0.25
- **Fallback:** If either missing, combined signal score = 0.
- **Missing-data handling:** K% from MLB Stats API — no trust-state impact. SwStr% from Statcast — trust-state tracks with Statcast status.

#### Velocity Signals
- **Owner:** pipeline via `clients/statcast.py`
- **Format:** float (mph) — two values: `fastball_velo_current` (3-start average) and `fastball_velo_season_avg`
- **Range:** 85.0–102.0 mph
- **Fallback:** If either value is `None`, velocity signal score = 0.
- **Missing-data handling:** Statcast unavailability. Trust-state tracks with Statcast status.

#### HVY Modifier
- **Owner:** pipeline via `clients/pitch_mix.py`
- **Format:** float in range [0.70, 1.40]
- **Range:** 0.70 (maximally unfavorable) – 1.40 (maximally favorable)
- **Fallback:** If pitch_mix unavailable, use neutral value `1.00` (no contribution).
- **Note:** HVY is display-only in the batter model — but is a real suppression input when UNFAVORABLE (≤0.88).

#### Platoon ISO Reduction
- **Owner:** pipeline via `engine/probability.py` (platoon splits)
- **Format:** float, proportion of ISO reduction vs opposite-hand pitcher (e.g., 0.18 = 18% ISO reduction)
- **Range:** 0.00–0.40
- **Fallback:** If no platoon split data, set to 0.00 (no contribution).

#### Weather Signals
- **Owner:** pipeline via `clients/weather.py`
- **Format:** `wind_mph` (float ≥ 0) and `wind_direction` (FROM direction string)
- **Wind toward home plate:** determined by `weather.py` FROM-direction logic
- **Fallback:** If weather unavailable, `wind_mph = None`. Weather signal score = 0. Trust-state tracks weather source status.

#### Pitcher Role
- **Owner:** pipeline via `clients/mlb_stats.py`
- **Format:** str: "STARTER" / "OPENER" / "BULK"
- **Suppression applies only to STARTER role.** OPENER and BULK receive no suppression score (role suppression is not meaningful for partial outings).
- **Fallback:** If role unknown, treat as STARTER for suppression scoring purposes (conservative).

#### Data Source Status
- **Owner:** pipeline
- **Format:** `dict[str, str]` — keys are source names, values are status strings
- **Valid status values:** "LIVE", "STALE", "DEGRADED", "UNAVAILABLE"
- **Consumed by:** trust-state escalation logic and UI caution rendering

---

## C. SCORE STRUCTURE

### Normalized Scale

Suppression score: integer 0–100.  
Higher score = more suppression = higher risk for HR deployment.  
Score 0 = no suppression signals active.  
Score 100 = theoretical maximum suppression (no real pitcher achieves 100 unless all signals fire simultaneously at maximum weight).

### Signal Weights

Eight approved suppression signals. Weights are additive. A pitcher can trigger multiple signals simultaneously.

| Signal | Trigger Condition | Score Points | Weight Class |
|--------|------------------|--------------|--------------|
| WEAK CONTACT ELITE | `barrel_allowed_rate` in bottom 15th percentile (≤0.037) | 15–20 | High |
| LOW BARREL ALLOWED | `barrel_allowed_rate ≤ 0.045` (below 82nd pct, above 15th pct) | 15–20 | High |
| PITCH MIX MISMATCH | `hvy_modifier ≤ 0.88` (UNFAVORABLE threshold) | 10–15 | Moderate |
| WEATHER SUPPRESSION | Wind toward home ≥ 8mph + `gb_rate ≥ 0.50` | 5–10 | Low-Moderate |
| HANDEDNESS SUPPRESSOR | Same-hand pitcher + `platoon_iso_reduction ≥ 0.15` | 10–12 | Moderate |
| GB DOMINANT | `gb_rate ≥ 0.55` | 15 | High |
| VELO SPIKE — 3-START | `fastball_velo_current − fastball_velo_season_avg ≥ 1.5` mph | 8–12 | Moderate |
| ELITE PUT-AWAY | `k_pct ≥ 0.28` AND `swstr_pct ≥ 0.13` | 15–20 | High |

**Note on overlapping barrel signals:** WEAK CONTACT ELITE and LOW BARREL ALLOWED represent different thresholds of the same metric. A pitcher in the bottom 15th percentile triggers WEAK CONTACT ELITE (15–20 pts) but NOT simultaneously LOW BARREL ALLOWED (reserved for 4.5–5.5% range). If `barrel_allowed_rate ≤ 0.037`, only WEAK CONTACT ELITE fires. If `0.037 < barrel_allowed_rate ≤ 0.045`, only LOW BARREL ALLOWED fires.

### Variable Point Assignment

For signals with ranges (e.g., 15–20 points), the exact point value is determined by severity within the signal:

- **WEAK CONTACT ELITE:** 15 pts at 10th–15th percentile, 20 pts below 10th percentile
- **LOW BARREL ALLOWED:** 15 pts at 4.0–4.5%, 18 pts at 3.0–4.0%, 20 pts below 3.0%
- **PITCH MIX MISMATCH:** 10 pts at hvy=0.85–0.88, 13 pts at hvy=0.80–0.85, 15 pts at hvy<0.80
- **WEATHER SUPPRESSION:** 5 pts at 8–12mph wind-in + moderate GB, 10 pts at >15mph wind-in + high GB rate
- **HANDEDNESS SUPPRESSOR:** 10 pts at 15–20% ISO reduction, 12 pts at >20% ISO reduction
- **VELO SPIKE:** 8 pts at 1.5–2.0mph spike, 12 pts at >2.0mph spike
- **ELITE PUT-AWAY:** 15 pts meeting both thresholds, 18 pts if K% ≥ 0.32, 20 pts if K% ≥ 0.35 AND SwStr% ≥ 0.16

### Aggregation Rules

```
raw_score = sum of all active signal point values
suppression_score = min(100, raw_score)
```

Aggregation is simple additive. No multiplicative stacking. No cross-signal bonuses. Signals are independent; their interaction effect on actual HR suppression is not modeled — only their individual contributions.

### Hard Caps

- Maximum score: 100 (hard ceiling)
- Minimum score: 0 (no negative suppression — a pitcher cannot boost HR confidence)
- A pitcher with no active signals scores exactly 0

### Suppression Floors

No suppression floor. A score of 0 is a valid and meaningful result — it means no signals fired.

The tier system maps 0–19 as NONE. A score of 0 is NONE, same as a score of 15. Both mean "no meaningful suppression."

### Escalation Interaction Rules

The suppression score does not modify the batter's escalation tier assignment. Suppression is not fed into the engine's probability model. These two systems operate independently. See `escalation_vs_suppression_doctrine.md` for conflict resolution doctrine.

---

## D. CONFIDENCE TIERS

Five tiers. Each tier maps to a deployment behavior, visual treatment, and caution language.

| Tier | Score Range | Deployment Stance | Override Required |
|------|-------------|-------------------|-------------------|
| NONE | 0–19 | No impact | No |
| LOW | 20–39 | Operator note only | No |
| MODERATE | 40–59 | Review before deploy | No |
| HIGH | 60–79 | Override required | Yes |
| LOCKDOWN | 80–100 | Explicit override required | Yes (explicit acknowledgement) |

### NONE (0–19)
No meaningful suppression. Pitcher profile does not reduce HR deployment confidence. Operator proceeds at stated escalation tier confidence. No suppression card visual emphasis.

### LOW (20–39)
Minor signal present. One signal has fired at low-to-moderate weight. Deployment confidence is nominally affected. No override required. Operator notes the signal and proceeds at judgment.

### MODERATE (40–59)
Notable risk. Multiple signals active, or one high-weight signal firing. Operator should review signal detail before deploying at full confidence. FIRE picks should be treated with STRONG-level confidence. STRONG picks require review. No override required but review is expected.

### HIGH (60–79)
Strong suppression. Multiple high-weight signals. Deployment confidence materially reduced. FIRE picks downgrade to WATCH-level deployment confidence. STRONG picks are deployment-blocked pending override. Operator must explicitly acknowledge suppression before deployment panel unlocks.

### LOCKDOWN (80–100)
Elite suppressor. Maximum suppression signals active. HR deployment against this pitcher carries structural risk regardless of batter escalation tier. No deployment proceeds without explicit operator override. Override requires deliberate acknowledgement — not a passive dismiss.

---

## E. STALE / DEGRADED STATE HANDLING

### Stale Weather Handling

If weather data age exceeds 90 minutes from game-time fetch, the weather signal is marked STALE.

**Behavior when weather STALE:**
- If weather suppression signal was ACTIVE when fresh: signal remains active in score but UI renders a staleness indicator ("Weather data may be outdated")
- If weather suppression was INACTIVE when fresh: signal remains inactive (conservative — do not add suppression for data not yet observed)
- Trust-state: weather staleness triggers DEGRADED trust (not RESTRICTED)

### Missing Statcast Handling

If `clients/statcast.py` returns no data for the pitcher:

- `barrel_allowed_rate = None`
- `swstr_pct = None`
- `fastball_velo_current = None` / `fastball_velo_season_avg = None`
- All Statcast-dependent signals score 0
- `data_source_status["statcast"] = "UNAVAILABLE"`
- Trust-state: DEGRADED

**UI behavior:** suppression card renders with "Statcast data unavailable — barrel and velocity signals suppressed" note. Score reflects only non-Statcast signals. Suppression tier may be NONE or LOW despite a genuinely high-suppression pitcher — this is acknowledged risk, not a bug.

### Degraded Confidence Behavior

When any source is DEGRADED or UNAVAILABLE:
- Suppression score reflects only available signals
- Missing signals are excluded from the total (not assumed to be zero suppression)
- The displayed score is labeled as a partial score: "Suppression score reflects available signals. Missing: [source list]."
- Trust-state degradation governs deployment panel behavior (see `deployment_trust_hierarchy.md`)

### Unavailable Source Behavior

| Source | If Unavailable | Signals Affected | Score Impact |
|--------|---------------|------------------|--------------|
| Statcast | UNAVAILABLE | WEAK CONTACT ELITE, LOW BARREL ALLOWED, VELO SPIKE, ELITE PUT-AWAY (SwStr%) | Up to −55 pts possible |
| MLB Stats API | UNAVAILABLE | GB DOMINANT, HANDEDNESS SUPPRESSOR, ELITE PUT-AWAY (K%) | Up to −27 pts possible |
| Weather | UNAVAILABLE | WEATHER SUPPRESSION | Up to −10 pts possible |
| Pitch Mix | UNAVAILABLE | PITCH MIX MISMATCH | Up to −15 pts possible |

If MLB Stats API is UNAVAILABLE, trust-state escalates to RESTRICTED (pitcher profile severely compromised).

### UI Caution Escalation Rules

| Trust State | UI Behavior |
|-------------|-------------|
| FULL | Normal suppression card rendering |
| DEGRADED | Staleness/missing indicator in suppression card header. Suppression tier badge renders with "partial" label. |
| RESTRICTED | Suppression card renders prominent data-integrity warning. Score not displayed. Tier displayed as "DATA RESTRICTED." |
| BLOCKED | Suppression card not rendered. Deployment panel shows data-blocked warning. Override not available. |

---

## F. FORBIDDEN LOGIC

The following patterns are rejected. They compromise score integrity, operator trust, and deterministic behavior.

### Hidden Weighting
Rejected. Every signal, its trigger condition, and its point contribution must be explicitly documented in this contract. No proprietary internal weighting that the operator cannot inspect. If a signal fires, its contribution must be traceable.

### Black-Box Escalation
Rejected. The tier threshold boundaries (NONE/LOW/MODERATE/HIGH/LOCKDOWN) are fixed at the values in Section D. A pitcher does not "escalate" to LOCKDOWN through an opaque process — they reach a score ≥ 80 through documented signal additions.

### Non-Deterministic Scoring
Rejected. Given the same `pitcher_data` input, `suppression_score()` must return the same score every time. No random factors. No A/B variations. No session-dependent weighting.

### Route-Owned Suppression State
Rejected. No page route computes or caches its own suppression state. The suppression score exists once, computed by the pipeline, consumed as props.

### UI-Owned Suppression Calculations
Rejected. No Streamlit component, no card renderer, no panel calculates any part of the suppression score. UI components receive the pre-computed score and render it. Period.

---

## G. IMPLEMENTATION SAFETY

### For Codex — Implementation Contract

**Function signature (required):**
```python
def suppression_score(pitcher_data: dict) -> dict:
    """
    Returns:
      {
        "score": int,          # 0–100
        "tier": str,           # "NONE" | "LOW" | "MODERATE" | "HIGH" | "LOCKDOWN"
        "signals": list[dict], # [{name, label, score_contribution, active}]
        "partial": bool,       # True if any input source was unavailable
        "missing_sources": list[str]
      }
    """
```

**Pure function requirement:** No session_state reads. No API calls. No caching side effects. Input in, output out.

**Centralized ownership:** Defined once in `engine/suppression.py` (new module). Called by `pipeline.py`. Result passed as props to all consumers.

**Deterministic calculation pipeline:**
1. Receive `pitcher_data` dict from pipeline
2. Check each signal trigger condition
3. Sum active signal contributions
4. Apply hard cap at 100
5. Map score to tier
6. Return result dict

**Render-only UI consumption:** `pitcher_suppression_card`, `deployment_panel`, Full Slate row renderer — all receive the result dict. None compute any part of it.

**Avoid component-owned score mutation:** No consuming component may modify the score for display purposes (e.g., rounding differently, applying a local override). Render the score as received.

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
