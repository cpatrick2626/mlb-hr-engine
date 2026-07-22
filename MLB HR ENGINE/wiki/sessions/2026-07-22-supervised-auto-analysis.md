# 2026-07-22 — Supervised Auto-Analysis Learning Loop

**Agent:** Claude Code  
**Status:** COMPLETE / PENDING MIGRATION APPLY (operator action required — 5 min)

---

## What Was Built

A read-only, fire-safe daily analysis loop that reads the modern warehouse
(`batter_stat_history.hr_outcome`) and settled legs (`legs` table), computes
calibration + discrimination metrics, and writes one row per run to a new
`learning_metrics` table. Never mutates scoring, prob_scale, calibration,
config, or `learned_adjustments.json`. Auto-learn remains frozen.

---

## Files

| File | Action | Notes |
|------|--------|-------|
| `mlb_hr_engine_v4/api/learning_analysis.py` | **created** (was skeleton — completed with --report flag + dotenv load) | Read-only on scoring; writes only to `learning_metrics` |
| `supabase/migrations/010_learning_metrics.sql` | **created** | DDL for `learning_metrics` table |
| `.github/workflows/settle_legs.yml` | **updated** | Added `Run supervised learning analysis` step (continue-on-error: true) after warehouse backfill |

---

## Table Schema (`learning_metrics`)

```sql
run_date               date PRIMARY KEY
run_ts                 timestamptz DEFAULT now()
settled_legs_count     integer NOT NULL
labeled_warehouse_rows integer NOT NULL
mean_predicted_prob    numeric(8,5)
actual_hr_rate         numeric(8,5)
brier_score            numeric(8,6)
ece                    numeric(8,6)
bucket_data            jsonb    -- [{bucket_low, bucket_high, count, mean_pred, actual_rate}]
discrimination_auc     numeric(8,5)   -- Mann-Whitney AUC
ready_for_refit_review boolean NOT NULL DEFAULT false
notes                  text
```

RLS enabled. No policies = service-role only. Write-separate from all scoring tables.

---

## First-Run Metrics (2026-07-22 dry-run, live data)

| Metric | Value |
|--------|-------|
| settled_legs_count | **338** |
| labeled_warehouse_rows | **126** |
| mean_predicted_prob | 0.19542 (19.5%) |
| actual_hr_rate | 0.19527 (19.5%) |
| brier_score | 0.159112 |
| ece | 0.056946 |
| discrimination_auc | **0.473** ← below 0.5 — see finding below |
| ready_for_refit_review | **false** (need 162 more settled legs → n=500) |

### Bucket Breakdown

| Band | n | mean_pred | actual_rate | diff |
|------|---|-----------|-------------|------|
| 0–5% | 0 | — | — | — |
| 5–10% | 0 | — | — | — |
| 10–15% | 39 | 13.3% | **20.5%** | +7.2pp (UNDER) |
| 15–20% | 139 | 17.4% | **22.3%** | +4.9pp (UNDER) |
| 20–25% | 131 | 21.9% | **13.0%** | −8.9pp (OVER) ← ranking inversion |
| 25%+ | 29 | 27.3% | **34.5%** | +7.2pp (UNDER) |

### Key Finding — Ranking Inversion Confirmed

AUC = 0.473 (below 0.5) confirms the discrimination issue flagged in the
context. The 20–25% band is over-predicting by 8.9pp while the 10–20% band
is under-predicting. Players ranked higher by the model are hitting HRs at a
**lower** rate than players ranked lower in the 20–25% range. This is
consistent with the calibration audit's "possible ranking-discrimination issue
in the 15–25% band."

Sample is n=338 — below the 500-leg threshold for ratified refit action.
No calibration change should be made until n≥500.

---

## Schedule / Trigger

Added as step 4 of `settle_legs.yml` (runs daily at 10:00 UTC after
settlement + warehouse backfill). `continue-on-error: true` — analysis
failure never breaks settlement. Idempotent per `run_date` (upsert).

---

## Operator Action Required

**Apply migration 010** via Supabase dashboard → SQL editor:

```
Paste contents of: supabase/migrations/010_learning_metrics.sql
```

Then run the first commit:
```bash
cd mlb_hr_engine_v4
python -m api.learning_analysis --commit
```

To view latest stored metrics later:
```bash
python -m api.learning_analysis --report
```

---

## Protection Confirmations

- prob_scale: **unchanged** (1.12)
- learned_adjustments.json: **not touched**
- auto_learn.py: **remains frozen** (AUTO_LEARN_FROZEN=True)
- dead CSV path: **not revived**
- config.py: **not modified**
- pipeline scoring / MAIN/JIG: **not modified**
- Sticky uncommitted files (index.html, a6cd8ef6…js, fa8fdb8f…js): **not touched**
- board/scoring byte-check: **clean** — only `api/learning_analysis.py` + migration + workflow changed

---

## Recommended Next Action

After applying migration 010 and running first commit:
- Monitor AUC weekly as settled legs grow toward n=500
- When `ready_for_refit_review` flips true, initiate Phase 2 Platt refit
  per `wiki/roadmap/PHASE2_PLATT_REFIT_PLAN.md` (separate human-ratified task)
