-- Migration 005: leg calibration fields
--
-- "Store now, calibrate later." These columns make every leg row calibration-ready.
-- No settlement logic is built here — that is a separate job.
-- Idempotent: all ADD COLUMN IF NOT EXISTS; safe to re-run.

-- hr_result: NULL=pending, 1=hit, 0=miss, -1=void (machine/math calibration field)
ALTER TABLE legs ADD COLUMN IF NOT EXISTS hr_result          smallint;

-- settlement_status: human-readable lifecycle field (pending/won/lost/void)
ALTER TABLE legs ADD COLUMN IF NOT EXISTS settlement_status  text NOT NULL DEFAULT 'pending';

ALTER TABLE legs ADD COLUMN IF NOT EXISTS settled_at         timestamptz;

-- market fields frozen at tap time; NULL until a real market-odds source is wired
ALTER TABLE legs ADD COLUMN IF NOT EXISTS market_odds_american integer;
ALTER TABLE legs ADD COLUMN IF NOT EXISTS market_prob          numeric;

ALTER TABLE legs ADD COLUMN IF NOT EXISTS pitcher             text;

-- leg_date mirrors tickets.date (the slate date this pick was made against)
ALTER TABLE legs ADD COLUMN IF NOT EXISTS leg_date            date;
