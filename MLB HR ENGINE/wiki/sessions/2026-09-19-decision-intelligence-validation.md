# MLB HR Engine — Decision Intelligence Validation & Formula Audit
2026-09-19

Repo HEAD: `1a49252ec9fa8fc35d7b0c4419ae52f264dc02b1`

Source report: `C:\MLB HR Engine\analysis-output\decision-validation-2026-09-19\VALIDATION_REPORT.md` (kept outside the repo; this page is the durable in-repo record).

## Status: PARTIAL

Every reconstructable surface was validated out of sample. The partial flag is driven entirely by four surfaces that are never persisted in point-in-time form and so could not be outcome-tested: AEE (Arsenal Edge / SIGNAL, since SIGNAL is AEE confidence), `hvy_modifier`, and CLV. Nothing about the completed work is downgraded by that gap.

This is Stage 1: historical outcome research and counterfactual simulation only. No production code, config, calibration, cache, or database record was modified. Nothing was committed, pushed, or deployed.

## Data coverage

| Item | Value |
|---|---:|
| Slates | 59 (2026-07-22 through 2026-09-19) |
| Games | 791 |
| Player-games built | 21,968 |
| Appeared in box score | 16,782 |
| Bettable (appeared + lineup confirmed) | 13,319 |
| HR events, bettable population | 1,458 |
| HR events, appeared population | 1,628 |

The 1,458 and 1,628 figures are two different scopes, not one number rounded two ways: 1,458 is home runs among batters who appeared *and* were lineup-confirmed pregame, the population every MAIN/JIG rate in this checkpoint is measured against. 1,628 adds batters who appeared but were not confirmed pregame.

MLB boxscore reconciliation agreed with stored labels on all 16,782 appeared rows, and the reconciled full-season HR total across covered games was 1,628 (matching the appeared population above). Thirty spot checks passed on team identity, pregame timing, and outcome. Of the 1,735 home runs hit in covered games, 1,713 (98.7%) were hit by a batter present on the engine's board.

## Source discovery

The first pass at this audit relied on `mlb_hr_engine_v4/tracking/pick_tracker.csv`, which covers only 14 dates and carries no JIG, role, or per-stat pregame snapshot. It returned insufficient data for nearly every signal and was abandoned.

The audit that produced this checkpoint used Supabase `batter_stat_history` instead: 423,280 immutable pregame snapshots with 130 payload fields per row. That table is the authoritative historical source for this kind of validation going forward, and it was never queried by the earlier attempt. Durable architecture note: any future outcome audit should start there, not with the pick tracker.

## MAIN findings

Observed HR rate 10.95% against a mean predicted 11.17% on the 13,319-row bettable population. AUC 0.6001, 95% CI [0.5842, 0.6161], stable across three chronological blocks (DEV/VAL/HOLD), with the six display tiers monotonic in every block.

Two problems sit inside MAIN rather than around it:

- Calibration slope is 0.686 (1.0 would be honest). Below roughly 7% predicted probability the model runs cold; above 17.5% it runs 4–5 percentage points hot; above 25% it runs about 14pp hot, on a thin n=86.
- Exact rank inside the top 40 carries little or no separation. Ranks 4–5 hit 11.9%, ranks 21–40 hit 15.6%, and rank 41+ drops to 9.98%. The useful object is the top-40 cohort, not the printed rank number.

MAIN remains useful as a broad cohort/filter. **MAIN calibration stays frozen; nothing here is a production calibration change,** and no calibration change may ship without separate operator authorization.

## JIG findings

Major research discovery: JIG adds statistically meaningful information beyond MAIN, and is not merely re-reading MAIN's probability.

- The top JIG quartile beat the bottom JIG quartile in all eight matched MAIN probability bands, with lift ranging from roughly +1.9pp to +7.1pp.
- Pooled coefficient +0.197 (p = 0.0002); untouched holdout coefficient +0.340 (p = 0.0001); holdout ΔAUC approximately +0.022.
- The tactical component (arsenal/pitch-damage inputs, not the Statcast inputs MAIN already consumes) replicated independently, which is what rules out JIG being a simple restatement of MAIN.

A research-only combined MAIN+JIG blend measured AUC moving from 0.6072 to 0.6262 on the holdout. That number is **RESEARCH ONLY / FORBIDDEN FOR PRODUCTION WITHOUT NEW DOCTRINE AND AUTHORIZATION.** No combined score was created. MAIN/JIG separation remains doctrine and was not touched.

## Role system findings

Roles show raw association with HR outcomes but little to no incremental value once MAIN is controlled for. EXPLOSIVE's raw HR rate is 15.8%, but its incremental coefficient after MAIN is roughly zero, with p-values from about 0.07 to 0.94. Within-tier role lift runs about 0.88 to 1.08, essentially noise.

