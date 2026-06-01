---
title: Environmental Leverage - Doctrine
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Environmental Leverage — Doctrine

## Core Concept

Environmental carry conditions are a genuine, measurable modifier to HR probability. The MLB HR ENGINE quantifies three real-world factors (temperature, wind, humidity) plus park-level infrastructure bias. Environmental leverage doctrine governs when these factors justify escalation or suppression independent of batter/pitcher quality.

## Tactical Signals

| Factor | Baseline | Range | Source |
|--------|----------|-------|--------|
| Temperature | 72°F | [0.82, 1.08] | Open-Meteo |
| Wind (CF component) | 0 mph | [~0.85, ~1.15] | Open-Meteo `winddirection_10m` |
| Humidity | 55% RH | [0.96, 1.04] | Open-Meteo |
| Park factor | 1.00 (neutral) | [0.70, 1.40] | `data/park_factors.py` |
| Combined outer bound | 1.00 | [0.80, 1.20] | clamped in `weather.py` |

## Escalation Conditions

1. **Hitter park + tailwind**: park ≥ 1.10 AND wind ≥ 8 mph to CF → full carry stack
2. **Thermal amplification**: game-time temp ≥ 85°F adds ~2.5% HR lift above baseline
3. **Humidity-carry combo**: RH > 70% in warm game → peak carry conditions
4. **Dome neutrality**: dome parks remove all weather variance — reliable neutral baseline
5. **Combined ≥ 1.25**: context multiplier ceiling for average-power batters; elite batters uncapped

## Failure Conditions

- **Suppressive park blocks**: SF (Oracle), SD (Petco) — `MAX_PARK_PENALTY = 0.87` fires automatically; no escalation possible
- **Cold opener**: temp < 50°F — suppress tier regardless of other signals
- **Direct headwind**: FROM CF direction at ≥ 10 mph — hard carry suppression
- **Indoor neutrality**: dome stadiums prevent environmental leverage; only park factor applies
- **Context moderation guard**: `power_mult < 1.0` batters get combined multiplier capped at 1.25 — prevents false environmental inflation

## Doctrine Rules

**Rule 1 — Wind direction is FROM, not TO.** OpenMeteo `winddirection_10m` reports the direction wind is coming FROM. Wind FROM 180° (south) = blowing north = toward CF in most parks. Confirm park orientation via GPS coordinates stored in `data/park_factors.py`.

**Rule 2 — Environmental factors are multiplicative, not additive.** Warm + tailwind + humid = compounded effect. A 1.06 × 1.08 × 1.02 stack reaches 1.168 before park factor — significant uplift.

**Rule 3 — Dome parks receive 1.0 weather factor.** No wind, temperature, or humidity applies to dome stadiums. Park factor still applies. Treat dome games as environmentally stable.

**Rule 4 — Suppressive parks override environmental positives.** Oracle Park (SF) and Petco Park (SD) are blocked via `MAX_PARK_PENALTY = 0.87` filter. Tailwind in SF does not rescue a suppressed pick.

**Rule 5 — Context moderation guards sub-average batters.** Average power batters (`power_mult < 1.0`) in stacked environments were the primary false-positive source (Session 22 audit). The context guard caps their combined multiplier at `CONTEXT_MODERATION_LOW_POWER_CAP = 1.25`. Do not escalate average-power batters on environment alone.

## Doctrine Priority

```
Park factor → wind direction → temperature → humidity → combined clamp
```

Environmental escalation requires two positive factors. Single-factor environmental edge (warm day only, or favorable park only) does not justify tier upgrade without barrel quality support.

## Related Doctrine Links

- [[Barrel_Quality/doctrine]] — barrel quality required co-signal for environmental escalation
- [[HR_Threat_Escalation/doctrine]] — environment is danger layer input #3
- [[Confidence_Tiering/doctrine]] — suppressive environments cap STRONG tier
- [[Market_Inefficiency/doctrine]] — books price park, not real-time weather → edge source
