# 2026-07-22 — Supervised Learning Loop Build

**Agent:** Claude Code  
**Status:** COMPLETE / NOT COMMITTED — operator gates commit/push

---

## What Was Built

A supervised auto-analysis learning loop that runs daily after settlement, computes calibration and discrimination metrics from settled legs and the labeled warehouse, writes one row per run-date to a new `learning_metrics` table, and flags when sample size crosses the ratified refit threshold. Analysis only — no scoring surface touched.

---

## Files Changed

| File | Change |
|------|--------|
| `supabase/migrations/010_learning_metrics.sql` | NEW — `learning_metrics` table migration |
| `mlb_hr_engine_v4/api/learning_analysis.py` | NEW — analysis job module |
| `.github/workflows/settle_legs.yml` | MODIFIED — added `learning_analysis --commit` step (non-blocking, `continue-on-error`) |

---

## `learning_metrics` Table Schema

| Column | Type | Notes |
|--------|------|-------|
| `run_date` | date PK | One row per calendar day |
| `run_ts` | timestamptz | DEFAULT now() — when the job ran |
| `settled_legs_count` | integer | Count of legs with settlement_status=settled + hr_result IN (0,1) |
| `labeled_warehouse_rows` | integer | Count of batter_stat_history rows with hr_outcome IN (0,1) |
| `mean_predicted_prob` | numeric(8,5) | Mean model_prob (decimal) across settled legs |
| `actual_hr_rate` | numeric(8,5) | Observed HR rate (mean hr_result) |
| `brier_score` | numeric(8,6) | Mean squared error of predicted vs actual |
| `ece` | numeric(8,6) | Expected Calibration Error (10-bin equal-width) |
| `bucket_data` | jsonb | Array of per-band stats: [{bucket_low, bucket_high, count, mean_pred, actual_rate}] |
| `discrimination_auc` | numeric(8,5) | Rank-based AUC (Mann-Whitney U). NULL when no positives or negatives |
| `ready_for_refit_review` | boolean | True when settled_legs_count ≥ 500 |
| `notes` | text | `refit_threshold=500` |

RLS enabled. No read policies — service-role writes only, same pattern as `fd_events`.

---

## What the Job Computes

**Data sources (read-only):**
- `legs` table: `model_prob` (decimal) + `hr_result` (0/1) for all settled legs
- `batter_stat_history`: count of labeled rows (hr_outcome IN (0,1)) for the warehouse count metric

**Metrics:**
1. `settled_legs_count` — sample size gate (n<500 → ready_for_refit_review=false)
2. `labeled_warehouse_rows` — warehouse coverage count
3. `mean_predicted_prob` — aggregate model output level
4. `actual_hr_rate` — observed hit rate
5. `brier_score` — mean((model_prob − hr_result)²) — lower is better
6. `ece` — Expected Calibration Error (10-bin) — lower is better
7. `bucket_data` — six bands: 0-5%, 5-10%, 10-15%, 15-20%, 20-25%, 25%+ with count, mean_pred, actual_rate per band
8. `discrimination_auc` — Mann-Whitney U AUC, pure Python, no sklearn
9. `ready_for_refit_review` — boolean flag only; no auto-apply

**Idempotent:** upsert on `run_date` — re-running the same day overwrites the row cleanly.

---

## Schedule

Added as non-blocking step 3 to `settle_legs.yml`:
- Trigger: **daily 10:00 UTC** (06:00 ET EDT / 05:00 ET EST) — same cron as settlement
- Sequence: settlement → warehouse backfill → **learning analysis**
- `continue-on-error: true` — analysis failure logs and continues; cannot block settlement

`--commit` mode writes one row. Dry-run (no `--commit`) prints metrics without writing.

---

## First-Run Expected Values (2026-07-22)

Based on 328 settled legs (as of session start):

- `settled_legs_count`: ~328
- `labeled_warehouse_rows`: ~126
- `mean_predicted_prob`: ~0.14–0.18 (typical MAIN model range)
- `actual_hr_rate`: ~0.08–0.12 (typical MLB daily HR rate)
- `brier_score`: ~0.10–0.14 (reasonable for rare-event HR prediction)
- `ece`: ~0.05–0.12 (depends on calibration alignment)
- `discrimination_auc`: ~0.55–0.70 (expected; ranking signal exists but is modest)
- `ready_for_refit_review`: **FALSE** (328 < 500 threshold)
- `bucket_data`: most mass in 10-25% bands; 0-5% and 25%+ will have small n

