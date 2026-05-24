# SPEC: Slip Builder Workflow v1
## MLB HR Engine — Step 7/12

**Version:** 1.0
**Date:** 2026-05-20
**Phase:** Step 7/12 — Deployment, Portfolio & Operations
**Status:** ARCHITECTURE / UX / DOCTRINE ONLY — no runtime code modified
**Author:** Claude (Visual Doctrine Authority)
**Cross-reference:** `deployment_command_center_doctrine.md`, `spec_deployment_queue_v1.md`, `spec_portfolio_exposure_system_v1.md`, `spec_bankroll_command_layer_v1.md`, `spec_deployment_panel_architecture_v1.md`

---

## A. SLIP BUILDER PURPOSE

The Slip Builder is the tactical deployment tray. It is the surface where individual deployment decisions are organized into executable FanDuel entry groups before any money is committed.

The Slip Builder operates between the Deployment Queue (where picks are staged) and the physical FanDuel bet entry (where picks are executed). It is a deliberation layer, not a copy-paste tool.

**Critical doctrine:** The Slip Builder does not submit to FanDuel. It organizes picks into typed deployment categories, applies sizing, and generates a clear execution summary the operator carries to FanDuel manually. The builder prevents execution without deliberation.

---

## B. SLIP DEPLOYMENT CATEGORIES

All picks are classified into one of five mutually exclusive deployment categories. Category assignment is not automatic — the operator assigns categories during slip construction.

### Category 1: Single Deployments
**Definition:** One pick, one independent HR wager. No parlay multiplier.

**Criteria for Singles:**
- Barrel ≥ 8% (edge-quality floor for single commitments)
- Suppression tier ≤ MODERATE
- Trust-state = FULL or DEGRADED with operator acknowledgement
- Position size: full Kelly unit (as computed by bankroll command layer)

**Why this category exists:** Singles are the highest-conviction, clearest expression of model edge. They are not hedged or diluted by correlation with other picks.

**Visual treatment:** Gold border. `SINGLE` label in primary typography.

---

### Category 2: Tactical Doubles
**Definition:** Two-leg parlays combining two correlated or complementary picks.

**Criteria for Tactical Doubles:**
- Both picks: Edge ≥ 2%, Barrel ≥ 6%
- Intended correlation: either same lineup (correlated upside) or opposing game (orthogonal risk)
- At least one pick: suppression tier ≤ LOW
- Position size: half Kelly unit (reduced from singles due to parlay compounding risk)

**Pairing doctrine:**
- FIRE + FIRE pairing = maximum double; requires operator confirmation
- FIRE + STRONG pairing = standard double
- STRONG + WATCH pairing = not recommended; requires override

**Why this category exists:** Doubles exploit correlated HR events (same lineup) or diversify across games. They amplify variance intentionally. The operator should enter this category knowing they accept higher swing for higher payout.

**Visual treatment:** Blue-amber border gradient. `DOUBLE` label.

---

### Category 3: Escalation Stacks
**Definition:** Three-to-five leg parlays from a single lineup or combined high-confidence targets.

**Criteria for Escalation Stacks:**
- All picks: barrel ≥ 6%
- Minimum two picks from same lineup (stack exploitation intent)
- At least one pick: FIRE tier
- No pick: suppression ≥ LOCKDOWN in the stack
- Position size: quarter Kelly or below; this is a high-variance category

**Stack validation before building:**
The operator must see the N_eff impact of the stack before building. If the stack would reduce N_eff below 2.0 (extreme correlation), an advisory appears.

**Stack types:**
- **LINEUP STACK** — 2-3 picks from same team batting in the same game
- **PITCHER TARGET STACK** — 2-4 picks from opposing team batters vs same pitcher
- **MULTI-GAME STACK** — 3+ picks across multiple games, selected for timing convergence

**Why this category exists:** Stacks are deliberate volatility instruments. The operator who builds a stack accepts explosive upside and explicit risk of total loss. The system should not encourage stacks but must support them deliberately.

**Visual treatment:** Amber-crimson gradient border. `STACK N-LEG` label.

---

### Category 4: Longshot Exposure
**Definition:** Single picks or doubles at long odds (+300 or above) representing controlled exposure to low-probability, high-payout outcomes.

**Criteria for Longshots:**
- Odds ≥ +300
- Position size: fixed small unit (NOT Kelly-based; flat dollar amount ≤ 1% session bankroll)
- Barrel ≥ 4% (lower quality floor — longshot category has different expectations)
- Escalation tier ≥ WATCH (minimum viability floor)

**Longshot doctrine:**
Longshots are NOT the primary deployment category. They represent a controlled allocation to high-payout opportunities that the model identifies as underpriced at long odds. The system caps longshot allocation at 10% of session bankroll in aggregate. Beyond that, no new longshot entries are accepted.

**Why this category exists:** Some qualified picks carry odds above +300 where model probability significantly exceeds market-implied probability. These represent real EV but low deployment priority. The category contains them without contaminating the primary deployment flow.

**Visual treatment:** Muted violet border. `LONGSHOT` label. Odds displayed prominently.

