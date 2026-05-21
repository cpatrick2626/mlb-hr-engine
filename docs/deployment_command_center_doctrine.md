# Deployment Command Center — Master Doctrine
## MLB HR Engine — Step 7/12

**Version:** 1.0
**Date:** 2026-05-20
**Phase:** Step 7/12 — Deployment, Portfolio & Operations
**Status:** ARCHITECTURE / UX / DOCTRINE ONLY — no runtime code modified
**Author:** Claude (Visual Doctrine Authority)
**Cross-reference:** `spec_deployment_queue_v1.md`, `spec_slip_builder_workflow_v1.md`, `spec_portfolio_exposure_system_v1.md`, `spec_bankroll_command_layer_v1.md`, `spec_clv_intelligence_system_v1.md`, `spec_post_slate_review_v1.md`, `spec_historical_intelligence_archive_v1.md`, `spec_risk_governance_v1.md`, `spec_tactical_deployment_hud_v1.md`, `spec_deployment_panel_architecture_v1.md`, `deployment_trust_hierarchy.md`

---

## A. SYSTEM PURPOSE

The Deployment Command Center is the operational execution layer of the MLB HR Engine.

It transforms qualified HR intelligence into disciplined, trackable, accountable deployment decisions.

The system does not generate picks. The engine generates picks. The system governs what happens after.

**Primary mandate:** Convert model output into execution-grade decisions with documented exposure, controlled sizing, measurable timing, and operational learning.

---

## B. CORE DOCTRINE: QUALIFY → DEPLOY → TRACK → LEARN

Every deployment interaction follows this exact sequence. No step is optional. No step can be skipped.

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ QUALIFY  │────▶│  DEPLOY  │────▶│  TRACK   │────▶│  LEARN   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

### QUALIFY
Picks arrive from the engine ranked by composite score. Qualification determines which picks enter the Deployment Queue and at what escalation readiness. Qualification is separate from execution.

Qualification considers:
- Escalation tier (FIRE → VOID)
- Suppression tier (NONE → LOCKDOWN)
- Exposure state (team/game/bankroll concentration)
- Portfolio fit (correlation risk, N_eff impact)
- Market timing state (opening / pre-game / closing proximity)
- Trust-state (FULL / DEGRADED / RESTRICTED / BLOCKED)

### DEPLOY
Deployment is the controlled execution step. It is not impulsive. It follows staged escalation. Each deployment decision is logged with context: sportsbook, odds, position size, market timing state, and operator notes.

Deployment is gated by:
- Queue readiness state
- Exposure checks
- Bankroll saturation checks
- Suppression acknowledgement (when required)
- Risk governance thresholds

### TRACK
Every deployed pick enters live tracking. Tracking captures:
- Pre-game market movement from deployed odds to closing line
- CLV won or lost
- Game result
- Settlement and P&L

Tracking is not optional. An untracked deployment is an invisible deployment. Invisible deployments cannot produce learning.

### LEARN
Post-slate review converts tracked outcomes into operational intelligence. Learning is not passive review. It is structured analysis of:
- Prediction accuracy vs outcomes
- Deployment quality vs prediction quality
- Sizing discipline vs exposure outcomes
- Market timing efficiency (CLV generation)
- Portfolio construction quality

Learning loops feed back into future deployment decisions through the Historical Intelligence Archive.

---

## C. SYSTEM ARCHITECTURE MAP

The Deployment Command Center is composed of nine integrated systems:

```
┌─────────────────────────────────────────────────────────────────┐
│                DEPLOYMENT COMMAND CENTER                         │
│                                                                  │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐     │
│  │  DEPLOYMENT   │   │  SLIP BUILDER │   │   PORTFOLIO   │     │
│  │     QUEUE     │──▶│   WORKFLOW    │──▶│   EXPOSURE    │     │
│  └───────────────┘   └───────────────┘   └───────────────┘     │
│          │                                        │              │
│          ▼                                        ▼              │
│  ┌───────────────┐                      ┌───────────────┐      │
│  │   BANKROLL    │                      │      CLV      │      │
│  │    COMMAND    │◀─────────────────────│  INTELLIGENCE │      │
│  └───────────────┘                      └───────────────┘      │
│          │                                        │              │
│          ▼                                        ▼              │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐     │
│  │   TACTICAL    │   │  POST-SLATE   │   │  HISTORICAL   │     │
│  │  DEPLOY HUD   │   │    REVIEW     │──▶│  INTELLIGENCE │     │
│  └───────────────┘   └───────────────┘   └───────────────┘     │
│                                                                  │
│                    ┌───────────────┐                             │
│                    │     RISK      │                             │
│                    │  GOVERNANCE   │                             │
│                    └───────────────┘                             │
│            (governs all nine systems above)                      │
└─────────────────────────────────────────────────────────────────┘
```

