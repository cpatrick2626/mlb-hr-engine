-- MLB HR Engine — Ticket/Data Capture schema (Phase 1a)
--
-- These tables are WRITE-SEPARATE from the engine. They are written only by
-- the capture layer. They READ engine output to snapshot it. They NEVER write
-- to MAIN prob, JIG score, tiers, ranking, pipeline, or scoring.
--
-- No FK to any engine table (picks, pipeline_runs, etc.). legs.player_id is a
-- plain text match, intentionally NOT a FK constraint — keeps capture-layer
-- history stable across player_id changes in engine tables.

-- ── tickets ──────────────────────────────────────────────────────────────────
-- One row per operator-submitted parlay / single. Ticket-grain store.
-- 'board' is derived from frontend board state at tap time ('MAIN' or 'JIG').
-- 'fd_deployed' is the deployment capture signal: TRUE = operator confirmed
--   they placed this exact parlay on FanDuel.

create table if not exists tickets (
  ticket_id      uuid         primary key default gen_random_uuid(),
  created_at     timestamptz  default now(),
  date           date,
  board          text,
  ticket_type    text,
  num_legs       int,
  stake          numeric,
  odds_american  int,
  sportsbook     text,
  status         text         default 'pending',
  fd_deployed    boolean      default false,
  notes          text,
  settled_at     timestamptz,
  completed_at   timestamptz
);

-- ── legs ─────────────────────────────────────────────────────────────────────
-- One row per player per ticket. FK cascades so deleting a ticket removes legs.
--
-- FROZEN ENGINE SNAPSHOT columns (model_prob, tier, model_tier_rank,
-- engine_generated_at): captured AS-IS at tap time. Later engine re-scoring
-- MUST NOT overwrite these. Immutability of the snapshot is the entire value
-- of the capture layer — calibration depends on predictions as-deployed.
--
--   model_prob          from /api/slate row.model_prob (4dp decimal)
--   tier                APEX/ELITE/EDGE/SIGNAL/WATCH/COLD at tap time
--   model_tier_rank     derived client-side from sorted position within tier
--                         at tap time; frozen here, never recomputed
--   engine_generated_at from TOP-LEVEL /api/slate generated_at (not a per-row
--                         field); captured once at tap time for the whole slate

create table if not exists legs (
  leg_id              uuid         primary key default gen_random_uuid(),
  ticket_id           uuid         references tickets(ticket_id) on delete cascade,
  removed             boolean      default false,
  player_name         text,
  player_id           text,
  team                text,
  opponent            text,
  model_prob          numeric,
  tier                text,
  model_tier_rank     int,
  engine_generated_at timestamptz,
  deployed_at         timestamptz
);

-- ── RLS ──────────────────────────────────────────────────────────────────────
-- Service-role key (FastAPI + cron) bypasses RLS.
-- No permissive read policy: capture data is operator-only. Direct anon /
-- authenticated client access is blocked by default until a policy is added.

alter table tickets enable row level security;
alter table legs    enable row level security;
