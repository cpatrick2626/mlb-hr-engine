# 2026-08-13 — MAIN calibration refit review

## Verdict

**NOT-WARRANTED.** No recalibration was applied or ratified.

## Clean-data gate

- Learning-loop review gate: 648 valid settled legs (>=500)
- Fixed canonical window: 2026-07-22 through 2026-08-06
- Raw labeled warehouse snapshots: 39,259
- Post-start snapshots excluded: 5,488
- Final clean canonical population: 5,522
- Clean earlier fit set: 3,877 rows across 11 slates
- Clean later holdout: 1,645 rows across 5 slates
- Fit/holdout key overlap: zero
- Fingerprint: `65dc484f327e30b5632e31c8113fbf7dd468a94482ee546156b935fed2479ca5`

## Baseline and candidate

The canonical full-window baseline reproduced AUC 0.6500 with 95% slate-date
cluster-bootstrap CI [0.6196, 0.6806]. On the untouched holdout, the do-nothing
baseline was AUC 0.6181 [0.6018, 0.6513], ECE 2.5384pp, and Brier 0.0739468.

A weighted PAVA isotonic challenger was fitted only on the clean earlier rows.
On the untouched holdout it produced AUC 0.6181, ECE 2.5226pp, and Brier
0.0734627. The paired ECE improvement was only +0.0158pp with 95% CI
[-0.8269pp, +1.1180pp]. The paired Brier improvement was +0.000484 with 95%
CI [-0.000704, +0.001086]. Neither improvement was beyond bootstrap noise.

Mapped candidate cutoffs preserved all holdout tier memberships, but held-out
tier lift was not strictly monotonic: ELITE observed 9.92% versus EDGE 11.36%.
That independently fails the review's promotion rule.

## Decision state

- MAIN probability scoring: unchanged
- JIG scoring: unchanged
- Calibration/config/tier thresholds: unchanged
- API payload and EV math: unchanged
- Commit/push/deploy: none

Keep calibration frozen. Any later application remains a separate HIGH-risk,
operator-gated decision after broader clean temporal evidence.

Full evidence: `mlb_hr_engine_v4/scripts/analysis/calibration_refit_review_2026-08-13.md`.
