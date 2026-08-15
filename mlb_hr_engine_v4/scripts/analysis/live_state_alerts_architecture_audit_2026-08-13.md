# Live Game State + Live-Aware Surfaces + In-App Alerts

**Architecture audit and phased program plan — 2026-08-13**

Status: **FEASIBLE, HIGH-RISK IMPLEMENTATION, AUDIT COMPLETE / NOT AUTHORIZED TO BUILD**

Recommended decision room: `USE EXISTING ROOM: MLB HR Engine Setup`

## Executive decision

Build the program as a parallel live-data lane. Do not turn the pregame pipeline or `/api/slate` into a live feed.

The smallest robust Phase 1 is:

1. a separate `GET /api/live/games/{game_pk}` endpoint backed by MLB's live feed and a 10-second per-game cache;
2. exact game identity on watched ticket legs (`player_id` + `game_pk`), exposed through the authenticated ticket read model;
3. a compact live game strip with score, inning/half, outs, occupied bases, active batter, and active pitcher;
4. one in-app, fire-once alert: **a watched slip batter homered**;
5. client polling only while the signed-in app is open, with no browser/PWA push and no always-on event worker.

This proves the complete chain with no change to MAIN/JIG scoring, `/api/slate`, `pipeline.py`, `api/cron.py`, or the `pipeline_runs` cache. It does require an additive ticket-leg schema migration and additive ticket API fields; omitting that identity work would make posted-slip alerts ambiguous for doubleheaders.

## Scope and evidence standard

- Read-only architecture investigation; only this report and the paired wiki plan were written.
- No runtime code, frontend code, schema, workflow, secret, deployment, or production state was changed.
- Graphify was consulted before direct tree search as requested.
- **GRAPHIFY: STALE.** `mlb_hr_engine_v4/graphify-out/graph.json` was written `2026-08-13T07:16:12Z`; current HEAD `8ffc53849ef3c128fe06a0c886df1eac01efe177` is dated `2026-08-13T08:29:18Z`. Graph results were used only to locate files, then every finding was re-verified in current source.
- Official MLB endpoint responses were inspected directly using completed game `823672` (BAL at MIN, 2026-08-12).

## Current architecture truth

The public React slate remains pregame/cache-first:

```text
GitHub Actions schedule
  -> python -m api.cron
  -> pipeline.load_game_data()
  -> api.main._build_slate_payload()
  -> Supabase pipeline_runs.payload.slate_cache
  -> GET /api/slate
  -> static Vercel frontend
```

Current-source corrections to the prior background:

1. The scheduled pipeline is no longer literally one run per day. `.github/workflows/daily_pipeline.yml:3-32` starts it hourly from 06:00 ET through 23:00 ET; `api/cron.py:197-269` rebuilds and stores the batch payload. It is still a static pregame snapshot lane, not continuous live state.
2. `/api/my-tickets` already has a narrow on-demand live-aware read. `api/ticket_history.py:22-33,101-123,154-186` hydrates schedule linescores and returns game status plus inning totals. It does **not** expose bases, outs, current batter, active pitcher, due-up state, or HR events, and it is not a reusable `/api/slate` live layer.
3. `clients/mlb_stats.py:278-290` has the stranded `get_live_game_status()` helper, but it returns only `current_inning`, `inning_state`, and `outs`. Its only consumer is Streamlit (`app.py:3822-3829`) behind a 60-second cache. FastAPI and `/api/slate` do not expose it.
4. `GET /api/slate` is explicitly cache-only and never rebuilds in-request (`api/main.py:1714-1774`). The existing contract can remain byte-compatible while a separate live endpoint is added.
5. Ticket legs persist `player_id`, team, opponent, and pitcher, but not `game_pk` (`api/cache.py:201-268`; `supabase/migrations/003_tickets_legs.sql`). The active slip is memory-only and also drops `game_pk` (`frontend/assets/js/slip-state.js:5-23,43-60,115-132`). `/api/my-tickets` omits `player_id` from its select/response (`api/ticket_history.py:14-19,101-123`). Team/opponent matching deliberately returns no game when doubleheader candidates are ambiguous (`api/ticket_history.py:126-139`).

