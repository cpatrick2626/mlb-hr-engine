---
title: Environmental Leverage - MLB HR Engine Translation
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Environmental Leverage — MLB HR Engine Translation

## MAIN Impact

`clients/weather.py` fetches temp, wind, and humidity from Open-Meteo API using park GPS coordinates stored in `data/park_factors.py`. Returns `temp_factor`, `wind_factor`, `humidity_factor`. These are passed to `game_hr_probability()` in `engine/probability.py` as part of the context multiplier chain. Park factor loaded from `data/park_factors.py` and applied separately. Combined context multiplier is clamped [0.80, 1.20] after all factors multiply.

## JIG Impact

JIG reads the combined environmental context from the player row (`park_factor`, `weather_factor`, `context_mult`). Favorable environment (combined ≥ 1.15) increments JIG danger layer count. Suppressive park (park_factor ≤ 0.87) triggers JIG suppression flag — overrides positive signals from barrel or pitch mix. JIG does not re-fetch weather; it reads pre-computed values from `pipeline.py`.

## STRATEGY Impact

STRATEGY uses environmental tier to set deployment posture ceiling:
- Combined context ≥ 1.20 AND barrel ≥ 0.10 → eligible for CORE tier
- Park factor ≤ 0.87 → ceiling capped at WATCH regardless of barrel quality
- Dome park → environmental neutral; tier determined solely by batter/pitcher signals

## Player Card Impact

Player cards display park factor as `PARK: [factor]` and weather as `ENV: [combined factor]`. Cards flag carry stack when combined ≥ 1.15: renders `CARRY STACK` indicator. Dome parks render `DOME — ENV NEUTRAL`. Suppressive parks render `SUPPRESSED PARK` warning. Wind direction and speed shown when relevant (non-dome, wind ≥ 5 mph).

## Escalation State Impact

Environmental signals feed [[HR_Threat_Escalation/overview]] danger stacking:
- Park factor ≥ 1.15 → +1 danger layer
- Combined weather ≥ 1.10 → +1 danger layer
- Combined context ≥ 1.25 → +2 danger layers (full carry stack)
- Park factor ≤ 0.87 → −1 danger layer (automatic suppression layer)
- Dome → 0 weather contribution to danger layers (neutral)

## Deployment Decision Impact

Environmental leverage alone does not deploy. Required structure:
1. `barrel_rate ≥ 0.08` — batter must have power quality to benefit from carry
2. `model_prob ≥ MIN_EV_PCT` — base probability clears filter threshold
3. Environmental combined ≥ 1.00 — neutral or better (no suppression active)

Deployment blocked when: park_factor ≤ 0.87 OR `MAX_PARK_PENALTY` filter fires OR combined context < 0.90 (headwind + cold stack).

## Config Parameters

```python
# config.py
MAX_PARK_PENALTY = 0.87          # blocks Oracle Park, Petco Park
CONTEXT_MODERATION_ENABLED = True
CONTEXT_MODERATION_LOW_POWER_CAP = 1.25  # cap for power_mult < 1.0 batters
LEAGUE_AVG_HUMIDITY = 55.0       # % RH baseline for neutral humidity factor

# clients/weather.py — factor ranges (hardcoded clamps)
TEMP_BASELINE = 72               # degrees F
TEMP_FACTOR_RANGE = (0.82, 1.08)
WEATHER_OUTER_BOUND = (0.80, 1.20)
```

## Related Doctrine Links

- [[Barrel_Quality/mlb_hr_engine_translation]] — barrel required co-signal for environmental escalation
- [[HR_Threat_Escalation/mlb_hr_engine_translation]] — environment feeds danger layer count
- [[Market_Inefficiency/mlb_hr_engine_translation]] — weather not priced by books → edge source
- [[Confidence_Tiering/mlb_hr_engine_translation]] — suppressive environment caps tier ceiling
