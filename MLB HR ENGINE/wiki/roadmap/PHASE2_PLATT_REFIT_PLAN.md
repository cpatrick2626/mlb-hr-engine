# Phase 2 Calibration — Platt Refit Plan (SCOPED, WAITING FOR REAL DATA)

## Status
SCOPED + twice-confirmed (independent audits in Fable and Codex, 2026-07-10). NOT shipped. VERDICT: wait for post-1.12 settled data before fitting. Ready to execute once enough fresh settled rows accumulate.

## Why Phase 2 exists
prob_scale=1.12 (live) fixed the AGGREGATE under-prediction (~21% → ~0% overall bias). But a flat scalar can't fix band-specific SHAPE. Residual miscalibration remains, and it's worse than "low band under-predicts": 1.12 traded low-band under-prediction for top-band OVER-prediction.

## The residual shape (MODELED at 1.12 — NOT observed; see caveat)
Both audits independently produced the same modeled-at-1.12 band table by inverting the recorded Platt, rescaling ×(1.12/0.88), re-applying current Platt. On 3,828 settled rows (May, 385 HRs, 10.06% base):
- 0-5%: pred 3.72% / actual 6.73% / +3.01pp / 1.81× (still badly under)
- 5-10%: pred 7.67% / actual 8.27% / +0.59pp
- 10-15%: pred 12.07% / actual 11.40% / -0.67pp
- 15-20%: pred 16.95% / actual 15.80% / -1.14pp
- 20-25%: pred 22.00% / actual 15.38% / -6.62pp (now OVER)
- 25%+: pred 26.90% / actual 19.23% / -7.66pp (now OVER)
- Overall bias ~0.00pp (confirms 1.12 fixed the aggregate).

## Current Platt (what gets refit)
- Form: calibrated = sigmoid(A * logit(p) + B). engine/calibration.py (~line 47-60, dispatch 107-150).
- Coefficients in config.py: Standard A=0.7805 B=-0.4611 (~line 184); Elite (barrel≥0.10) A=0.9200 B=-0.1000 (~line 232). Clamp (0.001, MAX_GAME_HR_PROB=0.29), round 4dp.
- Transform order: raw → ×0.82 (missing lineup) → prob_scale 1.12 (adaptive_weights.apply_prob_scale) → Platt(A,B by barrel tier) → clamp → recorded model_prob. PLATT IS AFTER PROB_SCALE — a refit must fit on POST-scale, PRE-Platt probs (invert current Platt, or fit on raw-through-1.12).

## Recommended fix (both audits agree): REFIT PLATT A+B, two-tier, CV-validated
- NOT isotonic (thin high bands → overfit; step discontinuities interact badly with MIN_QUAL_PROB threshold). NOT B-only (residual is a SLOPE problem not intercept — B-only leaves 0-5% at ~1.79×). NOT spline/per-band (adds engine code on a formula-contained surface, more governance burden).
- Fable fit CANDIDATE coefficients (SCOPING ESTIMATES, not ship values) on modeled pre-Platt-at-1.12 probs and ran the full-transform verification replay:
  - Two-tier full refit: standard A≈0.4126 B≈-1.2748; elite A≈0.4065 B≈-0.9886 → verification replay flattens EVERY band (0-5% ratio 1.00×, all within ±0.8pp, overall 0.00pp, Brier 0.08958 vs current 0.08992). Best result.
  - Pooled refit (A≈0.472 B≈-1.109) leaves 0-5% at 1.50× — tier-aware fitting is what fixes the low band.

## Barrel-tier handling
Standard n=3,514 (well-powered); Elite (barrel≥10%) n=314, 52 HRs (borderline-thin). Preserve two-tier structure. Do NOT independently refit elite as free 2-param unless CV proves stability — if unstable, shrink elite toward pooled (~50% blend) or use pooled-A + tier-specific-B. Avoid letting the thin 20%+ elite slice dominate.

## Thin-band handling
20-25% and 25%+ bands are thin (modeled n=117/52; observed-as-logged 46/9). Platt fits on individual outcomes, so thin bands don't get their own params (this is WHY Platt beats isotonic here). Use bands for EVALUATION only, with looser tolerance on thin bands.

## THE GATING CAVEAT — why we WAIT
All the above is MODELED, not OBSERVED. pick_tracker is May data logged under the OLD 0.88 scale; the 1.12 band table is a reconstruction (invert Platt + rescale), not real 1.12 outcomes. Compounding risk (Fable): pick_tracker is a RANGE-RESTRICTED / selected sample (only filtered picks), so slope (A) estimates on the truncated range are less stable — the fitted A dropping 0.78→0.41 partly reflects sample truncation, not just true miscalibration.
DECISION: do NOT refit on modeled/old-scale data. WAIT for genuine post-1.12 settled data (now accumulating daily via the auto-settlement workflow shipped 2026-07-09). Refit on REAL observations at the live config, with time-series CV. Stronger footing, avoids fitting the core probability transform on extrapolation.
Practical note (Codex): the original fitting harness scripts/analysis/analyze_calibration.py expects fb_pct_raw_data.csv, which is NOT in the current checkout — the harness can't be re-run as-is; its input must be reconstructed (or refit written fresh against settled data).

## Offline verification plan (when executing)
1. Collect pre-Platt probs under live 1.12 from REAL post-1.12 settled rows.
2. Fit candidates on time-series train folds (≥2 expanding): baseline / pooled A+B / standard-A+B-elite-frozen / pooled-A-tier-specific-B / isotonic as challenger only.
3. Evaluate on HELD-OUT dates (not fit rows).
4. Pass criteria: per-band |actual-pred| ≤1.5pp for n≥200 bands, ≤3pp thinner; overall |bias| ≤0.5pp; Brier ≤ current baseline (0.08992); A/B stable across CV folds (A spread <~0.15); rank ≈ monotone-preserved within tier; pick-volume sim at new probs lands near ~8-9/slate target OR MIN_EV_PCT re-tuned in the same change.

## Rollout (when executing)
- Coefficients in config.py → ship as config commit + flyctl deploy (NOT a volume edit — unlike prob_scale which is in learned_adjustments.json on the /data volume).
- COUPLING: refit lowers top-end probs → EV falls → fewer picks clear MIN_EV_PCT=14.0. Same coupling as commit 865f66d in reverse. MUST re-validate pick volume and adjust MIN_EV_PCT in the SAME change-set (or board starves).
- Keep AUTO_LEARN_FROZEN=True through and after — if auto-learn moves prob_scale off 1.12, the refit coefficients (fit conditional on 1.12 upstream) are invalidated.
- HIGH-risk formula/scoring surface: operator-authorized, Fable-tier, gated + regression + independent review before commit.

## Trigger to execute
When post-1.12 settled data reaches a sufficient sample (target: comparable to the current n≈3,800, or at minimum n≥200 per major band, per the calibration-change sample rule). Check accumulation periodically via the settled legs/pick_tracker data.
