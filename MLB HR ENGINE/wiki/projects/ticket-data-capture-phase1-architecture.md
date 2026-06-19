# Ticket/Data Capture Phase 1 Architecture
**Date:** 2026-06-17  
**Status:** PLAN ONLY — no Supabase tables created, no frontend code, no API changes  
**Operator sign-off required before any build**

> **Naming correction (2026-06-19):** This document was previously titled "Hermes Phase 1 Architecture." The capture-layer subsystem was mislabeled "Hermes" by an earlier session. "Hermes" actually refers to a separate, future NousResearch Hermes LLM plan (not yet specced). The capture layer is now "Ticket/Data Capture." Do not reuse "Hermes" for capture work.

---

## Operator Confirmation (2026-06-19) — Design Locked

Operator confirmed this design in session 2026-06-19. The following points are **locked** and must not be reinterpreted by a future build session without explicit operator re-authorization.

### Tap flow (locked)
- Operator taps tier icon on a player → currently opens FanDuel.
- NEW behavior: that tap ALSO adds the player as a leg to the CURRENT TICKET.
- Current ticket shows selected batters; each has a "–" button to remove a leg.
- "Ticket Complete" button = operator asserts "I placed this exact parlay on FanDuel." Sets `fd_deployed = true`.
- One ticket = one FanDuel parlay. After "Ticket Complete," next tap starts a NEW ticket.
- Per leg, capture at deploy time: player, date, opponent, pitcher, frozen engine snapshot (`model_prob`, `model_tier_rank`, `tier`), ticket linkage.

### Frozen snapshot (locked invariant)
Calibration needs the prediction AS IT WAS at deploy time. The snapshot is frozen at the moment of leg capture — later engine re-scoring must NOT overwrite it. This is the entire value of the capture layer.

### Live banner (locked — fun only, NOT data)
- Starts EMPTY. Populates as players are selected.
- Shows how the operator's picked batters are doing live; notifies on HR.
- **Collects NO data. Has NO calibration role.** Explicitly distinct from the ticket capture. Do not couple them.

### Hard invariant (locked)
Capture layer NEVER writes to MAIN prob, JIG score, tiers, ranking, pipeline, or scoring. It READS engine output to snapshot it; it NEVER writes back. Per AGENTS.md / LOOPS.md.

### Build instructions for fresh chat
BUILD IN A FRESH CHAT. Spans: frontend (ticket UI, tap handler, live banner), data layer (new Supabase tables), wiring change to tier-icon→FanDuel behavior.  
Fresh chat onboarding: read this doc, LOOPS.md, AGENTS.md, `wiki/architecture/supabase-schema.md`, `wiki/doctrine/feedback-loop-architecture.md`.  
Read-only audit of existing tap/icon + frontend surface FIRST, per LOOPS §1.  
Phased delivery: **1a** data layer → **1b** capture wiring → **1c** banner → **1d** settlement.

---

## Part 1 — Data Surface Verification (read-only findings)

### 1. `/api/slate` fields available at selection time

The board reads `/api/slate` (public, no auth). Each `leaderboard_rows` entry exposes:

| Field | Description |
|-------|-------------|
| `id` | player_id (stable) |
| `name`, `teamAbbr`, `bats` | identity |
| `model_prob` | MAIN Poisson probability (decimal, 4dp) |
| `hrprob` | same × 100, display % |
| `tier` | MAIN tier: APEX / ELITE / EDGE / SIGNAL / WATCH / COLD |
| `jigScore` | JIG tactical score (on `leaderboard_rows_jig`) |
| jig tier | derived client-side via `fsmJigTierLabel(jigScore)` |
| `prime`, `explosive`, `advantage`, `wildcard` | role flags (bool) |
| `quality` | matchup quality: ELITE / STRONG / AVG / WEAK / DANGER |
| `odds` | formatted American odds string (+400, -150, etc.) |
| `pitcher_name`, `pitcher_confirmed`, `pitcher_id`, `pitcher_hand` | pitcher identity |
| `pitcher_era`, `pitcher_whip`, `pitcher_k_pct`, `pitcher_bb_pct` | pitcher stats |
| `pitcher_barrel_allowed`, `pitcher_hh_allowed`, `pitcher_fb_allowed`, `pitcher_gb_allowed` | pitcher vulnerability |
| `gameId`, `gameStartUtc`, `gameStatus` | game context |
| `h2h_factor` | head-to-head historical factor |
| `fast`, `squp`, `blast` | signal flags |
| `pa`, `hr`, `hrpa`, `barrel`, `ev`, `la`, `pull`, `hh`, `xslg`, `xwoba`, `iso`, etc. | batter Statcast profile (40+ fields total) |

