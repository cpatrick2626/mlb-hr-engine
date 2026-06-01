# ROOM 06 — DEPLOYMENT, FD SLIP & TRACKING SYSTEMS DOCTRINE
## MLB HR Engine — Phase 3A · Step 03/10

**Version:** 1.0
**Date:** 2026-05-22
**Phase:** Phase 3A Step 03 — Deployment, FD Slip & Tracking Systems
**Author:** Claude (Visual Doctrine Authority)
**Status:** DOCTRINE / ARCHITECTURE ONLY — no runtime code modified

---

## CROSS-REFERENCE MAP

This document is the governing doctrine for Room 06. It synthesizes, extends, and governs these existing specifications:

| Document | Governs |
|----------|---------|
| `deployment_command_center_doctrine.md` | Master system architecture, QUALIFY→DEPLOY→TRACK→LEARN |
| `spec_deployment_panel_architecture_v1.md` | Per-pick 9-zone panel |
| `spec_deployment_queue_v1.md` | Queue architecture, escalation states |
| `spec_slip_builder_workflow_v1.md` | FD slip workflow, categories, review gates |
| `spec_portfolio_exposure_system_v1.md` | Exposure profiling, HHI, fragility scoring |
| `spec_bankroll_command_layer_v1.md` | Bankroll tiers, Kelly sizing, session budgeting |
| `spec_clv_intelligence_system_v1.md` | CLV tracking, timing states, market timeline |
| `spec_post_slate_review_v1.md` | Post-game review workflow |
| `spec_historical_intelligence_archive_v1.md` | Long-run intelligence storage |
| `spec_risk_governance_v1.md` | Hard stops, hard gates, soft gates, advisories |
| `spec_tactical_deployment_hud_v1.md` | HUD layer architecture |
| `deployment_trust_hierarchy.md` | Trust-state ladder, degradation rules |
| `operator_override_doctrine.md` | Override authorization, two-step gate rules |

**Reading sequence for new operators:** Read this document first for orientation. Then read `deployment_command_center_doctrine.md` for system architecture. Then drill into individual specs as needed.

---

## 1. DEPLOYMENT HIERARCHY DOCTRINE

### 1.1 Operational Identity

Deployment is operational execution. It is not prediction generation, investigation, or analysis. It begins after the engine produces qualified picks and ends after all outcomes are reviewed.

The operator's operational identity during deployment:
- Constructing deliberate exposure packages
- Managing concentration and correlation discipline
- Deploying conviction with documented sizing
- Tracking execution quality independently of outcomes

### 1.2 Deployment Confidence Tiers

Seven deployment confidence tiers govern how picks are treated during queue evaluation and slip construction. These are NOT escalation tiers (FIRE/STRONG/WATCH). They are deployment-layer assessments applied by the operator based on all available signals.

```
TIER 1: CORE DEPLOYMENT
  Conditions: FIRE escalation · Suppression ≤ LOW · Trust = FULL · Barrel ≥ 10%
  Exposure: Full quarter-Kelly unit
  Slip category: Single Deployment
  Psychology: Maximum conviction. The engine and the market align. Deploy with confidence.

TIER 2: HIGH CONVICTION
  Conditions: FIRE/STRONG escalation · Suppression ≤ MODERATE · Trust ≥ DEGRADED · Barrel ≥ 8%
  Exposure: Full quarter-Kelly unit
  Slip category: Single Deployment or Tactical Double
  Psychology: Strong edge. Known and understood. Reduced uncertainty.

TIER 3: TACTICAL EXPOSURE
  Conditions: STRONG/WATCH escalation · Suppression ≤ MODERATE · Trust ≥ DEGRADED · Barrel ≥ 6%
  Exposure: Half quarter-Kelly unit
  Slip category: Tactical Double or Escalation Stack
  Psychology: Qualifiable edge. Correlated or complementary use. Sized accordingly.

TIER 4: VOLATILITY EXPOSURE
  Conditions: Any escalation tier · Suppression ≤ HIGH · Odds ≥ +300
  Exposure: Fixed floor unit (≤1% session bankroll)
  Slip category: Longshot Exposure or Controlled Volatility
  Psychology: Low-probability opportunity. Known to be a speculative play. Capped unit.

TIER 5: HEDGE LAYER
  Conditions: Operator-initiated hedge against existing position · Any tier
  Exposure: Operator-determined; offset against primary position
  Slip category: Controlled Volatility (tracked separately)
  Psychology: Risk management, not conviction. Tracks separately from prediction-quality analysis.

TIER 6: WATCHLIST ONLY
  Conditions: Qualified pick that fails one exposure or governance check
  Exposure: None deployed
  Slip category: N/A — monitored in queue, not added to slip
  Psychology: The pick may be good. The context is not right today. Log it. Watch it.

TIER 7: NO DEPLOYMENT
  Conditions: Suppression ≥ LOCKDOWN (no override) · Trust = BLOCKED · Hard stop active
  Exposure: None
  Slip category: N/A — blocked
  Psychology: Clear stop. No ambiguity. Revisit if conditions change.
```

### 1.3 Confidence → Exposure Rule

**Hard rule:** Confidence tier does NOT auto-scale bankroll aggressively.

A CORE DEPLOYMENT pick gets a full quarter-Kelly unit — not more because it is FIRE. A WATCHLIST pick gets nothing deployed — not a small unit to "stay involved." There is no sliding scale of confidence-to-exposure. The tiers govern category and slip placement. Sizing is governed by the Bankroll Command Layer.

