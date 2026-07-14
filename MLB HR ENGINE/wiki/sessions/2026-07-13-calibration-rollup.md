# Live Calibration Rollup — 2026-07-13

Status: ANALYSIS SHIPPED / NO RETUNE AUTHORIZED

## Analysis surface

Commit `11be08a` added `mlb_hr_engine_v4/scripts/analysis/analyze_live_calibration.py`. The script is report-only and buckets frozen `model_prob` values by Full Slate tier bands. It does not change scoring, thresholds, calibration parameters, or API payloads.

The settlement gap proved minor because the Supabase legs lane never imported `pnl.py` and remained operational. Only one leg required settlement. CLV reconciliation matched 45 rows, covering every row with captured CLV in the audited window.

## `pick_tracker.csv` calibration result

Sample: 3,828 settled rows with odds, bucketed using Full Slate tier bands.

| Tier | Predicted | Actual | Actual minus predicted |
|---|---:|---:|---:|
| APEX | 22.2% | 20.0% | -2.2 pp |
| ELITE | 17.6% | 15.0% | -2.6 pp |
| EDGE | 12.9% | 13.4% | +0.6 pp |
| SIGNAL | 8.7% | 10.9% | +2.2 pp |
| WATCH | 5.6% | 7.3% | +1.7 pp |
| COLD | 3.0% | 7.2% | +4.2 pp |

## Verdict

The flagship claim holds: APEX produced approximately a 20% observed HR rate. EDGE was nearly calibrated. Lower bands under-predicted observed HR rate, although the sample is selection-biased because `pick_tracker.csv` contains players with available odds rather than the complete slate population.

No retune was approved. The top-tier samples remain thin (APEX `n=55`; ELITE `n=127`), both below the `n < 200` stability rule, and the sample is stale May-era data. The correct next calibration decision point is the same tier bucketing after approximately three to four weeks of fresh post-break capture.

The input CSVs, results files, and text output remain gitignored by design. Only the reusable analysis script was committed.
