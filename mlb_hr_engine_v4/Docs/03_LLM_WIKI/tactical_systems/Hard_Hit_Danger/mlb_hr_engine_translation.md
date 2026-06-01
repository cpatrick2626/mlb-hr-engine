---
title: Hard Hit Danger - MLB HR Engine Translation
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Hard Hit Danger — MLB HR Engine Translation

## MAIN Impact

`clients/statcast.py` fetches `hard_hit_pct` and `exit_velocity_avg` from Savant leaderboard. Both are passed to `batter_power_multiplier()` in `engine/probability.py`:

```python
# Weight in batter_power_multiplier
hard_hit_contrib = (hard_hit_pct - LEAGUE_AVG_HARD_HIT) / LEAGUE_AVG_HARD_HIT * 0.10
exit_velo_contrib = (exit_velo - LEAGUE_AVG_EXIT_VELO) / LEAGUE_AVG_EXIT_VELO * 0.04
```

Combined hard-contact contribution: 14% of `batter_power_multiplier`. Statcast blending applies same prior-year trust rules (`PRIOR_YEAR_TRUST = 0.85`) as all Statcast signals.

Pitcher hard-contact allowed is NOT in `model_prob` computation. It is stored in the pitcher stats row for JIG/STRATEGY use.

## JIG Impact

JIG reads `hard_hit_pct` from the player row. Does not trigger independent danger layer — hard-hit is counted as barrel co-signal confirmation. When `hard_hit_pct ≥ 0.45` AND `barrel_rate ≥ 0.08`, JIG flags `DUAL_POWER_CONFIRMED = True`. This confirmation is used in STRATEGY tier assignment (supports STRONG tier even if barrel is 0.08 rather than 0.10).

JIG game-level danger clustering: evaluates all batters in a lineup. If ≥ 4 batters with `hard_hit_pct ≥ 0.42` face a pitcher with `pitcher_hh_allowed ≥ 0.42`, JIG sets `GAME_DANGER_CLUSTER = True` for the game.

## STRATEGY Impact

STRATEGY uses `DUAL_POWER_CONFIRMED` flag to:
- Allow STRONG tier at barrel 0.08 (vs normal 0.08 minimum — confirms borderline cases)
- Apply +1 danger layer credit to the player when dual-power confirmed
- Apply game-context +1 layer when `GAME_DANGER_CLUSTER = True` for that player's game

## Player Card Impact

Player cards display:
- `HARD-HIT: [rate]%` — compared to league avg 39.9%
- `EXIT VELO: [avg] mph` — compared to league avg 89.1
- `DUAL POWER` badge when hard-hit ≥ 45% + barrel ≥ 8%
- `DANGER CLUSTER` badge when game-level clustering active
- Pitcher hard-contact allowed displayed in matchup section when available

## Escalation State Impact

Hard-hit danger contributes to [[HR_Threat_Escalation/overview]] through:
1. `batter_power_multiplier` → indirectly raises `model_prob` → may push EV% above threshold → EV layer fires
2. `DUAL_POWER_CONFIRMED` → STRATEGY-layer +1 danger layer credit
3. `GAME_DANGER_CLUSTER` → game-context layer credit for all qualifying picks in that game

Hard-hit does NOT fire an independent danger layer directly — it operates through barrel support and game-context cluster paths.

## Deployment Decision Impact

Hard-hit does not independently unlock deployment. Its impact path:
```
hard_hit_pct → power_multiplier → model_prob → EV% → EV layer → tier
```

Portfolio composite score barrel_bonus includes power_multiplier implicitly:
- Higher hard-hit → higher power_mult → higher model_prob → higher ev_pct → better composite score

Danger clustering provides additional deployment uplift via game-context layer for picks already near LIVE threshold.

## Config Parameters

```python
# config.py
LEAGUE_AVG_HARD_HIT = 0.399     # 39.9% hard-hit rate baseline
LEAGUE_AVG_EXIT_VELO = 89.1     # mph average exit velocity baseline
PRIOR_YEAR_TRUST = 0.85          # Statcast prior-year blend (same for hard-hit)
MIN_CURRENT_YEAR_PA = 50         # below this: prior-year blending active

# Danger clustering thresholds (JIG layer — not in config.py currently)
# DANGER_CLUSTER_BATTER_THRESHOLD = 0.42  # hard-hit rate floor for cluster count
# DANGER_CLUSTER_PITCHER_THRESHOLD = 0.42 # pitcher HH allowed floor
# DANGER_CLUSTER_MIN_BATTERS = 4          # min batters to trigger cluster flag
```

## Related Doctrine Links

- [[Barrel_Quality/mlb_hr_engine_translation]] — primary signal; hard-hit feeds same multiplier
- [[HR_Threat_Escalation/mlb_hr_engine_translation]] — danger clustering game-level layer
- [[Pitch_Mix_Exploitation/mlb_hr_engine_translation]] — pitcher HH allowed feeds arsenal matchup
- [[Confidence_Tiering/mlb_hr_engine_translation]] — dual-power confirmation supports tier escalation