This rule exists because:
- Aggressive confidence-scaling is emotional, not operational
- The model's confidence bands are not narrow enough to justify 2x or 3x units on high-confidence picks
- Variance in HR outcomes is high regardless of model confidence

### 1.4 Visibility Hierarchy

Operators see tiers in this order at the queue level:
1. CORE DEPLOYMENT picks at top (amber highlight, CORE badge)
2. HIGH CONVICTION picks next (blue-amber, CONVICTION badge)
3. TACTICAL EXPOSURE below (standard queue styling)
4. VOLATILITY EXPOSURE collapsed by default (expandable)
5. WATCHLIST at bottom (muted, no deployment controls visible)
6. NO DEPLOYMENT not shown in queue (visible in archive only)

---

## 2. FD SLIP CONSTRUCTION DOCTRINE

**Full specification:** `spec_slip_builder_workflow_v1.md`

This section states governing doctrine. Implementation detail lives in the spec.

### 2.1 Slip Architecture

The FanDuel slip is not a shopping cart. It is a deliberation artifact. The operator builds the slip to think through exposure, correlation, and sizing before touching FanDuel. The slip documents intent. FanDuel executes it.

Three parallel slip tracks:
- **PRIMARY SLATE SLIP** — main deployment set; tracks prediction quality
- **EXPLORATORY SLIP** — longshots and volatility plays; tracks separately
- **STACK-ONLY SLIP** — escalation stacks with correlation visibility

Performance metrics from PRIMARY SLATE SLIP are the canonical measure of operator discipline. EXPLORATORY performance is analyzed separately to avoid contaminating primary ROI with intentional speculation.

### 2.2 Grouping Logic

Picks are grouped within the slip by deployment category:

```
SINGLE DEPLOYMENTS    → independent, no correlated risk
TACTICAL DOUBLES      → explicit correlation intent stated
ESCALATION STACKS     → N_eff impact displayed before adding
LONGSHOT EXPOSURE     → capped unit, annotated
CONTROLLED VOLATILITY → experimental tag, tracked separately
```

Grouping is ALWAYS operator-assigned. The system never auto-assigns a pick to a category. Auto-population bypasses the deliberation the categories exist to enforce.

### 2.3 Stack Handling

Stack construction requires:
1. N_eff impact displayed before the first pick is added to a stack
2. Team concentration flag if ≥2 picks from same lineup
3. Pitcher concentration flag if ≥3 picks target same pitcher
4. Position size: quarter of Single unit (high-variance category)

Stack doctrine: Stacks are deliberate volatility instruments. The system supports them — it does not encourage them. A stack without deliberate rationale is an overexposed parlay with a different name.

### 2.4 Correlation Handling

Correlation risk is displayed but does not block. It informs.

The system displays:
- N_eff for the full slip and per category
- Team concentration percentage
- Same-game exposure percentage
- Pairwise correlation estimate for each Tactical Double

Correlated risk is shown in amber when N_eff < 3.0. The operator proceeds with awareness, not ignorance.

### 2.5 Anti-Overstack Rules

Hard rules:
- No single pick may exceed 20% of session bankroll (Level 1 governance)
- Escalation Stacks are capped at quarter-Kelly unit or below
- Longshot Exposure aggregate is capped at 10% of session bankroll
- LOCKDOWN suppression picks require two-step override before any slip category assignment

Soft rules (advisory, not blocking):
- Team concentration ≥ 35% generates a soft gate
- N_eff < 2.0 generates a hard gate (two-step)
- 4+ picks targeting same pitcher generates a soft gate

### 2.6 Diversification Logic

Healthy diversification targets:
- N_eff ≥ 5.0 across full slip
- No single team > 30% of deployed units
- No single game > 40% of deployed units
- Longshot allocation ≤ 10% of session total

The exposure system provides diversification advisory after each addition to the slip. The operator is never surprised by the concentration state of their slip at execution.

### 2.7 Dangerous Exposure Visibility

Dangerous exposure renders with:
- Amber border on the slip summary when N_eff < 3.0
- Orange-red border when fragility score > 50
- Crimson border and hard gate when fragility score > 70

The slip summary panel always shows:
- Total at risk ($ and % of session)
- N_eff current value
- Team exposure warning if triggered
- Trust-state if DEGRADED or worse

### 2.8 Execution Handoff

The slip does not connect to FanDuel. The final state of the slip is a clean execution summary — a human-readable list the operator carries to FanDuel manually. This is intentional. The deliberation layer and the execution platform are physically separated.

---

## 3. PORTFOLIO EXPOSURE DOCTRINE

**Full specification:** `spec_portfolio_exposure_system_v1.md`

### 3.1 Exposure Dimensions

Seven dimensions are tracked simultaneously:

| Dimension | Alert Threshold | Hard Gate |
|-----------|----------------|-----------|
| Team concentration | 20% of deployed units | 35% |
| Same-game concentration | 35% of session | 50% |
| Pitcher target count | 4 picks | 5 picks |
| N_eff | < 3.0 | < 2.0 |
| Session saturation | 60% of budget | 90% |
| HHI (barrel diversity) | > 0.20 | — |
| Fragility composite | > 50 | > 70 |

### 3.2 Duplicate Exposure Handling

When the same player appears in multiple slip categories (Single + a Tactical Double leg), the system warns: "This player appears in 2 deployment categories. Total risk across all categories: $X."

