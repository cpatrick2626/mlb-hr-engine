# MAIN Calibration Refit Review — 2026-08-13

## Status

**PASS — review completed. VERDICT: NOT-WARRANTED.**

This was a findings-only, offline review. It did not change MAIN probability,
JIG scoring, calibration runtime code, tier thresholds, EV math, API payloads,
configuration, or deployment state. No candidate was written into a scoring
path.

## Scope and method

- Canonical harness: `scripts/analysis/evaluate_model.py`
- Fixed evaluation window: 2026-07-22 through 2026-08-06
- Seed: `20260807`
- Bootstrap: 5,000 paired percentile replicates clustered by slate date
- Probability source: captured `batter_stat_history.raw_payload.model_prob`
- Canonical row: latest `game_status='Preview'` snapshot strictly before
  `game_time_utc`, one per `(slate_date, batter_id, game_pk)`
- Temporal split: earliest 11 slates for fitting; latest 5 slates untouched for
  evaluation
- Candidate: weighted PAVA isotonic fit on the clean fit rows only

The `learning_metrics` human-review gate and the canonical warehouse population
are separate populations. The current loop count of 648 valid settled legs
establishes eligibility for a review; those legs were not mixed into or silently
renamed as the warehouse fit population.

## Holdout cleanliness hard gate

| Check | Result |
|---|---:|
| Valid settled legs reported by loop | 648 |
| Raw labeled warehouse snapshots in fixed window | 39,259 |
| Valid labeled/scored warehouse snapshots | 39,259 |
| All-status snapshots at/after game start excluded | 5,488 |
| Non-Preview snapshots excluded | 6,307 |
| Canonical duplicate pre-start Preview snapshots removed | 27,376 |
| Final clean canonical observations | 5,522 |
| Clean fit set (2026-07-22 through 2026-08-01) | 3,877 |
| Clean untouched holdout (2026-08-02 through 2026-08-06) | 1,645 |
| Fit/holdout key overlap | **0** |
| Clean n >= 500 | **YES** |

The exclusion counts are diagnostic dimensions and are not additive: a
non-Preview row may also be post-start. The canonical filter was applied before
deduplication and before any candidate fitting.

Canonical fingerprint:
`65dc484f327e30b5632e31c8113fbf7dd468a94482ee546156b935fed2479ca5`

## Canonical baseline reproduction

The fixed full-window baseline reproduced exactly:

- n = 5,522; HR = 415; 16 slates
- AUC = **0.650038**; 95% slate-cluster CI **[0.619638, 0.680628]**
- ECE = **2.8504pp**
- Mean predicted = 10.3658%; observed = 7.5154%

The do-nothing comparison on the untouched holdout was:

- n = 1,645; HR = 132; 5 slates
- AUC = **0.618055**; 95% slate-cluster CI **[0.601758, 0.651317]**
- ECE = **2.5384pp**
- Brier = **0.0739468**
- Mean predicted = 10.2373%; observed = 8.0243%

## Candidate held-out result

The isotonic candidate used 10 monotone blocks fitted only on the 3,877 clean
fit rows. The 1,645 holdout rows were not used during fitting.

- Held-out AUC = **0.618055** (same CI as baseline; exact AUC delta 0)
- Held-out ECE = **2.5226pp**
- Held-out Brier = **0.0734627**
- Mean predicted = 7.1582%; observed = 8.0243%
- Runtime-shaped four-decimal simulation: AUC 0.618060, ECE 2.5225pp

Paired held-out deltas, where positive means the candidate improved:

| Metric | Point improvement | Paired 95% CI | Beyond noise? |
|---|---:|---:|---|
| ECE | **+0.0158pp** | **[-0.8269pp, +1.1180pp]** | No |
| Brier | **+0.000484** | **[-0.000704, +0.001086]** | No |
| AUC | **0.000000** | **[0.000000, 0.000000]** | No degradation |

The ECE and Brier intervals cross zero. The observed improvements are not
distinguishable from slate-level sampling noise.

## Reliability data — untouched holdout

| Decile | n | Baseline pred | Candidate pred | Observed | Baseline gap | Candidate gap |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 164 | 3.6223% | 1.6093% | 1.8293% | +1.7930pp | -0.2199pp |
| 2 | 165 | 5.7051% | 3.0794% | 3.6364% | +2.0687pp | -0.5570pp |
| 3 | 164 | 6.9043% | 3.6941% | 7.3171% | -0.4128pp | -3.6230pp |
| 4 | 165 | 7.9752% | 4.3063% | 5.4545% | +2.5207pp | -1.1482pp |
| 5 | 164 | 8.9299% | 5.5219% | 9.1463% | -0.2164pp | -3.6244pp |
| 6 | 165 | 9.9810% | 6.4739% | 7.2727% | +2.7082pp | -0.7989pp |
| 7 | 164 | 11.1494% | 7.6393% | 11.5854% | -0.4360pp | -3.9461pp |
| 8 | 165 | 12.7699% | 10.2898% | 13.3333% | -0.5635pp | -3.0435pp |
| 9 | 164 | 15.1475% | 13.1822% | 8.5366% | +6.6109pp | +4.6456pp |
| 10 | 165 | 20.1552% | 15.7610% | 12.1212% | +8.0339pp | +3.6398pp |

The candidate reduces top-decile overconfidence but replaces it with material
underprediction across several middle deciles. Aggregate ECE is therefore
essentially unchanged.

## Tier-lift check

For review only, each existing tier cutoff was mapped through the same monotone
candidate. This preserved all 1,645 holdout memberships exactly; no config or
threshold file was edited.

| Tier | n | HR | Observed HR rate |
|---|---:|---:|---:|
| APEX | 78 | 11 | 14.10% |
| ELITE | 121 | 12 | 9.92% |
| EDGE | 396 | 45 | 11.36% |
| SIGNAL | 629 | 46 | 7.31% |
| WATCH | 331 | 16 | 4.83% |
| COLD | 90 | 2 | 2.22% |

Strict monotonic lift fails on the untouched holdout because ELITE is below
EDGE. The candidate does not create membership drift, but it also cannot pass
the required `APEX > ELITE > EDGE > SIGNAL > WATCH > COLD` held-out check.

## Verdict

**NOT-WARRANTED.**

The clean candidate produces only a 0.0158pp held-out ECE improvement, and the
paired confidence interval spans both meaningful harm and benefit. Brier has
the same uncertainty problem. AUC is preserved, but strict tier-lift
monotonicity fails on the untouched five-slate holdout. This does not meet the
operator's rule requiring lower held-out ECE beyond bootstrap noise without an
AUC or tier-lift penalty.

The result is a recommendation only. It does not ratify a recalibration.

## Validation and protected-surface proof

- `python -m api.learning_analysis --report` confirmed the stored 648-leg gate.
- `python -m api.learning_analysis` reproduced 648 in dry-run mode with zero
  database writes.
- The canonical harness reproduced fingerprint `65dc484f...` and AUC 0.6500.
- Candidate fitting and paired bootstrap ran in memory; the holdout key set had
  zero overlap with the fit key set.
- SHA-256 hashes were captured before review for `config.py`, `pipeline.py`,
  `engine/calibration.py`, `engine/probability.py`, `output/ranker.py`, and
  `api/main.py`; final verification must match these hashes and show zero diffs.
- No commit, push, deploy, migration, scoring write, config write, threshold
  write, or `learning_metrics` write was performed.

## Operator decision

Keep the current calibration frozen. Do not apply this candidate. Revisit only
after a broader clean temporal holdout adds independent slate clusters and can
show a CI-backed ECE improvement while preserving tier lift.
