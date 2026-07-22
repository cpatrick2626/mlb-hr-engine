# Data Warehouse Phase 2 — HR Outcome Backfill

## Scope

Phase 2 labels `public.batter_stat_history.hr_outcome` after games become final.
The warehouse remains write-separate: MAIN and JIG do not read this table, and
the backfill never changes `raw_payload`, scoring, tiers, calibration, or slate
payloads.

## Resolution and trigger

`api/warehouse_backfill.py` reuses `api/settle_legs.py` MLB schedule and
boxscore primitives. A label is resolved only by exact `(batter_id, game_pk)`:
`1` when that player recorded at least one HR in that boxscore, otherwise `0`.
Non-final games and unavailable/empty boxscores remain NULL.

The daily `settle_legs.yml` workflow runs this backfill after legs settlement
for the same explicit date. The step is `continue-on-error`, so warehouse
failure cannot change the completed settlement result. Manual dry-run and
commit commands are:

```text
python -m api.warehouse_backfill --date YYYY-MM-DD
python -m api.warehouse_backfill --commit --date YYYY-MM-DD
```

## Write safety

Updates target one exact slate date, batter ID, and game PK and include
`hr_outcome IS NULL`. Re-runs therefore write zero rows after successful
labeling and cannot overwrite an existing label. Only `hr_outcome` is sent in
the update payload.
