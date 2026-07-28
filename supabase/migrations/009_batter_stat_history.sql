-- Migration 009: complete per-batter slate-run history
--
-- WRITE-SEPARATE from engine/scoring tables. This table receives immutable
-- unified pre-split pipeline snapshots and is never read by MAIN or JIG.
-- No outcome backfill or query surface is part of Phase 1.

CREATE TABLE IF NOT EXISTS public.batter_stat_history (
  slate_date  date        NOT NULL,
  run_ts      timestamptz NOT NULL,
  batter_id   bigint      NOT NULL,
  game_pk     bigint      NOT NULL,
  raw_payload jsonb       NOT NULL,
  hr_outcome  smallint    NULL CHECK (hr_outcome IN (0, 1)),
  created_at  timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (slate_date, run_ts, batter_id, game_pk)
);

-- Service-role writes from the pipeline bypass RLS. With no policies, direct
-- anon/authenticated reads and writes remain closed like tickets/fd_events.
ALTER TABLE public.batter_stat_history ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE public.batter_stat_history IS
  'Write-separate immutable per-run batter snapshots. Never read by MAIN/JIG scoring.';

COMMENT ON COLUMN public.batter_stat_history.raw_payload IS
  'Complete unified pre-split pipeline batter payload, deeply JSON-normalized without removing fields.';

COMMENT ON COLUMN public.batter_stat_history.hr_outcome IS
  'Reserved for a separately authorized outcome-backfill phase; NULL in Phase 1.';
