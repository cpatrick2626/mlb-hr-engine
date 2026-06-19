# Session Handoff — 2026-06-18

## Current State (verified this session)
- HOME@HOME matchup labels + gameId grouping: FIXED, deployed,
  cache-flushed, VERIFIED in production. Root cause: api/main.py
  derived `away` from `opponent`, which is "other team from batter's
  perspective" — collapsed to home===away for away batters. Fixed at
  both sites (L360-364 leaderboard gameId; L461-482 slate_games) with
  order-independent derivation (away = own team unless own IS home,
  else opponent). Verified: 8 clean matchups, NYM@PHI correct, zero
  self-paired gameIds. Model/calibration data NOT affected (computed
  from home_team/pitcher, never the away field).
- Board blank-on-empty: FIXED, deployed. Root cause: globals only
  seeded on non-empty API data (a6cd8ef6:39) → empty pipeline rendered
  silent blank. Fix: three states — LOADING / PIPELINE PENDING (amber)
  / BOARD OFFLINE (red, fetch failed), operator-actionable copy.
  hydrateRows + MAIN/JIG source-ownership untouched.
- "No Time Gate" toggle: DONE — was a dead stub (state tracked, counted
  as active filter, applyRoomFilters never read it). Hidden, dropped
  from active-filter count. Commit 2bfc7db. Frontend has NO hour-cutoff
  equivalent to Streamlit cutoff_utc_hour — wiring deferred (overlaps
  Exclude Started / Include Live; needs own audit).
- CRON_SECRET: reset to a new strong value this session (old value was
  unrecoverable). Stored by operator. Cache flush via
  POST /api/pipeline/run now authenticates correctly.
- [CARRIED FROM PRIOR — re-verify, not confirmed this session:]
  Tracking pipeline fix, Phase 2 CLV reconcile (committed not deployed),
  advisory bench (4 seats), Feedback Loop blueprint, Ticket/Data Capture Phase 1
  architecture. These predate this chat; confirm against vault before
  treating as current.

## Open Threads (next sessions)
1. Board cold-load HANG (distinct from the blank, which is fixed):
   cache-miss forces synchronous full pipeline on the request thread →
   3-4min hang. Cold-start is NOT the cause (~2-5s only). Real fix:
   background the compute on cache-miss + frontend loading/poll state.
   The empty-state fix shipped today handles the BLANK, not the HANG.
   Do in a calm window, never pre-game.
2. Pick LOGGING watch: no logged picks Jun 16-17. Confirm live-pipeline
   pick logging fires on game days (separate path from settlement).
3. Ticket/Data Capture Phase 1 BUILD: capture layer (tickets+legs schema, frozen
   engine snapshot per leg), own Supabase tables, write-separate from
   engine. Build in fresh chat / sandbox.
4. "No Time Gate" wiring (deferred, optional): only if a frontend
   hour-cutoff is genuinely wanted — audit overlap with existing time
   toggles first.

## Repo invariant
- MLB HR Engine repo root: C:\MLB HR Engine\mlb-hr-engine-master
  (remote: https://github.com/cpatrick2626/mlb-hr-engine.git)
- Engine code lives in subfolder: mlb_hr_engine_v4/
- Production frontend (Vercel board): ROOT-level frontend/ — NOT
  mlb_hr_engine_v4/frontend/
- Git + flyctl deploy run from repo ROOT (where fly.toml lives)
- NEVER use: C:\flag game (contaminated) or C:\ronans-flag-game (separate)
- Pre-flight every task: git rev-parse --show-toplevel must =
  C:/MLB HR Engine/mlb-hr-engine-master

## Key invariants (do not violate)
- Read-only audit → operator review → authorized fix. Operator runs deploys.
- Agents/Hermes never touch MAIN prob, JIG score, tiers, calibration,
  ranking, pipeline, scoring.
- GitHub push does NOT auto-deploy. API needs flyctl deploy + cache
  flush (POST /api/pipeline/run, X-Cron-Secret). Frontend auto-builds
  on Vercel from push.
- COMMIT BEFORE DEPLOY. `flyctl deploy` ships the working tree, NOT
  HEAD — deploying uncommitted code leaves production ahead of git and
  a clean checkout will silently regress. Sequence: commit → push →
  deploy → cache flush. (Learned 2026-06-18: away-fix + empty-state
  were deployed before commit; caught and reconciled in 371e071.)
- config.py = threshold source of truth. pipeline.py = canonical assembly.