The operator's specific question about PRIME: the top-ranked PRIME play hit 10.2%, while an average PRIME play hit 14.5%. Roles should be treated as context/archetype labels for now, not ranking authority or independent predictive confirmation.

## Market findings

The stored market data is thin and one-sided: 8,168 quotes, all from BetRivers, zero FanDuel, zero usable closing-line coverage. Mean market implied probability was 15.20% against an observed HR rate of 11.02%, a gap of +4.18pp. Betting every stored quote at one unit returned −26.81% ROI. No EV threshold tested from 0% to +30% was profitable in any validation window, and after controlling for `model_prob`, the EV% coefficient is −0.239 (p < 0.0001) — observed hit rate fell as prices lengthened.

This BetRivers-only sample does not support the hypothesis that progressively longer prices improve realized performance. It says nothing about FanDuel specifically, and it is not grounds to rewrite the project's longer-odds north star — that decision needs its own evidence and its own authorization. Current BetRivers-based EV/EDGE should not be treated as outcome-validated deployment authority from this dataset.

## Color / UI findings

Two display scales are inverted relative to their intended direction. K%: the "green" (good) bucket hit 7.4% (n=1,943) and the "red" (bad) bucket hit 12.9% (n=1,469) — Spearman ρ = +1.00 under the current bucket ordering, meaning the color is running backward. SQUP% shows the same inversion pattern. SQUP%'s interpretation carries a caveat: bat-tracking coverage exists on only about 59% of rows, and that covered population hit 12.5% against 8.8% for the uncovered population, so the inversion finding is subject to selection/coverage bias.

AVG, BABIP, LA, CENTER%, and LD% showed no useful HR ordering. Fourteen other tested color scales showed the expected monotonic ordering (Spearman ≈ −1.00).

## Threshold configuration drift

`config.FS_HEATMAP_THRESHOLDS` does not match the production frontend's cutoffs for at least five columns. This is a durable architecture issue — CONFIG / FRONTEND THRESHOLD DRIFT — flagged for a separate audit. This checkpoint does not fix it and does not decide which side is authoritative.

## Unpersisted systems

AEE, SIGNAL, `hvy_modifier`, and CLV cannot currently be validated historically because none of them is captured in point-in-time form. TM (true matchup score) is available only on 1,203 operator-leg snapshots, and its observed bands are non-monotonic (AVG 20.0%, ELITE 18.3%, STRONG 14.4%), so TM validation is limited and does not currently support treating its display bands as monotonic outcome quality.

## HVY / JIG discovery

`hvy_base` was found to be algebraically equivalent to JIG base × 100. It is not an independent signal. This is a future architecture/formula-review finding; HVY and JIG were not altered here.

## Counterfactual experiments

Each candidate was fitted on a DEV window only, then scored unchanged on an untouched HOLD block. None was implemented.

- **C4 — retire `hot_streak_factor`.** Best-supported candidate. Holdout AUC 0.6072 → 0.6092, ECE 1.52pp → 1.18pp, Brier and log loss both improved, direction replicated across all three chronological windows. Not authorized for production change.
- **C2 — shrink probabilities above 0.15.** Weakly supported; holdout ECE 1.52pp → 1.44pp, directionally consistent. Requires separate protected review.
- **C6 — retire `jigScore_shadow`.** Candidate for retirement. Correlation 0.9997 with the live score; the shadow scored worse in every window and carries no distinct information.
- **C1 — global Platt refit.** Rejected: holdout ECE moved 1.52pp → 1.69pp, i.e. worse.
- **C3 — remove the batter K suppressor.** Rejected, does not replicate: validation p = 0.006 but development p = 0.43 and holdout p = 0.40.
- **C8 — EV thresholds.** No deployment rule supported; every tested threshold was negative on the holdout.

No tested candidate materially changed which players reach the top of the board. The available upside identified by this audit is more honest probabilities, more honest color semantics, and less redundant or unsupported decision information — not materially better player selection.

## Doctrine / governance interpretation

No doctrine was modified in this task. This checkpoint preserves: MAIN/JIG separation; the HVY display-only boundary; MAIN rank = model_prob; market data not feeding MAIN; MAIN calibration frozen; parlays retired; operator authorization required for any formula change.

Every finding above is an **OBSERVED RESEARCH FINDING**, not an **APPROVED PRODUCTION CHANGE**. Stage 1 approved none.

## Persistence recommendation (future work only)

To make the four currently-untestable systems auditable, future immutable pregame snapshots should capture point-in-time values for: Arsenal Edge / AEE, SIGNAL/support, `hvy_modifier`, TM, CLV-relevant quote timestamps and prices, role labels/criteria state, and production color-bucket assignment where useful. Nothing here implements that persistence; it is a Stage 2 candidate.

## Files touched by this checkpoint

- This file (new)
- `wiki/log.md` (new dated entry, see below)

No runtime, frontend, API, config, pipeline, formula, or threshold file was touched. No commit, push, or deploy occurred.
