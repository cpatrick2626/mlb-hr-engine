# Operator Override Doctrine
## MLB HR Engine — Intentional Suppression Bypass Rules

**Version:** 1.0  
**Date:** 2026-05-20  
**Phase:** Step 5/12 — Suppression Intelligence Contract & Deployment Workflow Stabilization  
**Author:** Claude (Visual Doctrine Authority)  
**Status:** Specification only. No runtime code modified.  
**Cross-reference:** `spec_suppression_score_contract_v1.md`, `spec_deployment_panel_architecture_v1.md`, `deployment_trust_hierarchy.md`, `escalation_vs_suppression_doctrine.md`

---

## Overview

Override is the mechanism by which an operator intentionally proceeds with a deployment despite an active suppression signal that would otherwise block or caution the action.

Override is not a bypass of the system. It is a deliberate, documented operator decision to accept risk that the system has surfaced. The engine does not block the operator — it informs the operator and requires them to own the decision.

**Core doctrine:** The engine presents the risk. The operator accepts or rejects it. Override makes that acceptance visible, deliberate, and logged.

---

## A. OVERRIDE ELIGIBILITY

Override is available when and only when:

1. **Suppression tier = HIGH or LOCKDOWN** — the only suppression tiers that require operator acknowledgement before deployment proceeds
2. **Escalation tier ≠ VOID** — no deployment surface exists for VOID picks; override is not applicable
3. **Escalation tier ≠ COLD** — COLD picks have failed engine filters; override of suppression does not change the filter failure
4. **Trust-state ≠ BLOCKED** — data source integrity failure prevents confident deployment; override of suppression cannot resolve missing data

Override is NOT available for:
- MODERATE, LOW, or NONE suppression tiers (no override needed — operator proceeds at judgment)
- VOID escalation tier (no deployment action available)
- COLD escalation tier (filter failure governs — suppression override is irrelevant)
- Trust-state BLOCKED (data resolution required first)
- OPENER or BULK pitcher roles (suppression scoring is inapplicable to partial outings)

---

## B. OVERRIDE FRICTION PHILOSOPHY

Override friction is deliberate. It is not a UX failure to be smoothed away.

The friction level scales with suppression severity. LOW risk requires no friction. HIGH risk requires one deliberate step. LOCKDOWN requires two deliberate steps plus a reason.

**Why friction exists:**

A single-click deploy on a LOCKDOWN pick is a failure of operator judgment infrastructure. The operator should feel the resistance of the system before proceeding. That resistance is proportional to the structural risk being accepted.

**Why friction has limits:**

The engine does not block. An operator who has processed the risk and chooses to deploy should be able to do so. The system's job is to ensure the operator has genuinely seen the risk — not to prevent them from acting on it.

**The friction sweet spot:**
- Enough resistance to prevent accidental override
- Not so much resistance that operators train themselves to dismiss without reading

### Override Friction by Tier

| Suppression Tier | Override Required | Steps Required |
|-----------------|-------------------|----------------|
| NONE | No | 0 |
| LOW | No | 0 |
| MODERATE | No | 0 |
| HIGH | Yes | 1 (checkbox acknowledgement) |
| LOCKDOWN | Yes | 2 (checkbox + reason selection) |

---

## C. ACKNOWLEDGEMENT BEHAVIOR

### HIGH Suppression Override

**Step 1 only:**

Checkbox control renders in Zone 7 of the deployment panel with the text:

> "I acknowledge this pick faces high pitcher suppression. I accept reduced deployment confidence and will consider position sizing adjustments."

The operator must check this box. No bypass available. No timer dismissal. No passive alternative.

After checking:
- Zone 7 shows "Override acknowledged — proceed with caution"
- Zone 9 [Deploy] activates at normal visual prominence
- Deployment proceeds

**Language intent:** "I acknowledge" and "I accept reduced deployment confidence" — the operator is not just clicking through. They are explicitly owning the risk in the language of the system.

---

### LOCKDOWN Suppression Override

**Step 1 — Acknowledgement checkbox:**

> "I acknowledge this pitcher presents elite suppression. HR deployment against this pitcher carries structural risk regardless of batter tier."

**Step 2 — Override reason selection:**

Dropdown with four options (one must be selected):
- **OPERATOR-PREFERENCE** — I have reviewed the signal and choose to deploy based on personal judgment
- **SAMPLE-CONFIDENT** — I have additional data or context not reflected in the suppression model
- **POSITION-LIMITED** — I am deploying at a materially reduced position size that limits my exposure
- **OTHER** — (if selected, a brief text input appears — required, max 100 characters)

After both steps complete:
- Zone 7 shows "Override complete — LOCKDOWN acknowledged"
- LOCKDOWN confirmation modal appears (one modal: "Confirm deploy against LOCKDOWN pitcher?" — [Confirm] / [Cancel])
- After [Confirm]: Zone 9 [Deploy] activates

**Language intent:** The reason selection forces the operator to articulate their basis for overriding LOCKDOWN. This is not bureaucratic overhead — it is the operator's internal audit trail. When a LOCKDOWN pick hits, the operator can recall why they proceeded.

---

## D. PERSISTENCE RULES

Override acknowledgement is **session-scoped** and **pick-specific**.

- Acknowledging HIGH suppression for Pick A does not pre-acknowledge Pick B (even if same pitcher)
- Acknowledging LOCKDOWN for a pick in the morning does not persist to an afternoon session
- No "remember my override preference" setting — each deployment is an independent decision
- If the operator abandons a deployment and returns to the same pick, override is required again

