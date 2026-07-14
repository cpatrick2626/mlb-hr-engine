# Capture Health Observability Guard — 2026-07-13

Status: BUILT / VALIDATED LOCALLY / AWAITING COMMIT, PUSH, AND FLY DEPLOY

## Production-path change

- `api/cron.py` now fails immediately when `ODDS_API_KEY` is missing or blank.
- The pipeline exposes private capture metadata for scheduled games, attempted players, fetched odds lines, odds matches, and qualified picks. Public `stats` and API payload shapes are unchanged.
- The cron treats a zero-game slate as an expected successful run, hard-fails when games exist but zero odds lines were fetched, and warns when games and odds exist but no picks qualify.
- Every completed or capture-failed pipeline run emits one greppable `CAPTURE_SUMMARY` line with games, odds lines, matches, qualified picks, and picks upserted.

## Validation

- July 13 live local cron run: exit code 0; `games=0`; logged `[capture] no games scheduled — empty slate expected`; emitted `CAPTURE_SUMMARY` with zero qualified and zero upserted picks.
- Branch simulation: no games = success; games plus zero odds = raised hard failure; games plus odds plus zero qualified = warning and success.
- Missing-key simulation raised immediately with `[capture] FATAL: ODDS_API_KEY not set`.
- `python -m py_compile api/cron.py pipeline.py` passed under Python 3.12.

## Boundaries

No scoring formulas, qualification filters, thresholds, odds matching, MAIN/JIG logic, or public API payload fields changed. A commit and push are required before the July 16 GitHub Actions run is protected because `daily_pipeline.yml` executes `python -m api.cron` from the checked-out repository. A Fly deploy can follow to keep the deployed backend image aligned, but it is not the mechanism that updates the GitHub cron runner.
