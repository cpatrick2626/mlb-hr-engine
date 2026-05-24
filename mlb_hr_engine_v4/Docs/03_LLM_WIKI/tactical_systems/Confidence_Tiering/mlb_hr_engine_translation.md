---
title: Confidence Tiering - MLB HR Engine Translation
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Confidence Tiering — MLB HR Engine Translation

## MAIN Impact

MAIN does not assign confidence tiers — it computes the signal fields that feed tier assignment. `pipeline.py` outputs player rows with `ev_pct`, `edge_pct`, `model_prob`, `barrel_rate`, `hvy_modifier`, `fatigue_fac`, `context_mult`. The `output/ranker.py` composite score (`EV×0.40 + Edge×0.35 + Confidence×0.25`) incorporates tier confidence as a numeric weight. Tier is assigned downstream at STRATEGY layer.

## JIG Impact

JIG assigns `threat_level` which directly maps to confidence tier. JIG output field `threat_level` → STRATEGY maps to `confidence_tier` per the danger layer table. JIG is the only layer that computes danger layer count; MAIN and STRATEGY read JIG output.

## STRATEGY Impact

STRATEGY consumes JIG's `threat_level` and applies tier movement rules:
- Checks for hard BLOCK conditions — overrides JIG if any active
- Checks for odds-movement downgrade — re-evaluates EV% with current odds
- Assigns final `confidence_tier` field to player row
- Applies portfolio optimizer preset (`conservative`, `moderate`, `relaxed`, `barrel_focused`)

## Player Card Impact

Player cards render confidence tier as primary display element:
- Card header background: CORE=red, STRONG=orange, LIVE=yellow, WATCH=gray, NO DEPLOYMENT=blocked
- Tier label displayed prominently: `[CORE]`, `[STRONG]`, `[LIVE]`, `[WATCH]`
- Composite score displayed: `SCORE: [value]`
- Tier justification shown: confirmed signal indicators and any active BLOCK conditions
- Sizing recommendation displayed per tier: `SIZE: [recommended units]`

## Escalation State Impact

Confidence tier IS the final escalation state output. Tier flows from:
```
danger_layers (JIG) → threat_level (JIG) → confidence_tier (STRATEGY) → deployment action
```

Tier movement at STRATEGY layer responds to:
- Pre-game weather updates
- Lineup lock confirmation
- Odds movement check (closing line vs opening line)
- TTOP game-state evaluation at estimated start time

## Deployment Decision Impact

Deployment gate keys on `confidence_tier`:
- CORE → deploy at max configured bet size
- STRONG → deploy at 60–80% of max
- LIVE → deploy at minimum unit or 40–50% of max
- WATCH → no deployment; add to monitoring queue
- NO DEPLOYMENT → remove from slate; do not track

Portfolio optimizer picks per `optimize_daily.py`:
```python
# composite score (portfolio/optimizer.py)
score = ev * 0.35 + edge * 0.30 + (confidence / 50) * 0.20 + barrel_bonus * 0.15
```

Confidence normalized: CORE=50, STRONG=40, LIVE=30, WATCH=10.

## Config Parameters

```python
# output/ranker.py — composite score weights
RANKER_EV_WEIGHT = 0.40
RANKER_EDGE_WEIGHT = 0.35
RANKER_CONFIDENCE_WEIGHT = 0.25

# portfolio/optimizer.py — tier numeric values
TIER_VALUES = {"CORE": 50, "STRONG": 40, "LIVE": 30, "WATCH": 10}

# engine/filters.py — deployment gate floors
MIN_EV_PCT = 3.0
MIN_EDGE_PCT = 2.0
```

## Related Doctrine Links

- [[HR_Threat_Escalation/mlb_hr_engine_translation]] — threat_level → tier mapping
- [[Market_Inefficiency/mlb_hr_engine_translation]] — odds movement triggers tier downgrade
- [[Barrel_Quality/mlb_hr_engine_translation]] — barrel_rate sets tier floor
- [[Hard_Hit_Danger/mlb_hr_engine_translation]] — hard-hit danger layer feeds tier escalation