Duplicate entries are not forbidden — they represent intentional layered exposure. But they must be visible, not hidden.

### 3.3 Volatility Caps

- LONGSHOT picks: 1% session bankroll per pick, 10% session aggregate hard cap
- CONTROLLED VOLATILITY picks: 2% session bankroll per pick, 5% session aggregate
- STACK picks: quarter of Single unit per leg, full stack at or below Single unit total

### 3.4 High-Risk Grouping Visibility

When ≥3 picks share a high-risk characteristic, the system displays a grouping advisory:

```
HIGH-RISK CLUSTER DETECTED
  NYY lineup: 3 picks · Team share: 31%
  All face MODERATE suppression
  N_eff contribution: reducing overall N_eff by 1.4
```

This advisory does not block. It surfaces the cluster before the operator finalizes the slip.

### 3.5 Bankroll Pacing

Session progression is displayed as a timeline:

```
SESSION BUDGET: $250
  Deployed: $97.50 (39%)
  Remaining: $152.50
  Pace: 5 picks deployed, 3 remaining in queue
  Projected total if all queue deploys: $182.50 (73%)
```

The projection prevents the operator from depleting session budget before reviewing the full queue.

### 3.6 Diversification Thresholds

| Portfolio State | Description | Action |
|-----------------|-------------|--------|
| BALANCED | N_eff ≥ 5, no concentration alerts | Green — deploy freely |
| ELEVATED | N_eff 3–5, one mild concentration alert | Amber — monitor |
| CONCENTRATED | N_eff 2–3, one or more soft gates active | Orange — deliberate |
| FRAGILE | N_eff < 3, fragility score > 50 | Orange-red — reduce |
| OVEREXPOSED | Fragility score > 70 | Crimson — hard gate |

### 3.7 Operator Warnings

Warnings are tiered to avoid alarm fatigue:

```
ADVISORY (Level 4) — compact pill, does not interrupt
SOFT GATE (Level 3) — inline banner, one-step acknowledge
HARD GATE (Level 2) — full-panel block, two-step acknowledge
HARD STOP (Level 1) — full-width crimson, no override
```

---

## 4. CLV TRACKING DOCTRINE

**Full specification:** `spec_clv_intelligence_system_v1.md`

### 4.1 CLV as Deployment Quality Metric

CLV measures the operator's ability to exploit market inefficiency through timing. It is completely independent of game outcomes.

**Doctrine:** A pick that wins on a late, bad-price entry is a poorly timed pick. A pick that loses on an early, sharp-price entry is a well-timed pick. These two facts must be tracked separately.

### 4.2 Odds Timeline

Every deployed pick captures four timestamps:
- `OPENING` — first market price when prop was offered
- `DEPLOYED` — odds at moment of entry
- `CURRENT` — live odds at last refresh (intra-session)
- `CLOSING` — final market odds ~30 minutes before first pitch

CLV = `close_no_vig_pct - deploy_no_vig_pct` (positive = sharp entry)

### 4.3 Timing States

Six states govern timing quality:

```
EARLY STRIKE    → deployed in first 20% of market window · +1.5 to +4.0pp typical
MARKET DRIFT    → deployed 20–60% · -0.5 to +1.5pp typical
LATE STEAM      → deployed 60–90%, line moved favorably after entry · +0.5 to +2.5pp typical
PRICE COLLAPSE  → line moved against pick after entry · -2.0 to -5.0pp typical
VALUE RECOVERED → adverse movement reversed · 0 to +2.0pp typical
DEAD ENTRY      → deployed final 10%, no timing edge · -1.5 to 0pp typical
```

### 4.4 Operator Visibility

During active sessions:
- CLV HUD element shows session timing state summary
- PRICE COLLAPSE triggers amber escalation in HUD
- Aggregate negative CLV triggers soft advisory
- No timeline charts during session (cognitive load reduction)

Post-session:
- Full market movement timeline per pick
- Timing grade (A–F scale)
- Session timing verdict (SHARP → POOR)

### 4.5 Historical CLV Review

CLV is archived with these analysis dimensions:
- CLV by escalation tier (are FIRE picks deployed earlier by habit?)
- CLV by slip category (do Singles capture better CLV than Stacks?)
- CLV by day of week
- CLV by odds range
- CLV trend over rolling 30 sessions

### 4.6 Prediction vs Execution Quality Separation

**Hard doctrine:** CLV metrics and ROI metrics are NEVER combined into a single performance score.

Two separate panels in post-slate review:
- **PREDICTION QUALITY** — model accuracy, escalation tier hit rate, calibration
- **EXECUTION QUALITY** — CLV, timing states, deployment pacing, slip discipline

Mixing them obscures whether poor ROI comes from bad picks or bad timing. Operators who conflate these cannot improve.

### 4.7 CLV Capture Workflow

1. `capture_closing_lines.py` runs ~30 minutes before first pitch
2. Fetches current odds from The Odds API for all deployed picks
3. Stores as `snapshot_type=closing` in `line_snapshots.csv`
4. CLV computed: `clv_pp = close_no_vig - deploy_no_vig`
5. Written to `pick_tracker.csv` fields: `close_odds`, `close_no_vig_pct`, `clv_pp`, `clv_pct_rel`
6. CLV panel in session HUD updates

Missed automated capture: operator manually triggers CLV capture from session sidebar. Tagged `snapshot_type=manual`, flagged as potentially post-deadline.

---

