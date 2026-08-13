# 2026-08-07 — Warehouse isotonic recalibration (MAIN model_prob)

## Premise correction (important)

The tasking diagnosis ("6,558 labeled rows, predicted 17.9% vs observed 4.5%, ~4x overconfident, AUC 0.60") **does not reproduce against the current warehouse**. Actual labeled state of `batter_stat_history` on 2026-08-07:

- 39,385 labeled snapshot rows / **5,596 unique batter-games** across 17 slates (2026-07-21 → 2026-08-06)
- Stored final `model_prob`: mean **10.68%** vs observed **7.63%** (dedup) — mild overconfidence, not 4x
- **AUC 0.7092**, not 0.60
- No field in `raw_payload` averages 17.9%; no filter reproduces 6,558 rows or 4.5% observed
- Likely explanation for the stale diagnosis: earlier partial/incorrect labeling (cf. the mass-0 labeling guard added to `api/warehouse_backfill.py`)

The recalibration was still warranted: the 4–11% band over-predicts by +3.0 to +4.4pp, and the 25%+ region (elite-Platt players clamped at the 0.29 cap) predicted 27.5% vs observed 9.7%.

## What changed

Scoring chain (documented order): raw `game_hr_probability` → `apply_prob_scale` (learned, 1.12) → `apply_calibration` (Platt, unchanged) → **NEW: `apply_warehouse_isotonic`** → final `model_prob`.

- `engine/calibration.py` — new `apply_warehouse_isotonic()`; loads curve artifact once per session
- `mlb_hr_engine_v4/data/warehouse_isotonic.json` — fitted curve (17 monotone blocks), refit via `scripts/analysis/fit_warehouse_isotonic.py`. Deliberately NOT in `tracking/` (Fly volume shadows that dir)
- `pipeline.py` — applied at both model_prob finalization sites (real + projected)
- `config.py` — `WAREHOUSE_ISOTONIC_ENABLED=True`; `FS_TIER_THRESHOLDS` rethresholded to the isotonic image of the old cutoffs (0.20/0.16/0.11/0.07/0.04 → 0.189/0.152/0.061/0.027/0.018) so historical tier membership is preserved exactly

Isotonic fitted on the FINAL displayed model_prob (fit input == production input; no double-correction). Composes after Platt rather than replacing it, so the elite-Platt branch and current board ranking are preserved exactly.

## Validation

- AUC 0.7092 before AND after (delta 0.00000) — ranking preserved
- Mean calibrated 7.68% vs observed 7.63%; Brier 0.06873 → 0.06757; reliability within ±0.8pp per bin
- Tier occupancy unchanged (APEX 311, ELITE 507, EDGE ~1444, SIGNAL ~1973, WATCH 1054, COLD 307 on the 5,596)
- JIG unaffected: `_jig_score` consumes no model_prob (api/main.py:654); JIG tiers separate
- Model inputs/features unchanged — levels only

## NOT done / flags for operator

- **NOT deployed to Fly** — awaiting ratification
- EV/pick filters (`MIN_EV_PCT=14.0`, adaptive `min_model_prob` floor 0.04) and `MATCHUP_QUALITY_*` thresholds still assume the old scale — qualified-pick volume will shrink post-calibration; needs a separate scoped decision
- auto_learn's `prob_scale` suggestions now conflict with the isotonic stage (double-correcting levels); refit required if prob_scale or Platt params change
- app.py hardcoded legend strings (≥18%/≥13% etc.) had pre-existing drift vs config; untouched
- Pre-existing test-env failures: missing `rapidfuzz` in shell venv; pitcher-savant CSV regression test — unrelated to this change

## Live-application verification (2026-08-07, second pass)

Operator tasking asserted the isotonic calibration was NOT applied in the live scoring
path because /api/slate top picks still read ~0.18. Verified against the actual stored
runtime payload (Supabase `pipeline_runs.payload->slate_cache`, run ran_at
2026-08-07T15:02:14Z, GH Actions cron on origin/main):

- Mean model_prob 0.0568 across 389 rows (yesterday, pre-calibration code: 0.1099)
- 55 rows piled on the isotonic flat segment 0.0241-0.0244 (curve maps raw
  0.0496-0.0633 there); 4 rows at the exact 0.001 clamp floor — impossible uncalibrated
- Tiers assigned on new FS_TIER_THRESHOLDS: 15 ELITE (>=0.152), 0 APEX (>=0.189)
- The ~0.18 top picks (Abreu 0.1865, Goodman 0.1861, Ohtani 0.1833) ARE calibrated:
  the fitted curve is near-identity in the 0.17-0.21 region (raw 0.1777->0.1804,
  raw 0.207->0.191). The single-digit expectation came from the earlier 17.9%->4.5%
  diagnosis that did not reproduce (see NOTE in commit 54599fc).

No code change. Remaining gap: the Fly machine still runs pre-54599fc code — its
cache-miss live fall-through in /api/slate and any in-process tier derivation would
use the old scale until Fly deploy (awaiting ratification).
