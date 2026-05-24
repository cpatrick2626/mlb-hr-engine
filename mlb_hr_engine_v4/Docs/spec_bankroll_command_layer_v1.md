# SPEC: Bankroll Command Layer v1
## MLB HR Engine — Step 7/12

**Version:** 1.0
**Date:** 2026-05-20
**Phase:** Step 7/12 — Deployment, Portfolio & Operations
**Status:** ARCHITECTURE / UX / DOCTRINE ONLY — no runtime code modified
**Author:** Claude (Visual Doctrine Authority)
**Cross-reference:** `deployment_command_center_doctrine.md`, `spec_portfolio_exposure_system_v1.md`, `spec_risk_governance_v1.md`, `spec_tactical_deployment_hud_v1.md`

---

## A. PURPOSE

The Bankroll Command Layer is the financial authority of the Deployment Command Center. It defines session budgeting, position sizing rules, loss limits, and drawdown governance.

**Critical doctrine:** The Bankroll Command Layer is independent of model confidence. A FIRE-tier pick does not unlock larger positions than the bankroll command layer authorizes. The operator who overrides bankroll rules because of confidence is conflating two independent dimensions. This is the behavior that destroys bankrolls.

---

## B. BANKROLL ARCHITECTURE

### Three-Tier Bankroll Structure

The bankroll is managed across three time scopes:

```
┌──────────────────────────────────────────────────────────────┐
│  TOTAL BANKROLL      (long-term account balance)            │
│  $X,XXX.XX           Updated at session end only           │
├──────────────────────────────────────────────────────────────┤
│  SESSION BANKROLL    (today's authorized deployment budget) │
│  $XXX.XX             Set before first deployment            │
│  = Total Bankroll × Session Fraction                        │
├──────────────────────────────────────────────────────────────┤
│  PICK UNIT           (per-pick position size recommendation)│
│  $XX.XX              Derived from Kelly + Session Bankroll  │
└──────────────────────────────────────────────────────────────┘
```

### Session Fraction Doctrine

The Session Fraction determines what percentage of total bankroll is available for a single day's deployment. Default: **4% of total bankroll per session.**

Rationale:
- At 4% session fraction, the bankroll survives 25 consecutive total-loss sessions before depleting
- Combined with quarter-Kelly pick sizing, individual pick risk is roughly 0.5–1% of total bankroll
- This is consistent with long-term survival across high-variance outcomes

Session Fraction range: 2%–8%. Outside this range requires explicit configuration override.

### Pick Unit Calculation

```
Session Bankroll = Total Bankroll × Session Fraction

Base Unit = Session Bankroll × Quarter-Kelly Fraction × Avg_Recommended_Fraction

Pick Unit = Base Unit × Confidence_Scalar
```

Where `Confidence_Scalar` is tier-adjusted:
- FIRE tier: 1.2×
- STRONG tier: 1.0×
- WATCH tier: 0.6×

The pick unit recommendation is a starting point. The operator may adjust ±50% within session. Adjustments beyond ±50% require bankroll override acknowledgement.

---

## C. BANKROLL TIER STATES

The Bankroll Command Layer assigns the session a tier state based on total bankroll health and deployment trajectory.

| Tier State | Condition | Behavioral Impact |
|-----------|-----------|------------------|
| HEALTHY | Total bankroll ≥ starting balance | No restrictions |
| STABLE | Total bankroll ≥ 75% of starting | No restrictions |
| CAUTION | Total bankroll ≥ 50% of starting | Session fraction capped at 3% |
| REDUCED | Total bankroll ≥ 25% of starting | Session fraction capped at 2%; pick unit reduced 30% |
| RECOVERY | Total bankroll < 25% of starting | Session fraction capped at 1%; Singles only; Stacks blocked |
| SUSPENDED | Total bankroll < 10% of starting | Deployment blocked pending bankroll review |

The bankroll tier state is computed at session start and does not change during a session (even if the session shows wins). It reflects the long-term state entering the session.

---

## D. SESSION BUDGETING

### Pre-Session Configuration

Before any deployment occurs, the operator confirms three session parameters:

1. **Session bankroll** — pre-calculated from total bankroll × session fraction; operator may adjust down, not up
2. **Daily loss limit** — maximum acceptable session loss; default = 100% of session bankroll (lose session bankroll, stop)
3. **Deployment cap** — maximum number of picks to deploy in this session; default = 15

These three parameters are confirmed at session start and locked for the session. They cannot be modified during an active session without a deliberate "Reauthorize Session" flow that logs the change.

### Daily Loss Limit Enforcement

The daily loss limit is tracked in real-time as picks settle (when settling occurs same-day) or as a risk proxy (total capital at risk vs limit) when real-time settlement is not available.

**Loss limit gate states:**

- **< 50% of limit** — normal operation
- **50–75% of limit reached** — advisory banner: "Halfway to session loss limit"
- **75–90% of limit reached** — soft gate on new deployments; operator sees current loss proximity before each new deployment
- **90%+ of limit reached** — all new deployments blocked except for existing READY queue items with operator acknowledgement
- **100% of limit reached** — session halted; no further deployments; operator directed to post-slate review

---

## E. KELLY-BASED SIZING TIERS

The Bankroll Command Layer provides Kelly-based sizing guidance across four tiers. These tiers correspond to the slip builder deployment categories.

### Tier 1: Primary Single Sizing

For singles deployed in the "Single Deployments" category.

```
f* = (b × p - q) / b   [Kelly formula]

Where:
  b = decimal payout - 1 (e.g., +220 = 2.20 - 1 = 1.20)
  p = model probability (calibrated)
  q = 1 - p

Quarter-Kelly = f* × 0.25

Pick Size = Session Bankroll × Quarter-Kelly
```