## 5. PICK LIFECYCLE DOCTRINE

### 5.1 Lifecycle States

Every pick produced by the engine passes through this lifecycle. States are sequential. No pick skips a state. No state reverts to a prior state.

```
QUALIFIED → SHORTLISTED → STAGED → REVIEWING → DEPLOYED → LIVE → SETTLED → REVIEWED → ARCHIVED
```

### 5.2 State Definitions

**QUALIFIED**
- Engine has produced the pick and it passes all filter thresholds
- Available in the full engine output
- Not yet visible in the Deployment Queue
- Transitions to SHORTLISTED when operator marks it for queue

**SHORTLISTED**
- Operator has flagged the pick for queue consideration
- Visible in the Deployment Queue in staging area
- Exposure impact is computed but no deployment action has begun
- Transitions to STAGED when operator confirms queue placement

**STAGED**
- Pick is in the Deployment Queue, ranked by composite score
- Full deployment panel available on expand
- Trust-state, suppression, and exposure are live
- Transitions to REVIEWING when operator opens the deployment panel

**REVIEWING**
- Operator has opened the deployment panel for this pick
- All 9 zones are active and readable
- Timer starts (optional review pacing indicator)
- Transitions to DEPLOYED, ABANDONED, or returns to STAGED

**DEPLOYED**
- Operator has confirmed the pick via Slip Builder Checkpoint 4
- Logged in `pick_tracker.csv` with sportsbook, odds, size, timestamp
- CLV tracking begins from this point
- Transitions to LIVE when game starts

**LIVE**
- Game has started
- Pick cannot be recalled
- Market movement tracked but no new CLV capture after game start
- Transitions to SETTLED when game completes and result is known

**SETTLED**
- Game outcome applied
- `settle_pick_tracker.py` has assigned `hr_result=0/1/void` and computed P&L
- Available for post-slate review
- Transitions to REVIEWED after post-slate review is completed

**REVIEWED**
- Post-slate review completed for this pick's slate
- Prediction quality and execution quality both assessed
- Available for historical archive
- Transitions to ARCHIVED at end of session archive cycle

**ARCHIVED**
- Permanently stored in Historical Intelligence Archive
- Contributes to long-run CLV, ROI, calibration drift analysis
- Never deleted. Never modified. Read-only.

### 5.3 Non-Standard Transitions

**ABANDONED**
- Pick removed from Slip Builder before Checkpoint 4
- Returns to ABANDONED state (not STAGED — abandonment is final for this session)
- Logged with timestamp
- Visible in session log but not in active queue

**VOID**
- Game cancelled, player DNP confirmed, or data integrity failure
- `hr_result=void` logged
- P&L = $0 (no win, no loss)
- Progresses to SETTLED → REVIEWED → ARCHIVED normally
- CLV is excluded from timing efficiency analysis if voided post-deadline

### 5.4 Lifecycle Visibility in Queue

Queue filter applies lifecycle state visibility:

| Filter Mode | States Shown |
|-------------|-------------|
| ACTIVE (default) | SHORTLISTED, STAGED, REVIEWING |
| DEPLOYED | DEPLOYED, LIVE |
| SETTLED | SETTLED |
| REVIEW | REVIEWED (pending archive) |
| ARCHIVED | ARCHIVED |
| ALL | All states |

State is displayed as a compact badge on each queue card. Badge is secondary typography — not the primary information. The pick's tier and metrics are primary.

### 5.5 Deployment Memory

The system preserves deployment memory across sessions. An operator returning the next day sees:
- Yesterday's DEPLOYED picks now showing LIVE or SETTLED state
- SETTLED picks with results indicated
- ARCHIVED flag when the archive cycle runs

Deployment memory is never purged. The history is permanent.

---

## 6. DEPLOYMENT PACING DOCTRINE

**Detailed specification:** `deployment_command_center_doctrine.md` Section I

### 6.1 Pacing Principles

The system must not reward speed. Rapid deployment is an anti-pattern.

Five pacing enforcement mechanisms:

```
1. QUEUE VISIBILITY BEFORE ACTION
   Full queue must be rendered before deployment controls activate
   Prevents deploying first pick before understanding full slate exposure

2. EXPOSURE CHECK BEFORE EACH DEPLOYMENT
   Current portfolio exposure snapshot shown before every deployment decision
   Not skippable. Not dismissable without reading.

3. SEQUENTIAL DEPLOYMENT ONLY
   No "deploy all" control exists
   Each pick requires individual panel review and category assignment

4. SESSION BUDGETING BEFORE FIRST DEPLOYMENT
   Session bankroll and daily loss limit confirmed before any deployment
   Not adjustable mid-session without re-authorization

5. POST-DEPLOYMENT STATE REFLECTION
   After each deployment, portfolio exposure updates before next queue item presents
   Operator sees consequences of last decision before making next one
```

### 6.2 Urgency Escalation

When game time approaches, the system communicates escalating urgency without emotional pressure:

```
> 3 hours before pitch:    No pacing indicator. Normal queue.
90–180 min before pitch:   Compact time badge on queue card. Neutral blue.
30–90 min before pitch:    Time badge amber. "Approaching game time."
< 30 min before pitch:     Time badge orange-red. "Deploy or abandon — game approaching."
< 10 min before pitch:     Hard stop if not yet deployed. "Deployment window closed."
```

Urgency is factual, not emotional. "Game approaching" not "BET NOW." "Deployment window closed" not "You missed out!"

