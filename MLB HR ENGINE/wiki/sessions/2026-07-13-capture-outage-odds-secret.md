# Pick-Capture Outage and Missing Odds Secret — 2026-07-13

Status: ROOT CAUSE FIXED / OBSERVABILITY SHIPPED / LIVE CAPTURE PROOF DUE 2026-07-16

## Summary

The month-long capture gap was not one outage. Two independent failures affected the Supabase and CSV lanes, and both were distinct from the `pnl.py` parser outage.

## Outage 1 — Supabase picks capture never ran successfully in production

The GitHub Actions workflow `.github/workflows/daily_pipeline.yml` had no `ODDS_API_KEY` repository secret.

The failure chain was deterministic:

1. no odds key produced an empty odds result;
2. every player failed the EV, edge, and market qualification filters;
3. the ranked/qualified collection was empty; and
4. `insert_picks([])` wrote zero rows.

There have therefore never been production rows with `source_tab='cron'`. The apparent May 31 boundary was a red herring: it was the final date of a one-time backfill, while `insert_picks` did not exist until commit `5abb2ba` on June 16.

The raw key was recovered from `mlb_hr_engine_v4/.env` and added to the repository's GitHub Actions secrets as `ODDS_API_KEY`. Workflow inspection confirmed the value now reaches the job as the masked value `***`; it had previously been blank.

Two junk repository secrets, `BOO` and `SUP`, remain. They are approximately one month old and likely came from an earlier misnamed-key attempt. Do not remove them until the July 16 live-capture checkpoint succeeds; investigate and clean them afterward.

## Outage 2 — the CSV lane cannot be authoritative on GitHub Actions

GitHub-hosted runners are ephemeral and do not mount Fly's persistent `/data` volume. Any tracking CSV written only on the runner disappears with the job. The cron path also does not call the `picks_log` or `pick_tracker` writers, while the separate `pnl.py` syntax failure disabled `full_slate_log` writes.

This lane is architecturally incapable of durable scheduled capture in its current form. The permanent direction is to make Supabase authoritative for pick logging and treat local/Fly CSVs as analysis or export surfaces rather than the primary scheduled ledger.

## Structural observability guard

Commits `e486eb1` and `4ff4038` shipped the first structural defense against another silent zero-capture run. `api/cron.py` now:

- fails at startup when `ODDS_API_KEY` is empty;
- treats a no-game slate as expected success;
- hard-fails with exit code 1 when games exist but zero odds lines are fetched;
- warns when games and odds exist but zero picks qualify; and
- emits a greppable `CAPTURE_SUMMARY` with games, odds lines, matches, qualified picks, and upserts.

The detailed implementation and branch validation live in [[2026-07-13-capture-health-observability]]. That note was written before its commit/deploy gate closed; `e486eb1` and `4ff4038` subsequently shipped.

The guard was checked against the July 13 no-game slate. It saw zero scheduled games and 173 stale odds records, correctly reported an expected empty slate, and exited 0 rather than false-alarming.

## Systemic lesson

Silent failure is a recurring failure class, not a single bug: swallowed write errors, missing secrets, ephemeral filesystems, and parser failures can all turn production capture into an unnoticed zero. Every capture or write path needs an explicit success count and a loud, actionable failure state.

## Open checkpoint — first game day, 2026-07-16

Run `gh workflow run daily_pipeline.yml`, then confirm all of the following:

- the workflow logs `odds props: N` with `N > 0`;
- odds matching reports `N/N matched` at a credible nonzero count;
- qualification reports a nonzero or explicitly explained `N qualified`;
- insertion reports `N upserted`;
- Supabase contains new rows with `source_tab='cron'`; and
- rerunning the workflow is idempotent and does not duplicate captured picks.

This is the definitive proof that the live calibration loop is capturing fresh production data. Until it passes, the secret and guard are shipped but end-to-end recovery remains unproven.
