# SPEC: Risk Governance Architecture v1
## MLB HR Engine — Step 7/12

**Version:** 1.0
**Date:** 2026-05-20
**Phase:** Step 7/12 — Deployment, Portfolio & Operations
**Status:** ARCHITECTURE / UX / DOCTRINE ONLY — no runtime code modified
**Author:** Claude (Visual Doctrine Authority)
**Cross-reference:** `deployment_command_center_doctrine.md`, `spec_bankroll_command_layer_v1.md`, `spec_deployment_queue_v1.md`, `spec_portfolio_exposure_system_v1.md`, `deployment_trust_hierarchy.md`, `operator_override_doctrine.md`

---

## A. PURPOSE

Risk Governance is the pervasive authority layer of the Deployment Command Center. It does not belong to any single system — it governs all of them. Every deployment decision, bankroll allocation, exposure limit, and CLV calculation operates within boundaries set by Risk Governance.

**Core doctrine:** Risk governance is not a warning system. Warnings are suggestions. Governance is enforcement. Hard stops enforce session survival. Soft gates enforce deliberation. The architecture distinguishes clearly between what the system enforces and what it advises.

---

## B. GOVERNANCE AUTHORITY HIERARCHY

Four levels of governance authority. Each level has a different enforcement mechanism.

```
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 1: HARD STOPS                                            │
│  System enforces. No override possible.                         │
│  Prevents deployment that would breach absolute limits.         │
├─────────────────────────────────────────────────────────────────┤
│  LEVEL 2: HARD GATES (operator-overridable with two steps)      │
│  System blocks until operator explicitly acknowledges.          │
│  Override is logged with timestamp and reason.                  │
├─────────────────────────────────────────────────────────────────┤
│  LEVEL 3: SOFT GATES (operator-overridable with one step)       │
│  System warns. Operator acknowledges. Deployment proceeds.     │
│  Override logged.                                               │
├─────────────────────────────────────────────────────────────────┤
│  LEVEL 4: ADVISORIES (informational, no gate)                   │
│  System surfaces information. No blocking.                      │
│  No override required.                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## C. HARD STOPS (Level 1)

These conditions prevent any deployment action. No operator action can override them. They represent absolute limits.

| Condition | Hard Stop Trigger |
|-----------|------------------|
| Trust-state = BLOCKED | Data source critical failure — cannot confirm pick validity |
| Session bankroll = 0 | No remaining session budget |
| Daily loss limit = 100% | Session loss limit reached |
| Player scratched (confirmed) | Player not in lineup per API confirmation |
| Game has started (for non-live markets) | First pitch thrown |
| Bankroll tier = SUSPENDED | Total bankroll < 10% of starting balance |

**Hard stop visual treatment:** Full-width crimson banner. `HARD STOP — DEPLOYMENT UNAVAILABLE`. All deployment controls disabled. Queue is readable but no actions available. The operator can review and plan but not execute.

---

## D. HARD GATES (Level 2)

Two-step override required. Both steps logged. Gate remains active until both steps complete.

| Condition | Hard Gate Trigger |
|-----------|------------------|
| Suppression tier = LOCKDOWN | Pitcher profile is LOCKDOWN tier |
| Trust-state = RESTRICTED + suppression ≥ HIGH | Compounding data + suppression risk |
| Bankroll tier = RECOVERY | Total bankroll ≥ 25% of starting — severely depleted |
| Daily loss limit ≥ 90% reached | Near daily limit |
| Portfolio state = OVEREXPOSED | Fragility score > 70 |
| Override rate > 50% of LOCKDOWN picks session | Systematic override abuse pattern |

**Two-step override requirement:**
1. Checkbox: "I acknowledge this condition and accept the associated risk."
2. Reason selection from drop-down (options depend on specific gate trigger).

Both steps required. After completion, deployment proceeds and the override is permanently logged in the Historical Intelligence Archive.

---

## E. SOFT GATES (Level 3)

One-step acknowledgement required. Gate resolves on acknowledgement. Logged.

| Condition | Soft Gate Trigger |
|-----------|------------------|
| Suppression tier = HIGH | Pitcher profile is HIGH tier |
| Team concentration ≥ 35% of session | Team cap approaching |
| Game concentration ≥ 45% of session | Same-game overload |
| Pitcher target count ≥ 5 picks | Pitcher dependency risk |
| Session saturation ≥ 80% | Bankroll near session limit |
| N_eff < 2.0 | Extreme portfolio correlation |
| Pick sizing > 150% of Kelly recommendation | Manual override of Kelly recommendation |

**Single acknowledgement required:**
One checkbox: "I understand this condition and choose to proceed."

---

## F. ADVISORIES (Level 4)

Informational only. No blocking, no override required. Surfaced in the HUD.

| Condition | Advisory Content |
|-----------|-----------------|
| Session saturation 60–80% | "60%+ of session bankroll deployed" |
| N_eff 2.0–4.0 | "Moderate portfolio correlation" |
| CLV session average < 0 | "Session CLV negative — review timing" |
| WATCH tier pick at full Kelly | "WATCH tier — consider reduced sizing" |
| Calibration drift alert | "Model calibration drift detected in [bucket]" |
| Trust-state = DEGRADED | "One or more data sources operating at reduced capacity" |
| 3+ consecutive losses | "3-session losing streak — review discipline" |

Advisories appear as compact inline pills or soft banner messages. They do not interrupt workflow.

---

## G. DRAWDOWN GOVERNANCE

Drawdown governance operates across three time windows simultaneously.

### Intra-Session Drawdown

Triggered when session losses reach 50% of session loss limit.

**Level 4 Advisory (50%):** "Halfway to session loss limit. Consider reviewing remaining queue quality."

**Level 3 Soft Gate (75%):** Each new deployment requires one-step acknowledgement. "Session loss: [X]% of limit."

**Level 2 Hard Gate (90%):** Two-step acknowledgement. "Session approaching limit. Remaining budget: $X.XX."

**Level 1 Hard Stop (100%):** Session halted. No further deployment.

### Rolling 5-Session Drawdown

Triggered when rolling 5-session P&L is net negative ≥ 30% of 5-session budget.

**Level 3 Soft Gate:** "Rolling 5-session loss exceeds 30% of budget. Review model calibration before continuing."

**Governor action:** Reduce Session Fraction by 1% for next 3 sessions (recommended; requires acceptance).

### Rolling 30-Session Drawdown

Triggered when 30-session ROI < -20%.

**Level 2 Hard Gate:** "30-session ROI below -20%. Full calibration review strongly recommended."

**Governor action:** Prompt post-slate review completion backlog check; prompt analyze_calibration.py run.

---

## H. EXPOSURE GOVERNANCE

Exposure governance enforces the Portfolio Exposure System's limits with governance authority.

### Hard Limits (Level 1)
- No single pick > 20% of session bankroll (absolute position cap)
- No deployment after game start for non-live markets (timing lock)
- No deployment when player confirmed DNP

### Hard Gates (Level 2)
- Portfolio state = OVEREXPOSED (fragility score > 70): two-step acknowledgement required for any new deployment
- Game concentration > 50%: two-step gate

### Soft Gates (Level 3)
- Team concentration > 35%: one-step acknowledgement
- Pitcher target count ≥ 5: one-step acknowledgement

---

## I. OVERRIDE AUDIT TRAIL

Every governance override is logged in the Historical Intelligence Archive. The audit trail includes:

```
Override Log Entry:
  date              YYYY-MM-DD
  session_id        UUID
  pick_id           Related pick (if pick-specific)
  gate_type         HARD_GATE / SOFT_GATE
  condition         Text description of what triggered the gate
  override_reason   Operator selection or free text
  timestamp         UTC datetime
  outcome           0/1/void (filled after settlement)
