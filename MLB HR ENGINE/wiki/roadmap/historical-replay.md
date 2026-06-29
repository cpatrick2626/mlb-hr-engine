---
status: ROADMAP
shipped: false
created: 2026-06-29
---

> **STATUS: ROADMAP / NOT SHIPPED** — Backend data foundation is real; there is NO user-facing replay surface. A user cannot open a past day's slate today. This page is a plan, not documentation of a live feature.

# Historical Replay

## Summary

Historical Replay is a planned feature to let a user view past days' slates, review which predicted players actually homered, and see calibration over time. As of 2026-06-29 it is **NOT BUILT** as a user feature — but the underlying data infrastructure already exists, so shipping it is primarily a frontend + one-endpoint effort, not a from-scratch build.

---

## What EXISTS today (real, verified — file evidence)

- **Per-day slate snapshots (REAL):** `api/cache.py:43` `store_picks()` upserts one row per date into the `pipeline_runs` Supabase table (`on_conflict="date"`); yesterday's row is untouched when today runs — history accumulates. `api/main.py:780–803` `_build_payload()` stores the full ranked/all_by_model/auto_parlays/stats + React `slate_cache` shape per date. A `picks` table also stores one row per qualified pick per date.

- **Picks-by-date + run-list API (REAL):** `GET /api/picks/{date_str}` (`api/main.py:72`) returns ranked/all_players/stats/auto_parlays for a past date (gated by `require_beta`). `GET /api/runs` (`api/main.py:94`) lists the 30 most recent run dates + stats.

- **Outcome data (REAL, CLI only):** `backtest/outcomes.py` `get_game_results(date_str)` fetches real HR outcomes per batter from the MLB Stats API for any completed date.

- **Calibration reports (REAL, CLI only):** `backtest/calibration.py:50` `calibration_report()` — predicted vs actual HR% per bucket, Brier score, simulated P&L. Also `scripts/analysis/analyze_calibration.py`.

---

## What's MISSING to ship it (the actual remaining work)

- **Replay UI (MISSING):** No date picker, no historical-slate view in `frontend/`. The production frontend hardcodes today (`/api/slate?t=...`, no date param).

- **Full-slate-by-date endpoint (MISSING):** `/api/slate` is hardcoded to `date.today()` (`api/main.py:623`). The full React shape (`leaderboard_rows`, `jigScore`, `true_matchup_score`) is stored inside `slate_cache` per date but no endpoint surfaces it for a past date. Need `/api/slate/{date}` (or a date param).

- **Missed-HR review UI (MISSING):** No frontend joins predictions to outcomes; `legs.hr_result` is NULL until settled; no UI shows which predicted players actually homered.

- **Calibration surface (MISSING):** Calibration is terminal-output only; no API endpoint, no frontend renders it.

---

## Build path (when prioritized)

1. Add `/api/slate/{date}` surfacing the stored `slate_cache` React shape for a past date.
2. Add a date picker + historical-slate view to the frontend that hits it.
3. Join settled outcomes to show missed-HR review (which predicted players homered).
4. Optionally surface calibration via a new endpoint + frontend view.

The data layer (storage, outcomes, calibration math) already exists — this is mostly frontend + one endpoint.

---

## Status classification

**PARTIAL** — backend foundation real, no user-facing replay. NOT a live feature.

Revisit this classification when a replay UI ships; only then does this page graduate to DOCTRINE.

---

## Cross-References

- `wiki/architecture/supabase-schema.md` — `pipeline_runs` and `picks` tables
- `wiki/doctrine/clv-into-autolearn-phase3.md` — odds/CLV doctrine (deferred)
- `backtest/` tooling — `outcomes.py`, `calibration.py`
- `wiki/sessions/2026-06-19-calibration-coverage-N4-deferral.md` — calibration deferred until N threshold
