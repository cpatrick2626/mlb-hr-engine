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
| `tickets` | User-created bet slips (legs collection) | `003_tickets_legs.sql` + `004_add_tickets_user_id.sql` | `ticket_id` PK (uuid), `user_id` FK, `date`, `board`, `status`, `stake` numeric, `created_at` |
| `legs` | Individual legs within a ticket | `003_tickets_legs.sql` + `005_add_leg_calibration_fields.sql` + `006_add_legs_signal_snapshot.sql` | `leg_id` PK (uuid), `ticket_id` FK, `player_id`, `model_prob` (decimal — calibration key), calibration fields, `signal_snapshot` jsonb (see below) |

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
| `ticket_id` | uuid PK | |
| `user_id` | uuid NOT NULL | FK to auth.users — per-user ownership (added migration 004) |
| `date` | date | Slate date; derived from the slate's `engine_generated_at` converted to ET, ET-clock fallback when absent (see `leg_date` note below) |
| `board` | text | `'MAIN'` or `'JIG'` — frontend board state at tap time |
| `status` | text | DEFAULT `'pending'`; `add_leg` opens tickets as `'building'` |
| `stake` | numeric | Operator-entered stake amount; written by `complete_ticket` |
| `created_at` | timestamptz | |

(Migration 003 also declares `ticket_type`, `num_legs`, `odds_american`, `sportsbook`, `fd_deployed`, `notes`, `settled_at`, `completed_at`.)

### `legs` Table Columns (calibration-ready — migration 005)

| Column | Type | Notes |
|--------|------|-------|
| `leg_id` | uuid PK | |
| `ticket_id` | uuid FK | Parent ticket (cascade delete) |
| `removed` | boolean | DEFAULT false — leg pulled from slip before completion |
| `player_id` | text | `row.id` from API slate — calibration key |
| `player_name` | text | |
| `team` | text | |
| `opponent` | text | |
| `pitcher` | text | Opponent starter at leg-add time |
| `leg_date` | date | Derived from `engine_generated_at` converted to ET (the slate the operator was viewing), falling back to the current ET clock only when `engine_generated_at` is absent/unparseable. Kept consistent with `tickets.date`. NOT server UTC. |
| `model_prob` | numeric | Decimal (e.g. 0.187) — NOT ×100; calibration key |
| `tier` | text | APEX/ELITE/EDGE/SIGNAL/WATCH/COLD at tap time (frozen) |
| `model_tier_rank` | int | Client-derived rank within tier at tap time (frozen) |
| `engine_generated_at` | timestamptz | Top-level `/api/slate` `generated_at` captured at tap time; source of `leg_date` derivation |
| `hr_result` | smallint | NULL until settled; 0 = miss, 1 = hit |
| `settlement_status` | text | DEFAULT `'pending'`; values: `'pending'`, `'settled'`, `'void'` |
| `settled_at` | timestamptz | NULL until settled |
| `market_odds_american` | numeric | NULL — no market source on leg-add path yet |
| `market_prob` | numeric | NULL — same; stored for future market sourcing |
| `signal_snapshot` | jsonb | Migration 006 — pick-time signal state displayed on the adding surface (snapshot_version 1, all fields nullable). NULL for legs added without a snapshot (old callers). See roadmap/strategy-section-spec.md §5. |

(Migration 003 also declares `deployed_at` timestamptz.)

Note: `board` lives on `tickets`, not `legs` — leg queries needing board identity join through the ticket.

**Settlement status convention (actual, as written by the settlement resolver):** `hr_result` ∈ {NULL, 0, 1} and `settlement_status` ∈ {`pending`, `settled`, `void`}; a void leg keeps `hr_result` NULL. Migration 005's inline COMMENTs (`-1=void`, `won/lost` lifecycle) are stale artifacts of the original design — no code writes those values; the schema itself needs no change.

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
