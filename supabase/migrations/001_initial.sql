-- MLB HR Engine — Supabase schema
-- Paste into Supabase Dashboard → SQL Editor → Run

-- ── Tables ────────────────────────────────────────────────────────────────────

-- Full pipeline output cached per date (JSON blob)
create table if not exists pipeline_runs (
  date     date  primary key,
  payload  jsonb not null,
  ran_at   timestamptz default now()
);

-- Invite codes you generate manually (e.g. 'FRIEND1', 'LAUNCH2')
create table if not exists beta_invites (
  code        text primary key,
  note        text,
  used_by     uuid references auth.users(id),
  used_at     timestamptz,
  created_at  timestamptz default now()
);

-- Users who have redeemed a code
create table if not exists beta_users (
  user_id   uuid primary key references auth.users(id),
  added_at  timestamptz default now()
);

-- ── Row-level security ────────────────────────────────────────────────────────
-- The FastAPI backend uses the service-role key which bypasses RLS.
-- These policies protect direct anon/authenticated client access.

alter table pipeline_runs  enable row level security;
alter table beta_invites   enable row level security;
alter table beta_users     enable row level security;

-- Beta users can read picks
create policy "beta_users_read_picks" on pipeline_runs
  for select to authenticated
  using (exists (select 1 from beta_users where user_id = auth.uid()));

-- Users can read their own beta status
create policy "users_see_own_beta_row" on beta_users
  for select to authenticated
  using (user_id = auth.uid());

-- ── Seed: generate your first invite codes ────────────────────────────────────
-- Edit and run this block whenever you want to add more codes:
--
-- insert into beta_invites (code, note) values
--   ('FRIEND1',  'John'),
--   ('FRIEND2',  'Sarah'),
--   ('LAUNCH3',  'Discord drop');
