# 2026-09-21 — Probability Lineage Stage 2 production release

## Status

PASS — PRODUCTION COMPLETE / PROSPECTIVE EVIDENCE WINDOW STARTED

- Code release: `80c0d92278cadd432ff5a056bce29adcd3da64f4`
- Previous remote `main`: `1a49252ec9fa8fc35d7b0c4419ae52f264dc02b1`
- Push: normal fast-forward; no force push
- Blocked commit `ca3a4b84d3bc50cfab243ba076ee0d9362bb93d0` was excluded from release ancestry.
- Local archive `archive/blocked-adaptive-authority-ca3a4b8` remains at the blocked commit and was not pushed.

## Fly release

- App: `mlb-hr-api`
- Previous release: 152
- Previous image: `registry.fly.io/mlb-hr-api:deployment-01M2PYDF5HJ7DTT6N0F7CYNRJY`
- Previous digest: `sha256:0120e68ab96b76131b61bce4c1636c07ba52bcf334ad5673667caa21acb91664`
- New release: 153
- New image: `registry.fly.io/mlb-hr-api:deployment-01M32DY4Q3YD4EEF0146GYRMJD`
- New digest: `sha256:a6b6fb6a0d5325a0d18fe54139f6a7ca937d09d3488275b91d955f3469fdf143`
- Machine: `7841255a9d2e28`
- Health: machine good; `GET /health` returned 200.

The deployment source was the clean release worktree at the exact code release SHA. `TRACKING_DATA_DIR=/data` remained active. The only mounted adjustment file found was `/data/learned_adjustments.json`, containing `{"prob_scale": 1.12}`.

## Cross-lane production proof

| Lane | Code identity | Run | Effective scale | Artifact authority | Result |
|---|---|---|---:|---|---|
| GitHub manual production pipeline | `80c0d92278cadd432ff5a056bce29adcd3da64f4` | Actions `35628448517`; lineage `2026-09-21T16:53:39.88872+00:00` | 1.0 | Missing-artifact/default reader behavior | VALID |
| Fly generation | release 153 image `deployment-01M32DY4Q3YD4EEF0146GYRMJD`; deployed from `80c0d92278cadd432ff5a056bce29adcd3da64f4` | bounded trigger; lineage `2026-09-21T16:57:09.681066+00:00` | 1.12 | `/data/learned_adjustments.json` | VALID |

Each lane wrote 84 real MAIN rows for the 2026-09-21 slate. Every row carried `snapshot_kind=main_probability`, the expected source lane, full required lineage, and the expected scale. Both batches contained 80 standard-Platt rows and four elite-Platt rows.

Source-exact transition checks found zero scale, Platt, isotonic, or final-payload mismatches. For every inspected row, `probability_lineage.final_model_prob == raw_payload.model_prob`. The GitHub run also wrote 84 separate JIG shadow rows; none contained `probability_lineage`. No duplicate warehouse primary keys or lost MAIN batch was observed.

## Containment

- The 2,320-case regression passed with exact `float.hex()` equality.
- Focused lineage tests: 10 passed, plus 10 subtests.
- Six changed/new Python files compiled successfully.
- `git diff --check` passed.
- No migration or database schema change occurred.
- `GET /api/slate` returned 200, cache-fresh, with 84 MAIN rows and 84 JIG rows.
- No public `probability_lineage` field was exposed.
- Existing MAIN `hrprob` ordering and JIG `jigScore` ordering remained descending.
- No frontend file changed in the candidate; no frontend behavior change was expected from the push.
- Platt coefficients, elite threshold, isotonic state, tier thresholds, probability clamp, expected plate appearances, and the adaptive reader were unchanged.
- JIG, AEE, HVY, TM, Roles, sportsbook selection, odds parsing, implied probability, EDGE, EV, projected EDGE/EV, fair odds, buy odds, and CLV were unchanged.

## First fully instrumented production baseline

- Slate date: `2026-09-21`
- First valid GitHub lineage run: `2026-09-21T16:53:39.88872+00:00`
- Fly validation lineage run: `2026-09-21T16:57:09.681066+00:00`
- Code release: `80c0d92278cadd432ff5a056bce29adcd3da64f4`
- GitHub effective scale: 1.0
- Fly effective scale: 1.12

**PROSPECTIVE PROBABILITY-LINEAGE EVIDENCE WINDOW: STARTED**

Do not backdate the window. Historical rows without valid lineage are excluded.

## Prospective analysis contract

Use only `snapshot_kind=main_probability`, `game_status=Preview`, `run_ts < game_time_utc`, appeared and lineup-confirmed players, the latest eligible pregame snapshot per `slate_date + batter_id + game_pk`, valid lineage, and resolved HR outcomes. Exclude JIG shadows, missing lineage, post-start rows, non-appearances, unresolved or postponed games, duplicates, and unlabeled outcomes.

Later replay must start from the stored `pre_scale_model_prob` and pass scales 1.0 and 1.12 through the recorded clamp, four-decimal round, Platt branch and coefficients, and isotonic state. The scale winner remains undecided pending the approved sample and temporal thresholds. No probability scale, calibration coefficient, or formula authority changed in this release.

Minimum evidence remains 60 completed slates, 13,000 appeared and lineup-confirmed player-games, 1,400 binary HR events, 200 HR events among probabilities at or above 17.5%, and three predeclared chronological blocks. Target roughly eight contiguous regular-season weeks where the MLB calendar permits; carry collection into the next valid continuation rather than inventing an unavailable 2026 window.

The future decision will prioritize paired Brier delta with slate-cluster bootstrap 95% confidence intervals, paired log loss, calibration, fixed-bin ECE, calibration intercept and slope, top-band honesty, and temporal stability. AUC, tier movement, top-cohort movement, and market-display churn remain secondary. Do not select a winner by AUC alone.

GRAPHIFY STATUS: STALE / NOT REFRESHED.