### 6.3 Pacing Psychology

The deployment layer should feel:
- **Disciplined** — every action requires a decision
- **Operational** — it is a tool, not entertainment
- **Intentional** — the operator chooses every step
- **Controlled** — the system governs without overpowering

Forbidden psychological patterns:
- Urgency that creates pressure to deploy without review
- Reward animations after successful deployment
- Streak-tracking that encourages volume over quality
- Loss notifications designed to provoke recovery behavior
- Session comparisons that normalize overdeployment

### 6.4 Calmness Standards

Visual calmness is a first-class concern:
- Animation is limited to functional state transitions only
- No pulsing, flashing, or breathing effects during normal operation
- Glow effects reserved for FIRE tier picks in active review — not ambient
- Background is static deep-slate; no environmental motion
- Sound is absent by default (future audio doctrine: `spec_operational_audio_future_doctrine.md`)

---

## 7. TRACKING DASHBOARD DOCTRINE

### 7.1 Dashboard Purpose

The tracking dashboard is the historical accountability layer. It answers: What did I deploy? How was it timed? How did it perform? What can I learn?

It is not:
- A live betting interface
- A live score tracker
- A prediction generator
- A bankroll manager

It is a post-execution intelligence surface.

### 7.2 Hierarchy of What Matters Most

Primary visibility (top of page, always rendered):
```
SESSION P&L       → Did this session generate positive results?
CLV AVERAGE       → Was timing execution sharp or soft?
SETTLED COUNT     → How many picks are fully resolved?
OPEN POSITIONS    → How many picks are still live?
```

Secondary visibility (below fold, expandable):
```
ESCALATION TIER BREAKDOWN    → Which tiers performed?
BARREL TIER ROI              → Which barrel quality bets paid?
SLIP CATEGORY PERFORMANCE    → Singles vs Stacks vs Longshots
BOOK PERFORMANCE             → Which sportsbook offered best realized edge?
```

Tertiary visibility (drill-down, not default):
```
INDIVIDUAL PICK TIMELINES    → CLV movement per pick
OVERRIDE PERFORMANCE         → Did overrides gain or lose?
CALIBRATION DRIFT            → Is the model drifting?
PORTFOLIO FRAGILITY HISTORY  → Did overexposure cost?
```

### 7.3 Visual Priority Rules

- P&L sign (positive/negative) is the dominant visual signal on any history card
- CLV and P&L are always in separate visual blocks — never combined into one metric
- Winning picks do NOT receive special celebration styling
- Losing picks do NOT receive punishment styling
- Both outcomes receive identical neutral styling — only numbers distinguish them

### 7.4 Historical Review Flow

Post-slate review follows this sequence (full spec: `spec_post_slate_review_v1.md`):

```
1. OUTCOME SUMMARY     → settled count, P&L, void count
2. PREDICTION REVIEW   → tier accuracy, model probability vs outcome
3. EXECUTION REVIEW    → CLV by pick, timing grade, deployment pacing
4. EXPOSURE REVIEW     → fragility score that session, concentration outcomes
5. DISCIPLINE REVIEW   → override audit, pacing adherence
6. LEARNING CAPTURE    → operator notes, flags for archive
7. ARCHIVE             → confirm all picks moved to ARCHIVED state
```

No step is optional. A session without completed post-slate review is an unlearned session.

### 7.5 Variance Visibility

Variance context is displayed alongside P&L to prevent short-run overreaction:

```
SESSION P&L: -$47.50
  Expected value at deployment: +$12.80
  Variance delta: -$60.30
  N_eff this session: 4.2
  Estimated variance band: ±$85.00 (68% confidence)
  Assessment: WITHIN EXPECTED VARIANCE
```

This prevents: adjusting the model after one bad session. It contextualizes results within expected randomness.

---

## 8. VISIBILITY AND FILTERING DOCTRINE

### 8.1 Filter Modes

Eight filter modes govern the deployment and tracking interfaces:

```
ACTIVE MODE          → SHORTLISTED, STAGED, REVIEWING picks only
DEPLOYED MODE        → DEPLOYED and LIVE picks only (no queue picks)
HIGH-CONVICTION MODE → Deployment confidence tiers 1–2 only
SETTLED MODE         → SETTLED picks only (with results)
LIVE MODE            → LIVE picks only (games in progress)
REVIEW MODE          → REVIEWED picks pending archive
ARCHIVED MODE        → ARCHIVED picks (read-only history)
ALL MODE             → All lifecycle states
```

### 8.2 Filter Isolation Rules

Hard rules for filter mode behavior:

**FILTERS NEVER ALTER:**
- Deployment history records
- Tracking records
- Performance records
- CLV calculations
- P&L figures

**FILTERS ONLY ALTER:**
- What is visible in the current view
- What is rendered in the current panel

Filtering is a display operation. It changes nothing in the underlying data. Operators who use HIGH-CONVICTION MODE and see only 3 picks do not lose data on the 12 picks that were filtered. They remain in the system, unmodified.

### 8.3 Filter Persistence

Filter state persists within a session. If the operator selects HIGH-CONVICTION MODE, it remains active until changed. Session end resets to ACTIVE MODE default.

### 8.4 Filter Combinations

Filters may be combined:

```
DEPLOYED + LIVE        → Active deployed picks in live games
SETTLED + REVIEWED     → Completed picks ready for archive
HIGH-CONVICTION + DEPLOYED → High-tier picks already committed
```

