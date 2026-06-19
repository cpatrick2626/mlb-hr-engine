# Lint Rule: Bare except on persistence paths = HIGH RISK

## Rule

`except Exception as e: print(...)` on any Supabase write, file write, or
tracking insert is a **HIGH-risk pattern**. It must never be committed to
production persistence paths.

## Confirmed instances (all now fixed)

| # | File | Path | Root cause discovered |
|---|------|------|----------------------|
| 1 | `api/main.py` (cloud-capture) | Supabase insert in cloud-capture flow | Swallowed; surface unknown at time of fix |
| 2 | `app.py` ×4 | Streamlit session writes | Silent print; 4 separate write paths |
| 3 | `api/cron.py:62` | `insert_picks()` → `picks` table | Table didn't exist; 6 days of missing data (Jun 13–18) |

## Why this keeps happening

`try/except Exception as e: print(...)` looks like error handling but
provides no traceback, no log level, and no visibility in monitoring.
GitHub Actions treats cron `print()` as stdout — it does NOT surface as
a failure. The run shows green. Picks never write. Nobody notices until
a gap audit.

## Required pattern for persistence paths

```python
import logging
import traceback

logger = logging.getLogger(__name__)

try:
    result = supabase_write(...)
except Exception as e:
    logger.error("Write FAILED — data NOT persisted: %s", e, exc_info=True)
    raise   # or re-raise if the caller must know; at minimum log exc_info=True
```

`exc_info=True` captures the full traceback in the log record.
On GitHub Actions, `logging.error` writes to stderr, which surfaces as
a visible failure line (red in Actions UI).

## Schema gap corollary

Instance #3 was caused by `insert_picks()` targeting a table
(`picks`) that was never created in `supabase/migrations/`. Fix: always
verify the migration file exists before wiring a new Supabase write path.
Migration added: `supabase/migrations/002_picks_table.sql`.

## Scope note (instance #3)

`insert_picks()` captures ENGINE-QUALIFIED picks from the cron pipeline.
It does **not** capture deployed-state (fd_deployed, Ticket/Data Capture). The missing
Jun 13–18 data is engine picks data — not a substitute for calibration
capture, which requires the Ticket/Data Capture build and `fd_deployed` schema work
(separate initiative).

## Cross-references

- `wiki/architecture/supabase-schema.md` — picks table schema
- `wiki/architecture/pipeline-data-flow.md` — where picks enter the pipeline
- `supabase/migrations/002_picks_table.sql` — picks table DDL
