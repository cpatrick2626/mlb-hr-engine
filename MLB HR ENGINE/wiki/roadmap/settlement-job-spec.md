Status: SHIPPED — Phase S2 settlement resolver built + deployed; §6 dry-run gate passed; backlog settled; ledger live. Spec retained as design record. 2026-07-07.

> **SHIPPED 2026-07-07.** `api/settle_legs.py` resolver (dry-run + gated `--commit`) — commit `705fd6a`. `GET /api/ledger` (D5) — commit `f530567`. Durable capture-date fix (`leg_date`/`tickets.date` derived from `engine_generated_at` in ET) — commit `761105c`. All deployed to Fly; API healthy.
> - **§6 gate passed:** dry-run hand-checked against real box scores before the write path was built; first `--commit` was single-date (2026-07-06), verified row-by-row in Supabase, idempotency proven (re-run wrote 0 rows).
> - **Backlog settled** across 7 dates: 89 settled + 1 void ≈ 90 outcomes (ledger meta: MAIN 72 settled / 1 void, JIG 17 settled / 0 void).
> - **Decided rules held up in practice:** void keeps `hr_result = NULL` (§3), date-aggregate doubleheader handling, `removed=true` never settled, unresolvable IDs report-only — no rule needed revision after live runs.
> - **Still deferred:** the cron/ops automation (`POST /api/ops/settle-legs` + GH Actions wiring, §4 trigger 1) is NOT wired — settlement runs are manual `--commit` only so far.
> - See also: [[settlement-truth]] (doctrine earned during this build).

# Settlement Job — Design Spec (Phase S2 / D3–D5)

Companion to [[strategy-section-spec]] §4 (settle→learn loop). Constrained by [[supabase-schema]] and the operator decisions recorded in strategy-section-spec §9. This job is the data source the entire feedback loop depends on: **wrong settlement silently poisons calibration and is worse than no settlement.** Every design choice below optimizes for correctness over coverage — when in doubt, the job leaves a leg `pending` and reports it, rather than guessing.

**Decided rules baked in (not re-litigated here):**
- Void rule (§9 Q4): player with ≥1 PA in the game settles (`hr_result` 0 or 1); DNP / not-in-lineup / postponed / cancelled = void; suspended game settles when officially completed.
- Attribution is per-user via `tickets.user_id`. The ledger reports on LOGGED picks; `fd_deployed` distinction is future work (D6).

---

## 0. Ground truth (verified against live code 2026-07-06)

| Fact | Source |
|---|---|
| `legs` columns: `leg_id` PK, `ticket_id` FK, `player_id` text, `player_name`, `team`, `opponent`, `pitcher`, `leg_date` date, `model_prob` numeric, `board`, `tier`, `model_tier_rank`, `engine_generated_at`, `market_odds_american`, `market_prob`, `signal_snapshot` jsonb, `removed` boolean (soft delete), `hr_result` smallint, `settlement_status` text DEFAULT `'pending'`, `settled_at` timestamptz | `api/cache.py add_leg()/remove_leg()`, `supabase/migrations/005`, `006` |
| ⚠ Schema-doc drift: wiki says PK is `id`; live code reads/writes `leg_id`. Wiki omits `player_name`, `opponent`, `tier`, `model_tier_rank`, `engine_generated_at`, `removed`. | `api/cache.py:216,244,293` vs `wiki/architecture/supabase-schema.md` |
| ⚠ Status-value drift: migration 005 comments say `hr_result -1=void` and `settlement_status pending/won/lost/void`; wiki says `pending/settled/void`. Comments only — no CHECK constraint exists. §3 pins the canonical convention. | `supabase/migrations/005_add_leg_calibration_fields.sql:7,10` |
| `legs.player_id` = slate row `id` = `p.get("player_id") or player_name.lower().replace(" ", "-")` — **MLBAM person ID as text, with a name-slug fallback** | `api/main.py:484` (`_build_slate_payload`) |
| Pipeline `player_id` originates from MLB Stats API schedule/lineup hydration (`p.get("id")` on lineup entries) — same namespace MLB Stats API expects | `clients/mlb_stats.py:226–234 (_parse_lineup)`, `get_today_schedule` |
| Existing MLB Stats API client: public, no key, `statsapi.mlb.com/api/v1`, session + retry/backoff, 404/403 short-circuit | `clients/mlb_stats.py:_get` (lines 103–118) |
| Prior settlement art exists: `tracking/pnl._mlb_hr_result()` settles the CSV pick tracker via per-player gameLog; triggered by `POST /api/ops/settle` (X-Cron-Secret) → GH Actions `daily_settle.yml` | `tracking/pnl.py:609–625`, `api/main.py:120–146` |
| Supabase write pattern to reuse: `api/cache.py` `_client()` (service key), `.table("legs").update({...}).eq("leg_id", ...)` | `api/cache.py` |

