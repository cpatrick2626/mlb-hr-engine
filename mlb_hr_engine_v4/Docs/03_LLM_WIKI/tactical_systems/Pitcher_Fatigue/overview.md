---
title: Pitcher Fatigue - Overview
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Pitcher Fatigue — Overview

## Core Concept

Pitcher fatigue degrades command, velocity, and secondary pitch reliability — expanding HR windows for dangerous batters. The MLB HR ENGINE models fatigue as a days-rest factor applied to the base pitcher multiplier. Short rest (≤ 4 days) generates a measurable HR probability boost. Third-time-through-order exposure amplifies within-game fatigue risk beyond what the rest-based model captures.

## Tactical Signals

- **Short rest (≤ 4 days)**: 1.01–1.08 HR boost above neutral; severity scales with rest length
- **Velocity drop**: declining velocity relative to season average signals command fade (display signal)
- **TTOP risk**: third time through order — familiarity advantage shifts to batter, command degrades
- **Late-inning exposure**: starter in innings 6–7+ with full lineup turn — mistake-pitch probability elevated
- **Bullpen exposure**: handedness and arsenal mismatches amplify when team reaches secondary relievers
- **Recent workload**: high-IP prior start increases fatigue probability even at standard rest

## Escalation Conditions

- Rest days ≤ 3 → maximum fatigue boost (1.06–1.08 range)
- Rest days = 4 → moderate fatigue boost (1.01–1.03 range)
- Starter projected to face dangerous batter for third time → TTOP escalation
- Velocity down ≥ 2 mph vs season average at same pitch count (display signal — not in model)

## Failure Conditions

- Extra rest (≥ 6 days) — no longer applies linear decay (removed 2026-05-16 — no backtest evidence)
- Standard rest (5 days) = 1.00 neutral; fatigue doctrine inactive
- Bullpen game or opener deployment — short-rest fatigue factor irrelevant
- High-K pitcher maintains effectiveness through fatigue — command fade does not equal HR rate spike

## MLB HR ENGINE Usage

Fatigue factor computed in `engine/probability.py` from days since last start. Short rest (≤ 4 days): boost 1.01–1.08. Standard (5 days) and extra rest (6+ days): 1.00 neutral. Applied as `fatigue_fac` multiplier to pitcher component before pitcher factor attenuation (`PITCHER_FACTOR_SCALE = 0.60`).

## Related Doctrine Links

- [[Pitch_Mix_Exploitation/overview]] — fatigue amplifies pitch mix exploitation windows
- [[HR_Threat_Escalation/overview]] — fatigue is danger layer input
- [[Confidence_Tiering/overview]] — fatigue + barrel stack can push WATCH → LIVE
- [[Barrel_Quality/overview]] — barrel quality determines whether fatigue translates to HR