`slate_games` array (parallel, by `gameId`): `park`, `weather`, `hrFactor`, `wind`, `time`.

**Conclusion:** Every meaningful engine context field is available at selection time. A leg snapshot can capture the full operator signal picture without any new API calls.

### 2. Existing store grain

**`picks_log.csv`** columns:  
`date, model_version, player_id, player_name, team, opponent, pitcher, lineup_spot, model_prob_pct, market_prob_pct, ev_pct, edge_pct, american_odds, bet_dollars, park_factor, pitcher_factor, weather_factor, season_pa, recent_pa, confidence, score, streak_factor, barrel_pct, xslg, platoon_factor, statcast_source`

**`results.csv`** adds: `hr_result, profit_loss, notes`

Both are **pick-grain**: one row per player per date. No ticket grouping, no parlay structure, no stake, no sportsbook, no leg relationships. These stores track engine output — not operator betting decisions.

**Conclusion:** Ticket/Data Capture requires its own ticket-grain store. Reuse of existing stores is not possible without corrupting their grain and purpose.

### 3. Supabase table state

Confirmed tables in `api/cache.py`:
- `pipeline_runs` — one row per date, full JSON pipeline payload
- `picks` — qualified picks (model metrics, barrel, xslg, park/pitcher factors, confidence_tier, filter_reasons, source_tab, engine_version)
- `beta_invites` — invite codes
- `beta_users` — redeemed beta users

**No ticket, legs, or capture-related tables exist.** Supabase is the right home for the new schema: the board already reads from the API which reads from Supabase, adding two new tables (`tickets`, `legs`) is consistent with the existing pattern and requires no new data infrastructure.

### 4. Frontend selection state

`full-slate-matrix.js` holds exactly two pieces of state: `selGame` (game-filter dropdown value) and `pmOn` (pitch mix modal toggle). Both are display-only. **There is no concept of "selected player," "building a parlay," or captured legs anywhere in the existing board.** The capture UI is entirely net-new.

---

## Part 2 — Phase 1 Architecture

### A. Data Model (foundation)

Two tables. One ticket → many legs. Write path is capture-layer-only; zero overlap with engine scoring tables.

#### `tickets`
| Column | Type | Notes |
|--------|------|-------|
| `ticket_id` | UUID PK | auto-generated |
| `created_at` | timestamptz | server default now() |
| `date` | date | game date (not creation date — e.g. 2026-06-17) |
| `board` | text | `main` / `jig` / `combined` — which lens operator was using |
| `ticket_type` | text | `single` / `parlay` / `same-game-parlay` |
| `num_legs` | int | denormalized for quick queries |
| `stake` | numeric(10,2) | operator-entered dollars (manual entry Phase 1) |
| `odds_american` | int | ticket-level American odds (manual entry Phase 1, nullable for singles) |
| `sportsbook` | text | `fanduel` / `draftkings` / `betmgm` / etc. |
| `status` | text | `pending` / `won` / `lost` / `partial` / `void` |
| `notes` | text | optional operator notes |
| `settled_at` | timestamptz | nullable; set when status resolved |