```

**Override performance analysis:** Monthly, the Archive generates an override performance report:
- How often were overridden picks winners vs losers?
- Is there a pattern to override abuse (e.g., always overriding LOCKDOWN and consistently missing)?
- Override rate trend: is it increasing (degrading discipline) or decreasing (improving discipline)?

**Override governance doctrine:** If the 30-session override success rate for LOCKDOWN overrides is < 20% win rate (worse than expected), the system generates a governance alert: "LOCKDOWN override accuracy below floor — review override judgment."

---

## J. SESSION PAUSE PROTOCOL

When multiple governance conditions stack simultaneously, the session enters a PAUSE state.

**PAUSE triggers (any two simultaneously):**
- Session saturation ≥ 75% AND session CLV negative
- Portfolio state ≥ CONCENTRATED AND N_eff < 3.0
- Daily loss ≥ 75% AND 3+ consecutive missed picks
- Bankroll tier = REDUCED AND daily loss ≥ 50%

**PAUSE state behavior:**
1. All new deployments blocked (Level 1 equivalent)
2. Session PAUSE banner displayed with specific trigger conditions
3. Timer: 15-minute mandatory pause before re-evaluation
4. After timer: operator receives option to continue (two-step gate) or close session

**PAUSE doctrine:** The pause is not a punishment. It is a mandatory circuit breaker. Operators who are losing money rapidly often accelerate their losses by pressing. The mandatory pause forces a break in momentum before the session compounds damage.

---

## K. GOVERNANCE DASHBOARD

The Risk Governance status is visible at all times in the session HUD as a compact status line.

```
GOVERNANCE   ●FULL ●HEALTHY ●BALANCED   [2 advisories]
```

The status line shows:
- Trust-state: FULL / DEGRADED / RESTRICTED / BLOCKED (color coded)
- Bankroll tier: HEALTHY / STABLE / CAUTION / REDUCED / RECOVERY / SUSPENDED
- Portfolio state: BALANCED / ELEVATED / CONCENTRATED / FRAGILE / OVEREXPOSED

Expanding the governance line shows the full active advisory list. Any hard gate or hard stop replaces the compact status line with a full-width banner.

---

## L. GOVERNANCE CONFIGURATION

The following governance parameters are operator-configurable within the Bankroll Command Layer:

| Parameter | Default | Min | Max |
|-----------|---------|-----|-----|
| Session Fraction | 4% | 2% | 8% |
| Daily Loss Limit | 100% of session | 50% | 100% |
| Team Concentration Cap | 35% | 20% | 50% |
| Game Concentration Cap | 45% | 30% | 60% |
| Max Picks per Session | 15 | 5 | 30 |
| Max Position per Pick | 15% of session | 5% | 20% |
| N_eff Hard Gate Threshold | 2.0 | 1.5 | 4.0 |

Parameters outside these ranges are not configurable. They represent the outer bounds of defensible governance for a single-operator deployment system.

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
