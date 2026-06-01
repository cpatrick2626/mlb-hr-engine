---
title: HR Threat Escalation - Overview
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# HR Threat Escalation — Overview

## Core Concept

HR Threat Escalation is the multi-signal danger stacking system that converts individual tactical signals into deployment-ready threat states. A player does not escalate to deployment readiness on any single signal — escalation requires stacked confirmation across barrel quality, environmental context, pitcher matchup, and market position. Threat level determines whether a player reaches a confidence tier eligible for bet deployment.

## Tactical Signals

Five primary danger inputs:
1. **Barrel quality** — barrel_rate tier position relative to league avg (0.055)
2. **Environmental context** — combined park × weather multiplier
3. **Pitch mix exploitation** — HVY modifier from `clients/pitch_mix.py`
4. **Pitcher fatigue** — `fatigue_fac` from days-rest schedule
5. **Market inefficiency** — EV% and Edge% from odds comparison

Secondary inputs (overlay signals):
- TTOP exposure (game-state)
- Handedness platoon edge
- Bullpen exposure risk
- Recent hard-contact form (last 7-14 days)

## Escalation Conditions

- **2+ danger layers confirmed** → LIVE tier eligible
- **3+ danger layers** → STRONG or CORE tier eligible
- **4+ danger layers** → maximum threat state — CORE deployment priority
- Any single suppression signal (suppressive park, low barrel, negative HVY) blocks escalation

## Failure Conditions

- Single-signal confirmation only → WATCH tier maximum
- Suppressive park active → escalation blocked regardless of other signals
- `barrel_rate < 0.04` → NO DEPLOYMENT regardless of context
- Low `model_prob` (below MIN_EV_PCT) → blocks deployment even at max danger layers
- Context moderation guard fires for sub-average power batters in high-context environments

## MLB HR ENGINE Usage

Danger layer count is not a single computed field — it is synthesized from `barrel_rate`, `hvy_modifier`, `fatigue_fac`, `context_mult`, `ev_pct`, and `edge_pct` values in the player row. The HR Threat Card system in `output/` renders the threat state. Escalation rules are evaluated at JIG and STRATEGY layers.

## Related Doctrine Links

- [[Barrel_Quality/overview]] — primary danger layer signal
- [[Environmental_Leverage/overview]] — context danger layer input
- [[Pitch_Mix_Exploitation/overview]] — HVY modifier danger layer input
- [[Pitcher_Fatigue/overview]] — fatigue danger layer input
- [[Confidence_Tiering/overview]] — threat level maps to confidence tier
- [[Market_Inefficiency/overview]] — EV/Edge danger layer input
