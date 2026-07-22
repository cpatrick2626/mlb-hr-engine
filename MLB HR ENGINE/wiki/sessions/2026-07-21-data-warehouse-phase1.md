# Data Warehouse Phase 1

Status: implemented locally; migration application and live-row proof pending.

## Scope

- Added `public.batter_stat_history` as a write-separate Supabase store.
- Captures the complete unified pre-split `pipeline.py` batter payload once per pipeline run.
- Uses one `run_ts` per run and batch-upserts on `(slate_date, run_ts, batter_id, game_pk)`.
- A retry of the same batch is idempotent; a genuine same-date rerun creates a distinct snapshot set.
- `hr_outcome` is nullable and intentionally unwritten in Phase 1.

## Boundaries

- No scoring, `model_prob`, `jigScore`, TM, tier, rank, config, or payload-shape changes.
- No engine/scoring foreign keys and no warehouse reads from MAIN or JIG.
- Capture failures are warning-only in an asynchronous worker and cannot gate board generation.
- No outcome backfill and no query endpoint were added.

## Operational Step

Apply `supabase/migrations/009_batter_stat_history.sql` manually in the Supabase Dashboard SQL Editor before deploying the backend. A live pipeline run is then required for row-level proof.

## Validation Checkpoint

- Python compilation passed for `pipeline.py`, `api/cron.py`, and `api/main.py`.
- Static SQL contract check passed for required keys, JSONB, nullable outcome, RLS, and absence of engine-table foreign keys/query surfaces.
- Isolated capture test passed: two batter payloads were submitted in one upsert operation with nested weather and all source keys retained.
- Same-`run_ts` retry replaced the same keys; a new `run_ts` created a second snapshot set.
- Simulated Supabase and executor failures logged warnings and returned without raising.
- Real executor submission returned in under 1 ms while a simulated worker ran for 250 ms, confirming the caller does not wait.
- AST containment check confirmed all pre-existing pipeline semantics are unchanged after removing the additive warehouse helpers and call.
- Existing targeted tests passed under the repo-capable Python 3.12 environment (`17/17`).
- Live Supabase rows remain unverified until the dashboard migration is applied and the backend runs a slate.
