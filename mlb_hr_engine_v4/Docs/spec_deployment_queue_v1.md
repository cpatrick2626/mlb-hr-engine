# SPEC: Deployment Queue v1
## MLB HR Engine — Step 7/12

**Version:** 1.0
**Date:** 2026-05-20
**Phase:** Step 7/12 — Deployment, Portfolio & Operations
**Status:** ARCHITECTURE / UX / DOCTRINE ONLY — no runtime code modified
**Author:** Claude (Visual Doctrine Authority)
**Cross-reference:** `deployment_command_center_doctrine.md`, `spec_slip_builder_workflow_v1.md`, `spec_portfolio_exposure_system_v1.md`, `spec_deployment_panel_architecture_v1.md`, `escalation_vs_suppression_doctrine.md`, `spec_risk_governance_v1.md`

---

## A. QUEUE PURPOSE

The Deployment Queue is the pre-execution staging surface. It is not a picks list. It is not a browsing interface. It is an ordered, state-annotated queue of picks that have passed qualification and are ready for deployment consideration.

**Critical distinction:** Being in the queue is not the same as being ready to deploy. Queue items carry deployment readiness states that must be resolved before execution.

**Queue mandate:** Prevent impulsive deployment. Create deliberate pacing. Surface exposure conflicts before they happen. Sequence deployments by operational logic, not by arrival order.

---

## B. QUALIFICATION FLOW INTO QUEUE

Picks enter the queue through the qualification gate. Not all ranked picks qualify for the queue.

### Qualification Criteria

A pick enters the queue when ALL of the following are true:

| Criterion | Minimum Threshold |
|-----------|------------------|
| Escalation tier | ≥ WATCH |
| EV% | > 0% (positive expected value) |
| Edge% | ≥ 0% (model edge over market) |
| Trust-state | ≠ BLOCKED |
| Market line available | FD / DK line confirmed present |
| Game start | Not within 5 minutes |

A pick does NOT enter the queue when:
- Escalation tier = VOID (no deployment surface)
- Trust-state = BLOCKED (data failure — deployment unavailable)
- Game already started
- Player confirmed not in lineup

### Qualification-to-Queue Mapping

| Engine Output | Queue Eligibility | Queue Priority Tier |
|--------------|------------------|---------------------|
| FIRE tier, Edge ≥ 5% | Eligible | PRIORITY |
| FIRE tier, Edge 2-5% | Eligible | STANDARD |
| STRONG tier, Edge ≥ 3% | Eligible | STANDARD |
| STRONG tier, Edge 1-3% | Eligible | WATCH HOLD |
| WATCH tier, any edge | Eligible | WATCH HOLD |
| COLD tier | NOT eligible | Excluded |
| VOID tier | NOT eligible | Excluded |

Queue tiers:
- **PRIORITY** — deploy before game window closes; maximum urgency
- **STANDARD** — deploy in normal session workflow
- **WATCH HOLD** — eligible but reduced confidence; requires deliberate review before deployment

---

## C. QUEUE STATE SYSTEM

Every pick in the queue carries a deployment state. States are mutually exclusive.

```
STAGED → READY → REVIEWING → DEPLOYED
              ↓         ↓
           SUPPRESSED  ABANDONED
              ↓
           ESCALATED
```

### STAGED

Pick has entered the queue but is not yet cleared for execution. Pending checks:
- Exposure check (team/game concentration)
- Bankroll capacity check
- Correlation check (N_eff impact)

The staged state resolves automatically when checks pass or requires operator review when any check alerts.

### READY

All system checks passed. Pick is cleared for execution. Operator may proceed to the deployment panel.

### REVIEWING

Operator has opened the deployment panel for this pick. The pick is under active review. The queue displays a "REVIEWING" badge until the operator deploys or abandons.

### DEPLOYED

Pick has been confirmed and logged. The queue item grays out and moves to the bottom of the active session view. It is not removed — it remains visible as confirmation of the session's deployment history.

### SUPPRESSED

Automatic suppression conditions are active. The pick cannot move to READY without operator intervention.

Suppression conditions that trigger this state:
- Trust-state = RESTRICTED or BLOCKED
- Team concentration cap reached (N picks from same team ≥ max)
- Bankroll session cap reached (daily loss limit proximity)
- Exposure saturation warning (HHI alert threshold crossed)
- Pick is a duplicate of an already-deployed slip entry

A suppressed pick shows a suppression reason label. The operator can acknowledge and escalate (see Escalation below) or leave suppressed.

### ABANDONED

Operator reviewed and chose not to deploy. Pick is grayed and marked ABANDONED. It is not removed — abandonment is logged as a decision, not an erasure.

### ESCALATED

Operator has acknowledged a suppression condition and manually promoted the pick back to READY. Escalation is logged with the acknowledgement reason. This is an operator override, not system approval.