**Why no persistence:**

Persistent override trains operators to dismiss without reading. Each deployment of a HIGH or LOCKDOWN pick is a genuinely new risk acceptance. The friction must be paid each time to maintain its function.

---

## E. TRUST LOGGING PHILOSOPHY

The deployment panel logs the following data points for every deployment action:

**For all deployments:**
- `suppression_tier` at time of deployment
- `suppression_score` at time of deployment
- `trust_state` at time of deployment
- `escalation_tier` at time of deployment
- `data_source_status` at time of deployment (snapshot)

**For HIGH/LOCKDOWN override deployments (additional):**
- `override_type`: "HIGH" or "LOCKDOWN"
- `override_reason`: reason selection value (LOCKDOWN) or "HIGH-ACK" (HIGH)
- `override_timestamp`: ISO datetime

**Storage:** These fields extend the existing `pick_tracker.csv` schema. They are logged alongside the existing pick data — not in a separate audit table. Schema migration via `_migrate_schema()` (per Session 25 pattern).

**Why log suppression at deployment time:**

The suppression score at deployment time is the operator's operating context. If a pick was deployed against a HIGH suppressor and the outcome was a HR, that context is essential for calibration analysis. If a pick was deployed against a LOCKDOWN pitcher and missed, that also needs tracking — separately from picks deployed against LOW suppression pitchers.

---

## F. DEPLOYMENT AUDITABILITY

An operator reviewing their pick history should be able to answer the following questions for any past pick:

1. What was the suppression tier when I deployed this?
2. Did I override? What was my stated reason?
3. What was the trust-state at deployment time?
4. Was the suppression score partial (degraded source)?

All four questions are answerable from the logged data without model re-runs.

**Audit surface (future scope):** A pick history filter by `override_type` would allow operators to review all LOCKDOWN overrides and assess their historical accuracy. This is a future reporting feature — not in current scope.

---

## G. ESCALATION RECONCILIATION

When a pick is deployed with a HIGH or LOCKDOWN override and subsequently misses:

The system does not retroactively penalize the operator's escalation tier assessment. FIRE is still FIRE for the batter — the outcome does not change the tier assignment. The suppression system flagged the risk. The operator accepted it. The outcome is data.

When reviewing calibration (via `analyze_live_roi.py` and `analyze_calibration.py`): LOCKDOWN-override picks should be tracked as a separate segment. If LOCKDOWN override picks show systematically worse outcomes than model-predicted, that is suppression validation data — it confirms the suppression tier was correct and the operator's override carried real cost.

The engine does not punish overrides in the scoring model. But it does accumulate override outcome data for operational review.

---

## H. CAUTION ESCALATION BEHAVIOR

The system escalates caution through a defined pathway. Override does not skip steps — it completes them.

### The System Should WARN When

- Suppression tier = MODERATE for FIRE or STRONG picks
- Trust-state = DEGRADED
- Same-game concentration ≥ 2 picks
- Exposure summary shows team concentration ≥ 3 picks

Warning behavior: informational note in relevant zone. No blocking. No override required.

### The System Should SLOW When

- Suppression tier = HIGH for any pick
- Trust-state = RESTRICTED + suppression tier ≥ MODERATE
- LOCKDOWN pick where trust-state = DEGRADED

Slow behavior: override controls appear. Deployment pauses for acknowledgement. Still allowed — but deliberately paced.

### The System Should BLOCK When

- Trust-state = BLOCKED (data integrity failure)
- Escalation tier = VOID (no deployment surface)
- Pitcher role = OPENER/BULK when suppression score was computed (deployment panel shows role mismatch warning instead)

Block behavior: Zone 9 [Deploy] disabled. Reason displayed. No override available.

### The System Should ALLOW When

- Override steps are completed
- Trust-state is FULL or DEGRADED (operator has sufficient data confidence)
- Escalation tier ≠ VOID or COLD
- Suppression tier ≤ MODERATE (no override required)

---

## I. OPERATIONAL TONE DOCTRINE

MLB HR ENGINE should feel:

**Measured** — every caution is proportional to the actual risk level. HIGH suppression gets more friction than MODERATE. LOCKDOWN gets more friction than HIGH. The operator never feels over-warned for low-risk picks or under-warned for high-risk ones.

**Elite** — the system communicates through restraint, not alarm. No red banners. No flashing. No "Are you sure? Are you really sure?" loops. One deliberate step per risk level. The operator trusts the system because the system trusts the operator.

**Credible** — suppression signals are grounded in documented, traceable inputs. When an operator overrides, they do so knowing exactly what they are overriding and why it was flagged. No black boxes. No surprises.

**Tactical** — the language is intelligence-grade, not consumer-grade. Caution signals use the vocabulary from `tactical_language_dictionary.md`. The operator feels like they are consulting a professional analysis system, not being warned by a nanny filter.

### NOT:

- "Click green button because home run maybe."
- "DANGER DANGER DANGER — bad pitcher!"
- Forced optimism ("Despite some concerns, this could be a great pick!")
- Vague hedging ("Results may vary")
- Sportsbook energy ("Fire this one up — YOLO pick of the day!")

The operator who reaches the deployment panel has already done the work. The panel's job is to confirm they have considered the risk, document their decision, and get out of their way.

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