#### `legs`
| Column | Type | Notes |
|--------|------|-------|
| `leg_id` | UUID PK | auto-generated |
| `ticket_id` | UUID FK → tickets | |
| `player_id` | text | MLB Stats API player_id (matches `/api/slate` `id` field) |
| `player_name` | text | display name at selection time |
| `team` | text | |
| `matchup` | text | e.g. "CIN vs DET" |
| `selected_at` | timestamptz | when operator captured this leg |
| `game_date` | date | game date for settlement lookup |
| `game_id` | text | `gameId` from /api/slate (e.g. `cin-det`) |
| — **Engine snapshot** — | | frozen at selection time |
| `model_prob` | numeric(6,4) | from `/api/slate` `model_prob` |
| `tier` | text | MAIN tier at selection |
| `jig_score` | numeric(6,4) | nullable (null if captured from MAIN-only view) |
| `jig_tier` | text | nullable |
| `role_prime` | bool | |
| `role_explosive` | bool | |
| `role_advantage` | bool | |
| `role_wildcard` | bool | |
| `matchup_quality` | text | ELITE / STRONG / AVG / WEAK / DANGER |
| `odds_american` | int | leg-level odds at selection (nullable if not displayed) |
| `pitcher_id` | int | nullable |
| `pitcher_name` | text | nullable |
| `pitcher_confirmed` | bool | nullable |
| `h2h_factor` | numeric(6,4) | nullable |
| — **Outcome** — | | filled by settlement |
| `leg_status` | text | `pending` / `hit` / `miss` / `void` / `scratched` |
| `hr_outcome` | bool | nullable; true = hit HR, false = did not |
| `settled_at` | timestamptz | nullable |

**Why two tables:** A ticket has one stake, one sportsbook, one status. Legs are N. Flattening N legs into one ticket row makes parlay composition unqueryable and forces array columns — wrong grain. 1:N is the correct model.

### B. Capture Flow (Phase 1 core)

The sequence that makes everything else possible:

```
Operator on Vercel board
  → browses /api/slate leaderboard (MAIN or JIG view)
  → taps/clicks to SELECT 1..N players as legs
      [net-new UI: selection indicator on each player row]
  → opens CAPTURE PANEL
      enters: stake, sportsbook, ticket_type, optional notes
      leg-level odds pre-populated from /api/slate if available, editable
  → taps RECORD TICKET
  → client POSTs to new endpoint: POST /api/tickets
      body: { ticket metadata } + legs array (each includes full engine snapshot)
  → API writes:
      INSERT tickets → get ticket_id
      INSERT legs (N rows) with ticket_id FK + engine snapshot frozen at this moment
  → board shows confirmation: "Ticket #abc123 recorded — 3 legs"
```

**Phase 1 constraint:** FanDuel ticket slip is not machine-readable. Manual entry of stake/odds/sportsbook is acceptable. The snapshot is the value — the ticket is the container.

**Engine snapshot integrity:** The leg writes exactly what `/api/slate` returned at selection time. No re-computation, no model calls. The snapshot is frozen read-only from the board payload.

**New API endpoint required (Phase 1b/1c):**
- `POST /api/tickets` — write a new ticket + legs (no auth friction in Phase 1, or reuse beta auth)
- `GET /api/tickets?date=` — read tickets for a date (for Live Banner)
- `GET /api/tickets/{ticket_id}` — read one ticket + legs (for Review shell)

These are additive endpoints. They do not touch `/api/slate`, `pipeline.py`, scoring, or existing tables.

### C. Read-Only Surfaces (Phase 1 shells)

These surfaces display captured data. They have no write path to the engine.

#### C1. Selected Legs Monitor / Live Banner
- Reads: `GET /api/tickets?date=today`
- Shows: active tickets for today → list of legs with player name, tier, role flags, game status, leg_status
- Ticket-alive logic: ticket is alive while all legs are `pending` or at least one is `hit` with remaining pending
- Phase 1 scope: display only. No live score polling. Operator manually settles.