**Why the prior art is NOT copied as-is:** `pnl._mlb_hr_result` reads the player's gameLog and returns the *first* split matching the date — on a doubleheader day it silently reads one of two games; it can't distinguish DNP from postponed from suspended (all look like "date not in log"); and it never sees PA=0 appearances distinctly. Fine for a retryable CSV tracker; not good enough for the calibration source of truth. §2's boxscore-based algorithm supersedes it for legs (the CSV tracker keeps its own path, untouched).

---

## 1. Identity resolution (highest-risk section)

### 1.1 The identifier and the join

- **What a leg stores:** `legs.player_id` (text). In the normal path this is the **MLBAM person ID** (e.g. `"592450"`) — the exact integer namespace MLB Stats API uses for `/people/{id}` and boxscore keys (`"ID592450"`). It is NOT a Statcast-only or internal ID; Baseball Savant also keys on MLBAM IDs, so no cross-namespace mapping is needed.
- **The trap:** `api/main.py:484` falls back to a **name slug** (`"kyle-schwarber"`) when the pipeline row lacks `player_id`. `add_leg` also accepts `player_id=None` (older callers). So the join is: `int(legs.player_id)` **if it parses as an integer**; otherwise the leg is *unresolvable by ID* and must never be guessed.
- **Join:** `player_id (MLBAM int)` → all boxscores for games on `leg_date` → `teams.{home,away}.players["ID{player_id}"].stats.batting` → `homeRuns`, `plateAppearances`.

### 1.2 Everything that can go wrong, and the handling

