-- 011_user_layout_prefs.sql
-- Per-user column layout persistence (order + visibility) across all rooms.
-- Operator: run this in the Supabase dashboard SQL editor before enabling the endpoints.

create table if not exists public.user_layout_prefs (
  pref_id     uuid        primary key default gen_random_uuid(),
  user_id     uuid        not null references auth.users(id) on delete cascade,
  layout_key  text        not null,
  layout_data jsonb       not null,
  updated_at  timestamptz not null default now(),
  unique (user_id, layout_key)
);

alter table public.user_layout_prefs enable row level security;

-- Service-role client (used by the API) bypasses RLS automatically.
-- This policy is a safety net for any direct anon/user-role access.
create policy "Users can manage their own layout prefs"
  on public.user_layout_prefs
  for all
  using  (auth.uid() = user_id)
  with check (auth.uid() = user_id);
