# Odds Cache Attachment Fix - 2026-09-11

Status: **FIXED LOCALLY / COMMITTED / NOT DEPLOYED**

## Failure Point

The Odds API request and player matcher are functional. Production GitHub Actions logs from September 10 showed live `batter_home_runs` pulls attaching 62/62, 51/51, 50/53, 33/34, and 34/34 available player lines.

The loss occurred in `api/cron.py`. When `should_pull_odds()` found a fresh cache, it returned a skip decision. `run()` then handled that skip like an out-of-window block and called `_write_odds_skip_sentinel()`, replacing the valid cached props with an empty list. The pipeline consequently received zero props, skipped attachment, and stored null odds, implied probability, edge, and EV fields.

## Fix

`_prepare_odds_cache()` now separates three states:

- `PULL`: fetch odds normally.
- `REUSE`: preserve a fresh odds cache for pipeline attachment.
- `SKIP`: write the empty sentinel only when the schedule window or missing schedule should block an Odds API call.

No market key, request route, matching rule, API payload field, probability formula, MAIN/JIG logic, HVY logic, calibration, ranking, or deployment configuration changed.

## Evidence

- Current request remains `baseball_mlb` plus event-level `/odds`, market `batter_home_runs`, region `us`, American format.
- One controlled September 11 event request returned HTTP 200, one `batter_home_runs` market, and 36 outcomes. The configured local key used one request (`500` to `499`). That event had no FanDuel outcomes at the check time, so no FanDuel row claim was made.
- Regression: a temporary cache containing a deterministic player-prop fixture remains unchanged after the fresh-cache guard path.
- `tests/test_odds_guard.py`: 9 passed.
- Python compile check and `git diff --check`: passed.
- Adjacent isolated suites: ticket analysis 7 passed, ticket history 5 passed, my tickets 6 passed. Community posts had one unrelated date-sensitive failure.

## Production Boundary

The change is not deployed. Production remains unchanged pending operator ratification.
