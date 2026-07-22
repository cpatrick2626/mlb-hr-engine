# Calibration and Learning-Systems Audit — 2026-07-22

Status: evidence-backed documentation record. No code, scoring, configuration, calibration, or freeze-state changes were made.

## 1. Learning systems state

- Auto-learn has been **FROZEN** since 2026-07-09: `AUTO_LEARN_FROZEN=True`. It remains pending a calibration replay that never happened.
- The old CSV auto-learn path reads a dead local source: `pick_tracker.csv` has been stale since 2026-05-31, while production tracking moved to Fly/Supabase.
- The learning loop is broken in two places:
  1. Supabase outcomes are never bridged back into learning.
  2. The explicit freeze prevents automatic learning writes.
- Capture systems are all **ACTIVE**: Supabase picks contains 4,937 rows, settlement contains 328 settled legs, and the warehouse is active. Nothing currently closes this capture-to-learning loop.
- Only `prob_scale=1.12`, frozen on 2026-07-09, currently affects the model. MAIN/JIG separation remains unchanged; this is a MAIN probability-calibration finding, not JIG tactical scoring.

## 2. Calibration finding — `prob_scale=1.12`

Evaluation used 328 out-of-sample settled legs from 2026-06-25 through 2026-07-20. The observed HR rate was 19.5%.

**VERDICT: `1.12` validated — keep frozen.**

- Aggregate predicted rate: **19.50%**.
- Observed rate: **19.51%**.
- The aggregate result is dead-center matched.
- Brier across tested scales `0.85`–`1.25` varies by only **0.001**, which is noise at this sample size.
- Changing the scale would also invalidate `MIN_EV_PCT=14.0`.

Do **not** change `prob_scale` or unfreeze auto-learn based on the current data.

## 3. Real finding — ranking discrimination

Within the operator-selected 15%–25% top-pick band, the model-probability buckets are non-monotone:

- 15%–17.5% predicted: **25.4% actual**, `n=67` — overperforms.
- 20%–22.5% predicted: **10.8% actual**, `n=83` — underperforms.

A constant 19.5% prediction scores better in this slice (**Brier 0.1571**) than any scaled model. In this operator-selected betting range, `model_prob` therefore shows little discrimination **here**.

Caveats:

- These are operator-selected legs, not the full board; the result does not generalize automatically.
- The sample is insufficient to ratify: approximately 500 settled legs are needed.
- The signal is approximately 2σ: suggestive, not conclusive.

## 4. Ratify-worthy future action — not now

**Ranking discrimination — revisit at ~500 legs.**

At approximately 500 settled legs, re-run this audit. If the 20%–22.5% shortfall and 15%–17.5% overperformance persist, the appropriate corrective direction is a Platt/isotonic **shape refit on live legs**, not a scale change.

Any future work must be scoring-surface, ratify-first, and backtest-gated. Do not alter `prob_scale=1.12` or unfreeze learning from this evidence alone.

## Recommended next action

Warehouse Phase 2 outcome backfill: bridge settled outcomes into the warehouse/learning evidence path, while keeping the current calibration freeze intact until the future ratification threshold is reached.
