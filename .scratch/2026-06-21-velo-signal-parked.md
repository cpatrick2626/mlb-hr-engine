# Velo-Decline Signal: Diagnosed, Non-Production, Parked

**Date:** 2026-06-21
**Status:** CLOSED / PARKED — not urgent, not a production bug
**Action required:** None. Reviving velo-decline in live scoring is optional net-new work.

---

## Symptom

Live API log: `[arsenal] stats endpoint: 687 pitchers loaded for year=2026, fastball avg_speed: 0/687 pitchers`. Velocity null for all 687 pitchers.

## Root cause

NOT a fetch failure (CSV parsed fine — usage/ba/slg/whiff came through for all 687). NOT a key rename.

Direct fetch of Savant `pitch-arsenal-stats?year=2026&type=pitcher&csv=true` header confirmed: endpoint returns ONLY outcome metrics — `pitch_type, pitch_usage, pa, ba, slg, woba, whiff_percent, k_percent, put_away, est_ba/slg/woba, hard_hit_percent`. **No velocity column under any name.** Savant removed velocity from this endpoint entirely.

Adding a name to the `_f("mph") or _f("avg_speed") or ...` chain at `arsenal.py:231` will NOT work.

## What `pitcher_velo_decline_factor()` needs (arsenal.py:386-392)

Two seasons of per-pitch-type `avg_speed`: `arsenal_curr` and `arsenal_prior`. delta = prior_speed − curr_speed. Requires prior fastball PA ≥ 50 (line 383). Dies if either year's `avg_speed` is None. Fundamentally a two-season signal.

## Why the pitch_stats path doesn't complete the fix

`pitch_mix.py` reads `release_speed` from Statcast events and averages to `avg_speed` — this IS current-year velo, which is why the **frontend velo display works** (Detmers 94.2, Tolle 96.3). But it is current year only.

Prior-year (2025) velo has no source: the arsenal endpoint dropped velocity globally (not year-gated), so `year=2025` is also empty.

## Viable revival path (if wanted later)

**Path b:** Source prior-year velocity separately:
- 2025 Statcast pitch-by-pitch pull (high volume, new fetch), OR
- Wide-format `pitch-arsenals?year=2025&csv=true` fallback — `_parse_arsenal_csv()` at line 536 already reads `ff_avg_speed/si_avg_speed` from this format, IF the endpoint is still alive for 2025 (unverified).

Both require net-new work and are not currently implemented.

## CRITICAL: non-production scope

`pitcher_velo_decline_factor()` is **NOT wired into the live pipeline.** Confirmed: no call in `pipeline.py` or `engine/`. Referenced only in `scripts/analysis/analyze_2026_full.py:118` (offline analysis script). **Live picks do not use velo-decline and never did.** The 0/687 gap starves an analysis script, not production scoring. No pick is affected.

## What IS shipped and working

Frontend velo display fix (`full-slate-matrix.js`, `pitch_stats` fallback) — shipped, confirmed working. That was the real user-facing part.

## Carry-forward

Do not re-investigate this thinking it is a fire. If velo-decline is wanted as a live signal, it requires: (1) wiring into the pipeline, AND (2) sourcing prior-year velo via path b. Both are net-new feature work.

**Linked:** 2026-06-21-partial-signal-no-penalty.md, 2026-06-21-jig-saturation.md
