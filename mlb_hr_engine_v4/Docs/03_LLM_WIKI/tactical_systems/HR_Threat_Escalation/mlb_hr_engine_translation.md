---
title: HR Threat Escalation - MLB HR Engine Translation
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# HR Threat Escalation — MLB HR Engine Translation

## MAIN Impact

MAIN does not compute danger layers directly — it computes the underlying signal values that feed escalation. `pipeline.py` builds the player row with: `barrel_rate`, `hvy_modifier`, `fatigue_fac`, `context_mult`, `park_factor`, `ev_pct`, `edge_pct`, `model_prob`. The HR Threat Card system (`output/`) reads these fields and applies the danger layer logic to assign threat level. MAIN's filter system (`engine/filters.py`) blocks SUPPRESSED players before they reach output.

## JIG Impact

JIG is the primary escalation engine. JIG reads all signal fields from the player row and applies the danger layer scoring table. JIG output:
- `threat_level`: MAX / HIGH / LIVE / WATCH / SUPPRESSED
- `danger_layers`: integer count
- `escalation_flags`: list of triggered conditions
- `block_conditions`: list of any active BLOCK signals

JIG evaluates game-state overlays (TTOP, bullpen exposure) that MAIN cannot pre-compute.

## STRATEGY Impact

STRATEGY reads JIG's `threat_level` and maps it to confidence tier:
- MAX THREAT → CORE
- HIGH THREAT → STRONG
- LIVE THREAT → LIVE
- WATCH → WATCH
- SUPPRESSED → NO DEPLOYMENT

STRATEGY can downgrade tier if deployment context does not support (e.g., poor odds at time of deployment).

## Player Card Impact

Player cards render threat level prominently:
- Card header color: red (MAX) / orange (HIGH) / yellow (LIVE) / gray (WATCH) / blocked (SUPPRESSED)
- Danger layer breakdown shown on expanded card view
- Each contributing signal flagged: `[BARREL ✓] [ENV ✓] [HVY ✓] [FATIGUE ✓] [EV ✓]`
- Block conditions render as `[SUPPRESSED PARK ✗]` or `[BARREL TOO LOW ✗]`
- Game-level escalation flag shown when 3+ high-threat players in same game

## Escalation State Impact

Escalation state is the output of the danger layer system, not an input. The state flows:
```
Signal fields (MAIN) → Danger layers (JIG) → Threat level (JIG) → Confidence tier (STRATEGY) → Deployment decision
```

## Deployment Decision Impact

Deployment gate requires:
1. `threat_level` ≥ LIVE (danger_layers ≥ 2)
2. `model_prob ≥ MIN_EV_PCT` (currently 3.0%)
3. `barrel_rate ≥ 0.06` (minimum power quality)
4. No BLOCK condition active
5. `confidence_tier ≥ LIVE`

Portfolio optimizer (`optimize_daily.py`) applies additional constraints:
- `max_picks_total = 20` (moderate preset)
- `max_picks_per_team = 4`
- Composite score: `ev×0.35 + edge×0.30 + (confidence/50)×0.20 + barrel_bonus×0.15`

## Config Parameters

```python
# engine/filters.py
MIN_EV_PCT = 3.0          # minimum EV% to pass filter
MIN_EDGE_PCT = 2.0        # minimum edge% to pass filter
MIN_PA_THRESHOLD = 3.3    # blocks 9-hole batters
MAX_PARK_PENALTY = 0.87   # blocks SF, SD

# engine/probability.py
MAX_GAME_HR_PROB = 0.29   # hard ceiling on per-game HR probability
CONTEXT_MODERATION_LOW_POWER_CAP = 1.25
```

## Related Doctrine Links

- [[Barrel_Quality/mlb_hr_engine_translation]] — barrel_rate primary layer signal
- [[Environmental_Leverage/mlb_hr_engine_translation]] — context_mult layer signal
- [[Pitch_Mix_Exploitation/mlb_hr_engine_translation]] — hvy_modifier layer signal
- [[Pitcher_Fatigue/mlb_hr_engine_translation]] — fatigue_fac layer signal
- [[Confidence_Tiering/mlb_hr_engine_translation]] — threat level → tier mapping
- [[Market_Inefficiency/mlb_hr_engine_translation]] — ev_pct/edge_pct layer signals
