---
title: Hard Hit Danger - Overview
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Hard Hit Danger — Overview

## Core Concept

Hard-hit danger is the secondary contact authority signal that supports barrel quality as a co-predictor of HR probability. Hard-hit rate (≥ 95 mph exit velocity threshold) captures contact authority for batters who consistently damage the ball without reaching full barrel classification. When hard-hit danger aligns with barrel quality and favorable matchup conditions, it confirms the contact profile is genuine, not sample-driven.

## Tactical Signals

- **Hard-hit rate**: % of batted balls ≥ 95 mph EV (league avg = 39.9%)
- **Exit velocity**: average EV across all contact (league avg = 89.1 mph)
- **Contact authority**: sustained ability to damage ball regardless of launch angle
- **Pitcher hard-contact allowed**: pitcher's % of batted balls ≥ 95 mph allowed — matchup signal
- **Batter damage profile**: combination of hard-hit + pull% — identifies pull-air danger batter
- **Danger clustering**: multiple high hard-hit batters vs same pitcher → lineup-level danger

## Escalation Conditions

- Hard-hit rate ≥ 50% (elite contact authority — top decile MLB)
- Hard-hit rate ≥ 45% + barrel rate ≥ 8% — confirmed dual-power signal
- Pitcher hard-contact allowed ≥ 45% — batter-pitcher matchup in danger zone
- Hard-hit + pull-air profile vs pitcher with poor arm-side command — contact window confirmed

## Failure Conditions

- High hard-hit rate without barrel quality → ground-ball hard-hit hitter; does not translate to HR
- Hard-hit rate in small sample (< 100 PA Statcast) — unstable, regress to league avg
- Pitcher hard-contact allowed in small sample (< 60 BF) — matchup signal unreliable
- Hard-hit without favorable launch angle profile → line drives, not HR

## MLB HR ENGINE Usage

Hard-hit rate weighted at 10% in `batter_power_multiplier` in `engine/probability.py`. Exit velocity weighted at 4%. Together they contribute 14% of power multiplier — secondary to barrel (40%) and FB% (20%). Not a standalone escalation signal; requires barrel quality confirmation. `LEAGUE_AVG_HARD_HIT = 0.399` baseline in `config.py`.

## Related Doctrine Links

- [[Barrel_Quality/overview]] — primary power signal; hard-hit is secondary co-signal
- [[HR_Threat_Escalation/overview]] — danger clustering contributes to game-level escalation
- [[Pitch_Mix_Exploitation/overview]] — pitcher hard-contact allowed feeds pitch mix matchup signal
- [[Confidence_Tiering/overview]] — hard-hit danger supports tier escalation as co-signal
