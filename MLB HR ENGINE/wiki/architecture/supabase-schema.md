# Supabase Schema

## Summary

Supabase serves as the service layer for the MLB HR Engine's FastAPI surface. It provides JWT auth (gating read endpoints), storage for pick tracking and CLV data, and the database backing the API service. The Streamlit dashboard does not connect to Supabase directly — Supabase is a FastAPI/production concern. This page tracks known tables and schema elements; Claude Code should populate via Supabase CLI audit.

## Key Points

### Connection Pattern
- FastAPI service (`api/main.py`, `api/auth.py`) connects to Supabase using `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`.
- JWT validation uses `SUPABASE_JWT_SECRET`.
- The pipeline trigger endpoint is gated by `X-Cron-Secret` header (separate from Supabase auth).
- Streamlit dashboard does NOT connect to Supabase.

### Known Tables

| Table | Purpose | Migration | Notes |
|-------|---------|-----------|-------|
| `pipeline_runs` | Full JSON payload per date | `001_initial.sql` | `date` PK, `payload` jsonb |
| `beta_invites` | Manual invite codes | `001_initial.sql` | `code` PK |
| `beta_users` | Redeemed-code users | `001_initial.sql` | `user_id` PK |
| `picks` | Per-batter qualified picks from cron | `002_picks_table.sql` | UNIQUE `(date, player_id, source_tab)`; written by `insert_picks()` in `api/cache.py` |

### `picks` Table Columns

| Column | Type | Notes |
|--------|------|-------|
| `id` | bigserial PK | |
| `date` | date NOT NULL | |
| `player_id` | text | Nullable; NULL disables dedup on UNIQUE constraint |
| `player_name` | text | |
| `team` | text | |
| `opponent` | text | |
| `pitcher` | text | |
| `lineup_spot` | integer | |
| `model_prob_pct` | numeric(7,3) | model_prob × 100 |
| `market_prob_pct` | numeric(7,3) | market_no_vig_prob × 100 |
| `ev_pct` | numeric(8,3) | |
| `edge_pct` | numeric(8,3) | |
| `american_odds` | numeric(8,2) | best_american |
| `bet_dollars` | numeric(10,2) | |
| `barrel_pct` | numeric(6,3) | |
| `xslg` | numeric(6,3) | |
| `park_factor` | numeric(6,3) | |
| `pitcher_factor` | numeric(6,3) | |
| `confidence_tier` | text | |
| `qualified` | boolean NOT NULL | always true for cron picks |
| `filter_reasons` | jsonb NOT NULL | Python list serialized as JSON |
| `source_tab` | text NOT NULL | 'cron' for pipeline runs |
| `engine_version` | text NOT NULL | 'v4' |
| `created_at` | timestamptz | |

**Scope note:** `picks` captures engine-qualified picks — NOT deployed/fd_deployed state. Hermes capture and `fd_deployed` column are separate work.

### Environment Variables Required
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_SERVICE_KEY` — service role key (server-side only, never expose)
- `SUPABASE_JWT_SECRET` — for JWT validation on read endpoints

**Note:** Full schema requires Supabase CLI audit (`supabase db inspect` or equivalent). This stub reflects known architectural role from doctrine.

## Cross-References

- [Pipeline Data Flow](pipeline-data-flow.md)
- [Cache Ownership Map](cache-ownership-map.md)
