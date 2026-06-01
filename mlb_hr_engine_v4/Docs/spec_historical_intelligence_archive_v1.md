# SPEC: Historical Intelligence Archive v1
## MLB HR Engine — Step 7/12

**Version:** 1.0
**Date:** 2026-05-20
**Phase:** Step 7/12 — Deployment, Portfolio & Operations
**Status:** ARCHITECTURE / UX / DOCTRINE ONLY — no runtime code modified
**Author:** Claude (Visual Doctrine Authority)
**Cross-reference:** `deployment_command_center_doctrine.md`, `spec_post_slate_review_v1.md`, `spec_clv_intelligence_system_v1.md`, `spec_risk_governance_v1.md`
**Runtime cross-reference:** `tracking/pick_tracker.py`, `tracking/pnl.py`, `tracking/clv.py`, `tracking/line_snapshots.py`, `tracking/drift_monitor.py`

---

## A. PURPOSE

The Historical Intelligence Archive is the long-term memory of the Deployment Command Center. It stores every deployment decision, outcome, review finding, and operational note in a queryable, permanent record.

**Core doctrine:** Operators who do not record history are condemned to repeat its errors. The Archive transforms the Command Center from a day-to-day execution tool into a long-term learning system.

**The Archive answers:**
- Which deployment patterns produce the best ROI over time?
- Is CLV improving, degrading, or stable?
- Which slip categories perform best per model tier?
- Are there seasonal or market timing patterns the operator can exploit?
- What is the long-run bankroll trajectory and drawdown profile?

---

## B. ARCHIVE RECORD STRUCTURE

### Deployment History Record

Every deployed pick persists permanently in the archive. Schema extends `pick_tracker.py`:

```
Deployment Record (per pick):
──────────────────────────────────────────────────────────────────
Core identification:
  pick_id           SHA1[:12] deterministic ID
  date              YYYY-MM-DD
  player_name       Full name (normalized)
  team              3-letter abbreviation
  opponent          3-letter abbreviation
  pitcher           Opposing pitcher name
  sportsbook        Where deployed

Pre-deployment intelligence:
  escalation_tier   FIRE / STRONG / WATCH
  model_prob        Calibrated HR probability
  ev_pct            EV% at deployment
  edge_pct          Edge% at deployment
  barrel_rate       Batter barrel %
  hvy_modifier      JIG matchup modifier
  suppression_tier  NONE / LOW / MODERATE / HIGH / LOCKDOWN
  suppression_score Integer 0-100
  trust_state       FULL / DEGRADED / RESTRICTED

Deployment metadata:
  slip_category     Single / Double / Stack / Longshot / Volatile
  bet_dollars       Position size
  american_odds     Odds at deployment
  deploy_timestamp  Exact UTC timestamp
  timing_state      EARLY STRIKE / MARKET DRIFT / etc.

Market timeline:
  open_odds         Opening market odds
  deploy_odds       = american_odds
  close_odds        Closing line (~30min pre-game)
  clv_pp            Closing line value in probability points
  clv_pct_rel       CLV relative to opening probability
  timing_grade      A/B/C/D/F

Outcome:
  hr_result         0 / 1 / void
  profit_loss       $X.XX (0 if void)
  settled_date      YYYY-MM-DD

Post-slate review link:
  session_review_id Foreign key to session review record
  review_flags      List of flags from Phase 2-5 review
──────────────────────────────────────────────────────────────────
```

### Session Review Record

Every completed post-slate review persists as a session review record. Schema from `spec_post_slate_review_v1.md`:

