---
title: Barrel Quality - MLB HR Engine Translation
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Barrel Quality — MLB HR Engine Translation

## MAIN Impact

`clients/statcast.py` — fetches barrel_rate, exit_velo, hard_hit_pct, fb_pct, sweet_spot_pct, xslg, pull_pct from Baseball Savant leaderboard. Blends current-year and prior-year data when `current_pa < MIN_CURRENT_YEAR_PA (50)`.

`engine/probability.py` — `batter_power_multiplier(sc_stats)`:
- Barrel rate: 40% weight
- FB%: 20% (with quality gate when `FB_QUALITY_GATE_ENABLED=True`)
- Pull%: 10%, Sweet Spot%: 10%, Hard-Hit%: 10%, xSLG: 8%, Exit Velo: 4%

`base_hr_rate(season_hr_pa, recent_hr_pa, pa, barrel_rate)` — Bayesian regression with elite ceiling:
```python
reg_target_adj = max(0.30, min(ELITE_REG_TARGET_CEILING, statcast_mult))
# applies when barrel_rate >= ELITE_REG_TARGET_BARREL_THRESHOLD (0.08)
```

`apply_calibration(p, barrel_rate)` — elite tier (barrel ≥ 0.10) uses separate Platt params:
```python
A, B = ELITE_PLATT_A (0.92), ELITE_PLATT_B (-0.10)  # crossover 22.3%
# standard: A=0.7805, B=-0.4611, crossover 10.9%
```

## JIG Impact

JIG reads `barrel_rate` from the player row (pre-computed in pipeline). Applies danger layer logic:
- ≥ 0.12 → +2 layers; triggers elite tier flag
- 0.08–0.12 → +1 layer
- < 0.04 → BLOCK condition; suppresses all other signals

JIG also reads `blended_source` flag — if True and barrel ≥ 0.10, JIG notes cautious sizing recommendation on card.

## STRATEGY Impact

STRATEGY enforces barrel tier floors for confidence tier assignment:
- CORE eligible: `barrel_rate ≥ 0.10`
- STRONG eligible: `barrel_rate ≥ 0.08`
- LIVE eligible: `barrel_rate ≥ 0.06`
- WATCH maximum: `barrel_rate < 0.06`
- NO DEPLOYMENT: `barrel_rate < 0.04`

These are FLOORS — meeting the floor doesn't guarantee the tier; threat level must also confirm.

## Player Card Impact

Player cards display:
- `BARREL: [rate]%` with tier label (ELITE / ABOVE-AVG / AVG / BELOW-AVG / BLOCK)
- `POWER: [multiplier]` — `batter_power_multiplier` output
- `xSLG: [value]` — contact quality proxy
- `HARD-HIT: [rate]%` — secondary power indicator
- `FB%: [rate]%` — fly-ball rate with gate indicator if applicable
- `BLENDED SOURCE` flag when prior-year Statcast active

## Escalation State Impact

Barrel tier is the primary danger layer gatekeeper in [[HR_Threat_Escalation/overview]]:
- Sub-4% barrel = BLOCK → overrides all positive signals
- Elite barrel (≥ 12%) alone = 2 danger layers → minimum LIVE THREAT
- Elite barrel + any one other confirmed signal = 3 layers → HIGH THREAT

## Deployment Decision Impact

Barrel is the only signal that can single-handedly block deployment (< 4%) or single-handedly reach minimum deployment threshold (≥ 12%). All other signals require barrel support.

Portfolio optimizer (`portfolio/optimizer.py`) barrel bonus:
```python
barrel_bonus = max(0, (barrel_rate - LEAGUE_AVG_BARREL_RATE) / LEAGUE_AVG_BARREL_RATE)
# barrel_bonus weight: 15% of composite score
```

Preset-specific barrel floors:
- conservative: `min_barrel = 0.06`
- moderate: no hard floor (composite score handles)
- barrel_focused: `min_barrel = 0.08`

## Config Parameters

```python
# config.py
LEAGUE_AVG_BARREL_RATE = 0.055
LEAGUE_AVG_EXIT_VELO = 89.1
LEAGUE_AVG_HARD_HIT = 0.399
LEAGUE_AVG_XSLG = 0.418
LEAGUE_AVG_SWEET_SPOT = 0.334
LEAGUE_AVG_PULL_PCT = 0.392
LEAGUE_AVG_FB_PCT = 0.264          # Savant pure FB% (excludes popups)
PRIOR_YEAR_TRUST = 0.85
MIN_CURRENT_YEAR_PA = 50

# FB% quality gate
FB_PCT_WEIGHT = 0.20
FB_QUALITY_GATE_ENABLED = True
FB_QUALITY_GATE_FLOOR = 0.50
FB_PARK_SCALE = 0.30

# Elite barrel settings
ELITE_REG_TARGET_ENABLED = True
ELITE_REG_TARGET_CEILING = 1.5
ELITE_REG_TARGET_BARREL_THRESHOLD = 0.08
ELITE_PLATT_ENABLED = True
ELITE_PLATT_A = 0.92
ELITE_PLATT_B = -0.10
ELITE_PLATT_BARREL_THRESHOLD = 0.10
```

## Related Doctrine Links

- [[Hard_Hit_Danger/mlb_hr_engine_translation]] — hard-hit% secondary signal in same multiplier
- [[HR_Threat_Escalation/mlb_hr_engine_translation]] — barrel tier → danger layer count
- [[Environmental_Leverage/mlb_hr_engine_translation]] — context moderation guard uses barrel as gate
- [[Confidence_Tiering/mlb_hr_engine_translation]] — barrel floor gates tier assignment
