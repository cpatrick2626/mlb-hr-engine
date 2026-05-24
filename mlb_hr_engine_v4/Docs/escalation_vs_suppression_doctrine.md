# Escalation vs Suppression Doctrine
## MLB HR Engine — Conflict Resolution & Coexistence Rules

**Version:** 1.0  
**Date:** 2026-05-20  
**Phase:** Step 4/12 — Escalation Infrastructure & Pitcher Suppression Stabilization  
**Status:** Specification only. No runtime code modified.  
**Cross-reference:** `spec_escalation_badge_system_v1.md`, `spec_pitcher_suppression_card_v1.md`, `escalation_tier_visual_spec.md`

---

## Overview

Two independent intelligence systems operate simultaneously in the MLB HR Engine:

**Escalation system** — communicates batter deployment confidence (FIRE → VOID).  
**Suppression system** — communicates pitcher-side risk modifiers (NONE → LOCKDOWN).

These systems measure different things. They can produce contradictory-looking signals. This document defines how they coexist, how conflicts are resolved, and how operators should interpret compound states.

**Core principle:** Escalation and suppression never merge into a single signal. They always render separately. The operator sees both. The operator resolves the tension. The engine does not collapse them into one verdict.

---

## A. HOW ESCALATION AND SUPPRESSION COEXIST

### System Roles

| System | Measures | Source |
|--------|----------|--------|
| Escalation (batter tier) | Batter power profile, EV, park factor, confidence, all model filters | Engine probability model |
| Suppression (pitcher tier) | Pitcher barrel-allowed, GB rate, pitch mix mismatch, velocity trend | Pitcher profile layer |

### Visual Coexistence Rule

When both systems are active, they render in adjacent but distinct zones:

```
[ESCALATION BADGE: FIRE]   [SUPPRESSION BADGE: HIGH]
```

They never merge into one combined badge. A single "FIRE vs HIGH SUPPRESSOR" badge is forbidden — it collapses two distinct signals into an ambiguous composite that operators cannot interpret independently.

### Precedence Principle

**Escalation tier does not automatically override suppression. Suppression does not automatically block escalation tier display.**

Both render. The operator adjudicates. This is intentional. A FIRE batter against a LOCKDOWN pitcher is still a FIRE batter — but the suppression signal demands acknowledgement before deployment proceeds.

---

## B. SCENARIO-SPECIFIC RULES

### Scenario 1: FIRE Hitter vs LOCKDOWN Pitcher

**Visual state:**  
- Batter card: FIRE escalation badge (full amber treatment, full glow)  
- Suppression card: LOCKDOWN tier (crimson border, 3px left accent)  
- Both render simultaneously in STANDARD state

**Precedence rule:**  
Escalation tier is not downgraded. The card does not become WATCH or COLD because of pitcher suppression. The batter's underlying profile is genuinely strong — suppression does not invalidate that signal.

**Deployment impact:**  
LOCKDOWN suppression requires operator override before deployment panel unlocks. Operator cannot reach the deploy confirmation without explicitly acknowledging the suppression tier.

**Operator instruction (caution text):**  
"FIRE-tier batter faces elite suppressor. Batter profile is high-confidence. Pitcher profile creates structural risk. Deployment at reduced position size recommended pending operator judgment."

**Tie-break behavior:**  
If operator must choose between two FIRE picks — one facing LOCKDOWN suppression and one facing LOW suppression — the LOW-suppression pick has implied higher deployment confidence. The system does not auto-sort on this compound signal, but it must be visible enough for the operator to apply this judgment.

---

### Scenario 2: STRONG Matchup with Weather Suppression

**Visual state:**  
- Batter card: STRONG escalation badge  
- Suppression card: MODERATE (weather suppression pill active)  
- Weather suppression pill: cyan `#00D4FF` at 30% opacity — environmental signal (not pitcher-profile signal)

**Precedence rule:**  
STRONG escalation tier holds. Weather suppression at MODERATE does not downgrade the batter tier. It reduces operator confidence in the environmental conditions supporting the pick.

**Deployment impact:**  
No operator override required. Caution explanation visible in STANDARD state. Operator notes the signal.

**Operator instruction:**  
"STRONG batter in weather-modified environment. Wind and temperature factors suppressing HR surface area. Deployment confidence adjusted for environmental conditions."

