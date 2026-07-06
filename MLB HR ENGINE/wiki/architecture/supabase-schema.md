# Supabase Schema

## Summary

Supabase serves as the service layer for the MLB HR Engine's FastAPI surface. It provides JWT auth (gating read endpoints), storage for pick tracking and CLV data, and the database backing the API service. The Streamlit dashboard does not connect to Supabase directly — Supabase is a FastAPI/production concern. This page tracks known tables and schema elements; Claude Code should populate via Supabase CLI audit.

## Key Points

### Connection Pattern
- FastAPI service (`api/main.py`, `api/auth.py`) connects to Supabase using `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`.
- The pipeline trigger endpoint is gated by `X-Cron-Secret` header (separate from Supabase auth).
- Streamlit dashboard does NOT connect to Supabase.

### JWT Validation (ES256/JWKS — updated 2026-06-26)

Supabase issues ES256 JWTs signed with a per-project EC private key.
- `api/auth.py` fetches JWKS from `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`
- Key lookup by `kid` from JWT header; cache with force-refresh on cache miss (key rotation resilient)
- Algorithm hard-enforced to ES256 only — HS256 rejected
- `SUPABASE_JWT_SECRET` env var is retained in the environment but is **no longer used for decode**

**Auth gating functions:**
- `require_auth` — validates JWT; gates write endpoints (minimum auth)
- `require_beta` — validates JWT + checks `beta_users` table membership; gates beta-only endpoints

`user_id` from the validated JWT is stamped on all write paths (`add_leg`, `complete_ticket`).

### Known Tables

| Table | Purpose | Migration | Notes |
|-------|---------|-----------|-------|
| `pipeline_runs` | Full JSON payload per date | `001_initial.sql` | `date` PK, `payload` jsonb |
| `beta_invites` | Manual invite codes | `001_initial.sql` | `code` PK |
| `beta_users` | Redeemed-code users | `001_initial.sql` | `user_id` PK |
| `picks` | Per-batter qualified picks from cron | `002_picks_table.sql` | UNIQUE `(date, player_id, source_tab)`; written by `insert_picks()` in `api/cache.py` |
| `tickets` | User-created bet slips (legs collection) | `001_initial.sql` + `004_tickets_user_id.sql` | `id` PK (uuid), `user_id` FK, `stake` numeric, `created_at` |
| `legs` | Individual legs within a ticket | `005_legs_calibration.sql` + `006_add_legs_signal_snapshot.sql` | `id` PK, `ticket_id` FK, `player_id`, `model_prob` (decimal — calibration key), `board`, calibration fields, `signal_snapshot` jsonb (see below) |

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

**Scope note:** `picks` captures engine-qualified picks — NOT deployed/fd_deployed state. Ticket/Data Capture and `fd_deployed` column are separate work.

### `tickets` Table Columns

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `user_id` | uuid NOT NULL | FK to auth.users — per-user ownership (added migration 004) |
| `stake` | numeric | Operator-entered stake amount; written by `complete_ticket` |
| `created_at` | timestamptz | |

### `legs` Table Columns (calibration-ready — migration 005)

| Column | Type | Notes |
|--------|------|-------|
| `id` | bigserial PK | |
| `ticket_id` | uuid NOT NULL FK | Parent ticket |
| `player_id` | text NOT NULL | `row.id` from API slate — calibration key |
| `team` | text | |
| `pitcher` | text | Opponent starter at leg-add time |
| `leg_date` | date | Mirrors ticket's slate date (NOT server UTC) |
| `model_prob` | numeric NOT NULL | Decimal (e.g. 0.187) — NOT ×100; calibration key |
| `board` | text | `'main'` or `'jig'` — source board identity |
| `hr_result` | smallint | NULL until settled; 0 = miss, 1 = hit |
| `settlement_status` | text | DEFAULT `'pending'`; values: `'pending'`, `'settled'`, `'void'` |
| `settled_at` | timestamptz | NULL until settled |
| `market_odds_american` | numeric | NULL — no market source on leg-add path yet |
| `market_prob` | numeric | NULL — same; stored for future market sourcing |
| `signal_snapshot` | jsonb | Migration 006 — pick-time signal state displayed on the adding surface (snapshot_version 1, all fields nullable). NULL for legs added without a snapshot (old callers). See roadmap/strategy-section-spec.md §5. |

**Calibration doctrine:** `player_id` + `model_prob` + `hr_result` are the calibration triad. `market_odds_american` / `market_prob` are NULL at write time. Do NOT compute calibration stats until settlement data accumulates (operator threshold: n≥200 settled picks).

**Leg payload integrity rule:** `model_prob` is ALWAYS a decimal from `row.model_prob` (API field). NEVER `row.hrprob × 100`, NEVER `jigScore`, NEVER `hrpa`. Enforced in `window.__hrSlip.buildLegPayload()`. The `signal_snapshot` never substitutes for or alters `model_prob` — it is a display record only.

**Snapshot capture (Phase S1-a, 2026-07-06):** `POST /api/tickets/leg` accepts an optional `signal_snapshot` JSON object (422 if not an object or >16KB). Absent snapshot → NULL, never an error. Populating surfaces: `full-slate` (both add paths), `aei` (AeeCard), `strategy-rail`. Each surface records only what it displays; alignment rule and H2H threshold are canonical per strategy-section-spec operator decisions.

### Environment Variables Required
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_SERVICE_KEY` — service role key (server-side only, never expose)
- `SUPABASE_JWT_SECRET` — for JWT validation on read endpoints

**Note:** Full schema requires Supabase CLI audit (`supabase db inspect` or equivalent). This stub reflects known architectural role from doctrine.

## Cross-References

- [Pipeline Data Flow](pipeline-data-flow.md)
- [Cache Ownership Map](cache-ownership-map.md)
