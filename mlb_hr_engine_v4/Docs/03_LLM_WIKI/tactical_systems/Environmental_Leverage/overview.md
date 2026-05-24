---
title: Environmental Leverage - Overview
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Environmental Leverage — Overview

## Core Concept

Ballpark environment modulates HR probability independently of batter and pitcher quality. Park factor, wind, temperature, humidity, and roof status combine into a multiplicative context multiplier. Environmental leverage is deliberate targeting of favorable carry conditions to amplify existing batter quality signals.

## Tactical Signals

- **Park factor**: per-stadium HR factor from multi-year home/away HR rates; range [0.70, 1.40]
- **Wind to CF**: tailwind toward center field elevates carry; FROM convention (OpenMeteo `winddirection_10m`)
- **Temperature**: ~2% HR uplift per 10°F above 72°F baseline; range [0.82, 1.08]
- **Humidity**: humid air is less dense → more ball carry; range [0.96, 1.04]
- **Roof status**: dome = weather factor 1.0 (neutral); no wind/temp/humidity applied
- **Suppressive parks**: Oracle Park (SF), Petco Park (SD) — `MAX_PARK_PENALTY = 0.87` auto-blocks

## Escalation Conditions

- Park factor ≥ 1.15 — top-tier hitter environment
- Wind ≥ 10 mph toward CF
- Temperature ≥ 80°F
- Combined weather × park context multiplier ≥ 1.25
- Dome park with elite batter profile — no weather suppression possible

## Failure Conditions

- Headwind ≥ 10 mph into batter (FROM CF direction) suppresses carry regardless of park
- Temperature ≤ 50°F — meaningful suppression (~4%)
- `MAX_PARK_PENALTY = 0.87` auto-blocks SF and SD — filter fires before escalation
- Heavy precipitation or weather delay

## MLB HR ENGINE Usage

Three factors in `clients/weather.py`: temperature, wind, humidity. All clamped before outer combined bound [0.80, 1.20]. Park factors in `data/park_factors.py`. Combined multiplier feeds `game_hr_probability()` in `engine/probability.py`. Context moderation guard (`CONTEXT_MODERATION_ENABLED`) caps combined multiplier at 1.25 for sub-average power batters.

## Related Doctrine Links

- [[Barrel_Quality/overview]] — barrel quality determines how much carry matters
- [[HR_Threat_Escalation/overview]] — favorable environment is one danger layer input
- [[Confidence_Tiering/overview]] — suppressive environments cap tier ceiling
- [[Market_Inefficiency/overview]] — books price park factor; rarely price real-time wind/humidity
