# P0 `pnl.py` Smart-Quote Outage — 2026-07-13

Status: FIXED / DEPLOYED / VERIFIED ON FLY V96

## Incident

`mlb_hr_engine_v4/tracking/pnl.py` contained 210 Unicode smart-quote glyphs, including U+201C and U+201D, introduced by commit `71b36c5` on 2026-06-17 in and around `reconcile_clv_to_results`. Python could not parse the module and raised a hard `SyntaxError`.

For 25 days, `from tracking import pnl` failed. That disabled every import path depending on the module:

- the v4 CLI;
- `/api/ops/settle`;
- `full_slate_log` writes, whose failure was caught non-fatally so the pipeline continued without logging; and
- CLV reconciliation, which never ran.

The Supabase legs settlement lane was separate and did not import `pnl.py`, so it remained healthy; this distinction mattered during the later recovery audit.

## Fix

Commit `f817fe9` replaced all 210 smart-quote glyphs with ASCII equivalents. The repair was character-only: no logic, formulas, settlement behavior, or reconciliation rules changed.

Validation passed with `python -m py_compile mlb_hr_engine_v4/tracking/pnl.py` and a direct `from tracking import pnl` import. The deployed Fly v96 image was then verified importing the module successfully.

## Durable lesson

Curly quotes in a Python source file are a latent P0. Editor substitutions and pasted prose can break the parser even when the visible change looks typographic. Python-file review and validation must treat smart-quote introduction as a build-breaking condition, and critical import paths must fail loudly rather than disappear behind non-fatal logging guards.