---

### Category 5: Controlled Volatility Builds
**Definition:** Experimental multi-leg parlays at reduced position size. Used for tactical exploration, model validation, or intentional variance construction.

**Criteria for Controlled Volatility Builds:**
- Mix of tier levels (FIRE + WATCH acceptable)
- Position size: minimal (1–3% session bankroll maximum)
- No hard barrel floor; judgment-based entry
- Operator explicitly acknowledges this is an experimental allocation

**Why this category exists:** The operator may wish to test specific model hypotheses (e.g., does WATCH + FIRE parlay outperform standalone FIRE?) or construct intentional high-variance vehicles. The system should support this without contaminating primary deployment metrics. This category's results are tracked separately in historical analytics.

**Visual treatment:** Muted teal border. `VOLATILE` label. Experimental tag displayed.

---

## C. TACTICAL DEPLOYMENT TRAY — LAYOUT

The Slip Builder renders as a side panel (right side). It persists across queue interactions. The operator builds slips while simultaneously viewing the queue.

```
┌─────────────────────────────────────────────────┐
│  SLIP BUILDER                                    │
│  Session: 2026-05-20 · FanDuel                  │
├─────────────────────────────────────────────────┤
│  SINGLE DEPLOYMENTS                 [3 pending] │
│  ┌──────────────────────────────────────────┐   │
│  │ ★ FIRE  Aaron Judge     NYY  MDL:21.4%   │   │
│  │   +220  EV:+5.8%  EDGE:+4.2%  $12.50    │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │ ★ FIRE  Yordan Alvarez  HOU  MDL:19.8%   │   │
│  │   +250  EV:+4.9%  EDGE:+3.7%  $10.00    │   │
│  └──────────────────────────────────────────┘   │
│  + Add to Singles                               │
├─────────────────────────────────────────────────┤
│  TACTICAL DOUBLES                   [1 pending] │
│  ┌──────────────────────────────────────────┐   │
│  │ Judge (NYY) + Torres (NYY)  LINEUP       │   │
│  │ +800 combined · $5.00                    │   │
│  └──────────────────────────────────────────┘   │
│  + Add Double                                   │
├─────────────────────────────────────────────────┤
│  ESCALATION STACKS                  [empty]     │
│  + Build Stack                                  │
├─────────────────────────────────────────────────┤
│  LONGSHOT EXPOSURE                  [1 pending] │
│  CONTROLLED VOLATILITY              [empty]     │
├─────────────────────────────────────────────────┤
│  SLIP SUMMARY                                   │
│  Total entries: 4                               │
│  Total at risk: $32.50 / $250 session           │
│  N_eff: 2.4 (moderate correlation)              │
│  Team exposure: NYY 3 picks ⚠                  │
├─────────────────────────────────────────────────┤
│  [Review Full Slip]  [Clear Category]           │
└─────────────────────────────────────────────────┘
```

---

## D. SLIP ENTRY CONSTRUCTION

### Adding a Pick to the Slip Builder

Picks are added to the Slip Builder from the Deployment Queue, not from the queue directly. The workflow:

1. Operator opens deployment panel for a pick (queue → REVIEWING state)
2. Deployment panel Zone 9 offers: `[Deploy — log only]` or `[Add to Slip Builder]`
3. `[Add to Slip Builder]` opens a category selection sheet:

```
Select Slip Category:

○ Single Deployment     (Full Kelly · Best fit: barrel 8%+)
○ Tactical Double       (Add to existing double or start new)
○ Escalation Stack      (Add to existing stack or start new)
○ Longshot Exposure     (Capped unit · Odds +300+)
○ Controlled Volatility (Minimal unit · Experimental)

[Confirm]  [Cancel]
```

4. Pick is added to selected category. Slip Builder updates in real-time.
5. Queue item moves to DEPLOYED state once confirmed.

### Removing a Pick from the Slip Builder

Pick removal is allowed at any point before execution. Removing a pick:
- Returns it to ABANDONED state in the queue (not STAGED — abandonment is final)
- Updates slip totals and N_eff in real-time
- Logs the removal with timestamp

---

## E. CONTROLLED MULTI-SLIP ARCHITECTURE

The Slip Builder supports parallel slip construction. Multiple active slips can exist simultaneously.

**Slip types:**

| Slip Type | Description | Max Concurrent |
|-----------|-------------|---------------|
| Primary Slate Slip | Main deployment set for the slate | 1 |
| Secondary Exploration Slip | Longshot / volatile picks in separate tracking | 1 |
| Stack-Only Slip | Dedicated to escalation stack construction | 1 |

**Why multi-slip:** Primary and exploratory deployments should be tracked separately. The Primary Slate Slip's ROI should not be contaminated by experimental Controlled Volatility allocations.

**Multi-slip visibility:** The Slip Builder shows a tab bar at the top: `PRIMARY · EXPLORATORY · STACK`. Each tab shows that slip's summary. The session summary at the bottom aggregates across all active slips.

---

## F. WORKFLOW PACING

The Slip Builder enforces workflow pacing through these mechanisms:

