# Live Game State + Live-Aware Surfaces + In-App Alerts — Architecture Audit

**Date:** 2026-08-13
**Type:** Read-only architecture audit (Rule 13 Stage 1). No code changes.
**Repo/branch/HEAD:** `cpatrick2626/mlb-hr-engine`, branch `claude/mlb-hr-engine-cloud-audit-bsedt3`, HEAD `8ffc538` — 0 ahead / 0 behind `origin/main` at audit time (this branch currently equals `main`).
**Graphify:** `mlb_hr_engine_v4/graphify-out/` absent in this Cloud checkout (gitignored, home-PC tooling). Findings below are from direct source inspection, not graph queries.
**Authority files consulted:** `CLAUDE.md`, `AGENTS.md` (Rule 13 High-Risk Two-Stage, Rule 14 Protected Surface Declaration, GRAPHIFY WORKFLOW RULE, Mandatory Obsidian/Wiki Documentation Gate), `.claude/settings.json`.

---

## Executive summary

The engine's pregame architecture already carries one critical piece of scaffolding for this program: **every player row in `/api/slate` already includes `game_pk`**, explicitly commented in `pipeline.py` as *"MLB game_pk pass-through (display/identity only — additive, not yet keyed on)"* (`pipeline.py:1417-1418`, `:1682-1683`). This means the join key needed to correlate a pregame player row (or a ticket leg) to a specific live game already exists in the data model — it was anticipated, just never activated. That materially lowers the cost of Layer 1.

The MLB Stats API is free/unauthenticated (confirmed in `clients/mlb_stats.py`), and a **live-poll helper already exists** (`get_live_game_status`) — but it's minimal (inning/outs only, no score/bases/batter/pitcher/HR) and is wired only into Streamlit, not the API service. Building the full live layer is real but bounded work, not a rewrite.

The most important architectural finding: **the smallest viable live layer needs no new always-on infrastructure.** An on-demand, client-triggered fetch (mirroring the existing `@st.cache_data(ttl=60)` pattern already used for the Streamlit live badge) fits the current single-worker Fly process with `min_machines_running=1` and requires zero new workers, queues, or schedulers. A background poller only becomes necessary later, for alerts that must fire while the user's client isn't open — explicitly out of scope for Phase 1 per the operating assumptions.

---

## LAYER 1 — Live Game State

### Endpoints and fields (MLB Stats API, `https://statsapi.mlb.com/api/v1`, no key)

| Datum | Endpoint | Fields |
|---|---|---|
| Live score, inning, half, outs | `/game/{game_pk}/linescore` | `currentInning`, `inningState` ("Top"/"Middle"/"Bottom"/"End"), `outs`, plus (not currently parsed by the existing helper but present in the raw response) `teams.home.runs`/`teams.away.runs` for score |
| Base-runner occupancy | `/game/{game_pk}/linescore` (`offense.first`/`second`/`third` presence) — the richer `feed/live` response also carries this under `liveData.plays.currentPlay.matchup` and `linescore.offense` | Not currently fetched by the existing helper |
| Active (on-mound) pitcher | `/game/{game_pk}/linescore` → `defense.pitcher` (id/name), or `feed/live` → `liveData.linescore.defense.pitcher` | Not currently fetched |
| Current/due-up batter | `/game/{game_pk}/linescore` → `offense.batter` (current) / `offense.onDeck`, `offense.inHole` (due-up); `feed/live` gives the same plus at-bat-level detail via `liveData.plays.currentPlay.matchup.batter` | Not currently fetched |
| HR events as they happen | `/game/{game_pk}/feed/live` (the play-by-play feed) — walk `liveData.plays.allPlays`, filter `result.eventType == "home_run"` (or scan `liveData.plays.currentPlay` deltas between polls); alternatively `/game/{game_pk}/boxscore` gives final per-batter HR counts but is not event-timed, so **`feed/live` is the correct source for "just happened" HR detection**, not `linescore` or `boxscore` alone | Not currently fetched anywhere in the repo |