Combinations follow AND logic. Both conditions must be satisfied.

### 8.5 Dangerous Filter Patterns

The following filter patterns are flagged to prevent operator error:

```
ARCHIVED + deployment controls visible  → BLOCKED (archived picks are read-only)
SETTLED + "re-deploy" control          → BLOCKED (settled picks cannot be re-deployed)
ALL MODE during active deployment      → ADVISORY ("All-mode active — verify you are reviewing correct picks")
```

---

## 9. VALIDATION CHECKLIST

For use before implementing any deployment-layer component. All items must be verified.

### Exposure Calculation Visibility
- [ ] Team concentration % displayed on slip summary
- [ ] Game concentration % displayed on slip summary
- [ ] N_eff displayed and updates with each pick addition
- [ ] Fragility score displayed before execution confirmation
- [ ] Duplicate exposure (same player in multiple categories) flagged

### Slip Grouping
- [ ] Five category types available: Single, Double, Stack, Longshot, Volatility
- [ ] Category assignment is always operator-initiated (no auto-assignment)
- [ ] Category labels rendered with correct visual treatment per spec
- [ ] Multi-slip tabs (PRIMARY / EXPLORATORY / STACK) navigable
- [ ] Removing a pick from slip correctly transitions to ABANDONED (not STAGED)

### CLV Tracking
- [ ] `open_odds` captured at log time for each deployed pick
- [ ] `deploy_odds` captured at Checkpoint 4 confirmation
- [ ] `close_odds` populated by `capture_closing_lines.py` before first pitch
- [ ] CLV computed: `clv_pp = close_no_vig - deploy_no_vig`
- [ ] Timing state assigned (EARLY STRIKE through DEAD ENTRY)
- [ ] CLV panel in HUD updates after closing capture
- [ ] CLV and P&L displayed in separate panels — never merged

### Lifecycle Transitions
- [ ] Pick states render correctly: QUALIFIED through ARCHIVED
- [ ] No state reverts to prior state
- [ ] ABANDONED state is final (not returnable to STAGED)
- [ ] VOID picks excluded from timing efficiency analysis
- [ ] Filter modes show correct lifecycle states per mode definition

### Deployment Persistence
- [ ] `pick_tracker.csv` writes on Checkpoint 4 confirmation (not before)
- [ ] Deployment timestamp is UTC
- [ ] Session ID logged with each deployment
- [ ] Pick ID is deterministic SHA1[:12] for dedup (`pick_id` field)
- [ ] Removed picks from Slip Builder logged with removal timestamp

### Settlement Tracking
- [ ] `settle_pick_tracker.py` runs daily and resolves all past dates
- [ ] `hr_result` field: 0 (miss), 1 (hit), or void (DNP/cancelled)
- [ ] P&L computed only when `bet_dollars > 0` AND `american_odds != 0`
- [ ] Void picks show P&L = $0

### Review Flow
- [ ] Post-slate review sequence is enforced (7 steps, no skipping)
- [ ] Prediction quality and execution quality in separate sections
- [ ] Variance context (expected vs actual P&L, variance band) displayed
- [ ] Override audit included in review flow
- [ ] Session archive confirmation required before ARCHIVED state assigned

### Visibility Isolation
- [ ] Filter mode changes display only — no data modification
- [ ] Filter state persists within session, resets to ACTIVE on session end
- [ ] ARCHIVED picks are read-only: no deployment controls visible
- [ ] SETTLED picks cannot be re-deployed: re-deploy control blocked

### Mobile Degradation
- [ ] Slip Builder collapses to single-slip view on mobile
- [ ] Layer 4 HUD (session overview) persists on mobile as collapsed pill
- [ ] Tier badges and exposure alerts visible without horizontal scroll
- [ ] Review checkpoints accessible from mobile (no modal overflow)
- [ ] CLV panel collapses to single aggregate number on small screen

---

## 10. CODEX IMPLEMENTATION BOUNDARIES

### 10.1 What Codex MAY Implement

```
PERMITTED:

Persistence layer
  - Writing to pick_tracker.csv (lifecycle states, deployment records)
  - Writing to line_snapshots.csv (CLV snapshots)
  - Writing to clv_log.csv (CLV calculations)
  - Reading and writing override audit trail

Calculation layer
  - Kelly sizing computation (from bankroll command spec)
  - Exposure metrics (HHI, N_eff, fragility score)
  - CLV computation (close_no_vig - deploy_no_vig)
  - P&L calculation (bet_dollars × payout factor)

Deployment queue rendering
  - Queue card rendering with lifecycle state badge
  - Filter mode implementation (display only, no data mutation)
  - Pick ordering by composite score, then game time

Slip builder rendering
  - Five category sections with correct visual treatment
  - Multi-slip tab navigation
  - Slip summary totals (at-risk, N_eff, team concentration)
  - Review checkpoint gate rendering

Settlement
  - settle_pick_tracker.py daily settlement flow
  - MLB Stats API game log fetch for result resolution
  - Void handling

Governance enforcement
  - Hard stop rendering (deployment controls disabled)
  - Hard gate two-step acknowledgement flow
  - Soft gate one-step acknowledgement flow
  - Advisory pill rendering
```

### 10.2 What Codex MAY NOT Modify