Example: Aaron Judge +220, model probability 21.4%
```
b = 1.20
p = 0.214
q = 0.786
f* = (1.20 × 0.214 - 0.786) / 1.20
f* = (0.2568 - 0.786) / 1.20
f* = -0.529 / 1.20 = NEGATIVE (negative edge)

This pick has negative Kelly → model says no edge.
```

Example with positive edge: +250, model probability 22%
```
b = 1.50
p = 0.22
f* = (1.50 × 0.22 - 0.78) / 1.50
f* = (0.33 - 0.78) / 1.50 = 0.30

Quarter-Kelly = 0.30 × 0.25 = 0.075 (7.5% of session bankroll)

Session bankroll = $250 → Pick size = $18.75
```

The Command Center always displays the raw Kelly fraction and the quarter-Kelly recommendation. The operator sees both — they can make an informed choice rather than blindly accepting the recommendation.

### Tier 2: Parlay Sizing
Position size for doubles and stacks is the quarter-Kelly of the combined leg probability.

```
Combined probability = p1 × p2 × ... × pN (independent assumption)
Parlay Kelly = (b_combined × p_combined - q_combined) / b_combined × 0.25

Note: Combined odds grow rapidly. Size down aggressively for stacks.
```

### Tier 3: Longshot Floor
Longshot allocation is NOT Kelly-based. It is a fixed dollar floor.

```
Longshot unit = min(Session Bankroll × 1%, $5.00)
```

Rationale: Kelly sizing at longshot odds (+350 to +600) with model probabilities (10–18%) often recommends aggressive positions that are not appropriate for high-variance long shots. The fixed floor is more conservative and prevents outlier large bets from distorting the session.

### Tier 4: Volatility Minimum
Controlled volatility picks use minimal sizing regardless of Kelly output.

```
Volatility unit = min(Session Bankroll × 2%, $10.00)
```

---

## F. DRAWDOWN GOVERNORS

Drawdown governors prevent systematic bankroll erosion. They are behavioral controls, not just analytical observations.

### Intra-Session Drawdown Governor

If the session shows losses (based on settled picks or capital at risk proxy) exceeding 50% of the session loss limit, the operator receives a **Drawdown Advisory**:

```
┌─────────────────────────────────────────────────────────────────┐
│  DRAWDOWN ADVISORY                                              │
│                                                                  │
│  Session position: −$42.50 (57% of daily loss limit)          │
│                                                                  │
│  Recommended: pause remaining deployments for 15 minutes.      │
│  Review queue quality before continuing.                        │
│                                                                  │
│  [Continue deploying]    [Pause and review]                     │
└─────────────────────────────────────────────────────────────────┘
```

The operator chooses to continue or pause. This is advisory — it does not force a stop. The acknowledgement is logged.

### Multi-Session Drawdown Governor

Tracked across rolling 7-session and 30-session windows.

| Drawdown Window | Condition | Governor Action |
|----------------|-----------|----------------|
| 3-session | Loss all 3 sessions | Advisory: review model calibration |
| 5-session | Net loss > 50% of 5-session budget | Reduce session fraction by 1% for next 3 sessions |
| 7-session | Net loss > 75% of 7-session budget | Reduce session fraction by 2%; shift to Singles only for 2 sessions |
| 30-session | Net ROI < -20% | Full bankroll review trigger; flag for calibration audit |

These governors are recommendations, not locks. The operator must actively override them if they choose to continue at normal sizing.

---

## G. RISK THRESHOLDS

Hard thresholds that the system enforces without operator override:

| Threshold | Value | Enforcement |
|-----------|-------|-------------|
| Per-pick max position | 15% of session bankroll | Hard cap — operator cannot exceed |
| Session total at risk | 100% of session bankroll | Hard cap — cannot deploy beyond session budget |
| Total bankroll at risk | 4% per session × Kelly fraction | Enforced through session fraction calculation |
| SUSPENDED state | Total bankroll < 10% | Deployment fully blocked |
| Daily loss limit | Operator-configured | Hard stop at 100% of configured limit |

Soft thresholds (operator-overridable with acknowledgement):

| Threshold | Value | Override Behavior |
|-----------|-------|------------------|
| Single pick position | 10% of session bankroll | Acknowledge + reason logged |
| Team concentration cap | 35% of session capital | Acknowledge + exposure shown |
| Session saturation | 85% deployed | Acknowledge + final confirmation |

---

## H. BANKROLL COMMAND HUD ELEMENT

The session bankroll state is always visible in the Command Center HUD. It occupies the top-right corner of the session view and is never hidden.

```
BANKROLL
─────────────────────────
Total:     $1,250.00
Session:   $50.00
At Risk:   $28.50 (57%)
Loss Limit: $50.00
State: ████████░░ 57%

Remaining: $21.50
Units left: ~1.7
─────────────────────────
```

The HUD element updates after every pick is added to or removed from the Slip Builder. The "Units left" estimate uses the current average pick unit size.

---

## I. POST-SESSION BANKROLL SETTLEMENT

At session end (when operator marks the session as complete), the Bankroll Command Layer requires a settlement reconciliation:

1. **Confirm total actual deployed capital** (sometimes differs from planned if odds changed or picks were dropped)
2. **Confirm settled results** (wins, losses, voids) if available
3. **Update total bankroll balance** for next session calculation

This reconciliation is required to keep session fraction calculations accurate. Sessions that do not reconcile accumulate as "unreconciled" and the system will flag this in the pre-session configuration for the next day.

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
