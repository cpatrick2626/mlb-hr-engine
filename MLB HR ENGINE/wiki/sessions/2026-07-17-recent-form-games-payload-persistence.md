# Recent-Form Game Logs Payload Persistence

## Status

Committed, deployed via manual `flyctl deploy`, and verified live — pipeline run #203, machine-restart-confirmed on 2026-07-17 (`recent_form_games` populated on 378/379 rows post-restart, log-less batter returns `[]`).

## Production behavior added

Each persisted batter profile now includes `recent_form_games`, a display-only list of up to five cached MLB game-log records shaped as `{date, hr, avg, slg, pa}`. `pipeline.py` snapshots the already-warm `_GAME_LOG_CACHE` without fetching or changing cache behavior, and `api/main.py::_build_slate_payload()` passes the list into MAIN slate rows. JIG rows inherit the same additive display field through their existing shallow-copy path.

The field is serialized into `pipeline_runs.payload` through both `all_by_model` and `slate_cache`, so it remains available after the in-process cache is cleared or a Fly machine restarts. Missing or malformed cache entries produce `[]`.

## Boundaries preserved

No MAIN probability, `base_hr_rate`, TM, JIG score, arsenal math, tier, threshold, odds/CLV, `/api/batter-detail`, or `clients/mlb_stats.py` cache behavior changed. No existing payload field was renamed or modified.

## Validation

Real MLB game-log cache reads populated five correctly shaped rows for Aaron Judge and Shohei Ohtani. A scoped payload comparison found all 101 pre-existing MAIN row keys and all 104 pre-existing JIG row keys byte-equivalent after excluding only the new key; HR probability, `model_prob`, `jigScore`, tier, TM, and projected TM were identical. JSON round-trip validation after clearing `_GAME_LOG_CACHE` retained the field in `all_by_model`, MAIN slate rows, and JIG slate rows. Python compilation, the existing batter-detail contract tests, and `git diff --check` passed.

Graphify was stale relative to HEAD, so live source files were used and the graph was not queried or updated.