```
PROTECTED — NO MODIFICATION WITHOUT DOCTRINE AUTHORITY REVIEW:

Routing
  - Page routing architecture
  - Navigation between MAIN and JIG contexts
  - Session routing logic

Session state ownership
  - st.session_state keys owned by MAIN orchestrator
  - Trust-state assignment and transitions
  - Hydration sequence

Cache ownership
  - Cached data sources (Statcast, MLB API, Weather)
  - Cache invalidation rules
  - Cache key namespace

Full Slate orchestration
  - Full Slate parent orchestrator logic
  - Player Card investigation flow
  - TCC batter table rendering

MAIN/JIG identity
  - MAIN vs JIG identity boundaries
  - Cross-engine command surface routing

Engine model
  - config.py model constants
  - Probability calculation pipeline
  - Calibration parameters
  - Filter threshold values

Trust-state systems
  - Trust-state ladder definitions (FULL/DEGRADED/RESTRICTED/BLOCKED)
  - Source freshness thresholds
  - Trust-state escalation rules
```

### 10.3 Protected Runtime Zones

These zones must not be touched during deployment layer implementation:

```
mlb_hr_engine_v4/engine/probability.py     → core model — no deployment logic here
mlb_hr_engine_v4/engine/calibration.py     → calibration — no deployment logic here
mlb_hr_engine_v4/api/main.py               → API routing — no deployment logic here
mlb_hr_engine_v4/api/cache.py              → cache management — no deployment logic here
app.py                                      → Streamlit orchestrator — deployment UI wires here
                                              but routing and session_state init are protected
```

### 10.4 Safe Implementation Boundaries

Codex implements deployment layer features in:

```
SAFE ZONES:

mlb_hr_engine_v4/tracking/              → CLV, settlement, P&L, pick tracking
mlb_hr_engine_v4/portfolio/             → Correlation, exposure, optimization
mlb_hr_engine_v4/deployment/            → Queue, slip builder, governance (new module if needed)
reporting/                              → Post-slate review, historical archive display
```

Any new deployment UI component in `app.py` is gated by:
1. Does it read from session_state keys it owns? (OK)
2. Does it write session_state keys owned by the orchestrator? (NOT OK — requires review)
3. Does it trigger a new API call or cache invalidation? (NOT OK — requires review)

---

## 11. UX ANTI-PATTERNS

These patterns are explicitly rejected. They contaminate the operational identity of the deployment layer.

### Sportsbook Aesthetics
- Giant green "BET NOW" buttons
- Flashing odds or "BOOST" labels
- Odds counters that spin up
- Live score tickers as primary UI
- Parlay builder "jackpot" animations

### Casino Psychology
- Streak counters ("You're on a 3-win streak!")
- Session P&L in oversized green/red numerals with animation
- "Your picks are HOT" marketing language
- Near-miss framing ("Almost won!" on SETTLED losses)
- Recovery nudges ("Recoup with this FIRE pick")

### Gambling App Feel
- Bright orange/green primary color palette
- Sports imagery (photos, team logos) as decorative background
- Fantasy sports "lineup card" metaphors
- Multiple CTAs competing for attention
- Infinite scroll on the queue (encourages passive browsing, not deliberate review)

### Fake Urgency
- Countdown timers with red flashing
- "Limited opportunity" language
- Odds labeled "moving fast"
- Game time displayed as "STARTING SOON" without exact time
- Pop-up notifications mid-deployment-review

### Overcomplicated Hierarchy
- More than 3 typography levels in any panel
- More than 4 colors in active use simultaneously
- Nested accordions deeper than 2 levels
- Tooltips that open other tooltips
- Metrics that require scrolling to compare side by side

---

## 12. RUNTIME CONTAMINATION RISKS

Risks that arise from improper deployment-layer implementation. Codex must prevent all of these.

### Session State Contamination
**Risk:** Deployment layer writes to `st.session_state` keys owned by the Full Slate orchestrator.
**Consequence:** Hydration sequence corrupted. Page reload shows stale or incorrect data.
**Prevention:** Deployment layer reads orchestrator state. Never writes to it. Owns separate `deployment_*` prefixed keys only.

### Cache Poisoning
**Risk:** CLV snapshot fetch triggers an unexpected cache invalidation, forcing a re-fetch of model data mid-session.
**Consequence:** Model re-runs mid-session. Pick order changes. Operator is viewing stale queue while model regenerates.
**Prevention:** CLV capture (`capture_closing_lines.py`) is a standalone script, not a Streamlit callback. It does not share the app's cache context.

### Pick Tracker Duplication
**Risk:** Deployment confirmation fires twice (double-click, slow response, retry). Pick logged twice.
**Consequence:** Duplicate entries in `pick_tracker.csv`. ROI double-counted. Reconciliation required.
**Prevention:** Deterministic `pick_id` = SHA1[:12] of (date + player + source_tab). Dedup on write enforced in `log_picks_bulk()`.

### Lifecycle State Regression
**Risk:** Filter mode implementation accidentally returns ARCHIVED or SETTLED picks to editable queue state.
**Consequence:** Operator sees a pick they believe is active when it is settled. Attempts to re-deploy it. Data corruption.
**Prevention:** Lifecycle state is stored in `pick_tracker.csv`. Filter mode never modifies this field. The filter reads it. It does not write it.

### CLV Timestamp Drift
**Risk:** Manual CLV capture runs after first pitch but is timestamped as "closing" rather than "manual."
**Consequence:** Late capture appears as sharp pre-deadline entry. CLV timing analysis is inflated.
**Prevention:** `snapshot_type=manual` when manually triggered. Excluded from timing efficiency analysis with flag `post_deadline=True` if run after game start.

