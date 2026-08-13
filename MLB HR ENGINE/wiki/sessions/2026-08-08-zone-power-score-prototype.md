# 2026-08-08 — Zone Power Score Prototype: Signal Feasibility Test

**Agent:** Claude Code  
**Status:** COMPLETE — NO-GO verdict delivered. No production changes made.

---

## Task

Offline prototype to test whether a four-region zone matchup score adds predictive
signal for HR outcomes beyond the existing model. Pure feasibility test — no pipeline
changes, no scoring surfaces touched.

## Deliverable

`mlb_hr_engine_v4/scripts/analysis/zone_power_score_prototype.py`

All fetched data cached under `scripts/analysis/zone_cache/` (641 JSON files:
454 batter + 187 pitcher profiles, 2025 prior season).

---

## Results

### Canonical population
5,522 rows / 415 HRs / 16 slates / 2026-07-22 to 2026-08-06  
Baseline AUC: 0.6500 [0.6196, 0.6806]

### Coverage
- 98.8% of canonical rows got a ZPS (only 67 rows had no pitcher_id)
- 67.2% (3,709 rows) cleared usable threshold (batter >=30 BBE + pitcher >=100 pitches in 2025)

### Zone score alone
AUC: **0.5802 [0.5556, 0.6049]**  
Weak but real standalone signal (CI doesn't include 0.50).

### Paired delta AUC
model_prob vs rank-average(model_prob, ZPS):

| | AUC |
|---|---|
| Baseline model_prob | 0.6505 |
| Combined | 0.6411 |
| **DELTA** | **−0.0094 [−0.0250, +0.0078]** |

Point estimate is negative. CI straddles zero. Does NOT clear the ~0.04 noise floor. Adding ZPS slightly hurts.

### Redundancy correlations

| Feature | r | Note |
|---|---|---|
| model_prob | +0.310 | moderate |
| xwOBA (batter) | +0.378 | HIGH — substantial redundancy |
| barrel_pct | −0.002 | negligible |
| pull_air_pct | +0.042 | low |
| pitcher_barrel_allowed | +0.009 | negligible |

### Leakage
Zero — 2025 full prior season for both batter and pitcher profiles.

---

## Verdict: NO-GO

The four-region vertical-band zone score (UP/MID/DOWN/CHASE, 2025 prior season) adds
no incremental discriminative power beyond the existing model. The redundancy with
batter xwOBA (r=0.378) is the explanation: the zone-profile damage score remaps
aggregate contact quality that already feeds the model via the Statcast leaderboard.

**Do not build zone caching infrastructure for this version of the signal.**

---

## What Might Work (if revisiting)

1. **Handedness-adjusted quadrants** — in/out × up/down rather than pure vertical bands. The model has no per-zone directional interaction term; this is the most likely source of genuinely new information.
2. **2026 current-season pitcher profiles** — prior-season pitcher location may miss
   pitchers who changed their attack pattern; contemporaneous pitch distribution with
   careful temporal cutoffs could be a tighter matchup signal.

Both require more infrastructure than a one-session prototype.

---

## Design

Four regions: UP (zones 1-3) / MID (4-6) / DOWN (7-9) / CHASE (11-14).  
Used categorical `zone` column (not raw plate_x/plate_z) — immune to 2026 coordinate schema change.

Zone Power Score:
```
ZPS = sum_region[ (batter_xwoba[r] - league_avg[r]) * pitcher_pitch_pct[r] ]
```
Shrinkage: `trust = n / (n + 50)` for batter xwOBA; `trust = n / (n + 100)` for pitcher location.
Combination: rank-average of model_prob and ZPS (scale-invariant, no coefficient fitting).

## Protected Surfaces
pipeline.py, config.py, engine/, scoring/EV/filters — NOT imported, NOT modified.  
MAIN/JIG separation preserved. No Fly.io deploy. No config changes. No commits.
