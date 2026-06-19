-- MLB HR Engine — picks table
-- Tracks per-batter qualified picks written by the cron pipeline.
-- Run in Supabase Dashboard → SQL Editor → Run

create table if not exists picks (
  id               bigserial    primary key,
  date             date         not null,
  player_id        text,
  player_name      text,
  team             text,
  opponent         text,
  pitcher          text,
  lineup_spot      integer,
  model_prob_pct   numeric(7,3),
  market_prob_pct  numeric(7,3),
  ev_pct           numeric(8,3),
  edge_pct         numeric(8,3),
  american_odds    numeric(8,2),
  bet_dollars      numeric(10,2),
  barrel_pct       numeric(6,3),
  xslg             numeric(6,3),
  park_factor      numeric(6,3),
  pitcher_factor   numeric(6,3),
  confidence_tier  text,
  qualified        boolean      not null default true,
  filter_reasons   jsonb        not null default '[]',
  source_tab       text         not null default 'cron',
  engine_version   text         not null default 'v4',
  created_at       timestamptz  default now(),

  -- NOTE: player_id is nullable; NULL != NULL in Postgres unique index,
  -- so rows without player_id will never deduplicate across runs.
  -- Enforce player_id presence upstream if dedup is required.
  unique (date, player_id, source_tab)
);

alter table picks enable row level security;

-- Service-role key (used by FastAPI + cron) bypasses RLS.
-- Beta users can read picks.
create policy "beta_users_read_picks_table" on picks
  for select to authenticated
  using (exists (select 1 from beta_users where user_id = auth.uid()));