The calibration audit (2026-07-10) identified a possible ranking-discrimination issue in the 15-25% band. The `bucket_data` column surfaces this per-band, and `discrimination_auc` tracks it in aggregate. Approximately 172 more settled legs needed to cross the 500-leg review threshold.

---

## Protected Surfaces — Confirmed Untouched

| Surface | Status |
|---------|--------|
| `prob_scale` | Unchanged (1.12, validated) |
| `learned_adjustments.json` | Not read, not written |
| `auto_learn.py` / AUTO_LEARN_FROZEN | Not touched — remains frozen |
| `config.py` calibration constants | Not read for scoring, not written |
| `pipeline.py` scoring | Not touched |
| `engine/` probability/EV/sizing | Not touched |
| Dead CSV auto-learn path | Not revived |
| `legs.hr_result` | Read-only |
| `batter_stat_history.hr_outcome` | Count-read-only |
| MAIN/JIG separation | Preserved |
| Board/scoring/slate payload | Byte-unchanged |

---

## How to View Latest Metrics

**Option A — Supabase dashboard SQL:**
```sql
SELECT
  run_date,
  settled_legs_count,
  labeled_warehouse_rows,
  mean_predicted_prob,
  actual_hr_rate,
  brier_score,
  ece,
  discrimination_auc,
  ready_for_refit_review
FROM learning_metrics
ORDER BY run_date DESC
LIMIT 5;
```

**Option B — CLI dry-run (prints without writing):**
```bash
cd mlb_hr_engine_v4
python -m api.learning_analysis
```

**Option C — Force a dated re-run:**
```bash
python -m api.learning_analysis --commit --date 2026-07-22
```

---

## Migration SQL for Dashboard

Apply via Supabase Dashboard → SQL Editor:

```sql
-- paste contents of supabase/migrations/010_learning_metrics.sql
```

Or via Supabase CLI if linked:
```bash
supabase db push
```

---

## When `ready_for_refit_review` Flips True

The flag fires when `settled_legs_count >= 500`. At that point:
- The job logs a `*** REFIT REVIEW FLAG ***` line in the Actions run
- The `learning_metrics` row carries `ready_for_refit_review=true`
- **No calibration change is made automatically**
- Human operator decides: inspect bucket_data, review brier/ECE trend, authorize or defer a Platt/isotonic shape refit
- The refit itself is a separate future authorized task (Phase 2 Platt refit plan in `wiki/roadmap/PHASE2_PLATT_REFIT_PLAN.md`)

---

## Commit / Push Recommendation

**DO NOT COMMIT / DO NOT PUSH without operator authorization.**

Files to stage when authorized:
```
supabase/migrations/010_learning_metrics.sql
mlb_hr_engine_v4/api/learning_analysis.py
.github/workflows/settle_legs.yml
MLB HR ENGINE/wiki/sessions/2026-07-22-supervised-learning-loop.md
MLB HR ENGINE/wiki/log.md
MLB HR ENGINE/wiki/index.md
```

Suggested commit message:
```
feat(learning-loop): supervised analysis job + learning_metrics table

Daily GitHub Actions step (after settlement) reads settled legs and
labeled warehouse rows, computes calibration/Brier/ECE/AUC/buckets,
writes one row per run_date to learning_metrics. Read-only on all
scoring surfaces. ready_for_refit_review flags at n>=500 settled legs
(currently 328 — flag=false). Auto-learn remains frozen.
```

---

## Next Action

1. **Apply migration 010** via Supabase Dashboard SQL Editor
2. **Commit + push** when authorized (workflow activates on next push to main)
3. **First live run**: next daily settlement cron (10:00 UTC) — or trigger manually via `workflow_dispatch`
4. **Monitor**: check Actions run log for `[learning-analysis]` lines; check `learning_metrics` table for first row
5. **At ~500 settled legs**: `ready_for_refit_review` flips true → initiate Phase 2 Platt refit review