#### C2. Ticket Review / Postgame Debrief Shell
- Reads: ticket + legs from Supabase, cross-referenced with `results.csv` or `hr_outcome` on the leg
- Shows: per-leg outcome, ticket result, engine snapshot vs outcome (model_prob vs actual hit/miss)
- Phase 1 scope: shell display. No statistical analysis, no pattern learning, no recommendations.
- Settlement dependency: leg `hr_outcome` is populated by the existing settlement pipeline (`pnl.settle_all_unsettled()` → `results.csv`). Ticket/Data Capture settlement queries results.csv or the `picks` Supabase table by `player_id + game_date` to flip `leg_status` and `hr_outcome`. **Do not rebuild settlement — reuse it.**

### D. What Phase 1 Explicitly Does NOT Do

- No learning or pattern analysis
- No parlay recommendations or auto-generation
- No engine scoring changes of any kind (model_prob, JIG score, tiers, formulas, calibration — untouched)
- No sportsbook API integration (FanDuel, DraftKings) — manual entry only
- No bet placement of any kind
- No CLV calculation at the ticket level (that is Phase 3+)
- No modification to `picks_log.csv`, `results.csv`, `pipeline_runs`, or the `picks` Supabase table
- No changes to `pipeline.py`, `config.py`, `app.py`, or any v4 engine module

### E. How Leg Outcomes Resolve

Settlement chain (existing, reuse as-is):

```
GitHub Actions daily_settle.yml
  → POST /api/ops/settle (X-Cron-Secret)
  → tracking/pnl.settle_all_unsettled()
  → writes hr_result to results.csv

Ticket/Data Capture settlement (additive, Phase 1c):
  → reads results.csv (or picks Supabase table) by player_id + game_date
  → for each pending leg: if match found → set hr_outcome, leg_status = hit/miss
  → updates ticket status (won/lost/partial/void) from leg outcomes
```

Ticket/Data Capture settlement can run as a background task on the same `/api/ops/settle` call (add a step), or as a separate `POST /api/ops/tickets-settle` endpoint. The dependency is one-way: Ticket/Data Capture reads from settlement output, never writes to it.

**Settlement must complete before Ticket Review shows outcomes.** This is expected — postgame debrief is not real-time.

### F. Phased Delivery Within Phase 1

Each step is independently shippable and testable:

| Step | Deliverable | Dependencies |
|------|-------------|-------------|
| **1a** | Supabase schema (`tickets` + `legs` tables) + `POST /api/tickets` endpoint + capture panel UI on board | None (pure additive) |
| **1b** | Live Banner: reads captured tickets, shows leg status | 1a: tickets must exist |
| **1c** | Postgame Review shell: reads settled outcomes, shows ticket result | 1a + settlement pipeline running |

Phase 1a is the unlock. 1b and 1c are readers — they only work once tickets exist.

### G. Risk + Boundaries

**Read-only-over-engine guarantee:**  
Capture tables (`tickets`, `legs`) are write-separate from all engine scoring tables. The only engine data the capture layer writes is the snapshot — a copy of `/api/slate` fields frozen at selection time. There is no shared write path between the capture layer and the engine.

**Validation gate (before any build):**  
- Confirm `tickets` and `legs` table names do not conflict with any existing Supabase table
- Confirm `POST /api/tickets` route does not shadow any existing route
- Confirm capture panel does not touch `window.SLATE_DATA`, `window.SLATE_GAMES`, or any existing board state — it only reads from them

**MAIN/JIG separation preserved:**  
The `board` column on `tickets` records which lens was active at capture. JIG scores on legs are nullable — a ticket captured from the MAIN view has no JIG data and that is correct. No blending.

**No ops risk in Phase 1a:** Schema creation and a new API endpoint are additive-only. Rollback = drop two tables + remove one route. Zero impact on existing pipeline, settlement, or board behavior.

---

## Cross-References
- `CLAUDE.md` §6 (Architectural Invariants) — engine pipeline untouched
- `CLAUDE.md` §7 (MAIN vs JIG Doctrine) — board column preserves lens identity
- `wiki/architecture/supabase-schema.md` — update after Phase 1a build
- `wiki/doctrine/room-governance.md` — Ticket/Data Capture is a new surface; may need room entry
- `wiki/sessions/2026-06-15-validation-and-capture-loop.md` — prior context on capture gap
