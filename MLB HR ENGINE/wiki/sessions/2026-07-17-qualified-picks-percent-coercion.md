# Qualified Picks Percent Coercion

## Status

Built and locally validated on 2026-07-17. Not committed, pushed, or deployed.

## Production behavior corrected

`api/cache.py::insert_picks()` now normalizes the persistence-boundary values for `ev_pct`, `edge_pct`, `barrel_pct`, and `xslg` to `float` or `None` before the Supabase `picks` upsert. Percent display strings retain percentage-point units, so `"4.5%"` is stored as `4.5`, consistent with existing numeric percent rows. xSLG retains its raw rate unit, such as `0.512`.

Missing markers such as `"--"` and `None` are stored as `NULL`. The source pipeline row and the display formatting in `clients/statcast.py` are unchanged.

## Boundaries preserved

No scoring, probability, JIG, config threshold, odds/CLV, API payload, Mode 2 guard, or fail-closed persistence behavior changed.

## Validation

A mocked Supabase upsert confirmed one synthetic qualified row persisted with numeric values, including `barrel_pct="4.5%"` becoming `4.5`. Separate cases confirmed `"--"` and `None` become `None`. Python compilation and `git diff --check` passed.