**Risk Governance** is not a workflow step. It is a pervasive authority layer. Every system answers to it.

---

## D. CRITICAL OPERATIONAL SEPARATION

The Command Center maintains six independent analytical dimensions. These dimensions must never be collapsed into one another.

| Dimension | What It Measures | What It Does NOT Determine |
|-----------|-----------------|---------------------------|
| Prediction Confidence | Engine probability, tier, composite score | Position size, bankroll allocation |
| Market Value | EV%, Edge%, CLV potential | Whether to deploy, how much to deploy |
| Portfolio Exposure | Team/game/player concentration | Model quality, tier validity |
| Correlation Risk | N_eff reduction, lineup overlap | Individual pick quality |
| Bet Sizing | Kelly fraction, position size | Pick rank, EV quality |
| Deployment Status | Staged, Queued, Deployed, Settled | Any analytical dimension above |

**Critical rule:** A high-confidence HR edge does NOT automatically justify max exposure. Deployment discipline is operationally isolated from model confidence. A FIRE-tier pick may still be subject to bankroll saturation limits, team concentration caps, and suppression override requirements.

The operator who conflates prediction quality with bankroll sizing is deploying emotionally, not operationally.

---

## E. PLATFORM IDENTITY

The Deployment Command Center must feel:

- **Tactical** — every surface communicates a decision, not a display
- **Operational** — the system is a tool for execution, not entertainment
- **Disciplined** — friction is intentional where decisions require deliberation
- **Cinematic** — premium, restrained, structured; visual hierarchy earns attention
- **Controlled** — escalation is earned, not automatic
- **Reviewable** — everything that happens leaves a trace

Visual references:
- Military logistics center
- Proprietary trading desk
- Formula 1 strategy wall
- Command-and-control risk terminal

Anti-patterns (rejected):
- Sportsbook CTA styling
- Cartoon betting graphics
- Giant green bet buttons
- Emotional urgency framing
- Fake cyberpunk effects
- Excessive stat density without hierarchy

---

## F. DESIGN LANGUAGE

### Color Semantics

Colors carry operational meaning. They are not decorative.

| Color | Meaning |
|-------|---------|
| `#60a5fa` (blue) | Informational, neutral, ambient |
| `#F5A623` (amber) | Active, engaged, deployable |
| `#4CAF50` (green) | Confirmed, settled, profitable |
| `#E87040` (orange-red) | High caution, reduced confidence |
| `#C0392B` (crimson) | Stop, override required, maximum risk |
| `#6B6B9A` (muted violet) | Suppressed, below threshold, inactive |
| `#2A2A45` (deep slate) | Background, secondary zones |

### Typography Hierarchy

Three levels. Never more.

- **Primary** — player name, tier badge, action label: large, high-contrast, `#E8E8F0`
- **Secondary** — scores, stats, context: medium, `#9090C0`
- **Tertiary** — labels, timestamps, metadata: small, `#5A5A80`

### Glow Usage

Glow is reserved for:
- Active FIRE-tier escalation badge
- Live market movement indicator
- Deployment confirmation state

Glow is NOT used for:
- Standard card states
- Navigation elements
- Table rows
- Any background treatment

---

## G. HUD HIERARCHY DOCTRINE

The Command Center operates on a layered HUD architecture. Each layer communicates at a different temporal and decisional scope.

```
┌────────────────────────────────────────────────────────────┐
│  LAYER 4: SESSION OVERSIGHT (ambient, always visible)       │
│  Bankroll state · Daily P&L · Deployed count              │
├────────────────────────────────────────────────────────────┤
│  LAYER 3: PORTFOLIO STATE (active during deployment)        │
│  Exposure heatmap · N_eff · Saturation warnings            │
├────────────────────────────────────────────────────────────┤
│  LAYER 2: DEPLOYMENT QUEUE (main operational surface)       │
│  Ranked picks · Escalation states · Slip staging          │
├────────────────────────────────────────────────────────────┤
│  LAYER 1: PICK-LEVEL PANEL (per-pick deployment detail)     │
│  Full 9-zone deployment panel (spec_deployment_panel)      │
└────────────────────────────────────────────────────────────┘
```

Each layer is readable without expanding the layers below it. A session-level concern never forces the operator into pick-level detail. A pick-level concern never floods the session overview.

**Layer 4** is persistent. It never disappears. It is the ambient state of the operator's session.

**Layer 1** is contextual. It appears only when a specific pick is being evaluated for deployment. It is the most detailed surface and the most deliberate.