```
Session Review Record:
──────────────────────────────────────────────────────────────────
  session_date          YYYY-MM-DD
  picks_settled         integer
  picks_won             integer
  total_pnl             float
  expected_pnl          float
  variance_pnl          float
  
  prediction_grade      STABLE / DRIFTING / ALERT
  deployment_grade      OPTIMAL / ACCEPTABLE / POOR
  sizing_grade          A / B / C / FLAG
  portfolio_grade       A / B / C / FLAG
  clv_grade             A / B / C / D / F
  
  n_eff_achieved        float
  session_timing        SHARP / EFFECTIVE / NEUTRAL / SOFT / POOR
  clv_avg_pp            float
  
  notable_flags         list[str]
  learning_notes        str (free text)
  created_at            UTC timestamp
  locked_at             UTC timestamp (24h after creation)
──────────────────────────────────────────────────────────────────
```

---

## C. BANKROLL PERFORMANCE TIMELINE

The Archive maintains a running bankroll equity curve with granularity at the session level.

```
BANKROLL TIMELINE

Date         Session P&L   Total Bankroll   Drawdown
──────────────────────────────────────────────────────
2026-04-24   -$28.50       $971.50          -2.9%
2026-04-25   +$12.00       $983.50          -1.7%
2026-04-26   SKIP                            —
2026-04-27   +$8.50        $992.00          -0.8%
2026-04-28   -$14.00       $978.00          -2.2%
...
2026-05-20   +$XX.XX       $X,XXX.XX        X.X%

Peak balance:        $1,042.00 (2026-05-03)
Current drawdown:    -X.X% from peak
Longest losing run:  3 sessions (Apr 24-28)
```

The bankroll timeline is stored as a time series. It is rendered as a sparkline in the session HUD and as a full equity curve in the Historical Intelligence Archive view.

**Drawdown metrics tracked:**
- Maximum drawdown from peak (all-time)
- Current drawdown from peak
- Average drawdown from local peaks
- Drawdown duration (sessions)
- Recovery rate (sessions from trough to new peak)

---

## D. DEPLOYMENT EFFICIENCY TRACKING

The Archive tracks deployment efficiency across five operational dimensions over time.

### 1. Selection Efficiency
The ratio of actually deployed picks to available qualified picks by tier.

```
Selection Rate by Tier (rolling 30 sessions):
  FIRE:   89% of qualified FIRE picks deployed
  STRONG: 64% of qualified STRONG picks deployed
  WATCH:  31% of qualified WATCH picks deployed
```

A declining FIRE selection rate may indicate the operator is being too cautious with high-confidence picks. A rising WATCH selection rate may indicate deployment discipline is weakening.

### 2. Timing Efficiency
Average CLV across sessions. Trend line over time. Target: flat or improving.

### 3. Sizing Discipline Rate
Percentage of picks sized within ±20% of Kelly recommendation. Target: ≥ 85%.

### 4. Override Rate
Percentage of sessions where suppression override was used. Flagged if > 30% of sessions have LOCKDOWN overrides.

### 5. Review Completion Rate
Percentage of sessions with completed post-slate reviews. Target: 100% of sessions within 48h.

---

## E. STACK PERFORMANCE ANALYTICS

The Archive maintains dedicated analytics for multi-leg deployment patterns.

### Stack Performance Table (rolling season)

```
ESCALATION STACK PERFORMANCE
────────────────────────────────────────────────────────────────
Stack Type       N     Full Win %   Partial %   Total Loss %   ROI
────────────────────────────────────────────────────────────────
Lineup 2-leg    12     8.3%         41.7%        50.0%          -8.2%
Lineup 3-leg     4     0.0%         50.0%        50.0%         -41.3%
Pitcher Target   8     25.0%        37.5%        37.5%         +12.4%
Multi-game 3+    3     0.0%         33.3%        66.7%         -55.1%
────────────────────────────────────────────────────────────────
```

**What to look for:**
- Pitcher target stacks outperforming lineup stacks (common finding — pitcher dominance or weakness affects all batters in the same direction)
- Correlation confirmation: are same-lineup picks winning and losing together as expected?
- Leg count return: does adding a leg materially improve or worsen ROI?

### N_eff Tracking
The Archive plots N_eff over time per session. A declining trend suggests increasing correlation (building more stacks, fewer diversified singles). An improving trend suggests the operator is diversifying.

