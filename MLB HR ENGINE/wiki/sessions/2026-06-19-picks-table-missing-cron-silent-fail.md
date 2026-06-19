# Session: picks table missing — cron.py silent insert failure

**Date:** 2026-06-19
**Agent:** Claude Code
**Room:** RUNTIME & STABILITY COMMAND (08)
**Risk level:** MEDIUM (schema creation + error surfacing, no pipeline logic touched)

## Problem

`insert_picks()` in `api/cache.py` silently failed on every cron run since
at least Jun 13. The `picks` table in Supabase was empty for Jun 13–18
despite the pipeline running and `pipeline_runs` writing successfully.

Exception was swallowed: `except Exception as e: print("[cron] picks table write failed (non-fatal): {e}")`.

## Root Cause (A)

**`picks` table never existed in Supabase.**

`supabase/migrations/001_initial.sql` only creates `pipeline_runs`,
`beta_invites`, `beta_users`. No `picks` table was defined.

supabase-py v2 (version `>=2.4.0` per requirements-api.txt) raises
`PostgrestAPIError` on `.execute()` failure. The error would have been:
```
relation "public"."picks" does not exist
```
This was printed to stdout and silently continued. GitHub Actions showed
a green run; picks never wrote.

## Fixes Applied

### B — Error surfacing (cron.py)

`mlb_hr_engine_v4/api/cron.py`:
- Added `import logging`, `import traceback`, `logging.basicConfig(...)`,
  `logger = logging.getLogger(__name__)`
- Replaced bare `print(f"[cron] picks table write failed (non-fatal): {e}")` with:
  - `logger.error(..., exc_info=True)` — full traceback in log record
  - `print(..., file=sys.stderr)` — surfaces as visible error in GitHub Actions
  - `traceback.print_exc(file=sys.stderr)` — full stack to stderr

A failed picks insert now writes to stderr and shows exc_info. It remains
non-fatal (cron continues), but it is NEVER silent.

### C — Underlying fix

Created `supabase/migrations/002_picks_table.sql`:
- All columns matching `insert_picks()` payload in `api/cache.py`
- UNIQUE constraint `(date, player_id, source_tab)` for upsert dedup
- RLS enabled; beta_users can read; service-role key bypasses RLS

**Operator action required:** Run `002_picks_table.sql` in Supabase Dashboard
→ SQL Editor → Run. Then trigger a pipeline run to verify picks write.

### Lint doctrine

Created `wiki/doctrine/bare-except-persistence-lint-rule.md` — standing
rule: bare except on persistence paths = HIGH risk. Documents all 3
confirmed instances:
1. api/main.py cloud-capture
2. app.py ×4 Streamlit writes
3. api/cron.py insert_picks (this session)

## Scope Note

This fix captures ENGINE-QUALIFIED picks from the cron pipeline. It does
**not** create deployed-pick tracking. The `fd_deployed` schema gap and
Ticket/Data Capture build are separate work — this fix should not be mistaken
for solving the calibration capture problem.

## Files Changed

| File | Change |
|------|--------|
| `supabase/migrations/002_picks_table.sql` | CREATED — picks table DDL |
| `mlb_hr_engine_v4/api/cron.py` | MODIFIED — error surfacing |
| `MLB HR ENGINE/wiki/doctrine/bare-except-persistence-lint-rule.md` | CREATED |
| `MLB HR ENGINE/wiki/architecture/supabase-schema.md` | UPDATED — picks table schema documented |
| `MLB HR ENGINE/wiki/log.md` | UPDATED |

## Verify Steps

1. Run `supabase/migrations/002_picks_table.sql` in Supabase SQL Editor
2. Trigger pipeline: `POST /api/pipeline/run` with `X-Cron-Secret` header
3. Check Supabase `picks` table — expect rows for today's date
4. Check cron log output — picks insert should say `N rows upserted`
5. If insert fails again: check stderr/logs for full traceback (now visible)

## Cross-references

- `wiki/doctrine/bare-except-persistence-lint-rule.md`
- `wiki/architecture/supabase-schema.md`
- `supabase/migrations/002_picks_table.sql`
- `mlb_hr_engine_v4/api/cache.py` — `insert_picks()` implementation