## Target separation

```text
PREGAME LANE (unchanged)
pipeline -> Supabase slate_cache -> /api/slate -> MAIN/JIG surfaces

LIVE LANE (new, additive)
MLB game feed -> short-TTL live adapter -> /api/live/games/{game_pk}
                                     |-> compact live display / tracker
                                     `-> watched-leg event matcher -> in-app alerts

ALERT IDENTITY
auth user -> tickets -> active non-removed legs -> player_id + game_pk
```

The live lane must not write into model inputs, probability, ranks, tiers, JIG scores, HVY, EV, or the `pipeline_runs` slate cache.

# FINDINGS

## Layer 1 — Live game state

### MLB endpoints and exact fields

| Endpoint | Exact useful fields | Role |
|---|---|---|
| [`GET /api/v1/schedule?sportId=1&date=...`](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-08-13&hydrate=team,linescore) | `dates[].games[].gamePk`, `gameDate`, `status.abstractGameState`, `status.detailedState`, `teams.home/away.team.{id,abbreviation}`, optional hydrated `linescore` | Discover games and Preview/Live/Final transitions. Not sufficient for alert-grade play state. |
| [`GET /api/v1/game/{game_pk}/linescore`](https://statsapi.mlb.com/api/v1/game/823672/linescore) | `currentInning`, `currentInningOrdinal`, `inningState`, `inningHalf`, `isTopInning`, `balls`, `strikes`, `outs`, `teams.away/home.{runs,hits,errors}`, `offense.{batter,onDeck,inHole,first,second,third}`, `defense.pitcher` | Lightweight score, inning/count, bases, active batter/pitcher, and on-deck state. Base keys are absent when empty and must normalize to `null`. |
| [`GET /api/v1.1/game/{game_pk}/feed/live`](https://statsapi.mlb.com/api/v1.1/game/823672/feed/live) | `gameData.status.*`; `liveData.linescore.*`; `liveData.plays.currentPlay.{atBatIndex,about,result,matchup,runners,playEvents}`; `liveData.plays.allPlays[]`; embedded `liveData.boxscore` | Canonical one-call source for the Phase 1 live endpoint. It supplies the diamond plus event history and active matchup. Use the v1.1 feed path. |
| [`GET /api/v1/game/{game_pk}/boxscore`](https://statsapi.mlb.com/api/v1/game/823672/boxscore) | `teams.{home,away}.{players,batters,pitchers,battingOrder}`; `players.ID{person,position,allPositions,battingOrder,stats}` | Lineup order, substitutions, used/current roster context, and player lookup. It is embedded in `feed/live`; a second call is not required unless a narrower service is chosen. |
| [`GET /api/v1/game/{game_pk}/playByPlay`](https://statsapi.mlb.com/api/v1/game/823672/playByPlay) | `allPlays[].{atBatIndex,result,about,matchup,runners,playEvents}` | Alternative event-only source, but it is still large and does not replace linescore/boxscore state. |

Required datum mapping:

- Live score: `liveData.linescore.teams.away.runs` and `.home.runs`.
- Inning/half: `liveData.linescore.currentInning`, `currentInningOrdinal`, `inningHalf`/`inningState`, `isTopInning`.
- Outs and count: `liveData.linescore.outs`, `balls`, `strikes`.
- Bases: presence of `liveData.linescore.offense.first`, `.second`, `.third`; each occupied value supplies player identity.
- Active pitcher: `liveData.linescore.defense.pitcher`; cross-check current plate appearance with `liveData.plays.currentPlay.matchup.pitcher`.
- Current batter: `liveData.plays.currentPlay.matchup.batter` or `liveData.linescore.offense.batter`.
- Coming up: define Phase 2 semantics as **on deck**, using `liveData.linescore.offense.onDeck`. `inHole` is also available. Predicting more than two batters ahead requires batting-order/substitution logic from the embedded boxscore and is not the minimum alert.
- HR event: a completed `liveData.plays.allPlays[]` entry where `result.eventType == "home_run"` and `about.isComplete == true`; player is `matchup.batter.{id,fullName}`. Include `atBatIndex`, pitcher, inning/half, description, RBI, post-play score, and event end time.
- Stable Phase 1 HR event key: `hr:{game_pk}:{atBatIndex}:{batter_id}`. `atBatIndex` is unique within a game; the last `playEvents[].playId` can be retained as source evidence when present but should not be required.

Observed response characteristics on game `823672`:

| Response | Bytes observed | MLB cache header |
|---|---:|---|
| linescore | 3,170 | `public, max-age=10, stale-while-revalidate=30, stale-if-error=86400` |
| boxscore | 171,807 | same 10-second freshness hint |
| full v1.1 live feed | 815,056 | same 10-second freshness hint |
| v1.1 live feed with required `fields=` projection | 81,283 | same 10-second freshness hint |

These are one-game measurements, not a guaranteed size or latency SLA. They show why the service should request only needed fields and cache each game for about 10 seconds.

### Freshness and polling

Recommended Phase 1 cadence:

- Poll the engine live endpoint every **15 seconds** while the app is visible and at least one watched game is Live.
- Backend cache: **10 seconds per `game_pk`**, honoring MLB's observed `max-age=10` response hint.
- Poll only unique watched live games plus the explicitly opened tracker game; do not sweep every MLB game from every browser.
- Back off to 30-60 seconds for Preview/delay states, stop event polling at Final, and use bounded retries with last-good state clearly marked stale.
- The existing Streamlit 60-second cache is acceptable for an inning badge, but too slow for a useful on-deck alert.

Quota/cost verdict:

- Current calls succeeded without a key, and the repo already treats MLB Stats API access as free/no-key (`clients/mlb_stats.py:1-19`; `api/cron.py:39-41,60-86`).
- No per-request billing or response quota headers were observed.
- **Do not call it guaranteed “unmetered.”** MLB publishes no dependable public quota or availability SLA in the accessible documentation. Use caching, a real User-Agent, backoff, concurrency limits, and fail-soft behavior.
- This lane does not consume The Odds API and therefore does not worsen the existing Odds API quota pressure.

### Runtime mechanism

| Mechanism | Verdict | Why |
|---|---|---|
| Existing hourly GitHub Actions cron | **Not viable for alerts** | Current cadence is hourly; GitHub's documented minimum scheduled interval is five minutes, still too slow and subject to scheduler delay. |
| New high-frequency cron | **Not recommended** | Process startup and five-minute floor cannot deliver on-deck or timely HR alerts. [GitHub schedule docs](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule). |
| On-demand FastAPI fetch driven by the open app | **Phase 1 choice** | The existing Fly web service can fetch/cache live state; no second process or service is required. Alerts are intentionally available only while the app is open. |
| Long-running worker | **Phase 2+ requirement** | Required for durable notifications, multi-user fan-out, or detection while no app is open. Must be a separately governed Fly worker/process or equivalent, not an in-request background task. |

Current `fly.toml` runs one Uvicorn worker and keeps one machine minimum. A process-local 10-second cache is sufficient for single-user Phase 1. It is ephemeral and per-instance by design; multi-instance or durable delivery requires shared state later.

### Additive API contract

Preferred route:

```text
GET /api/live/games/{game_pk}
```

Proposed normalized response:

```json
{
  "game_pk": 823672,
  "state": "live",
  "status": {"abstract": "Live", "detailed": "In Progress"},
  "source_timestamp": "20260813_181045",
  "fetched_at": "2026-08-13T18:10:47Z",
  "stale": false,
  "poll_after_seconds": 15,
  "inning": {
    "number": 5,
    "ordinal": "5th",
    "half": "Top",
    "state": "Top",
    "outs": 1,
    "balls": 2,
    "strikes": 1
  },
  "score": {
    "away": {"team_id": 114, "abbr": "CLE", "runs": 2},
    "home": {"team_id": 116, "abbr": "DET", "runs": 1}
  },
  "bases": {
    "first": {"id": 123, "name": "Runner Name"},
    "second": null,
    "third": null
  },
  "matchup": {
    "batter": {"id": 456, "name": "Batter Name"},
    "on_deck": {"id": 789, "name": "On Deck Name"},
    "in_hole": null,
    "pitcher": {"id": 321, "name": "Pitcher Name"}
  },
  "events": {
    "latest_at_bat_index": 42,
    "home_runs": [
      {
        "event_id": "hr:823672:23:687637",
        "at_bat_index": 23,
        "batter_id": 687637,
        "pitcher_id": 805673,
        "inning": 3,
        "half": "Top",
        "rbi": 3,
        "away_score": 4,
        "home_score": 1,
        "description": "...",
        "completed_at": "2026-08-12T18:32:07Z"
      }
    ]
  }
}
```

Contract rules:

- Separate route; no mutation of `/api/slate` keys or freshness semantics.
- Normalize absent bases/players to `null`; never fabricate.
- Return Preview/Delayed/Final honestly with nullable live fields.
- Validate/allowlist `game_pk` against the current schedule or cached slate to avoid becoming an unrestricted proxy.
- Return explicit `stale`, `fetched_at`, and poll guidance.
- Keep raw MLB payload server-side; expose a small stable contract.

**Additive-contract confirmation: YES.** The live endpoint can be completely separate. Phase 1 does not require changes to `pipeline.py`, `api/cron.py`, `api/cache.py`'s `pipeline_runs` methods, the persisted `slate_cache`, or `/api/slate`.

### Architectural impact

This program breaks the product's pregame-only assumption, but it does not have to break the pregame architecture. The honest change is a second freshness class:

- pregame intelligence: hours-old persisted batch data, current behavior preserved;
- live state: seconds-old ephemeral MLB game data, fetched independently;
- alert state: per-user watched identity and event dedupe, initially browser-local and later durable.

The smallest viable live layer is a field-projected MLB feed adapter, a 10-second game cache, one separate route, and client polling for watched games. It is not a pipeline rerun and must never recompute model outputs during a game.

## Layer 2 — Live-aware surfaces

| Surface/flag | Buildable? | Data and caveat |
|---|---|---|
| Baseball diamond | **Yes** | Bases from `linescore.offense.first/second/third`; batter/on-deck and defensive pitcher from linescore/current play; inning, count, outs, score from linescore. All required fields exist. |
| Game started | **Yes** | `gameData.status.abstractGameState == "Live"` plus detailed state. Do not infer solely from scheduled time. |
| Matchup live | **Yes** | Exact when current play batter ID equals the slate/ticket batter ID; stricter predicted matchup also compares pitcher ID. |
| Your pitcher still in | **Yes, contextual** | Compare the pregame opponent `pitcher_id` with the current defensive pitcher for the batter's team half. Outside that half, use embedded boxscore/current-position context or the last observed pitcher for that defensive team. |
| Your pitcher pulled | **Yes, contextual** | A live replacement pitcher ID after the tracked pitcher has appeared establishes pulled/replaced. A pregame probable mismatch at first pitch may be a starter change, not “pulled”; label it separately. |
| Rich pitch tracker | **Yes, later** | `currentPlay.count`, `playEvents[]`, pitch details/coordinates exist, but a pitch-by-pitch UI materially expands contract and QA scope. |

Minimum Phase 1 display:

```text
LIVE · TOP 5 · 1 OUT     CLE 2 — DET 1
[three occupied/empty base indicators]
AT BAT: Batter Name     P: Pitcher Name
```

This is enough to prove freshness and matchability. A full-screen tracker, pitch trail, spray/zone visualization, substitutions, and pitch-by-pitch history belong in Phase 2. Any implementation is a frontend/UI task and must use Claude Design as layout authority plus the operator-selected design skill required by AGENTS.md.

## Layer 3 — In-app alerts

### Trigger feasibility

| Trigger | Data verdict | Identity/logic verdict |
|---|---|---|
| 1. Watched slip batter homered | **Provided** | Match completed `home_run` event `matchup.batter.id` to watched `legs.player_id` and exact `game_pk`. Fire once by event ID. Recommended Phase 1 trigger. |
| 2. Watched batter coming up | **Provided** | Define “coming up” as watched player equals `linescore.offense.onDeck.id`. Fire on transition into on-deck, not every poll. Click opens `/live-game/{game_pk}?batter_id=...` or equivalent tracker route built in Phase 2. |
| 3. Top-cohort +EV matchup went live | **Data available; semantics not canonical** | Live transition comes from game status. `ev_pct` is on `/api/slate`. The current BEST COHORT predicate exists only in `frontend/assets/js/full-slate-matrix.js:150-160` and is not an emitted canonical flag. Do not duplicate it into backend alert logic without separate operator ratification/source-of-truth work. Assess as feasible, defer. |

For trigger 3, current client logic defines BEST COHORT as expected PA at least 4.2, season HR/PA at least 4.35%, and vs-hand SLG at least .440. “+EV” would additionally require a real `ev_pct > 0`; odds-pending rows are ineligible. This is display/filter logic, not permission to add scoring or a new cohort formula.

### Watched state and existing reuse

Reusable now:

- JWT auth and `require_auth`;
- per-user `tickets.user_id` ownership;
- `tickets`/`legs` write-separate capture architecture;
- persisted `legs.player_id` for newer legs;
- ticket lifecycle fields and `/api/my-tickets` read path;
- production frontend auth wrapper `window.__hrAuth.authFetch`.

Gaps that block robust posted-slip alerts:

- no `legs.game_pk` column;
- slip add payload does not send `game_pk`;
- active client slip does not retain `game_pk`;
- `/api/my-tickets` omits `player_id` and has no `game_pk` to expose;
- old/name-only legs need a documented non-alertable or best-effort policy;
- team/opponent schedule matching cannot disambiguate doubleheaders.

Recommended watched definition for Phase 1:

- authenticated user's current-date, non-removed legs;
- tickets in `building` or `pending`/completed-deployed state;
- exclude settled/void legs and Final games;
- require numeric `player_id` and `game_pk` for alert-grade matching;
- legacy rows without exact identity remain visible in history but do not silently generate approximate alerts.

Required Phase 1 identity hardening is additive: nullable `legs.game_pk`, optional `game_pk` in the slip write contract, and `player_id`/`game_pk` in the owner-only `/api/my-tickets` response. This is an existing-table migration and protected API-contract work, not a scoring/pipeline change.

### Smallest in-app delivery with no push infrastructure

1. On authenticated app start, load watched legs from `/api/my-tickets`.
2. Group by unique current-date `game_pk`.
3. While the page is visible, poll `/api/live/games/{game_pk}` every 15 seconds for games in Live state.
4. On first snapshot, seed the per-game high-water mark without replaying old events as new toasts.
5. On a later snapshot, match unseen HR events to watched `(game_pk, player_id)` pairs.
6. Show an in-app toast and add the item to a small notification-center list.
7. Persist seen IDs and a bounded notification list in `localStorage`, namespaced by authenticated user ID and date.

No push provider, service worker, Realtime channel, notifications table, or background worker is needed for this Phase 1 mode. The explicit limitation is that detection and delivery work only while the web app is open; browser timer throttling means “visible tab” should be the promised behavior.

### Noise and duplicate control

- Event key: `hr:{game_pk}:{atBatIndex}:{batter_id}`.
- First response seeds the watermark; do not toast every historical HR in `allPlays`.
- Persist a bounded seen-event set across reloads, keyed by user/date.
- Fire the due-up alert only on transition from not-on-deck to on-deck.
- Suppress alerts for removed, settled, void, legacy-unidentified, or wrong-date legs.
- One toast per event even if the batter appears on multiple slips; the center item may list all affected slip IDs.
- Stop polling at Final and expire browser-local state after a short retention window.
- If the endpoint returns stale state, show stale UI and do not create new alerts until a fresh transition is observed.

### Browser/PWA push later

Push is explicitly outside Phase 1. It later requires:

- HTTPS and a service worker with `push` and `notificationclick` handlers;
- notification permission UX initiated by a user action;
- `PushManager.subscribe()` and an application-server/VAPID key;
- secure per-user/device subscription storage (`endpoint`, encryption keys, expiry) plus unsubscribe/rotation handling;
- an always-on server event worker to detect events when no app is open;
- an application-server Web Push sender and failure cleanup;
- deep-link routing into the live tracker;
- a web-app manifest/install path if the product is to be treated as a PWA.

The browser supplies a push-service endpoint through `PushSubscription`; the application server must store it and send encrypted messages. See [MDN Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API) and [`PushManager.subscribe()`](https://developer.mozilla.org/en-US/docs/Web/API/PushManager/subscribe).

# FEASIBILITY

| Layer | Verdict | Primary constraint |
|---|---|---|
| Layer 1: live game state | **FEASIBLE** | Requires a seconds-fresh lane and careful MLB polling/cache discipline; current batch cache cannot supply it. |
| Layer 2: live-aware surfaces | **FEASIBLE** | Minimum display is straightforward; full pitch tracker is materially larger UI/contract work. |
| Layer 3 trigger 1: HR | **FEASIBLE after exact identity hardening** | Current ticket path lacks `game_pk` and owner history omits `player_id`. |
| Layer 3 trigger 2: coming up | **FEASIBLE** | Define it narrowly as on-deck; a deeper due-up forecast needs substitution-aware lineup logic. |
| Layer 3 trigger 3: top-cohort +EV live | **TECHNICALLY FEASIBLE, NOT READY TO AUTHORIZE** | BEST COHORT is a client-only predicate, not a canonical backend flag. |
| In-app only, app open | **FEASIBLE without new service** | Client polling plus browser-local dedupe. |
| Closed-app/background delivery | **NOT Phase 1** | Requires durable event processing and push infrastructure. |

# PHASED PLAN

## Phase 1 — Minimum viable end-to-end chain

**Goal:** prove live MLB state -> stable engine endpoint -> live display -> exact watched-leg match -> one fire-once in-app alert.

Includes:

- new field-projected MLB live adapter and 10-second per-game cache;
- separate `GET /api/live/games/{game_pk}` route;
- Preview/Live/Final/delay normalization, score, inning/half/count/outs, bases, batter/on-deck/in-hole, active pitcher, and completed HR events;
- additive nullable `legs.game_pk` migration;
- capture/pass through `game_pk` on every slip-add surface;
- expose `player_id` and `game_pk` on owner-only `/api/my-tickets`;
- compact live game strip/mini-diamond on one canonical production surface;
- authenticated watched-leg loader;
- visible-tab 15-second polling of watched live games;
- HR toast plus small browser-local notification list;
- localStorage fire-once ledger and stale-state suppression;
- fixture/contract tests and one real live-game runtime validation before any production approval.

Does not include:

- full live tracker, pitch chart, due-up alert, notification database, Realtime, background worker, PWA/service worker, browser push, multi-user subscriptions, cohort alert, or any model/scoring change.

Dependencies:

- operator approval of this Stage 1 audit;
- HIGH-risk Stage 2 implementation packet;
- operator-selected design skill and Claude Design source for the UI portion;
- a current live MLB game for final runtime proof.

Rough surface area: 7-10 code/test files plus one additive Supabase migration. No new hosted service.

Protected-surface flags:

- **API contract: YES** — new live contract and additive ticket fields; audit-first ratification required.
- **Supabase migration: YES** — existing `legs` table gets nullable `game_pk`; manual migration approval required.
- **Production frontend: YES** — mounted Vercel surface and shared slip capture.
- **Existing `/api/slate`: NO TOUCH.**
- **Pipeline: NO TOUCH.**
- **Cron/workflow: NO TOUCH.**
- **`pipeline_runs` cache: NO TOUCH.**
- **MAIN/JIG formulas, calibration, ranks, tiers, filters, EV, HVY: NO TOUCH.**

New infrastructure: no new platform/service; one existing-database schema migration and ephemeral Fly memory cache only.

Phase 1 done means a watched, exact-game leg receives exactly one in-app HR alert from a fresh MLB event while the app is visible, and the compact live state matches MLB for score/inning/outs/bases/batter/pitcher. `/api/slate` contract tests remain unchanged.

## Phase 2A — Rich live tracker + second trigger

Includes:

- dedicated clickable live game tracker;
- full diamond, richer score/inning/count state, substitutions, pitcher-in/pulled/starter-changed flags;
- current and recent plate-appearance/pitch events as contract scope allows;
- **coming-up alert**, defined initially as watched batter transitions to on-deck;
- deep link from notification to the watched batter/game;
- multi-tab coordination if needed.

Dependencies: stable Phase 1 live contract and measured polling reliability.

Rough surface area: 3-6 frontend/backend/test files; no new service if it remains open-app only.

Protected surfaces: additive live API and production UI; no slate/pipeline/scoring touch. Any pitch-coordinate contract expansion requires a separate privacy/performance review.

New infrastructure: none for open-app-only behavior.

## Phase 2B — Durable in-app center + multi-user/friend-group subscriptions

Includes:

- notification preferences/subscriptions keyed by `user_id`, `game_pk`, `player_id`, and trigger type;
- a write-separate `notifications` table with unique event key, created/read/dismissed timestamps, and RLS;
- one live-game polling worker that fetches each game once and fans out to users;
- authenticated notification read/ack endpoints;
- durable in-app center, unread count, per-trigger controls, and group/friend routing rules;
- server-side idempotency with unique `(user_id, event_key, trigger_type)`.

Dependencies: Phase 1 event identity, Phase 2A tracker route, multi-user product/privacy decisions.

Rough surface area: 5-9 backend/frontend/test/workflow files plus 2-3 migrations.

Protected surfaces: auth/RLS, API contracts, deployment/runtime configuration. Keep notification tables write-separate from engine/scoring tables.

New infrastructure: **YES** — durable Supabase tables/RLS and a separately governed long-running Fly worker/process or equivalent. GitHub Actions cron is not suitable.

## Phase 3 — Browser/PWA push and optional cohort alert

Includes:

- service worker, permission UX, PushManager/VAPID subscriptions, secure subscription storage, Web Push sender, notification click routing, and subscription cleanup;
- PWA manifest/installability if desired;
- alerts while the app is closed;
- optional “top-cohort +EV game went live” only after a separate decision establishes a canonical, display-only cohort eligibility source and confirms that no scoring/filter doctrine is being changed.

Dependencies: durable server-side worker and notifications from Phase 2B; explicit secrets/deployment approval; separate cohort semantics ratification.

Rough surface area: 5-8 frontend/backend/test/config files plus secrets and subscription migration.

Protected surfaces: auth, secrets, deployment/runtime config, service worker caching behavior, and potentially `/api/slate` if a cohort flag is emitted. Any `/api/slate` field must be additive and separately approved.

New infrastructure: **YES** — Web Push application-server capability/VAPID secret and subscription storage. A paid notification vendor is not inherently required.

# OPERATOR DECISION

## Recommendation

**Approve Phase 1 only as a HIGH-risk Stage 2 implementation after ratifying these boundaries:**

1. `/api/slate`, `pipeline.py`, `api/cron.py`, and `pipeline_runs.payload.slate_cache` remain unchanged.
2. Phase 1 alerts are promised only while the signed-in app is visible.
3. The first trigger is watched batter HR, not due-up or cohort.
4. Exact `game_pk` persistence/exposure is included; name/team matching is not accepted as alert-grade identity.
5. No PWA/browser push, notifications table, or always-on worker in Phase 1.
6. MLB feed polling is limited to watched/open games at 15 seconds through a 10-second backend cache.
7. UI work follows Claude Design and the operator's selected design skill.

This is the smallest scope that proves the real product payoff without contaminating the pregame engine or creating premature push infrastructure.

## Unresolved decisions before Stage 2 implementation

- Exact canonical frontend placement for the compact Phase 1 live strip.
- Whether `building` tickets are watched alongside posted/deployed `pending` tickets; recommendation is yes for today's non-removed exact-identity legs.
- Legacy leg policy; recommendation is visible but non-alertable when `player_id` or `game_pk` is missing.
- Final route name/deep-link convention for Phase 2 tracker.
- Operator design-skill selection, required before frontend implementation.

## Protected systems touched by this audit

No. Read-only inspection plus documentation only.

## Graphify status

`GRAPHIFY STATUS: STALE`

The graph was useful for navigation but not treated as current-source authority. No graph update/rebuild was run.
