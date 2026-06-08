# Session: MAIN / JIG / JIG Builder Production Fix Validation
Date: 2026-06-08
Agent: Claude Code
Owner: Claude Code
Project: MLB HR ENGINE - OPERATIONS
Room: Obsidian Governance Update
Risk Class: LOW
Phase: Post-production validation documentation

## Scope

This session records completed production validation and fix history in Obsidian only.

No runtime files were modified.
No frontend files were modified.
No backend, API, pipeline, config, or `app.py` files were modified.
No commit was created.
No push was performed in this session.

## Production Surfaces Validated

- Frontend: `https://mlb-hr-engine-one.vercel.app`
- API: `https://mlb-hr-api.fly.dev/api/slate`

## Production Validation Result

- Page loaded: yes
- Data loaded: yes
- Crash-level JavaScript exception observed: no
- Nonblocking 404 observed: `https://mlb-hr-engine-one.vercel.app/.image-slots.state.json`
- App-load failure observed: no
- Data-load failure observed: no

## API Payload Snapshot

- MAIN count: `184`
- MAIN top 3:
  1. Luke Raley
  2. Dominic Canzone
  3. Casey Schmitt
- JIG count: `184`
- JIG top 3:
  1. Yordan Alvarez
  2. Collin Price
  3. Kyle Schwarber

## Live Production UI Validation

### MAIN Full Slate

- Batter count: `184 / 184`
- Top 3:
  1. Luke Raley
  2. Dominic Canzone
  3. Casey Schmitt
- Matches API `leaderboard_rows` top 3: yes

### JIG Full Slate

- Batter count: `184 / 184`
- Top 3:
  1. Yordan Alvarez
  2. Collin Price
  3. Kyle Schwarber
- Matches API `leaderboard_rows_jig` top 3: yes
- Mirrors MAIN: no

### JIG Builder

- Batter count: `184 / 184`
- Validation mode: PLAYER VIEW for ordered player-source validation
- Top 3:
  1. Yordan Alvarez
  2. Collin Price
  3. Kyle Schwarber
- Matches JIG-side source / API `leaderboard_rows_jig`: yes
- Mirrors MAIN: no

## Verdict

- MAIN/JIG Full Slate production fix validated: yes
- JIG Builder Phase A production fix validated: yes
- MAIN order live = API MAIN: yes
- JIG order live = API JIG: yes
- JIG Builder player-source live = API JIG, not MAIN: yes

## Commits Involved

1. `a4c4cc8` `fix(frontend): preserve main jig full slate order`
   - `frontend/assets/js/full-slate-matrix.js`
   - `frontend/assets/js/cfdd4178-a139-4f84-b282-b84f76971c49.js`
2. `08d7051` `fix(frontend): route jig builder to jig source`
   - `frontend/assets/js/jig-command.js`

## Push Result Recorded

- Push succeeded: `c1833c9..08d7051 main -> main`
- Final repo status after validation:
  - `main` synced with `origin/main`
  - working tree clean

## Technical Summary

### 1. Full Slate bug

- Stage already had separate `mainRows` and `jigRows`.
- Real bug was `FullSlateMatrix` forcing all incoming rows through default `hrprob` sort.
- Fix preserved incoming API order by default.
- Explicit user/operator sort still works.

### 2. Hydration bug

- Stage could miss `hrEngineDataLoaded`.
- `mainRows` and `jigRows` could remain `[]`.
- Fix added `hydrateRows()` so Stage seeds from globals on mount and still listens for `hrEngineDataLoaded`.

### 3. JIG Builder Phase A

- JIG Builder previously used `window.LEADERBOARD_ROWS`, meaning MAIN rows.
- Fix changed source priority:
  1. `window.SLATE_ROWS_RAW`
  2. `window.RAW_SLATE_ROWS`
  3. `window.LEADERBOARD_ROWS_RAW`
  4. `window.LEADERBOARD_ROWS_JIG`
  5. `window.LEADERBOARD_ROWS` only as commented degraded last-resort fallback
- No raw globals currently exposed, so JIG Builder Phase A uses JIG-side rows.
- This is a stopgap, not full raw-workspace doctrine compliance.

## Outstanding Future Work

### 1. JIG Builder Phase B

- Raw-workspace UI cleanup
- Hide or reduce formula-first language where needed
- Avoid implying JIG Builder is fully raw while it still uses JIG-side scored rows

### 2. JIG Builder Phase C

- HIGH-risk backend/API raw data surface audit if true raw unscored slate rows are required
- Current `/api/slate` exposes only `leaderboard_rows`, `leaderboard_rows_jig`, `slate_games`, and `generated_at`

### 3. JIG Top Targets

- Previously audited adjacent issue: JIG Top Targets hard-coded `mainRows`
- **RESOLVED** — fixed and validated in follow-on session [[2026-06-08-jig-top-targets-production-validation]]
- Commit: `9962d27` (generic vault backup message; do not rewrite history)

## Files Touched By This Documentation Session

- `MLB HR ENGINE/wiki/log.md`
- `MLB HR ENGINE/wiki/doctrine/build-log-and-spec-status.md`
- `MLB HR ENGINE/wiki/sessions/2026-06-08-main-jig-jig-builder-production-validation.md`