| # | Failure mode | Detection | Handling |
|---|---|---|---|
| 1 | **Non-numeric `player_id`** (name-slug fallback or NULL) | `int()` parse fails / NULL | **Never name-match automatically.** Leave `pending`; report in the job summary as `unresolvable_id` with leg_id + player_name for operator review. (Open question Q2: whether to add a manual-resolution path.) |
| 2 | **Doubleheader** — two games, same `leg_date` | schedule returns 2 gamePks for the player's team | Legs carry no game reference, only `leg_date`. **Recommended: aggregate the date** — PA summed across both final games; `hr_result=1` if ≥1 HR in either. Rationale in §4; flagged as open question Q1 because FanDuel grades per-game. If one game is final and the other isn't, **defer** (don't settle on partial-day data). |
| 3 | **Player traded / team changed** since pick time | `legs.team` no longer matches the roster | Immune by design: the algorithm scans **all** boxscores on the date for the person ID rather than routing through `legs.team`. MLBAM IDs are globally unique. `legs.team` is used only as a logged sanity cross-check (mismatch → settle normally but flag `team_drift` in the report). |
| 4 | **Name collisions** (two "Will Smith"s) | n/a | Non-issue on the ID path — person IDs are unique. This is exactly why failure mode 1 must never fall back to name matching. |
| 5 | **Namespace mismatch** (ID that isn't MLBAM) | ID absent from every boxscore AND `/people/{id}` returns empty | Leave `pending`, report as `id_not_found`. Do not void — absence of evidence isn't DNP evidence if the ID itself is suspect. |
| 6 | **No game found for `leg_date`** (off-day, bad leg_date, all-star break) | schedule returns 0 games, or 0 games involving any team | If the schedule call itself succeeded and the date has games but none contain the player → treat as DNP (row 7). If the date has **no MLB games at all** → suspicious leg_date; leave `pending`, report `no_games_on_date`. |
| 7 | **On roster but DNP** (benched, scratched, IL) | player absent from all boxscore player maps, OR present with `plateAppearances = 0`, and all games on the date are Final | **Void** (decided rule: <1 PA = void). Both shapes occur: scratched players sometimes appear in the boxscore with all-zero stats, sometimes not at all. Only void once **every game that date is Final** — otherwise defer. |
| 8 | **Postponed / cancelled** | schedule `detailedState` ∈ {Postponed, Cancelled} | **Void.** The makeup game lands on a different calendar date and will not be matched to this leg (the leg was priced against the original slate; decided rule voids it). |
| 9 | **Suspended, not yet completed** | `detailedState` contains Suspended / game not Final | **Defer** — leave `pending`. Daily re-runs pick it up when the game goes Final (MLB credits suspended-game stats to the original gamePk/date, so the boxscore finalizes in place — the settle-on-completion rule falls out naturally). |
| 10 | **API/network failure mid-run** | request exception after retries | Leave affected legs `pending`; job is idempotent (§5), next run retries. Never write a result derived from a partial/failed response. |
| 11 | **Stats correction after settlement** (official scorer changes a call) | not detectable by the job | Accepted residual risk; settle only after a game is Final (not Live), which is when scorer changes are rarest. No auto re-settlement — a settled row is immutable (§5). Operator can manually re-open by setting status back to `pending`. |

### 1.3 Resolution algorithm (recommended)

```
for each leg_date D with pending legs (grouped):
  schedule = GET /schedule?sportId=1&date=D            # 1 call
  games    = schedule.dates[date==D].games             # gamePk, status per game
  final    = [g for g in games if abstractGameState == "Final"
              and detailedState not in (Postponed, Cancelled)]
  boxscores = { g.gamePk: GET /game/{gamePk}/boxscore  # 1 call per final game (~≤15/day)
                for g in final }
  # per-date person index: pid -> [(gamePk, PA, HR), ...] across ALL final boxscores
  for each pending leg on D:
    pid = parse_int(leg.player_id)  → fail ⇒ report unresolvable_id, skip
    apps = person_index.get(pid, [])
    team_games_pending = any non-final, non-postponed/cancelled game
                         involving a team the player appeared for OR leg.team
    if apps and sum(PA) >= 1:
        if team_games_pending: defer                    # doubleheader half-played etc.
        else: settle  hr_result = 1 if sum(HR) >= 1 else 0
    elif all games on D are terminal (Final/Postponed/Cancelled):
        void                                            # DNP / scratch / PA=0 / date fully postponed
    else:
        defer                                           # something on D still live/suspended
```

Settled write per leg (single UPDATE, §5): `hr_result`, `settlement_status`, `settled_at = now()`. Nothing else.

---

## 2. MLB Stats API integration

- **Endpoints** (all public, no auth, no key, no documented hard rate limit):
  - `GET /api/v1/schedule?sportId=1&date=YYYY-MM-DD` — gamePks + `status.abstractGameState` / `status.detailedState` / `status.codedGameState` per game. One call per settlement date.
  - `GET /api/v1/game/{gamePk}/boxscore` — `teams.home.players` / `teams.away.players` keyed `"ID{personId}"`, each with `stats.batting.homeRuns` and `stats.batting.plateAppearances`. One call per final game (≈15/day max; a 7-day backlog ≈ 8 schedule + ~105 boxscore calls — trivial).
- **Batching:** grouping by date means cost scales with *dates × games*, not with leg count. A day with 200 legs costs the same ~16 requests as a day with 2.
- **Reuse:** follow `clients/mlb_stats.py`'s `_get()` pattern (shared session, 3-try exponential backoff, 404/403 short-circuit, 15s timeout). The settlement module needs exactly two thin functions (`schedule-for-date`, `boxscore-for-game`); `get_today_schedule()` is not reused directly because it **skips Final games** (line 175) and applies today-slate parsing the job doesn't want. Recommended: add the two functions to the new settlement module itself (not to `clients/mlb_stats.py`) so pipeline client code is untouched — zero blast radius into the engine's data layer. A polite fixed delay (~0.3–0.5s) between boxscore calls mirrors existing client etiquette.
- **Field verification is part of the gate:** exact response shapes (`plateAppearances` presence, status strings like `"Suspended: Rain"`, `"Completed Early"`) are confirmed against real past dates during the dry-run phase (§6) before any write mode exists.

---

## 3. Void/settle decision table

Canonical value convention (pins the migration-005-comment vs wiki drift; **recommendation, operator confirms**):
- `settlement_status` ∈ `'pending' | 'settled' | 'void'` (matches wiki + column DEFAULT; the migration comment's `won/lost` was never implemented anywhere).
- `hr_result` ∈ `1 | 0 | NULL`. **Void rows keep `hr_result = NULL`** (not `-1`): the calibration triad (`model_prob` × `hr_result` over settled rows) stays clean with no sentinel filtering; voids are excluded by `settlement_status` alone. Migration 005's `-1=void` comment should be corrected in a future doc pass — no schema change needed (comment only, no constraint).

| Real-world state on `leg_date` | Decision | Writes |
|---|---|---|
| Game Final, player ≥1 PA, ≥1 HR (summed across date) | **settle-as-1** | `hr_result=1`, `'settled'`, `settled_at` |
| Game Final, player ≥1 PA, 0 HR | **settle-as-0** | `hr_result=0`, `'settled'`, `settled_at` |
| Game(s) Final, player in boxscore with 0 PA (late defensive sub, pinch-runner never batting, listed scratch) | **void** | `hr_result=NULL`, `'void'`, `settled_at` |
| Game(s) Final, player absent from every boxscore (DNP / not in lineup / not rostered) | **void** | same as above |
| Postponed (no play that date) | **void** — makeup game is a different slate | same |
| Cancelled | **void** | same |
| Suspended, not officially completed | **defer** — stays `pending`, retried daily | none |
| Suspended, later officially completed (incl. "Completed Early") | **settle** by PA/HR from the finalized boxscore (stats credit the original date) | as rows 1–3 |
| Doubleheader, both games Final | **settle on date-aggregate** (recommended — Q1): PA and HR summed across both games | as rows 1–3 |
| Doubleheader, one game Final, one not | **defer** until both terminal | none |
| Game in progress / not started (job ran early, or leg_date is today) | **not selected** — selection requires `leg_date < today` (US/Eastern); if selected and live anyway → defer | none |
| Pending leg older than a staleness horizon with still-unresolvable state | **flagged to operator** — see Q3 (auto-void mirrors `pnl.py`'s 7-day rule, or stays manual) | none until decided |

States the decided rule doesn't crisply cover → operator open questions (§8): doubleheader aggregation semantics (Q1), tie games / games called early that are official (recommend: if MLB marks it Final, it settles — PA rule applies unchanged; flagged for confirmation under Q1's umbrella).

---

## 4. Job shape & scheduling

- **Home:** new module `mlb_hr_engine_v4/api/settle_legs.py` — an `api/cron.py` sibling, matching the existing ops pattern (`/api/ops/settle` + GH Actions `daily_settle.yml` already do exactly this for the CSV tracker). Not `scripts/ops/` because it needs the Supabase service client and runs headless in CI, like `api/cron.py`.
- **Triggers (both):**
  1. **Cron:** extend the existing overnight GH Actions settle workflow with a second step calling a new `POST /api/ops/settle-legs` endpoint (X-Cron-Secret gated, background task — same shape as `ops_settle`). Overnight ET guarantees all games are Final.
  2. **Manual/local:** `python -m api.settle_legs [--date YYYY-MM-DD] [--dry-run|--commit]` from inside `mlb_hr_engine_v4/` (cwd rule per CLAUDE.md §11; reads `.env` like `api/cron.py`). **`--dry-run` is the default; `--commit` is explicit.**
- **Selection:** `settlement_status = 'pending' AND leg_date < today AND removed = false`, look-back window default 14 days (older stragglers are the Q3 staleness question). `removed=true` legs are never settled (they weren't picks; see Q4).
- **Idempotency:**
  - Re-running is safe by construction: only `pending` rows are selected; a `settled`/`void` row is never re-selected and **no code path updates a non-pending row** — a settled result can never flip.
  - Each leg is one `UPDATE legs SET hr_result=…, settlement_status=…, settled_at=… WHERE leg_id=… AND settlement_status='pending'` (the status guard in the WHERE makes even a concurrent double-run write-once).
  - No inserts, no deletes, no other columns — `WRITE-SEPARATE` like `add_leg`.
- **Failures / partial days:** per-leg writes mean a mid-run crash leaves the remainder `pending` for the next run. Deferred states (suspended, half-played doubleheaders) resolve on subsequent daily runs automatically. The job ends with a structured summary log: `{settled_1, settled_0, void, deferred, unresolvable_id, id_not_found, no_games_on_date, team_drift}` — the operator-facing health signal.

---

## 5. Ledger read endpoint (D5)

Read-only; JWT-gated (`require_auth`); `user_id` from the token, never from the query string.

```
GET /api/ledger?lane=main|jig&from=YYYY-MM-DD&to=YYYY-MM-DD
```

- **Base query:** `legs` joined to `tickets` on `ticket_id` where `tickets.user_id = <jwt sub>` and `legs.removed = false` and `settlement_status IN ('settled','void')`, filtered to `board = lane`. **`lane` is required — there is no merged view** (per-lane grading doctrine; a combined view is a doctrine change, not a query param).
- **Response shape:**
  - `legs`: settled legs with `leg_id, leg_date, player_name, board, model_prob, tier, hr_result, settlement_status, settled_at, signal_snapshot` (raw — the UI derives display).
  - `buckets`: server-computed hit-rate rollups over **settled (non-void)** legs only, each as `{n, hits, hit_rate}`, keyed by the snapshot dimensions from strategy-section-spec §4.3: `aei.verdict`, `aei.alignment`, `dot_state`, `rank_signal_used`, `tier`, `surface`, `role_slot`. Legs with `signal_snapshot IS NULL` roll into an explicit `no_snapshot` bucket — never silently dropped.
  - `meta`: `{lane, total_settled, total_void, total_pending, small_sample: total_settled < 200}` — the UI's honesty banner (SMALL SAMPLE band, "no calibration change below n≥200") keys off `small_sample`; the endpoint reports, it never tunes.
- Attribution/scope note in the response docstring: figures cover **logged** picks; `fd_deployed` distinction is D6 future work.

---

## 6. Verification plan — the gate before any real write

Correctness is proven **before** the job is allowed to write `hr_result`:

1. **Dry-run mode is the only mode that exists at first build.** `--dry-run` performs the full resolve pipeline and emits a table (stdout + CSV under `reports/`): `leg_id, leg_date, player_name, player_id, board, would_status, would_hr_result, evidence (gamePk(s), PA, HR), flags`. Zero database writes — asserted by construction (no update call is reachable in dry-run).
2. **Known-slate hand-check:** run dry-run against one or more past dates that have real logged legs (the 2026-07-06 validation rows — Caglianone, Schwarber — plus whatever has accumulated). Operator hand-checks every proposed row against actual box scores (MLB.com / Baseball Reference). **Must include at least:** one HR hit, one 0-HR game, one DNP, and — if the calendar provides them — one doubleheader and one postponement. If real legs don't cover these, dry-run a synthetic check by pointing the resolver at known historical player/date pairs (read-only; nothing logged).
3. **Cross-check vs prior art:** for overlapping dates/players, compare dry-run output against `results.csv` outcomes from the CSV tracker. Disagreements are investigated, not averaged.
4. **Edge-state probe:** during dry-run development, capture and record actual API status strings for postponed/suspended/cancelled games from the current season into the spec's decision table (verifying §3's assumptions about `detailedState` values).
5. **Operator sign-off gate:** only after the operator approves a hand-checked dry-run does `--commit` get built/enabled. First live run targets a **single date**, is verified row-by-row in Supabase, and only then does the cron trigger get wired.
6. **Standing safety:** the endpoint and cron path run the same code as `--commit`; the dry-run flag is honored end-to-end so the operator can re-audit any date at any time without writes.

---

## 7. Blast radius + phasing

**Files touched at build time (nothing touched by this spec):**

| Surface | Change | Notes |
|---|---|---|
| `mlb_hr_engine_v4/api/settle_legs.py` | new module (resolver + CLI) | net-new |
| `mlb_hr_engine_v4/api/main.py` | add `POST /api/ops/settle-legs` + `GET /api/ledger` | additive endpoints only |
| `mlb_hr_engine_v4/api/cache.py` | add `select_pending_legs()`, `settle_leg()`, `ledger_query()` helpers | additive; reuses `_client()` |
| GH Actions settle workflow | second step calling the new endpoint | additive |
| Wiki: this spec, supabase-schema.md (drift fixes from §0), log.md | doc gate | |

**Explicitly NOT touched:** `config.py`, `pipeline.py`, `engine/`, `output/`, `clients/` (settlement's two API calls live in its own module), Streamlit surfaces, frontend trees, MAIN/JIG scoring, tiers, `model_prob`, `signal_snapshot`, `board`, any snapshot content, the CSV tracker path (`tracking/pnl.py` untouched), migrations (no schema change needed — all three target columns exist).

**Write surface (hard invariant):** the job writes **only** `legs.hr_result`, `legs.settlement_status`, `legs.settled_at`, and only on rows currently `pending`. The ledger endpoint writes nothing.

**Phasing:**
- **Buildable immediately on spec approval:** settlement module in dry-run-only form + verification runs (§6 steps 1–4). No writes exist yet, so risk is zero.
- **Gated on dry-run sign-off:** `--commit` write path, ops endpoint, cron wiring (§6 step 5).
- **Buildable in parallel, useful only after settlement runs:** ledger endpoint (D5) — returns honest empty aggregates until settled rows exist.
- **Blocked / out of scope:** `fd_deployed` (D6), market-odds sourcing (D7), any ledger UI, any calibration or threshold change (n≥200 rule stands), any auto-tuning.

---

## 8. Open questions for operator review

1. **Doubleheader semantics (highest leverage).** Legs carry only `leg_date`, no game reference. Recommended: settle on the **date aggregate** (≥1 PA across both games settles; HR in either game = 1). This maximizes correct attribution given what's stored — but FanDuel grades HR props **per game**, so a real slip on game 1 that voided (DNP) while the player homered in game 2 would grade differently at the book than in our ledger. Alternative: void all doubleheader legs (conservative, loses ~scarce data). Doubleheaders are rare enough (~30–50 dates/season league-wide) that either is livable — but the choice defines ledger truth. *Also confirm under this umbrella: any game MLB marks Final (incl. shortened/official early-ended games) settles by the PA rule.*
2. **Name-slug / NULL `player_id` legs.** Recommended: leave `pending` + report for manual operator resolution (never auto name-match). Confirm, or authorize a one-time assisted backfill where the job proposes an MLBAM ID per slug and the operator approves each before it's used.
3. **Staleness horizon.** Legs still `pending` after N days (unresolvable IDs, weird states). Mirror `pnl.py`'s auto-void-after-7-days, or keep indefinitely-pending + operator report? Recommended: report-only for the first weeks of live running; add auto-void later if the pending queue actually accumulates.
4. **`removed = true` legs.** Recommended: never settle (they were retracted, not picked). Confirm — the alternative (settle them anyway as shadow data) blurs what "logged pick" means in the ledger.
5. **Value convention sign-off** (§3): `settlement_status ∈ pending/settled/void`, void keeps `hr_result = NULL`. This contradicts migration 005's *comments* (`-1`, `won/lost`) but matches the wiki, the column default, and keeps the calibration triad sentinel-free. Confirm so the drifted comments can be corrected in the next doc pass.
6. **Ledger bucket set** (§5): confirm the seven snapshot dimensions, or trim for v1 (minimum viable: `aei.verdict`, `alignment`, `rank_signal_used`, `tier`).

---

## Cross-refs

- [[strategy-section-spec]] §4 (settle→learn), §4.4 (D3–D5), §5 (snapshot shape), §9 (decided rules)
- architecture/supabase-schema.md — legs/tickets (needs the §0 drift fixes)
- `tracking/pnl.py` — prior settlement art (CSV tracker; superseded pattern for legs, path untouched)
- `api/cron.py`, `api/main.py` `/api/ops/settle` — the ops/cron pattern this job mirrors