### Governance Override Bypass
**Risk:** Two-step hard gate acknowledges step 1, then fails to log step 2 before deployment proceeds.
**Consequence:** Deployment proceeds on LOCKDOWN suppression without complete override logged. Audit trail incomplete.
**Prevention:** Deployment action at Checkpoint 4 is blocked unless both override fields are non-null in the override log entry. Atomic write — both steps or neither.

### Trust-State Mismatch
**Risk:** Trust-state computed at session start becomes stale mid-session as sources degrade. UI shows FULL trust while source is now DEGRADED.
**Consequence:** Operator deploys with false confidence in data freshness.
**Prevention:** Trust-state is refreshed at each queue expansion (when a pick's deployment panel is opened). Stale trust-state (> 15 minutes without refresh) triggers DEGRADED floor.

### Slip Builder Silent Logging
**Risk:** Slip Builder logs picks to `pick_tracker.csv` before Checkpoint 4 confirmation.
**Consequence:** Picks appear as DEPLOYED before the operator has finalized execution. Session data is incorrect.
**Prevention:** `pick_tracker.csv` write is triggered only by `[Mark All as Submitted]` at Checkpoint 4. No prior write to DEPLOYED state.

---

## 13. DEPLOYMENT WORKFLOW HIERARCHY — FINAL SUMMARY

The complete deployment workflow, from engine output to archive:

```
┌────────────────────────────────────────────────────────────────────────┐
│  ENGINE OUTPUT                                                          │
│  Ranked picks from pipeline.py · Composite score · Tier assigned       │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  QUALIFY                                                                │
│  Operator reviews full queue · Trust-state confirmed · Exposure loaded  │
│  Picks move: QUALIFIED → SHORTLISTED → STAGED                          │
│  Budget confirmed · Session loss limit set                              │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  DEPLOY                                                                 │
│  Sequential pick review · 9-zone deployment panel per pick              │
│  Suppression acknowledged (if required) · Exposure checked              │
│  Slip category assigned · Sizing confirmed                              │
│  Four review checkpoints enforced · Execution summary generated         │
│  [Mark All as Submitted] → DEPLOYED state logged in pick_tracker.csv   │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  TRACK (LIVE)                                                           │
│  CLV capture runs ~30 min before first pitch                           │
│  Timing states assigned (EARLY STRIKE through DEAD ENTRY)              │
│  Picks move: DEPLOYED → LIVE                                            │
│  Portfolio exposure held for session record                             │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  SETTLE                                                                 │
│  settle_pick_tracker.py runs daily                                     │
│  Game results fetched from MLB Stats API                               │
│  hr_result and P&L written · Void picks handled                        │
│  Picks move: LIVE → SETTLED                                             │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  REVIEW                                                                 │
│  7-step post-slate review sequence (non-skippable)                     │
│  Prediction quality assessed separately from execution quality          │
│  Variance context applied to P&L                                       │
│  Override audit reviewed · Operator notes captured                     │
│  Picks move: SETTLED → REVIEWED                                        │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  LEARN                                                                  │
│  Historical Intelligence Archive updated                               │
│  CLV trend · ROI by tier · Calibration drift · Override performance    │
│  Picks move: REVIEWED → ARCHIVED                                       │
│  Permanent. Read-only. Never deleted.                                   │
└────────────────────────────────────────────────────────────────────────┘
```

### Governing Authorities (active across all phases)

```
TRUST-STATE LADDER          → governs data confidence at every decision point
RISK GOVERNANCE HIERARCHY   → hard stops, hard gates, soft gates, advisories
DEPLOYMENT PACING DOCTRINE  → enforces sequential, deliberate execution
EXPOSURE GOVERNANCE         → fragility score, concentration caps, N_eff
OVERRIDE AUDIT TRAIL        → every governance bypass permanently logged
```

### Operator Psychological Contract

The operator who uses this system correctly:
- Constructs the slip before touching FanDuel
- Knows the exposure state of their portfolio before each deployment
- Treats CLV and P&L as separate measures of separate things
- Reviews every session — win or lose — before the next one
- Reads the variance context before adjusting anything
- Treats overrides as rare, deliberate, logged decisions — not workarounds

The system enforces this contract through structure, not trust.

---

## APPENDIX A: ROOM 06 COMPLETION CHECKLIST

Room 06 is complete when:

- [ ] Deployment hierarchy doctrine written and reviewed
- [ ] FD slip construction doctrine written and reviewed
- [ ] Portfolio exposure doctrine written and reviewed
- [ ] CLV doctrine written and reviewed
- [ ] Pick lifecycle doctrine written and reviewed (QUALIFIED → ARCHIVED)
- [ ] Deployment pacing doctrine written and reviewed
- [ ] Tracking dashboard doctrine written and reviewed
- [ ] Visibility/filtering doctrine written and reviewed
- [ ] Validation checklist produced (Section 9)
- [ ] Codex implementation boundaries defined (Section 10)
- [ ] UX anti-patterns documented (Section 11)
- [ ] Runtime contamination risks documented (Section 12)
- [ ] Final deployment workflow hierarchy summary produced (Section 13)

**Room 06 completion status: COMPLETE**
**Next room: Room 07 — Data Integrity, Trust States & Resiliency**

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
*Author: Claude (Visual Doctrine Authority) · 2026-05-22*
*Room: 06 — Deployment, FD Slip & Tracking Systems · Phase 3A Step 03/10*
