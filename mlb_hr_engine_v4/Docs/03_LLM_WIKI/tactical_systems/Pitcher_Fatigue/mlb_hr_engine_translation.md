---
title: Pitcher Fatigue - MLB HR Engine Translation
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Pitcher Fatigue — MLB HR Engine Translation

## MAIN Impact

Fatigue factor computed in `engine/probability.py` → `_pitcher_fatigue_factor(days_rest)`. Returns `fatigue_fac` multiplier: 1.06–1.08 for ≤ 3 days rest, 1.01–1.03 for 4 days, 1.00 for 5+ days. Applied to `pit_factor` before pitcher factor attenuation in `game_hr_probability()`. Attenuation: `PITCHER_FACTOR_SCALE = 0.60` compresses all pitcher signals including fatigue boost.

Applied pipeline order:
```
pit_factor → fatigue_fac → PITCHER_FACTOR_SCALE attenuation → combined context multiplier
```

## JIG Impact

JIG reads `fatigue_fac` from the pre-computed player row. If `fatigue_fac > 1.03` (short rest confirmed), JIG increments danger layer count by +1. JIG also evaluates TTOP risk as game-state overlay — not from `fatigue_fac` directly. JIG does not re-compute fatigue; it uses pipeline output.

## STRATEGY Impact

STRATEGY uses fatigue signal to adjust confidence tier ceiling:
- `fatigue_fac ≥ 1.06` (≤ 3 days rest) + barrel ≥ 0.10 → eligible for CORE tier
- `fatigue_fac ≥ 1.01` (4 days rest) + barrel ≥ 0.08 → eligible for STRONG tier
- Standard rest → fatigue contributes nothing to STRATEGY tier position

TTOP evaluation at STRATEGY layer: if starter projected to face target batter a third time AND `fatigue_fac > 1.0` → maximum escalation posture.

## Player Card Impact

Player cards display `REST: [N] days` indicator. Short rest renders `SHORT REST` flag with color coding (orange/red). TTOP projections displayed as `TTOP RISK: [inning estimate]` when starter pitch count projection is available. `fatigue_fac` value displayed as `FATIGUE: [factor]` in model details row.

## Escalation State Impact

Fatigue feeds [[HR_Threat_Escalation/overview]] danger stacking:
- `fatigue_fac ≥ 1.06` → +1 danger layer
- `fatigue_fac ≥ 1.06` + TTOP projected → +2 danger layers
- Standard rest (1.00) → 0 contribution to danger layers
- Extra rest (1.00) → 0 contribution (same as standard)

## Deployment Decision Impact

Short rest alone insufficient for deployment. Required:
1. `barrel_rate ≥ 0.08` — power quality to exploit fatigue window
2. `model_prob ≥ MIN_EV_PCT` — base probability clears filter
3. `fatigue_fac ≥ 1.01` — at minimum 4-day rest short (mild signal)

Effective fatigue boost after attenuation (PITCHER_FACTOR_SCALE = 0.60):
- Raw 1.08 → ~1.048 effective
- Raw 1.03 → ~1.018 effective

## Config Parameters

```python
# config.py
PITCHER_FACTOR_SCALE = 0.60    # compresses pit_factor range [0.55,1.60] → [0.73,1.36]

# engine/probability.py — fatigue factor thresholds (hardcoded)
# ≤ 3 days: 1.06–1.08
# 4 days: 1.01–1.03
# 5+ days: 1.00
# Extra rest linear decay REMOVED 2026-05-16
```

## Related Doctrine Links

- [[Pitch_Mix_Exploitation/mlb_hr_engine_translation]] — fatigue amplifies pitch mix HVY modifier
- [[Barrel_Quality/mlb_hr_engine_translation]] — barrel required co-signal for fatigue deployment
- [[HR_Threat_Escalation/mlb_hr_engine_translation]] — fatigue feeds danger layer count
- [[Confidence_Tiering/mlb_hr_engine_translation]] — short rest maps to tier escalation gate