---

## H. OWNERSHIP BOUNDARIES

### Claude Owns
- Tactical UX architecture
- Operational workflow design
- Deployment pacing doctrine
- Cinematic hierarchy and visual language
- Portfolio presentation design
- Escalation and review system structure
- Cognitive load reduction
- Command-center readability

### Codex Owns
- All runtime implementation
- Optimizer enforcement
- Persistence and storage
- Bankroll calculations
- Exposure calculations
- Settlement and P&L systems
- CLV calculations
- State safety
- Performance stability

Claude produces doctrine. Codex executes it. No implementation is produced here.

---

## I. DEPLOYMENT PACING DOCTRINE

Deployment pacing is a first-class concern. The system must not reward rapid deployment.

**Pacing principles:**

1. **Queue visibility before action** — The operator must see the full queue state before beginning individual deployments. Deploying the first pick without reviewing the full slate creates invisible correlation risk.

2. **Exposure check before each deployment** — Every deployment decision is preceded by a current exposure snapshot. This is not optional. The system presents the snapshot; the operator proceeds or pauses.

3. **Sequential not parallel deployment** — Deploying multiple picks simultaneously is an anti-pattern. Each deployment decision deserves individual deliberation. The slip builder enforces this through staged escalation.

4. **Session budgeting before first deployment** — Before any deployment occurs, the operator confirms the session bankroll allocation and daily loss limit. These are not adjustable mid-session without deliberate re-authorization.

5. **Post-deployment state reflection** — After each deployment, the Command Center updates the portfolio exposure display before presenting the next queue item. The operator sees the consequences of the decision before making the next one.

---

## J. INFORMATION DENSITY DOCTRINE

The Command Center operates at high information density without becoming overwhelming.

**Density rules:**

- **Progressive disclosure** — Default state shows tier badges, scores, and exposure summary. Tactical detail is available on expand. Full pitcher profiles, historical splits, and CLV timelines are available on drill-down.

- **No duplicate information** — The same signal does not appear in two zones simultaneously. If the escalation tier is displayed in Zone 1, it is not repeated in Zone 4. Each zone owns its signal.

- **Ambient vs active** — Ambient information (session bankroll, total exposure %) renders in low-contrast peripheral space. Active information (current pick under review, exposure alerts) renders in high-contrast primary space.

- **Alert sequencing** — When multiple caution signals are active, they appear in priority order. Suppression tier warnings precede exposure warnings precede market timing notes. The operator encounters the most critical signal first.

- **Scan-first, read-on-demand** — The operator should be able to scan the entire queue in 30 seconds. Full deliberation on a single pick should require no more than 60 seconds of reading. Everything beyond that is operator choice to drill deeper.

---

## K. RELATIONSHIP TO EXISTING SPEC DOCUMENTS

This doctrine extends and governs the following existing specifications:

| Document | Relationship |
|----------|-------------|
| `spec_deployment_panel_architecture_v1.md` | **Zone 9 of the Command Center HUD** — the per-pick deployment confirmation panel. All 9-zone spec rules apply when a pick is being individually evaluated. |
| `deployment_trust_hierarchy.md` | **Trust-state governs all eight operational systems.** BLOCKED trust-state locks the Command Center. DEGRADED trust-state adds caveat overlays across all surfaces. |
| `escalation_vs_suppression_doctrine.md` | **Governs queue state rendering.** Escalation and suppression render independently in the queue, the slip builder, and the deployment panel. |
| `spec_escalation_badge_system_v1.md` | **Badge system applies across all layers** of the Command Center. |
| `spec_suppression_score_contract_v1.md` | **Suppression visibility rules enforced in Deployment Queue and slip review.** |
| `operator_override_doctrine.md` | **Override logic governs deployment gating** in the Queue and the Deployment Panel. |

---

## L. IMPLEMENTATION PATHWAY

This document is planning only. The implementation sequence for Step 7 deliverables:

1. `spec_deployment_queue_v1.md` — defines queue architecture and escalation logic
2. `spec_slip_builder_workflow_v1.md` — defines FanDuel slip workflow
3. `spec_portfolio_exposure_system_v1.md` — defines exposure architecture
4. `spec_bankroll_command_layer_v1.md` — defines bankroll command
5. `spec_clv_intelligence_system_v1.md` — defines CLV tracking system
6. `spec_post_slate_review_v1.md` — defines post-slate review workflow
7. `spec_historical_intelligence_archive_v1.md` — defines historical intelligence
8. `spec_risk_governance_v1.md` — defines risk governance architecture
9. `spec_tactical_deployment_hud_v1.md` — defines HUD systems

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