**Cross-reference to the existing helper:** `clients/mlb_stats.py:278-290`, `get_live_game_status(game_pk)`, calls only `/game/{game_pk}/linescore` and returns exactly `{current_inning, inning_state, outs}` — three fields. It does **not** fetch score, bases, active pitcher/batter, or HR events. It is called from exactly one place in the whole tree: `app.py:3823-3829` (`_fetch_live_status`, `@st.cache_data(ttl=60)`), feeding a "● LIVE" badge at `app.py:3851-3899`. It is never imported or called anywhere under `api/`. This confirms the audit's premise: the helper is real but minimal, and fully stranded from the FastAPI service.

**Confirms:** every live datum this program needs is available from the MLB Stats API; the gap is entirely on the "we don't fetch/expose it yet" side, not data availability.

### Freshness / polling

- **Useful cadence:** for a diamond + due-up-batter display, 15–20s polling is typical industry practice (linescore/feed-live doesn't update faster than play-by-play pace). For fire-once HR alerts, polling `feed/live` every 10–15s while a game is live is sufficient — HR alerts don't need sub-5s latency to be useful.
- **Quota/cost:** MLB Stats API is free and unauthenticated — no key, no request budget found anywhere in `clients/mlb_stats.py` (contrast with `clients/odds_api.py`, which explicitly parses `x-requests-remaining` and enforces a 500 req/month free-tier budget). This is a real advantage: **live-state polling has zero quota interaction with the Odds API budget.** The only cost is MLB's own servers, which is why polling should stay conservative (15–20s, only for games actually live, only while a client has a view open) rather than aggressive — good citizenship, not a hard technical limit found in code.
- **Does it fit the current model?** The current model is GitHub Actions cron (18x/day, hourly-ish, driving `api/cron.py` → one full pipeline run → Supabase write) plus a single Fly machine running one uvicorn worker (`Dockerfile` CMD, `--workers 1`; `fly.toml`: `min_machines_running = 1`, `auto_stop_machines = true`, `auto_start_machines = true`). Neither of the existing recurring mechanisms is fast enough for live polling (tightest cadence is hourly), and piggybacking a live poll onto the hourly cron would be far too coarse for in-game alerts.
- **Realistic mechanism — recommended:** **on-demand fetch, triggered by an open client view**, not a new background worker. The existing Streamlit pattern (`@st.cache_data(ttl=60)`, i.e., "fetch on request, cache briefly") is exactly the right shape to port to the API service: a new endpoint fetches from MLB Stats API on request, holds a short (10-20s) in-process TTL cache keyed by `game_pk` so concurrent requests for the same game within the TTL window don't re-hit MLB, and returns fresh data on cache miss. This needs **no new process, no queue, no scheduler** — it lives inside the existing single uvicorn worker as an ordinary request handler plus a small in-memory dict cache (same shape as `api/cache.py`'s pattern, but in-process rather than Supabase-backed, since live state is inherently ephemeral and doesn't need durability across restarts).
- A **background poller** (asyncio task inside the same worker, looping while games are live) becomes necessary only when alerts must fire without a client actively polling — i.e., Phase 3+/push territory, explicitly deferred per the operating assumptions. Flagging this honestly: `min_machines_running=1` means one machine does stay warm, so a background task is *technically* feasible on the current Fly config without new infra — but it's not needed for the Phase 1 chain the operator asked to prove, so scoping it now would be premature.

### API contract (proposed, additive-only)

A new endpoint, e.g. `GET /api/live-state/{game_pk}`, separate from `/api/slate`:

```json
{
  "game_pk": 745123,
  "status": "Live",
  "inning": 6,
  "inning_half": "Top",
  "outs": 2,
  "score": {"home": 3, "away": 2},
  "bases": {"first": true, "second": false, "third": true},
  "current_pitcher": {"id": 123, "name": "..."},
  "current_batter": {"id": 456, "name": "..."},
  "on_deck": {"id": 789, "name": "..."},
  "recent_home_runs": [
    {"player_id": 456, "player_name": "...", "inning": 5, "at": "2026-08-13T23:41:00Z"}
  ],
  "fetched_at": "2026-08-13T23:45:10Z"
}
```

**Additive-contract confirmation:** this is a brand-new route (`api/main.py` currently has 27 routes, none named `live-state`/`live`), reading from a new/separate code path (`clients/mlb_stats.py` extended with new functions, or a new `clients/mlb_live.py` module), writing nothing to `pipeline_runs`, `tickets`, or `legs`. `/api/slate`'s existing contract (`api/main.py:1714-1774`, the cache-first / last-good-fallback / empty-shape logic) is untouched by this design — no field added to it, no behavior changed. **Confirmed additive and non-breaking**, contingent on actually building it that way (this audit proposes the shape; it does not implement it).

### Architectural impact — honest accounting

- The "pregame-only, one-run-a-day" assumption is **not violated by Phase 1** as scoped here: the daily pipeline, cron cadence, and Supabase `pipeline_runs` cache stay exactly as they are. What's added is a parallel, independent, on-demand read path that happens to reuse the same MLB Stats API client module.
- What *does* change conceptually: the API service goes from "serves whatever the last cron run wrote" to "also serves live, uncached-beyond-seconds data for a narrow slice of endpoints." That's a real shift in the service's operating character — it stops being purely a read-replica of a nightly batch job — but it's additive, not a replacement of the existing model.
- Smallest viable live layer: one new client function per live datum (or one function returning the full bundle from a single `feed/live` call, which is more efficient than separate `linescore`/`boxscore` calls), one new additive endpoint, one small in-process TTL cache. No schema migration required for Layer 1 alone (no new Supabase table needed if state is purely ephemeral/in-memory).

---

## LAYER 2 — Live-Aware Surfaces

### Baseball diamond
All required fields (inning/half, outs, bases, score, current pitcher, current batter) come directly from the Layer 1 `feed/live`+`linescore` bundle. Fully buildable from Layer 1 alone — no additional data source needed.

### Live-aware slate flags
- **"Game started"** — derivable from the live-state endpoint's `status` field (or even more cheaply, from the schedule's `abstractGameState`, which is already fetched every pipeline run — no live poll needed for this flag specifically, just a comparison against wall-clock/cron-cached status).
- **"Your pitcher still in / pulled"** — needs the pregame `probablePitcher` (already in every slate row) compared against Layer 1's `current_pitcher.id` for that `game_pk`. Buildable, but requires joining a slate row's pregame pitcher to the live feed's current pitcher — straightforward given `game_pk` is already on both sides.
- **"Matchup live"** — trivially derivable (`status == "Live"` for the row's `game_pk`).

### Minimum viable Phase-1 display
A single detail view (not the full diamond) showing: game status badge (reusing the existing Streamlit visual pattern), score, inning/half/outs, and a due-up/current-batter readout — is the smallest thing that proves Layer 1 end-to-end and gives the operator something to click into from a slate row. The full animated diamond (base occupancy rendered graphically) is a Phase 2 richness upgrade on the same data, not a new data requirement.

---

## LAYER 3 — In-App Alerts

### Existing reuse points (confirmed)
- **Auth:** `api/auth.py` — JWT `sub` claim scopes every authenticated route already (`require_auth`/`require_beta`, confirmed via `Depends`). Correct, existing reuse point.
- **Tickets/legs:** `tickets` (per-ticket: `date`, `board`, `status`, `user_id`) and `legs` (per-player-per-ticket: `player_name`, `player_id`, `team`, `opponent`, `pitcher`, `leg_date`, `settlement_status`, `signal_snapshot`, and a `removed` soft-delete flag) — schema confirmed in `api/cache.py:200-406` (`add_leg`, `remove_leg`, `complete_ticket`, `ledger_legs`). **Gap to flag:** legs do **not** store `game_pk` directly. Deriving it requires joining `leg.team` + `leg.leg_date` against that date's schedule (already fetched via `mlb_stats.get_today_schedule`, which returns `game_pk` per team) — straightforward on a normal day, but **doubleheaders are a real edge case**: a team can have two `game_pk`s on the same date, and the pipeline already has to disambiguate this itself (`api/main.py:1301-1315`, `_slug_pks`/`_game_slug` doubleheader handling) — any alerts feature needs the same disambiguation, not a new problem but a real one to carry forward.
- **Bet Slip History:** `/api/my-tickets` (confirmed route, `api/main.py:496`) is the natural place a "watched legs" list already effectively exists — a user's pending legs are already the candidate set for both trigger types.

These are confirmed as the right reuse points — no new auth, no new user table, no new ticket/leg storage needed for the alert *subject matter itself*.

### Per-trigger data confirmation

1. **Slip batter homered** → needs `feed/live`'s HR events (Layer 1, confirmed above) keyed by `game_pk` + `player_id`, cross-referenced against the user's pending legs (`player_id` + `leg_date`, joined to `game_pk` as above). **Confirmed buildable**, contingent on the doubleheader join caveat.
2. **Batter coming up** → needs Layer 1's `current_batter`/`on_deck` (or lineup-position + outs/inning to estimate "coming up soon") cross-referenced the same way. **Confirmed buildable.**
3. **[Assess only] Top-cohort +EV matchup went live** → needs Layer 1's `status == "Live"` plus a "cohort" flag that already exists conceptually in the pregame slate (tier/EV ranking is already computed and cached per player in `pipeline_runs`). This is **buildable but is a different shape of alert** — it's slate-driven (any qualifying player, not just the user's own legs), so it needs a "top N by EV/tier" query against the day's cached slate rather than the user's ticket data. Flagging as assessed-only per the operating assumptions: feasible, not committed to Phase 1.

### In-app delivery mechanism (no push infra)

**Smallest viable option:** poll-driven client check. While the app is open, the client periodically (e.g., every 15-30s) calls a new lightweight endpoint — e.g. `GET /api/alerts/check` — that, server-side, cross-references the authenticated user's pending legs against the current live state for their relevant `game_pk`s (using the same in-process live-state cache from Layer 1, so this doesn't multiply MLB API calls) and returns any new events since the client's last-seen marker. The client renders these as toasts using the **already-existing DOM toast pattern** (`#hr-lb-fd-toast` / `#md-qp-fd-toast` in `frontend/assets/js/`) and/or a small notification-center list. No service worker, no push subscription storage, no new persistent table is strictly required for Phase 1 — this is client-poll + server-side cross-reference, nothing more.

A lightweight **notifications table** (Supabase) becomes worth adding once alerts need to survive a page reload or be visible across devices/sessions (e.g., "show me alerts I missed since I last had the app open") — that's a reasonable Phase 2 addition, not required to prove the chain in Phase 1.

### State reuse

Confirmed: "which legs are watched" is simply "the user's own pending (`settlement_status == 'pending'`, `removed == False`) legs for today," which is exactly what `/api/my-tickets` already computes. No new "watch" concept or subscription table is needed for single-user Phase 1 — every pending leg is implicitly watched.

### Noise control

Fire-once-per-event dedup needs a small piece of state: either (a) client-side, tracking the highest event timestamp/ID already shown (simplest, but lost on page reload — acceptable for a poll-only-while-open Phase 1 alert), or (b) server-side, a `last_seen_event_id` per user+leg if durability across reloads matters. Recommend (a) for Phase 1 (zero new storage), noting (b) as the natural Phase 2 upgrade once a notifications table exists anyway.

### What browser/PWA push would need later (not scoped now)

- A service worker registered on the frontend (root `frontend/` static site currently has none).
- A push subscription endpoint (store per-user push subscription objects — new Supabase table).
- A push service integration (e.g., Web Push via VAPID keys, or a third-party push provider) — separate from the existing `tracking/notify.py` ntfy.sh integration, which is a *server-triggered, external-app* push (phone notification via the ntfy app), not a *browser-native* push and not in-app. Worth noting `tracking/notify.py` already proves the team is comfortable with a lightweight push mechanism (ntfy, no account/key), which could inform a later push choice, but it's a distinct mechanism from PWA/service-worker push and is out of scope for the in-app Phase 1 goal.

---

## PHASED PLAN

### Phase 1 — minimum viable chain (proves Layer 1 → 2 → 3 end to end)
**Includes:**
- One new client function (or module) fetching `feed/live` + `linescore` for a `game_pk`, returning the bundled shape proposed above.
- One new additive endpoint, `GET /api/live-state/{game_pk}`, in-process short-TTL cache, no new Supabase table.
- One minimal live-aware display (score/inning/outs/due-up-batter — not the full animated diamond) reachable from a slate row.
- One in-app alert trigger — recommend **"batter coming up"** over "batter homered" for Phase 1, since it's lower-stakes to get slightly wrong (a late/early "coming up" ping is a minor annoyance; a missed or duplicate HR alert is more visibly a bug) and exercises the exact same due-up-batter field the diamond already needs — but either trigger is a legitimate Phase 1 choice; this is a recommendation, not a determination.
- Client-side poll (`GET /api/alerts/check` or reuse the live-state endpoint directly) + toast rendering via the existing toast DOM pattern.

**Depends on:** nothing outside the current stack. No migration, no new infra, no deploy config change (same Fly machine, same worker count).
**Surface area:** ~1 new client module/functions, 1-2 new API routes, small frontend addition (poll loop + toast render, reusing existing patterns).
**Protected-surface touches:** none if built as designed (additive routes only; `/api/slate`, `pipeline.py`, `api/cron.py`, `config.py`, MAIN/JIG scoring untouched). Still requires **audit-first ratification** before execution per Rule 13/14, since any new route in `api/main.py` and any new client module are still "backend/API" surface — this document is that Stage-1 audit; Stage 2 (execution) needs separate explicit authorization.
**Home-PC/secrets/deploy:** none required to build; a Fly deploy (existing pipeline, `fly deploy`) is required to make it live, which per doctrine is a deploy action requiring explicit operator authorization at execution time — not part of this audit.

### Phase 2 — richness + second trigger
- Full animated diamond (base occupancy rendered graphically) — same data, better presentation.
- Second trigger: "slip batter homered" (the higher-stakes one, benefits from Phase 1's toast plumbing and dedup pattern already proven).
- Live tracker surface (a dedicated per-game live view, not just a slate-row popover).
- Lightweight Supabase `notifications` table (survives reload, enables the (b) server-side dedup option, sets up multi-device visibility).
**Depends on:** Phase 1 shipped and stable. **New Supabase migration** required (notifications table) — protected-surface flag: touches Supabase schema, needs the same migration-and-manual-run pattern already established for `community_posts` (per `wiki/architecture/community-bet-slips-phase-1.md` precedent) — home-PC/operator-run migration step.

### Phase 3+ — push/PWA and multi-user (explicitly deferred, not scoped)
- Service worker + Web Push subscription storage + push service integration for alerts that fire without the app open.
- "Top-cohort +EV matchup went live" trigger (assessed feasible above, not committed).
- Multi-user/friend-group alert subscriptions (would need a new subscription model beyond "my own legs" — a real design task, not just infra).
**Depends on:** Phase 2's notifications table (durable event log makes push straightforward to layer on top). **Protected-surface + infra flags:** new service worker on the static `frontend/` site, new Supabase table(s), potentially a background poller if push needs to fire while no client is open (revisits the Layer 1 "on-demand vs. background worker" decision) — all deploy/secrets/home-PC-authorized actions, none of which this audit scopes or recommends committing to now.

---

## Files written

- `mlb_hr_engine_v4/scripts/analysis/live_state_alerts_program_audit_2026-08-13.md` (this file)
- `MLB HR ENGINE/wiki/architecture/live-state-and-alerts-program.md` (staged, not committed — see below)

No other files were created, edited, or deleted. No source, config, migration, or protected-surface file was touched.

## Recommended Phase-1 scope (decision for the operator)

Build exactly the Phase 1 bullet list above: one additive live-state endpoint + in-process cache, one minimal live-aware display, one in-app alert trigger (recommend "batter coming up" first), client poll + existing-toast-pattern rendering. Zero new infrastructure, zero migrations, zero protected-surface changes. This is a Stage-1 audit only — building it requires a separate, explicitly authorized Stage-2 execution packet per Rule 13.