### Review Gate Before Execution

Before the operator can finalize any slip category (mark as "ready to execute at FanDuel"), the system requires a review checkpoint:

```
┌─────────────────────────────────────────────────────────────────┐
│  REVIEW: SINGLE DEPLOYMENTS                                     │
│                                                                  │
│  3 picks · Total at risk: $32.50                               │
│  Average EV: +5.3% · Average Edge: +4.1%                       │
│  Lowest model confidence: 16.2% (P. Alonso)                    │
│  Exposure: NYY 2 of 3 picks — moderate concentration           │
│  Trust-state: FULL                                              │
│                                                                  │
│  Suppression: 1 pick faces MODERATE suppression (P. Alonso)    │
│                                                                  │
│  [Proceed to Execute]    [Back to Editing]                      │
└─────────────────────────────────────────────────────────────────┘
```

This review card is not a modal. It replaces the slip category view until the operator proceeds or returns.

### Execution Handoff

After the operator confirms the review and presses `[Proceed to Execute]`, the Slip Builder displays the **Execution Summary** — a clean, FanDuel-entry-ready list:

```
EXECUTION SUMMARY — 2026-05-20

SINGLES (enter at FanDuel — HR Yes/No):
  1. Aaron Judge (NYY) — +220 — $12.50
  2. Yordan Alvarez (HOU) — +250 — $10.00
  3. Pete Alonso (NYM) — +280 — $10.00    ← MODERATE suppression noted

DOUBLES (enter as 2-leg parlay at FanDuel):
  4. Judge + Torres 2-leg — ~+800 — $5.00

LONGSHOTS:
  5. Adolis García (TEX) — +450 — $2.50

───────────────────────────
Total at risk: $40.00
Session remaining: $210.00
───────────────────────────
[Mark All as Submitted]    [Edit]
```

`[Mark All as Submitted]` logs every pick on the list as DEPLOYED in the tracker, captures the entry timestamp, and closes the Slip Builder. This is the final action.

---

## G. DEPLOYMENT CATEGORIES — SIZING HIERARCHY

Sizing recommendations are computed by the Bankroll Command Layer and surfaced in the Slip Builder. They are not enforced — they are informed suggestions the operator may adjust.

| Category | Default Sizing Basis | Adjustment Range |
|----------|---------------------|-----------------|
| Single Deployments | Quarter-Kelly unit | 50%–150% of recommendation |
| Tactical Doubles | Half of Single unit | 25%–100% of recommendation |
| Escalation Stacks | Quarter of Single unit | 10%–50% of recommendation |
| Longshot Exposure | Fixed floor (≤1% bankroll) | Not adjustable above floor |
| Controlled Volatility | Minimal (≤2% bankroll) | Not adjustable above floor |

**Sizing override doctrine:** The operator may adjust sizing within the stated ranges. Adjustments outside the range require an explicit "Override sizing" acknowledgement. The override is logged. The system never silently accepts out-of-range sizing.

---

## H. TICKET HIERARCHY

Within each slip category, picks are ordered by deployment priority:

1. Highest composite score
2. Earliest game start time (urgency)
3. Highest EV%

Ordering within a parlay leg is:
1. Highest-confidence pick first
2. Correlated picks grouped together
3. Longshots always last in multi-leg combinations

The operator may manually reorder picks within a category. Reordering within a parlay leg does not change the math — it only affects the execution summary presentation.

---

## I. REVIEW CHECKPOINTS

Four review checkpoints occur during slip construction. None are skippable.

### Checkpoint 1: Category Assignment Confirmation
When adding a pick to a slip category, the operator confirms the category fits the pick's profile. (See Section D.)

### Checkpoint 2: Stack Correlation Warning
When building an Escalation Stack, a correlation summary appears before construction can begin. N_eff impact, team concentration, and pitcher concentration are shown. Operator proceeds or cancels.

### Checkpoint 3: Pre-Execute Category Review
Per-category review card shown before finalizing each category for execution. (See Section F.)

### Checkpoint 4: Full Slip Execution Summary
Final execution-ready summary before marking picks as submitted. No picks are logged as deployed until this summary is confirmed.

---

## J. FORBIDDEN PATTERNS

The following patterns undermine the Slip Builder's operational discipline and are explicitly rejected:

### One-Click Mass Deployment
Rejected. No "deploy all" button exists. Each category requires individual review and confirmation.

### Auto-Population of Slip Categories
Rejected. The system never auto-assigns picks to categories. The operator always chooses the category. Auto-population would bypass the deliberation the category system is designed to enforce.

### Unsized Picks
Rejected. No pick enters the slip without a size. The system prompts for sizing at category assignment if not pre-populated from the bankroll command layer.

### Silent Logging
Rejected. The Slip Builder does not log picks to the tracker without operator confirmation at Checkpoint 4. Background auto-logging is forbidden.

### Parlay Optimization Engine
Rejected. The Slip Builder does not suggest optimal parlay combinations. That is the portfolio optimizer's domain, not the execution tray's domain. The slip builder executes intent — it does not generate intent.

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
