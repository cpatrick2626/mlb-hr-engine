---
title: Confidence Tiering - Overview
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Confidence Tiering — Overview

## Core Concept

Confidence tiering is the five-level classification system that converts HR threat escalation state into a deployment posture. Each tier carries explicit rules for whether a pick is deployable, how much sizing is appropriate, and what conditions trigger tier movement. Tiers are not static — they respond to new information, odds changes, and game-state updates.

## Tier Definitions

| Tier | Threat Required | Deployment | Sizing |
|------|----------------|------------|--------|
| **CORE** | MAX THREAT (4+ layers) | Full deployment | Quarter-Kelly or higher |
| **STRONG** | HIGH THREAT (3 layers) | Deploy with size discipline | Scaled Kelly |
| **LIVE** | LIVE THREAT (2 layers) | Deploy with minimum size | Flat or small Kelly |
| **WATCH** | WATCH STATE (0–1 layers) | No deployment — monitoring only | None |
| **NO DEPLOYMENT** | SUPPRESSED or BLOCK | Hard block | None |

## Tactical Signals

- **CORE**: elite barrel + favorable environment + confirmed HVY + market edge all confirmed
- **STRONG**: 3 of 4 major signals confirmed; one incomplete or borderline
- **LIVE**: 2 signals confirmed; deployable but not maximum conviction
- **WATCH**: monitoring player — insufficient signals confirmed; conditions may improve
- **NO DEPLOYMENT**: hard block condition active (suppressive park, barrel < 0.04, model_prob below threshold)

## Escalation Conditions

- WATCH → LIVE: second danger layer confirmed (odds improve, weather update, TTOP materializes)
- LIVE → STRONG: third signal confirmed during pre-game monitoring window
- STRONG → CORE: fourth signal confirmed; full stack achieved
- Any tier → NO DEPLOYMENT: suppression signal fires (weather reversal, lineup scratch, park factor re-check)

## Failure Conditions

- CORE pick scratched by lineup change → immediate NO DEPLOYMENT
- Odds move against model by ≥ 15% implied probability → downgrade one tier
- TTOP projected but starter pulled early → TTOP layer removed; re-evaluate tier
- Context moderation guard fires on CORE candidate → forced downgrade to STRONG maximum

## MLB HR ENGINE Usage

Confidence tier assigned at STRATEGY layer after JIG threat evaluation. Tier stored as `confidence_tier` field in player row. Displayed on player card header. `output/ranker.py` composite score: EV×0.40 + Edge×0.35 + Confidence×0.25. Portfolio optimizer (`portfolio/optimizer.py`) uses tier as primary sort key for pick selection.

## Related Doctrine Links

- [[HR_Threat_Escalation/overview]] — threat level is tier input
- [[Market_Inefficiency/overview]] — odds movement triggers tier downgrade
- [[Barrel_Quality/overview]] — barrel tier maps to confidence floor
- [[Hard_Hit_Danger/overview]] — hard-hit danger can accelerate tier escalation
