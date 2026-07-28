-- Migration 010: supervised learning-loop metrics table
--
-- WRITE-SEPARATE from engine/scoring tables. This table is written only by
-- api.learning_analysis and is never read by MAIN, JIG, pipeline, or any
-- scoring surface. Calibration changes are never applied automatically —
-- ready_for_refit_review is a FLAG for human decision only.

CREATE TABLE IF NOT EXISTS public.learning_metrics (
  run_date               date        PRIMARY KEY,
  run_ts                 timestamptz NOT NULL DEFAULT now(),
  settled_legs_count     integer     NOT NULL,
  labeled_warehouse_rows integer     NOT NULL,
  mean_predicted_prob    numeric(8,5),
  actual_hr_rate         numeric(8,5),
  brier_score            numeric(8,6),
  ece                    numeric(8,6),
  bucket_data            jsonb,
  discrimination_auc     numeric(8,5),
  ready_for_refit_review boolean     NOT NULL DEFAULT false,
  notes                  text
);

ALTER TABLE public.learning_metrics ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE public.learning_metrics IS
  'Per-run calibration and discrimination metrics. Write-separate from scoring. '
  'Never read by MAIN/JIG/pipeline. Human operator decides on any refit action.';

COMMENT ON COLUMN public.learning_metrics.settled_legs_count IS
  'Count of legs with settlement_status=settled and hr_result NOT NULL at run time.';

COMMENT ON COLUMN public.learning_metrics.labeled_warehouse_rows IS
  'Count of batter_stat_history rows with hr_outcome IN (0,1) at run time.';

COMMENT ON COLUMN public.learning_metrics.mean_predicted_prob IS
  'Mean model_prob (decimal) across settled legs used in this run.';

COMMENT ON COLUMN public.learning_metrics.actual_hr_rate IS
  'Observed HR rate (mean hr_result) across settled legs.';

COMMENT ON COLUMN public.learning_metrics.brier_score IS
  'Mean squared error of predicted probabilities vs binary outcomes.';

COMMENT ON COLUMN public.learning_metrics.ece IS
  'Expected Calibration Error — weighted mean absolute deviation per probability bin.';

COMMENT ON COLUMN public.learning_metrics.bucket_data IS
  'JSON array of per-probability-bucket stats: [{bucket_low, bucket_high, count, mean_pred, actual_rate}].';

COMMENT ON COLUMN public.learning_metrics.discrimination_auc IS
  'Rank-based AUC (Mann-Whitney U statistic). NULL when positives or negatives absent.';

COMMENT ON COLUMN public.learning_metrics.ready_for_refit_review IS
  'True when settled_legs_count >= REFIT_THRESHOLD (default 500). '
  'Human operator decides whether to initiate a ratified Platt/isotonic shape refit.';
