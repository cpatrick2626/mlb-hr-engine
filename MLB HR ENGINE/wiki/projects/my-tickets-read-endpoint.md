# My Tickets Read Endpoint

**Date:** 2026-07-20  
**Status:** BUILT + LOCALLY VALIDATED WITH REAL JWT; live two-user proof pending; do not commit, push, or deploy

## Contract

`GET /api/my-tickets` requires `Depends(require_auth)` and derives ownership only from the verified JWT `sub`. It returns:

- all caller-owned tickets, including tickets with pending legs and tickets whose legs are settled or void;
- nested, non-removed legs with `player_name`, `team`, `opponent`, `pitcher`, `hr_result`, and `settlement_status`;
- normalized per-leg `game_status`: `Final`, `In Progress`, or `Scheduled` when game context is mapped;
- a per-inning runs grid and away/home runs, hits, and errors totals for every mappable leg date.

No odds are returned because odds were not reliably captured for this history surface. The endpoint does not fabricate them.

## Game Context

Game context uses the settlement resolver's existing retrying MLB Stats API client. It calls `/schedule` with:

```text
sportId=1
date=YYYY-MM-DD
hydrate=team,linescore
```

Calls are batched once per distinct leg date within a request, then games are matched by the stored team abbreviation and opponent when available. Scheduled games return an empty innings list and null totals. Every leg includes `game_status` and `linescore` keys. Ambiguous team/date matches, including uncaptured doubleheaders, and legacy legs without a stored team return `game_status: null` plus an empty linescore rather than attaching a potentially wrong game.

The response intentionally excludes `currentInning`, balls, strikes, outs, and all GUMBO/live-feed data.

## Isolation

This is a SELECT-only capture-layer endpoint. It reads only `tickets` and the confirmed nested `legs` relation. It does not read from, join to, or write any engine/scoring table. It does not modify `/api/ledger`, `api/settle_legs.py`, `/api/slate`, `config.py`, `pipeline.py`, MAIN probability, JIG scoring, HVY, odds, or CLV.

## Validation Snapshot

- 11 focused endpoint/contract tests pass for pending plus settled history across all dates, empty history, missing-sub and unauthenticated `401`, fixture-based cross-user isolation, scheduled empty linescores, exact resolver hydration, and per-date batching.
- A read-only live-data exercise returned 112 caller-owned tickets and 330 non-removed legs, including 9 pending and 321 settled/void legs.
- The live-data exercise made 18 schedule calls for 18 distinct leg dates, not one call per leg, and every returned leg included game-context keys.
- A completed 2026-07-19 game matched the MLB box score for both clubs' runs, hits, errors, and inning-run totals.
- A real signed browser session called the local endpoint successfully: HTTP `200` in 4.3 seconds, with 112 tickets, 330 legs, all required leg keys, final-game linescore context, no odds keys, and no live-feed fields. The JWT was passed only inside the browser runtime and was not printed or written to disk.
- A real unauthenticated local HTTP request returned `401 Not authenticated`.
- Only one real ticket owner exists in the current dataset, so live two-user isolation could not be exercised; fixture-based isolation passed.
- Full repository discovery ran 45 tests: all 11 My Tickets tests passed; three unrelated pre-existing failures remain (`app.py` syntax, missing `rapidfuzz`, and a pitcher-detail baseline mismatch). Focused tests and API `py_compile` pass.