**Tie-break behavior:**  
If STRONG pick without weather suppression and STRONG pick with MODERATE weather suppression are equivalent on model score: prefer the non-suppressed pick. Weather suppression at MODERATE is a marginal signal but a real one.

---

### Scenario 3: WATCH Hitter with Elite Pitch Exploit

**Visual state:**  
- Batter card: WATCH escalation tier (muted, white border, no glow)  
- Suppression card: NONE (no pitcher suppression)  
- But: HVY modifier FAVORABLE — batter's contact profile exploits pitcher's arsenal

**Precedence rule:**  
WATCH escalation tier holds. A favorable HVY modifier does not promote the pick to STRONG. HVY is a display-only matchup signal — it is explicitly not modeled in engine probability. It cannot upgrade an escalation tier.

**Deployment impact:**  
WATCH picks require review before deployment. A favorable HVY modifier is additional context that may support operator judgment to deploy despite WATCH tier — but the engine does not act on it.

**Operator instruction:**  
"WATCH-tier pick. Marginal edge by model metrics. Pitch mix matchup shows FAVORABLE signal — batter's contact profile aligns with pitcher's arsenal tendencies. Operator may apply judgment."

**Tie-break behavior:**  
Among multiple WATCH picks, a pick with FAVORABLE HVY and NONE suppression is preferred over a pick with UNFAVORABLE HVY and NONE suppression. This is a soft preference signal — visible to the operator, not enforced by the engine.

---

### Scenario 4: FIRE Hitter but Low Confidence Environment

**Visual state:**  
- Batter card: FIRE escalation badge  
- Suppression card: LOW (minor signal, no environmental threat)  
- But: environment score below 6.0 (marginal park + weather conditions)

**Precedence rule:**  
Environment score is incorporated into the engine's probability model — it affects the batter's escalation tier directly. A FIRE pick in a poor environment is still FIRE because the model has already penalized for environment. Suppression card does not need to re-flag what the model already accounts for.

**Exception:** If a weather threshold event occurs mid-session (wind shift, temperature drop) that was not reflected at model-run time, the environmental suppression layer in the pitcher suppression card may activate to surface the updated risk. This is the only case where environment appears in suppression without pitcher-profile cause.

**Deployment impact:**  
Normal. FIRE tier. Operator proceeds with standard deployment confidence.

---

## C. VISUAL CONFLICT HANDLING

When escalation and suppression signals pull in opposite directions, visual rendering must prevent confusion — without collapsing the two signals into one.

### Rule 1: Separation of Signal Zones

Escalation badge is always anchored to the **player identity zone** (top-right of card).  
Suppression badge is always anchored to the **suppression card section** (inside EXPANDED state or STANDARD pitcher panel).  
They never share a zone. They never overlap.

### Rule 2: No Combined Tier Labels

Forbidden pattern:
```
❌ [FIRE — HIGH RISK]
❌ [STRONG*]   (* = suppression active)
❌ [FIRE ⬇ SUPPRESSED]
```

Required pattern:
```
✓ [FIRE]   [SUPPRESSOR: HIGH]
```

Two badges. Two signals. One operator.

### Rule 3: Suppression Visibility at STANDARD State

For MODERATE and above suppression, the suppression tier badge must be visible in STANDARD card state — not hidden behind expansion. The operator cannot miss it.

For LOW and NONE, the suppression section may remain collapsed at STANDARD state.

### Rule 4: Color Conflict Resolution

Amber (FIRE) and crimson (LOCKDOWN suppression) appear simultaneously on the same card. This is intentional — they represent different systems. They must not be confused for each other.

The escalation badge amber (`#F5A623`) is warm and energetic — top-right corner.  
The suppression crimson (`#C0392B`) is darker, more muted — suppression section border.  
Spatial separation + color temperature difference prevents ambiguity.

---

## D. OPERATOR TRUST RULES

### Operators Trust Both Systems Independently
The engine does not synthesize a "net" deployment signal. It presents both signals and trusts the operator to weigh them. This is intentional — automated signal collapse loses information.

### Operators Are Not Required to Deploy Against Suppression
A FIRE pick with LOCKDOWN suppression is a deployment decision, not a deployment mandate. The engine presents the pick. The operator decides.