---

## D. QUEUE VISUAL ARCHITECTURE

### Queue Row Structure

Each queue row is a horizontal card. Fixed information density. Seven data points per row. No more.

```
┌──────────────────────────────────────────────────────────────────┐
│ [TIER] [Player Name] [Team/Opp] [MDL%] [EV%] [EDGE%] [STATUS] │
│ [Suppression badge if active]  [Urgency countdown]  [Exposure!] │
└──────────────────────────────────────────────────────────────────┘
```

**Row data points:**

1. **TIER badge** — escalation tier (FIRE / STRONG / WATCH) — color coded per escalation badge spec
2. **Player name** — full name, high-contrast primary text
3. **Team/Opponent** — team abbreviation + opponent + pitcher hand
4. **Model probability** — `MDL 18.2%` — calibrated HR probability
5. **EV%** — `EV +5.1%` — expected value at FD/DK
6. **Edge%** — `EDGE +3.8%` — model edge vs no-vig probability
7. **Status badge** — current queue state (READY / STAGED / SUPPRESSED / REVIEWING / DEPLOYED / ABANDONED)

**Secondary row (compact, visible without expanding):**

- Suppression badge (if suppression tier ≥ MODERATE)
- Game urgency countdown (`1h 22m` before first pitch)
- Exposure warning pill (if concentration alert active: `⚠ 3 NYY`)

### Row Hierarchy by Queue Priority Tier

- **PRIORITY** rows: left border `#F5A623` (amber), full contrast
- **STANDARD** rows: left border `#4a4a70` (slate), normal contrast
- **WATCH HOLD** rows: left border `#2A2A45` (muted), reduced contrast
- **DEPLOYED** rows: opacity 0.4, moved to session history section
- **ABANDONED** rows: opacity 0.3, strike-through on name

### Queue Sort Order

Default sort: composite score descending (EV × 0.35 + Edge × 0.30 + Confidence × 0.20 + Barrel Bonus × 0.15)

Operator can re-sort by:
- Game time (urgency-first)
- EV% (value-first)
- Edge% (edge-first)
- Tier (escalation-first)

Operator CANNOT sort by player name alphabetically — alphabetic sort has no operational meaning and creates cognitive noise.

---

## E. CONFIDENCE GROUPING

The queue organizes picks into three operational confidence groups. Groups are visually separated in the queue by a tactical divider.

### Group 1: ESCALATION TARGETS
- FIRE tier, Edge ≥ 4%
- Maximum deployment confidence
- Barrel ≥ 8%
- Suppression tier ≤ MODERATE
- Operator deploy priority: first

### Group 2: DEPLOYMENT CANDIDATES
- FIRE or STRONG tier, Edge ≥ 2%
- Standard deployment confidence
- Normal review required
- Operator deploy priority: second

### Group 3: WATCH POOL
- WATCH tier, any positive edge
- STRONG tier with suppression ≥ HIGH
- Reduced confidence; deploy at smaller position size or not at all
- Operator deploy priority: discretionary

The group labels are permanent fixtures in the queue layout. They are not collapsed. A slate with no Group 1 picks shows an empty Group 1 section with "No escalation targets" — this is operationally meaningful and should not be hidden.

---

## F. EXPOSURE WARNINGS IN QUEUE

The queue surfaces exposure conflicts inline — before the operator opens the deployment panel.

### Team Concentration Warning

When a team already has N ≥ 3 picks in the queue (deployed or staged), any additional pick from the same team shows an amber warning pill: `⚠ 4 NYY`

When N ≥ 4 (at cap), the pick is auto-suppressed: state changes to SUPPRESSED with reason "Team cap reached."

### Pitcher Concentration Warning

When a single pitcher is the opponent for N ≥ 3 queue picks, a blue information pill appears: `ℹ 3 vs Snell`. This is informational, not a block. The operator acknowledges it.

### Game Concentration Warning

When N ≥ 3 queue picks share the same `game_pk` (same game, different players/teams), an amber pill appears: `⚠ 3 same game`. Above N = 4, auto-suppression triggers.

### Bankroll Saturation Warning

When total deployed unit value reaches 60% of session bankroll, all WATCH HOLD picks receive a soft caution overlay. When total reaches 80%, a session saturation banner appears at the top of the queue.

---

## G. CORRELATION VISIBILITY

Every pick row in the queue shows its correlation context with other queue items.

**Stack relationship indicators:**

```
[FIRE] Aaron Judge NYY vs BOS  ...  ◉ LINKED: G. Torres, A. Rizzo
```

A `◉ LINKED` pill appears when another queue pick shares a lineup (same team as this batter). This is not a block — it is visibility. The operator knows before deploying that this pick is correlated with others already in the queue or deployed.

