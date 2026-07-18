-- Migration 008: append-only FanDuel handoff events
--
-- WRITE-SEPARATE from engine/scoring tables. One row records that the
-- authenticated operator initiated a FanDuel handoff for a player; it is not
-- proof that a wager was placed. No engine table is referenced.

CREATE TABLE IF NOT EXISTS fd_events (
  event_id        uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid         REFERENCES auth.users(id),
  player_id       text,
  slate_date      date,
  occurred_at     timestamptz  DEFAULT now(),
  event_type      text         NOT NULL DEFAULT 'handoff_initiated'
                               CHECK (event_type = 'handoff_initiated'),
  source_surface  text,
  board           text,
  idempotency_key text,
  UNIQUE (user_id, idempotency_key)
);

-- FastAPI uses the service-role key and enforces JWT ownership. Keep direct
-- anon/authenticated table access closed, matching the migration 003 pattern.
ALTER TABLE fd_events ENABLE ROW LEVEL SECURITY;
