# Live Game State + Live-Aware Surfaces + In-App Alerts — program plan

Status: audited (Rule 13 Stage 1), not implemented. See full findings in `mlb_hr_engine_v4/scripts/analysis/live_state_alerts_program_audit_2026-08-13.md`. Nothing in this program has been built; this page records the plan for when the operator authorizes Stage 2.

## Boundary

Additive-only. Does not touch `/api/slate`'s pregame contract, `pipeline.py`, `api/cron.py`, `config.py`, or MAIN/JIG scoring/calibration. Reads today's schedule and per-`game_pk` live state from the free MLB Stats API; writes nothing to `pipeline_runs`. No new infra required for Phase 1 — no background worker, no new Supabase table.

## Key finding

`pipeline.py` already carries `game_pk` on every slate row (`pipeline.py:1417-1418`, `:1682-1683`, commented "additive, not yet keyed on") — the join key this program needs already exists. `clients/mlb_stats.get_live_game_status()` is a real but minimal live-poll helper (inning/outs only, via `/game/{game_pk}/linescore`), wired only into Streamlit (`app.py:3823-3899`), never called from `api/`. The full live bundle (score, bases, active pitcher/batter, HR events) needs `/game/{game_pk}/feed/live`, not yet fetched anywhere in the repo.

## Mechanism

Smallest viable live layer: on-demand fetch on client request, short in-process TTL cache (mirrors the existing `@st.cache_data(ttl=60)` Streamlit pattern), inside the current single Fly worker. No background poller needed for Phase 1 — that's deferred to whenever alerts must fire without a client open (push/PWA territory).

## Phase 1 (recommended scope)

One additive `GET /api/live-state/{game_pk}` endpoint, one minimal live-aware display (score/inning/outs/due-up batter), one in-app alert trigger (recommend "batter coming up" over "batter homered" first), client poll + the existing toast DOM pattern (`#hr-lb-fd-toast` / `#md-qp-fd-toast` in `frontend/assets/js/`) for delivery. Zero migrations, zero new infra.

## Phase 2+

Full animated diamond, second trigger ("slip batter homered"), a Supabase `notifications` table (needs a migration + manual run, same pattern as `community_posts` — see `wiki/architecture/community-bet-slips-phase-1.md`), then later (not scoped): push/PWA (service worker, push subscription storage) and multi-user alert subscriptions.

## Known gap to carry forward

`legs` rows don't store `game_pk` — deriving it means joining `leg.team` + `leg.leg_date` against the day's schedule, with doubleheaders needing the same disambiguation the pipeline already does (`api/main.py:1301-1315`). Not a blocker, just not a new problem to rediscover later.
