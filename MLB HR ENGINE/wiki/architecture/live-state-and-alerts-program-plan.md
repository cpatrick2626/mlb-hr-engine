# Live State and Alerts Program Plan

Status: **CANONICAL PLAN — AUDIT COMPLETE, IMPLEMENTATION NOT AUTHORIZED**

Date: 2026-08-13

Decision room: `USE EXISTING ROOM: MLB HR Engine Setup`

Detailed evidence: [Live Game State + Live-Aware Surfaces + In-App Alerts audit](../../../mlb_hr_engine_v4/scripts/analysis/live_state_alerts_architecture_audit_2026-08-13.md)

## Decision

Add live state as a parallel lane. Do not make `/api/slate` or the pregame pipeline poll live games.

```text
PREGAME (unchanged)
pipeline -> Supabase slate_cache -> /api/slate -> MAIN/JIG

LIVE (new, additive)
MLB feed -> 10 s per-game cache -> /api/live/games/{game_pk}
                               |-> live display / tracker
                               `-> watched-leg matcher -> in-app alerts
```

## Current truth

- The public React slate is a persisted pregame snapshot served by `GET /api/slate`; it never rebuilds in-request.
- GitHub Actions currently invokes the batch pipeline hourly during the 06:00-23:00 ET operating window. More frequent batch runs do not make the slate a live feed.
- `clients/mlb_stats.get_live_game_status()` exists but returns only inning/state/outs and is consumed only by Streamlit behind a 60-second cache.
- `/api/my-tickets` already attaches narrow schedule/linescore context, but it has no bases, outs, active matchup, due-up state, or HR event stream.
- Ticket legs persist `player_id` but not `game_pk`; `/api/my-tickets` omits `player_id`. Team/opponent matching is not doubleheader-safe.
- Graphify was stale relative to HEAD and was used only to locate source files; all statements above were verified in current source.

## Live data contract

Preferred endpoint:

```text
GET /api/live/games/{game_pk}
```

Source: MLB Stats API v1.1 `game/{game_pk}/feed/live`, field-projected and normalized.

Minimum response groups:

- status: Preview/Live/Final/detailed state;
- score: away/home teams and runs;
- inning: number/ordinal/half/state, balls, strikes, outs;
- bases: first/second/third player or null;
- matchup: batter, on-deck, in-hole, defensive pitcher;
- HR events: stable event ID, at-bat index, batter/pitcher IDs, inning, RBI, score, description, completion time;
- freshness: source timestamp, fetched time, stale flag, next-poll guidance.

MLB endpoint evidence:

- [linescore](https://statsapi.mlb.com/api/v1/game/823672/linescore)
- [v1.1 live feed](https://statsapi.mlb.com/api/v1.1/game/823672/feed/live)
- [boxscore](https://statsapi.mlb.com/api/v1/game/823672/boxscore)

Observed MLB responses advertise `max-age=10`. Phase 1 should poll the engine endpoint every 15 seconds for watched/open Live games and use a 10-second backend cache. MLB requires no API key in current use, but no official public quota/SLA was confirmed; do not call it guaranteed unmetered.

## Surface feasibility

- Compact score/inning/outs/base display: feasible now from linescore.
- Full diamond with active batter/pitcher: feasible.
- Game started: use MLB status, never scheduled-time inference alone.
- Matchup live: current batter ID match; optionally require current pitcher ID too.
- Pitcher still in/pulled: feasible with team/half context and embedded boxscore/current pitcher history.
- Pitch tracker: feasible but Phase 2 because pitch event/visual QA broadens scope.

Minimum Phase 1 surface:

```text
LIVE · TOP 5 · 1 OUT     AWAY 2 — HOME 1
[three base indicators]
AT BAT: Batter Name     P: Pitcher Name
```

Claude Design remains layout authority. The operator must select the required design skill before frontend implementation.

## Alert doctrine

Canonical triggers:

1. **Watched slip batter homered** — Phase 1.
2. **Watched batter coming up** — Phase 2, defined initially as the player entering MLB's `onDeck` slot.
3. **Top-cohort +EV game went live** — assessed as feasible but deferred. BEST COHORT is currently a client-only predicate, not a canonical emitted field; no backend duplication without separate ratification.

Watched Phase 1 state:

- current-date, non-removed legs owned by the authenticated user;
- ticket status `building` or active posted/deployed `pending`;
- exact numeric `player_id` and `game_pk` required;
- settled/void/final and legacy unidentified legs do not alert.

Fire-once HR identity:

```text
hr:{game_pk}:{atBatIndex}:{batter_id}
```

The initial poll seeds the high-water mark and does not replay old events as new toasts. Seen IDs are browser-local, user/date namespaced, and bounded in Phase 1.

## Phase plan

### Phase 1 — Minimum viable chain

- field-projected MLB live adapter;
- separate `/api/live/games/{game_pk}` contract;
- 10-second process cache and 15-second visible-tab client polling;
- nullable `legs.game_pk` migration;
- slip capture carries `game_pk`;
- owner-only `/api/my-tickets` exposes `player_id` and `game_pk`;
- compact live strip/mini-diamond;
- one in-app HR toast and small browser-local notification list;
- no worker, notifications table, Realtime, service worker, or push.

Protected/new-state flags:

- new/additive API contracts: **YES — audit-first**;
- Supabase migration: **YES — manual approval**;
- production frontend: **YES**;
- `/api/slate`, pipeline, cron, `pipeline_runs` cache: **NO TOUCH**;
- scoring, calibration, ranks, tiers, filters, EV, MAIN/JIG/HVY: **NO TOUCH**;
- new hosted service: **NO**.

### Phase 2A — Tracker + due-up

- rich diamond/live tracker and pitcher state;
- current/recent plate appearances and bounded pitch detail;
- on-deck transition alert;
- notification deep link to game/batter.

New service: no, if delivery remains open-app only.

### Phase 2B — Durable in-app + multi-user

- subscriptions/preferences and notifications tables with RLS;
- authenticated read/ack APIs;
- one live-game worker that polls each game once and fans out events;
- per-user/server idempotency and durable unread center;
- friend/group policy and privacy controls.

New infrastructure: **YES — Supabase schema/RLS plus separately governed always-on worker.** GitHub Actions cron is not alert-grade; its documented minimum is five minutes.

### Phase 3 — Browser/PWA push + optional cohort alert

- service worker, permission UX, PushManager/VAPID subscription, secure subscription storage, Web Push sender, click routing, PWA manifest/install path;
- closed-app delivery;
- optional cohort +EV live alert only after separate source-of-truth ratification.

New infrastructure/secrets: **YES.** See [MDN Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API).

## Ratification recommendation

Approve Phase 1 only, with these hard boundaries:

1. separate live endpoint; never append live state to `/api/slate` in Phase 1;
2. exact `game_pk` ticket identity is mandatory for posted-slip alerts;
3. HR is the only Phase 1 trigger;
4. delivery is in-app and visible-tab only;
5. poll only watched/open live games;
6. no push, notification table, multi-user worker, or cohort trigger;
7. no model, scoring, filter, tier, rank, EV, MAIN/JIG, or HVY changes.

This is the smallest honest proof of the live-state-to-alert payoff.
