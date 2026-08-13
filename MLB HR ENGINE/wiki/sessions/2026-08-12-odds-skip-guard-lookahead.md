---
date: 2026-08-12
agent: Claude Code
task: Odds skip-guard + selective lookahead fetching
commits: 3a06cd1 (skip-guard), 50d211d (lookahead)
---

## Summary

Two changes working together to reduce Odds API quota burn on the free 500 req/month plan.

---

## Change 1 — Odds skip-guard (`should_pull_odds()`)

**File:** `mlb_hr_engine_v4/api/cron.py`  
**Commit:** `3a06cd1`

Adds `should_pull_odds(target_date)` to `api/cron.py`. Returns `(bool, reason_str)`. Uses the free MLB Stats API (zero Odds API cost) to read game start times, then blocks the Odds API fetch when:

- Odds cache is still fresh (age ≤ 45 min, `_ODDS_CACHE_TTL_MINUTES`)
- Current UTC < first pitch − 4 h (`_PULL_WINDOW_H_BEFORE`)
- Current UTC ≥ last pitch + 3 h (`_PULL_WINDOW_H_AFTER`)
- No games scheduled / start times unavailable

When the guard blocks, `_write_odds_skip_sentinel()` writes a fresh-cache sentinel so `odds_api._load_cache()` short-circuits the real fetch and the pipeline continues in existing-odds (projected-slate) mode. The 6 AM run still builds the full MLB Stats board; it just skips Odds API.

Guard decision (`pull` / `skip` + reason string) is logged and stored in the pipeline payload as `odds_guard` for operator visibility.

**Cron schedule change:** Replaced 4 fixed daily cron triggers with 18 hourly gated triggers across 6 AM–midnight ET (10:00–03:00 UTC). Each trigger fires the pipeline; the guard decides whether to spend Odds API requests. GitHub Actions minutes are effectively free at this scale.

**Estimated quota:** ~1,600 → ~1,100 req/month (6 AM waste eliminated). Still over the 500/month free cap — the real quota firewall is fetch cadence, not window width. A live cadence reading against the deployed schedule is needed to confirm actual burn.

**Tests:** `mlb_hr_engine_v4/tests/test_odds_guard.py` — 7 unit tests pass (6 AM too-early skip, 3 PM pull, 8 AM day-game boundary pull, post-last-game skip, no-games skip, fresh-cache skip, zero odds_api calls confirmed).

---

## Change 2 — Per-game props lookahead (`PROPS_LOOKAHEAD_HOURS`)

**File:** `mlb_hr_engine_v4/clients/odds_api.py`, `mlb_hr_engine_v4/config.py`  
**Commit:** `50d211d`

When a fetch does happen, `odds_api.py` now filters the events list before calling `_get_event_props()` per game. Games are skipped if:

- `commence_time > now_utc + PROPS_LOOKAHEAD_HOURS` (default 6 h) — too far ahead
- `commence_time < now_utc − 3 h` — already past the post-game window

`PROPS_LOOKAHEAD_HOURS = 6` is set in `config.py`.

This cuts the number of per-game props requests fired per fetch cycle, but the total quota reduction depends on how many daily games are outside the window at fetch time. The skip-guard (Change 1) is the primary quota firewall; the lookahead is a secondary trim. Neither alone is sufficient to stay within 500/month under an 18-trigger-per-day schedule.

---

## Protected surfaces

- No model probability, EV, tier, ranking, or `pipeline.py` logic touched.
- No schema change.
- Guard result (`odds_guard`) is metadata — display-only, not scored.
