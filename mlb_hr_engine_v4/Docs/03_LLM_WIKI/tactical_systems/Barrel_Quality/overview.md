---
title: Barrel Quality - Overview
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Barrel Quality — Overview

## Core Concept

Barrel quality is the primary predictor of HR probability in the MLB HR ENGINE. Barrel rate (percentage of batted balls meeting Statcast's barrel definition: exit velo ≥ 98 mph + launch angle in HR-optimal window) is the highest-weight signal in the `batter_power_multiplier`. It drives the Bayesian regression target, the elite tier calibration, and the deployment BLOCK threshold. No other signal overrides insufficient barrel quality.

## Tactical Signals

- **Barrel rate**: percentage of batted balls classified as barrels (league avg = 5.5%)
- **Launch angle quality**: sweet spot rate (8°–32°) — air contact that produces extra bases
- **xSLG**: expected slugging from quality of contact profile
- **xISO**: expected ISO (power proxy) independent of park and luck
- **Pull-air profile**: pull% combined with FB% — ball hit to pull side in the air is highest HR zone
- **Exit velocity**: average EV (league avg = 89.1 mph) — secondary power indicator
- **Hard-hit rate**: ≥ 95 mph EV threshold (league avg = 39.9%)
- **Recent hard-contact form**: last 7–14 days Statcast trends (display signal)

## Escalation Conditions

- `barrel_rate ≥ 0.12` — elite tier; +2 danger layers; elite Platt calibration applied
- `barrel_rate ≥ 0.08` — above-average; +1 danger layer; STRONG tier eligible
- `barrel_rate ≥ 0.06` — minimum LIVE deployment threshold
- `barrel_rate < 0.04` — hard BLOCK regardless of all other signals

## Failure Conditions

- Sub-average barrel rate (< 0.055) with favorable environment → context moderation guard fires
- Barrel data from prior year blending with no current-year Statcast → blended-source bias (+1.75pp)
- High FB% without barrel quality → FB% quality gate discounts upside (up to 50%)
- Small sample (< 50 PA current year) → prior-year Statcast trusted at 85% weight

## MLB HR ENGINE Usage

Barrel rate feeds `batter_power_multiplier` in `engine/probability.py`. Weight breakdown: barrel=40%, FB%=20%, hard-hit%=10%, xSLG=8%, exit velo=4%, pull%=10%, sweet spot%=10%. FB% quality gate active when `FB_QUALITY_GATE_ENABLED=True`. Elite barrel tier (≥ 0.10) uses separate Platt calibration params with higher crossover (22.3%). `ELITE_REG_TARGET_ENABLED=True` raises Bayesian anchor for barrel ≥ 0.08.

## Related Doctrine Links

- [[Hard_Hit_Danger/overview]] — hard-hit rate is secondary barrel quality co-signal
- [[HR_Threat_Escalation/overview]] — barrel tier is primary danger layer input
- [[Confidence_Tiering/overview]] — barrel floor gates CORE/STRONG/LIVE tiers
- [[Pitch_Mix_Exploitation/overview]] — barrel quality determines if pitch mix windows produce HR
