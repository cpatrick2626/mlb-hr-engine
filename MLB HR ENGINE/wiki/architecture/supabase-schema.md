# Supabase Schema

## Summary

Supabase serves as the service layer for the MLB HR Engine's FastAPI surface. It provides JWT auth (gating read endpoints), storage for pick tracking and CLV data, and the database backing the API service. The Streamlit dashboard does not connect to Supabase directly — Supabase is a FastAPI/production concern. This page tracks known tables and schema elements; Claude Code should populate via Supabase CLI audit.

## Key Points

### Connection Pattern
- FastAPI service (`api/main.py`, `api/auth.py`) connects to Supabase using `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`.
- JWT validation uses `SUPABASE_JWT_SECRET`.
- The pipeline trigger endpoint is gated by `X-Cron-Secret` header (separate from Supabase auth).
- Streamlit dashboard does NOT connect to Supabase.

### Known Tables (requires audit to confirm)
| Table | Purpose | Notes |
|-------|---------|-------|
| picks | Pick tracking log | Persisted to Fly.io volume `/app/tracking` |
| clv | Closing line value log | CLV tracking per pick |
| (others TBD) | TBD | Requires Supabase CLI audit |

### Environment Variables Required
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_SERVICE_KEY` — service role key (server-side only, never expose)
- `SUPABASE_JWT_SECRET` — for JWT validation on read endpoints

**Note:** Full schema requires Supabase CLI audit (`supabase db inspect` or equivalent). This stub reflects known architectural role from doctrine.

## Cross-References

- [Pipeline Data Flow](pipeline-data-flow.md)
- [Cache Ownership Map](cache-ownership-map.md)