### Operators Can Override Suppression
At HIGH and LOCKDOWN suppression tiers, the deployment panel requires an explicit acknowledgement step before the deploy action is available. This is friction by design — not a block. The operator must consciously proceed past the caution signal.

### Operators Cannot Override Escalation Tier
The engine's escalation tier assignment (FIRE/STRONG/WATCH/COLD/VOID) is a model output. Operators cannot promote a COLD pick to STRONG via UI interaction. If they believe the tier is wrong, they investigate the caution flags in the suppression and filter detail — they do not reassign tiers manually.

---

## E. TIE-BREAK BEHAVIOR

When two picks are equivalent on model score and escalation tier, the following signals are used as tie-break criteria, in order:

1. **Suppression tier** — lower suppression wins (NONE over MODERATE, MODERATE over HIGH)
2. **HVY modifier direction** — FAVORABLE over NEUTRAL over UNFAVORABLE
3. **Environmental score** — higher environment score wins
4. **Confidence** — higher confidence value wins
5. **PA ceiling** — pick with more expected PA tonight wins

Tie-break resolution is visible in the deployment panel — the system displays which factor broke the tie. Operators can override based on judgment.

---

## F. CAUTION PRIORITY LOGIC

Caution signals from multiple systems must be prioritized when multiple are active simultaneously.

### Caution Priority Stack (highest to lowest)

1. **LOCKDOWN pitcher suppression** — always surfaces first. Renders in STANDARD state. Requires override.
2. **HIGH pitcher suppression** — surfaces in STANDARD state. Requires reduced-size recommendation.
3. **Engine filter failure** — reflected in escalation tier (COLD/VOID). No additional suppression caution needed.
4. **MODERATE pitcher suppression** — surfaces in STANDARD state for FIRE/STRONG picks. Note for WATCH picks.
5. **Weather threshold breach** — surfaces in suppression environmental layer.
6. **Handedness suppression** — surfaces as pill in suppression card. Note in caution explanation.
7. **LOW pitcher suppression** — collapsed in STANDARD state. Visible on expansion.
8. **Unfavorable HVY modifier** — visible in matchup suppression layer. Note only.

### Multiple Caution Signals Active Simultaneously

If both HIGH suppression and MODERATE weather suppression are active:
- PRIMARY caution: HIGH suppression (governs override requirement)
- SECONDARY caution: weather suppression (note in caution explanation)
- Combined wording: "High pitcher suppression active. Environmental conditions provide additional risk modifier. Both signals present."

If LOCKDOWN suppression and COLD escalation tier are active simultaneously:
- This is a contradictory compound state — a batter who failed model filters AND faces an elite suppressor
- No operator should deploy this pick
- Caution wording: "Engine filter failure (COLD tier) compounded by elite pitcher suppression. No deployment basis. Informational only."

---

## G. COMPOUND STATE REFERENCE TABLE

| Escalation Tier | Suppression Tier | Deployment Stance | Override Required | Display Priority |
|-----------------|-----------------|-------------------|-------------------|------------------|
| FIRE | NONE | Full confidence | No | T1 — immediate deploy |
| FIRE | LOW | Full confidence — note signal | No | T1 — immediate deploy |
| FIRE | MODERATE | Reduced confidence — review | No | T1 — review before deploy |
| FIRE | HIGH | Materially reduced — caution | Yes | T1 with HIGH caution visible |
| FIRE | LOCKDOWN | Structural risk — operator decision | Yes (explicit) | T1 with LOCKDOWN override |
| STRONG | NONE | High confidence | No | T2 — deploy |
| STRONG | MODERATE | Confidence reduced — review | No | T2 — review |
| STRONG | HIGH | Deployment-blocked pending override | Yes | T2 with HIGH caution visible |
| STRONG | LOCKDOWN | Structural risk | Yes (explicit) | T2 with LOCKDOWN override |
| WATCH | NONE | Review required | No | T3 — review before deploy |
| WATCH | MODERATE | Compounded caution | No | T3 — strong caution |
| WATCH | HIGH | Do not deploy | Implicit | T3 — deployment not recommended |
| COLD | Any | Do not deploy | Not applicable | T4 — filter failure governs |
| VOID | Any | Invalid — no deployment | Not applicable | T5 — no action |

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
