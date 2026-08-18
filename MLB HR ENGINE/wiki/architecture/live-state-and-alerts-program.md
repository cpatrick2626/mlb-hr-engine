# Live Game State + Live-Aware Surfaces + In-App Alerts — program record

Status: **Phase 1 built, merged, and deployed, 2026-08-13** (PR #5, merge commit `d1cf518`). **Phase 2a built 2026-08-13 and merged 2026-08-17** (PR #6, merge commit `be2a583`; code `a7df7b0`, wiki `dcec28d`). The live Fly OpenAPI currently exposes `/api/live-state/{game_pk}`. The August 18 synchronization did not have a non-empty production slate or a confirmed public frontend URL, so real-game banner rendering remains unverified. Phase 2b+ (diamond, homered trigger, notifications table) remain unbuilt. See `mlb_hr_engine_v4/scripts/analysis/live_state_alerts_program_audit_2026-08-13.md` for the original Phase 1 audit.

## Phase 2a — LIVE TARGETS banner real-data wiring

**What it replaces:** the `LiveTargets`/`TargetCard` banner (`frontend/assets/js/f2ee1fd2-*.js`, mounted from `frontend/assets/js/a6cd8ef6-*.js`) previously rendered `window.LIVE_TARGETS` (`frontend/assets/js/0ead2d7a-*.js:5-16`), a fully hardcoded mock array with no `game_pk`/`player_id` — free-text `name`/matchup/inning/score strings only. Its default ("mon") card state unconditionally rendered a `"LIVE"` badge and a fake inning string regardless of real game status.

**What was built:** new `frontend/assets/js/live-targets-live.js`, a self-mounting IIFE that:
- Resolves each `LIVE_TARGETS` entry to a real `game_pk` by case/accent-insensitive name matching against `window.LEADERBOARD_ROWS` / `LEADERBOARD_ROWS_JIG` (already fetched for the dashboard; each row carries `game_pk` per the existing `/api/slate` pass-through, `api/main.py:1460`, itself sourced from the Phase 1 `_match_game()` join). Zero or ambiguous (multiple distinct `game_pk`) name matches → unresolved; never guessed. No new backend matcher was written — this reuses the existing join transitively via the slate response.
- Polls `GET /api/live-state/{game_pk}` for each distinct resolved `game_pk` every 20s (`LT_POLL_INTERVAL_MS`), matching `LIVE_STATE_CACHE_TTL_SECONDS` and `live-alerts.js`'s `LA_POLL_INTERVAL_MS`. Also re-resolves on the existing `hrEngineDataLoaded` event (slate refresh).
- Publishes `window.LIVE_TARGETS_STATE` (per-target `{resolved, status, inningLabel, scoreLabel, gamePk}`) and dispatches `liveTargetsStateUpdated`, which `TargetCard` subscribes to via `React.useState`/`useEffect` (same event-driven pattern already used by `OddsPendingBanner`/`OddsQuotaBanner` in `a6cd8ef6-*.js`).

**Scope boundary (intentional):** only the `"mon"` (default) badge/inning path is now real-status-driven — `Live` → real `"LIVE"` + inning; `Final` → honest `"FINAL"`/"GAME OVER"; unresolved, `Preview`, or a fetch error → honest `"PREGAME"`, never a guessed live state. The `"hr"`/`"dead"` badges and the HR-count line (`t.hrs`) are **untouched** — those represent the batter-homered trigger, still a Phase 2b+ concern (see "Known gap to carry forward" below, now partially resolved for the banner but not for that trigger). The top-line score (`t.g`, now real when resolved, `"—"` otherwise) is wired for all card states since it's an objective fact, not a trigger claim.

**Validation performed:** the pre-merge throwaway Node harness (`.scratch/phase2a_live_targets_validation.mjs`, not committed) passed all six resolution, fallback, error, and name-normalization cases. Production checks confirmed the live Fly route and a successful API response, but the empty production slate could not exercise real-game banner rendering.

**Still requires a live-browser check:** confirm the banner renders the correct inning and score for a genuinely live game, and falls back to `PREGAME`/`FINAL` rather than stale or fabricated `LIVE` status. The August 18 production check could not exercise this because `/api/slate` returned a stale empty cache with zero rows and zero games.

**Protected-surface confirmation:** `/api/slate`, `pipeline.py`, `api/cron.py`, `config.py`, MAIN/JIG scoring/calibration, and the `/api/live-state` endpoint itself have zero diff hunks (verified via `git diff main --stat`). No backend file touched at all — this is a frontend-only change. No migration, no secret, no new infra.

**Repository status:** merged to `main` through PR #6 on 2026-08-17. No Fly deploy is required for the Phase 2a frontend-only change. Vercel deployment is expected from the merge-to-`main` workflow, but this synchronization did not independently verify the public frontend artifact.

## Phase 1 — what shipped

**Layer 1 (live state):** `clients/mlb_stats.py` gained `get_live_game_state(game_pk)` (+ `get_game_abstract_status`, `_live_person` helper) — a null-safe bundle of status/inning/outs/score/bases/current-pitcher/current-batter/on-deck, built from `/schedule?gamePk=` (status) + `/game/{game_pk}/linescore` (everything else), both free/unauthenticated. Never raises; any unresolved field comes back `None` rather than omitted.

`api/main.py` exposes it as `GET /api/live-state/{game_pk}` — public (no auth, same posture as `/api/batter-detail`), backed by an in-process TTL cache (`LIVE_STATE_CACHE_TTL_SECONDS = 20`, `_LIVE_STATE_CACHE` dict keyed by `game_pk`). No new worker, no migration. Route wraps the client call in its own try/except so it cannot 500 even if the client function's own null-safety were ever bypassed.

Contract:
```json
{
  "game_pk": 745123, "status": "Live", "inning": 6, "inning_half": "Top", "outs": 2,
  "score": {"home": 3, "away": 2},
  "bases": {"first": true, "second": false, "third": true},
  "current_pitcher": {"id": 123, "name": "..."},
  "current_batter": {"id": 456, "name": "..."},
  "on_deck": {"id": 789, "name": "..."},
  "fetched_at": "2026-08-13T23:45:10Z"
}
```
`recent_home_runs` (the audit's proposed field for a future "batter homered" trigger) was **not** built — out of Phase 1 scope, deferred to Phase 2 alongside that trigger.

**Layer 2 (display):** not built as a standalone UI in this pass — Phase 1 focused on proving the data + alert chain (Layers 1 and 3). The endpoint contract carries everything a minimal score/inning/outs/due-up-batter view needs; wiring that view into the board is the smallest remaining Phase 1 follow-up, not a new data requirement.

**Layer 3 (game_pk derivation + alert trigger):** `legs` still don't store `game_pk`. `api/ticket_history.py::_clean_leg` now derives it by reusing the *existing* `_match_game()` join (team + date, opponent-narrowed) that `/api/my-tickets` already used for `game_status`/`linescore` — no new disambiguation logic was written. `_TICKET_SELECT` and `_clean_leg` also now surface `player_id` (already a real column on `legs`, previously unselected). Both are additive fields on `/api/my-tickets`'s existing response.

**Doubleheader decision:** when a leg's team+date matches more than one game and `opponent` doesn't narrow it to exactly one, `_match_game()` returns `None` — so `game_pk` is `None` on that leg. The frontend watchlist (`frontend/assets/js/live-alerts.js`) skips any leg without both `game_pk` and `player_id`. Net effect: an unresolved doubleheader leg is silently never watched, never polled, never alerted on — no wrong-game alert is possible by construction, not by a runtime check.

**Alert trigger — "batter coming up":** new `frontend/assets/js/live-alerts.js`, a vanilla-JS (non-React) self-mounting IIFE loaded after `auth.js`. On sign-in, pulls `/api/my-tickets`, keeps pending legs with a resolved `game_pk`+`player_id` as the watchlist, then every 20s (`LA_POLL_INTERVAL_MS`, matched to the server TTL) polls `/api/live-state/{game_pk}` for each distinct watched game and checks whether the leg's `player_id` matches that game's `current_batter.id` or `on_deck.id`. First match fires one toast (reusing the existing bottom-center toast DOM pattern from `hr-lb-fd-toast`/`md-qp-fd-toast`) and marks the leg fired for the session (`firedLegIds` Set) so it never re-fires. The watchlist itself re-pulls every 120s (`LA_WATCHLIST_REFRESH_MS`) to pick up newly-submitted slips without a full reload. Every fetch failure, missing field, or empty watchlist is a silent no-op — never a thrown alert.

## Protected-surface confirmation

`/api/slate`, `pipeline.py`, `api/cron.py`, `config.py`, and MAIN/JIG scoring/calibration were not touched (verified via `git diff` — zero hunks in any of those files). No Supabase migration, no new secret. All backend changes are additive: one new client function pair, one new route, two new fields appended to an existing response shape.

## Validation performed (Cloud, mocked)

- `tests/test_mlb_stats_live_state.py` — `get_live_game_state`/`get_game_abstract_status`: live, non-live (Preview), missing-id-person, linescore-request-failure, and both-requests-failing cases. All return well-formed dicts; none raise.
- `tests/test_live_state_endpoint.py` — `/api/live-state/{game_pk}` contract shape, non-live nulls, client-exception-never-500, and TTL cache behavior (within-TTL dedup, post-TTL refetch, independent per-`game_pk` caching).
- `tests/test_live_state_game_pk_derivation.py` — single-game resolves; doubleheader-ambiguous (no opponent, or opponent matches both games) leaves `game_pk` null; opponent correctly disambiguates two unrelated same-day games; no-match case is null.
- Regression sweep (per-file, not full-suite per the repo's known cross-pollution issue): `test_ticket_history_contract.py`, `test_my_tickets.py`, and the rest of `tests/` — all green except two pre-existing failures (`test_pitcher_detail.py`, `test_community_posts.py`) confirmed to fail identically on `main` before this change (verified via `git stash`).

**Remaining validation gap:** the alert toast still needs observation against a real due-up batter in a live game. The endpoint is deployed; this is a live-game behavior check, not a deployment prerequisite.

## Deploy status

Phase 1 is merged and its API routes are present in the live Fly OpenAPI. Phase 2a is merged to `main`; its public frontend rendering has not been independently verified in a live game. The August 18 API check returned HTTP success but a stale empty slate, so row-level live behavior could not be validated.

## Original plan (Phase 1 scope, as authored pre-build)

### Boundary

Additive-only. Does not touch `/api/slate`'s pregame contract, `pipeline.py`, `api/cron.py`, `config.py`, or MAIN/JIG scoring/calibration. Reads today's schedule and per-`game_pk` live state from the free MLB Stats API; writes nothing to `pipeline_runs`. No new infra required for Phase 1 — no background worker, no new Supabase table.

### Key finding

`pipeline.py` already carries `game_pk` on every slate row (`pipeline.py:1417-1418`, `:1682-1683`, commented "additive, not yet keyed on") — the join key this program needs already exists. `clients/mlb_stats.get_live_game_status()` is a real but minimal live-poll helper (inning/outs only, via `/game/{game_pk}/linescore`), wired only into Streamlit (`app.py:3823-3899`), never called from `api/`. The full live bundle (score, bases, active pitcher/batter, HR events) needs `/game/{game_pk}/feed/live`, not yet fetched anywhere in the repo.

### Mechanism

Smallest viable live layer: on-demand fetch on client request, short in-process TTL cache (mirrors the existing `@st.cache_data(ttl=60)` Streamlit pattern), inside the current single Fly worker. No background poller needed for Phase 1 — that's deferred to whenever alerts must fire without a client open (push/PWA territory).

### Phase 1 (recommended scope)

One additive `GET /api/live-state/{game_pk}` endpoint, one minimal live-aware display (score/inning/outs/due-up batter), one in-app alert trigger (recommend "batter coming up" over "batter homered" first), client poll + the existing toast DOM pattern (`#hr-lb-fd-toast` / `#md-qp-fd-toast` in `frontend/assets/js/`) for delivery. Zero migrations, zero new infra.

### Phase 2+

Full animated diamond, second trigger ("slip batter homered"), a Supabase `notifications` table (needs a migration + manual run, same pattern as `community_posts` — see `wiki/architecture/community-bet-slips-phase-1.md`), then later (not scoped): push/PWA (service worker, push subscription storage) and multi-user alert subscriptions.

### Known gap to carry forward

`legs` rows still do not store `game_pk`. Phase 1 resolves it through the existing team + date join, narrowed by opponent. If a doubleheader remains ambiguous, `_match_game()` returns `None`; the alert client skips that leg. A wrong-game alert is therefore impossible by construction.

## Home-PC Graphify follow-up

Graphify is home-PC-only and gitignored. Run `graphify update mlb_hr_engine_v4` on the home PC because Phase 1 added `/api/live-state/{game_pk}` and `get_live_game_state()`. Do not attempt this refresh from the work laptop.