**N_eff impact display:**

The queue header shows real-time `N_eff` for the session. As picks are deployed, N_eff updates.

```
Session: 8 deployed  |  N_eff: 3.2  |  Correlation: HIGH
```

When N_eff drops below 4.0, an advisory appears: "High correlation — effective slate is narrow."
When N_eff drops below 2.0, a warning appears: "Extreme correlation — consider diversifying."
Neither is a hard block. Both are operator information.

---

## H. STACK RELATIONSHIPS

The queue surfaces explicit stack relationships between picks.

**Stack types identified:**

| Stack Type | Description | Visual Treatment |
|-----------|-------------|-----------------|
| SAME LINEUP | Same team batting lineup | Amber `◉ STACK` pill |
| SAME GAME | Opposing teams in same game | Blue `◉ GAME` pill |
| PITCHER TARGET | Multiple picks vs same pitcher | Teal `◉ PITCHER` pill |
| PARK CONCENTRATION | 3+ picks from same ballpark | Yellow `◉ PARK` pill |

Stack pills appear on the secondary row of each affected pick. Clicking a stack pill filters the queue to show only that stack group — useful for intentional stack construction review.

**Stack deployment doctrine:**

The system does not prevent stack deployment. It surfaces it. Intentional stacks (same lineup, correlated outcomes) are a valid deployment strategy. The operator must see them explicitly — not discover them after deployment.

---

## I. DEPLOYMENT GATING LOGIC

These conditions gate the READY state. A pick cannot become READY while any gate condition is active.

### Hard Gates (System-enforced, cannot be overridden)
- Trust-state = BLOCKED
- Game start has passed
- Player not in lineup (confirmed scratch)
- Team cap reached (N ≥ max per session configuration)

### Soft Gates (Operator-overridable)
- Suppression tier = HIGH (requires single acknowledgement)
- Suppression tier = LOCKDOWN (requires two-step acknowledgement + reason)
- Trust-state = RESTRICTED + suppression ≥ HIGH (override blocked per trust hierarchy)
- Game concentration cap reached (N ≥ 3 same-game picks)
- Session bankroll ≥ 80% deployed (saturation soft gate)

### Escalation Gate Resolution

When a soft gate is triggered, the operator encounters a gate resolution card:

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠ DEPLOYMENT GATE ACTIVE                                        │
│                                                                  │
│  SUPPRESSION TIER: HIGH — Blake Snell (LHP)                      │
│  Score: 72 · Active signals: GB DOMINANT, LOW BARREL ALLOWED    │
│                                                                  │
│  [Acknowledge and proceed to deployment]                         │
│  [Suppress this pick]                                            │
└─────────────────────────────────────────────────────────────────┘
```

Acknowledging moves the pick from SUPPRESSED to READY with the override logged. Suppressing moves the pick to SUPPRESSED with suppression reason "Operator suppressed."

---

## J. OPERATIONAL PACING RULES

The queue enforces operational pacing. Speed is the enemy of deliberation.

1. **No bulk deployment** — The queue does not support "deploy all READY" as a single action. Each pick requires individual panel review and confirmation.

2. **Review-before-next** — The queue does not present the next pick's deployment panel while another pick is in REVIEWING state. One active review at a time.

3. **Exposure re-check after each deployment** — After each deployment is confirmed, the queue pauses for 2 seconds to update exposure state before presenting the next pick as READY. The operator sees updated exposure numbers before proceeding.

4. **Group 3 pacing friction** — WATCH HOLD picks require one additional acknowledgement step before entering REVIEWING: "Confirm you are reviewing a WATCH tier pick." This is not a modal — it is an inline acknowledgement control on the pick row itself.

5. **Post-deployment count** — The queue always shows a session counter: `Deployed: 6 · Remaining: 4 · Abandoned: 2`. This prevents operators from losing track of session scope.

---

## K. SUPPRESSION RULES

Picks are suppressed by the system under these conditions. Suppression is not rejection — it is a gate requiring operator resolution.

| Trigger | Suppression Reason | Resolvable? |
|---------|-------------------|-------------|
| Team cap reached | "Team cap: 4 NYY deployed" | Yes — reduce other team picks |
| Same-game cap reached | "Game cap: 4 NYK vs BOS deployed" | Yes — operator acknowledgement |
| Bankroll saturation (80%) | "Session cap: 80% deployed" | No — session limit respected |
| Trust-state = BLOCKED | "Data unavailable" | No — until source resolves |
| Game started | "Game in progress" | No |
| Player scratched | "Player not in lineup" | No |
| Suppression tier = LOCKDOWN | "Pitcher: LOCKDOWN tier" | Yes — two-step override |
| Suppression tier = HIGH | "Pitcher: HIGH tier" | Yes — single acknowledgement |

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
