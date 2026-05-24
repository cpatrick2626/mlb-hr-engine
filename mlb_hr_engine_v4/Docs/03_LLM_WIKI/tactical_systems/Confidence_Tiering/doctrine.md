---
title: Confidence Tiering - Doctrine
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Confidence Tiering — Doctrine

## Core Concept

Confidence tiers formalize the relationship between signal confirmation count, threat level, and deployment action. They exist because not all deployable picks carry equal conviction — a 2-layer LIVE pick and a 4-layer CORE pick both clear the deployment gate but require different sizing and risk posture. Tiers enforce this discipline systematically.

## Tier Specifications

### CORE
- **Requires**: MAX THREAT (4+ danger layers)
- **Barrel floor**: ≥ 0.10 (above-average power mandatory)
- **Deployment**: full deployment, maximum allowed size
- **Sizing**: quarter-Kelly or scaled based on bankroll config
- **Composite score position**: top decile of ranked slate
- **Player card**: red header, all signal indicators confirmed

### STRONG
- **Requires**: HIGH THREAT (3 danger layers)
- **Barrel floor**: ≥ 0.08
- **Deployment**: deploy with size discipline — do not max-size STRONG picks
- **Sizing**: 60–80% of CORE sizing
- **Composite score position**: top quartile of ranked slate

### LIVE
- **Requires**: LIVE THREAT (2 danger layers)
- **Barrel floor**: ≥ 0.06
- **Deployment**: minimum deployment size — confirms edge exists but conviction limited
- **Sizing**: flat unit or 40–50% of CORE sizing
- **Composite score position**: second quartile

### WATCH
- **Requires**: WATCH STATE (0–1 danger layers)
- **Deployment**: no deployment — active monitoring for signal improvement
- **Use case**: pre-game tracking; re-evaluate at lineup lock, weather update, or TTOP confirmation
- **Composite score position**: third quartile and below

### NO DEPLOYMENT
- **Triggers**: any hard BLOCK condition
  - `barrel_rate < 0.04`
  - `park_factor ≤ 0.87` (suppressive park)
  - `model_prob < MIN_EV_PCT`
  - Context moderation guard fires on sub-average power batter
  - Active lineup scratch or DNP
- **Action**: immediate removal from slate; no monitoring
- **Player card**: blocked; not rendered in deployment tab

## Tier Movement Rules

**Upgrade triggers** (must occur before lineup lock):
- New danger layer confirmed → re-evaluate tier
- Odds improve (implied prob drops) → recalculate EV%; if EV% crosses threshold, may upgrade
- Weather update shows improved carry conditions → re-check environmental layer

**Downgrade triggers** (can occur any time):
- Lineup scratch or position change (batter moves from 3-hole to 9-hole) → immediate NO DEPLOYMENT
- Odds move ≥ 15% implied probability against model → downgrade one tier
- Starter pulled before TTOP materializes → remove TTOP layer; re-evaluate
- Context moderation guard fires → CORE/STRONG forced to STRONG/LIVE maximum

**Hard downgrade triggers** (no recalculation — immediate NO DEPLOYMENT):
- Batter confirmed scratch
- Suppressive park identified (late weather data shows dome closed when expected open — edge case)
- `model_prob` drops below `MIN_EV_PCT` after pre-game update

## Composite Score in Tier Context

`output/ranker.py` composite score: `EV×0.40 + Edge×0.35 + Confidence×0.25`

Confidence input is normalized tier value (CORE=50, STRONG=40, LIVE=30, WATCH=10). This means CORE picks always rank above STRONG picks at equivalent EV/Edge — tier acts as a multiplier, not just a label.

## Portfolio Tier Distribution (target)

Per moderate preset in `portfolio/optimizer.py`:
- CORE: 2–5 picks (max conviction, max sizing)
- STRONG: 6–10 picks (high conviction, disciplined sizing)
- LIVE: 4–8 picks (confirmed edge, minimum sizing)
- WATCH: 0 picks deployed (monitoring only)

## Related Doctrine Links

- [[HR_Threat_Escalation/doctrine]] — danger layers are tier input
- [[Market_Inefficiency/doctrine]] — odds movement drives tier downgrade
- [[Barrel_Quality/doctrine]] — barrel floor is CORE/STRONG gate
- [[Hard_Hit_Danger/doctrine]] — hard-hit danger layer accelerates tier