---

## F. EXPLOIT TRACKING

The Archive identifies and tracks market exploit patterns — recurring edges that the operator successfully captures.

### Exploit Pattern Categories

**Pricing Inefficiencies:**
When a specific book consistently underprices a market segment (e.g., FanDuel consistently overprices ground-ball pitchers' opponent batters), this is an exploit that should be systematically targeted.

Archive query: "Show picks where book = FanDuel AND pitcher_gb_rate > 55% AND CLV > +2pp"

**Park Timing Exploits:**
Certain parks (high-altitude, hitter-friendly dimensions) may be systematically underpriced early in the day before public action pushes lines. Archive tracks this by park × timing state.

**Weather Edge Exploits:**
High-temperature, low-humidity, tailwind conditions that consistently produce positive CLV when deployed early.

**Archetype Exploits:**
Specific batter archetypes (barrel ≥ 12%, fly ball ≥ 28%, vs specific pitcher types) that consistently produce above-average CLV and ROI.

### Exploit Archive Structure

```
Exploit Entry:
  exploit_id      UUID
  pattern_type    PRICING / PARK / WEATHER / ARCHETYPE
  description     "FanDuel underprices barrel≥12% vs K-heavy pitchers"
  first_observed  YYYY-MM-DD
  n_observations  Integer (picks confirming the pattern)
  avg_clv         Float (average CLV for this pattern)
  avg_roi         Float (average ROI — track separately)
  status          ACTIVE / DEGRADING / CLOSED
  notes           Free text
```

An exploit is marked DEGRADING when its CLV falls below +0.5pp over 20 recent observations (market may have corrected). It is marked CLOSED when CLV is consistently negative.

---

## G. ADAPTIVE LEARNING OUTPUTS

The Archive generates adaptive learning outputs that feed back into future deployment decisions.

### Calibration Drift Reports
Automated: after every 50 settled picks, the Archive runs a calibration drift check (per `tracking/drift_monitor.py`). If any bucket shows > 3pp drift at n ≥ 30, a calibration alert is generated and stored in the Archive.

**Archive action:** Calibration alerts are displayed in the pre-session HUD for the next deployment session. The operator sees the drift before deploying.

### Deployment Pattern Analysis
Monthly: the Archive generates a deployment pattern report comparing:
- Average composite score of deployed picks vs abandoned picks
- Are better picks being deployed?
- Is the operator avoiding suppressed picks appropriately?

### Long-Run EV Realization
Quarterly: the Archive computes whether long-run P&L is tracking toward or away from the theoretical EV prediction.

```
Expected long-run ROI (from model EV): +8.2%
Actual long-run ROI (n=X settled): X.X%
Realization rate: XX%
```

A realization rate < 50% at n ≥ 200 is a red flag — the model may be computing edge incorrectly or the operator's deployment process is destroying theoretical edge.

---

## H. LONG-TERM HISTORICAL REVIEW SURFACES

Three surface types for operator historical review:

### 1. Session Timeline View
Chronological list of all sessions with key metrics. Quick scan of P&L, grades, N_eff, CLV trend. Color-coded by session grade.

### 2. Pattern Analysis View
Cross-tabulation analytics. Drill by: barrel tier × ROI, slip category × CLV, timing state × outcome, suppression tier × ROI (were overrides profitable?).

### 3. Equity Curve View
Full bankroll equity curve with session-level resolution. Overlay with drawdown curve. Annotate with significant events (model changes, regime shifts, high-variance sessions).

---

## I. ARCHIVE GOVERNANCE

**Immutability:** Deployment records are immutable once settled. Session review records are editable for 24 hours post-creation, then locked. Notes are always editable.

**Retention:** All records retained indefinitely. No expiry policy.

**Export:** Archive supports CSV export of deployment history, session reviews, and CLV records for external analysis.

**Privacy:** Archive lives locally in `tracking/` directory. No cloud sync unless operator explicitly configures it.

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
