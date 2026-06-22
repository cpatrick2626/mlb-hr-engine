# JIG Normalization Saturation Finding

**Date:** 2026-06-21
**Status:** OPEN — do NOT patch until calibration loop validates
**Boundary:** Formula-containment — do not touch _jig_score, weights, or _n() centers/sigmas without operator sign-off

---

> **CORRECTION — 2026-06-21 (live API measurement, GET /api/slate leaderboard_rows_jig, n=318)**
>
> Verified against live API: production JIG is **HEALTHY**. "3 metrics dead / ceiling 55 / every player APEX / stale 13.5 thresholds" were derived from `app.py` (dead Streamlit surface) — not production. This finding applies only to the dead Streamlit surface for those claims.
>
> Live: jigScore 5.6–93.0, mean 47.5, 14 APEX (4.4%) — well-spread pyramid. **Formula saturation (base_score clamping) is CONFIRMED as a code fact** (recompute-verified). **Distribution-level ceiling clustering is RESOLVED — NOT occurring (2026-06-21, n=318):** >= 90: 7 (2.2%), >= 85: 21 (6.6%), top 10 scores well-separated (93.01 → 88.63), zero at ceiling. The clamp exists but does not compress live output. "Elite hitters jam to identical scores" was a Streamlit ceiling-55 artifact. No live saturation problem as of 2026-06-21; revisit if future slate shows top-end bunching.

---

## Finding

The realigned power weights (xSLG .25 / barrel .20 / xISO .15 / pull_air .15 / hard_hit .15 / sweet_spot .10, confirmed live at commit e4d19db) are **inert at the elite tier** because all six base components clamp to 1.0 before elite Statcast values. `base_score` is identical across elite hitters; ranking at the top is driven by `hr_term` + tactical signals, not the power weights.

## Evidence

| Batter | Barrel% | xSLG | base_score |
|--------|---------|------|------------|
| Alvarez | 13.3% | .719 | 1.0 |
| Kurtz | 8.9% | .464 | 1.0 |

Both elite and merely-good profiles produce `base_score = 1.0`. The weights do not differentiate them.

## Mechanism

`_n(value, center, sigma)` maps each component to [0, 1]. Elite Statcast values saturate the sigmoid before the weights are applied. Changing weights from `.25/.20/...` to any alternative distribution has zero effect on rank order within the saturated tier.

## The real lever

`_n()` centers and sigmas — NOT the weights. Shifting centers upward into elite territory would restore weight sensitivity. This is a calibration decision, not a weight decision.

## What NOT to do

- Do not re-tune weights to fix saturation — they are already correctly aligned per e4d19db
- Do not patch _n() centers/sigmas speculatively
- Do not merge JIG and MAIN to "fix" ranking at the elite tier

## Next step (operator call)

Validate whether current ranking has an edge in the calibration loop before deciding whether saturation is a problem. If elite-tier ordering already tracks outcomes, saturation may be harmless (or beneficial — avoids overfitting on noisy high-end Statcast). Only re-center _n() if calibration shows ordering failure at the top.

**Linked:** 2026-06-21-partial-signal-no-penalty.md, 2026-06-21-velo-signal-parked.md
