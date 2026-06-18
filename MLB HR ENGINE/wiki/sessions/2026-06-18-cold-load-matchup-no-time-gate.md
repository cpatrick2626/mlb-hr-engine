# Session: Cold-Load Diagnostic / Matchup Label Diagnostic / No Time Gate Hidden
**Date:** 2026-06-18  
**Agent:** Claude Code  
**Room:** RUNTIME & STABILITY COMMAND (08)  
**Scope:** Items 1–2 read-only diagnostics; Item 3 fix + commit; Item 4 cold-load empty-state fix

---

## ITEM 1 — COLD-LOAD BLANK BOARD (diagnostic, read-only)

### Symptom
Hard cold load (no session_state / cleared cache) renders blank board — no rows, no cards, no spinner.

### Investigation Findings

**A. Console exceptions on initial render:**  
No JS exception. `rows.map(fsmAdjustRow)` on `[]` returns `[]`; `pool = [].filter(...)` returns `[]`. FullSlateMatrix renders with 0 rows — blank but no throw. If fetch fails, `a6cd8ef6:50` logs `console.warn("HR Engine API fetch failed:", err)` — silent to user, no UI error state.

**B. Event timing — does `hrEngineDataLoaded` fire before Stage mounts?**  
No. React runs child effects before parent effects. Stage (`cfdd4178:103`) attaches listener first. MasterDashboard (`a6cd8ef6:35`) then starts fetch (async). Fetch resolves after listener is attached. No missed-event on cold load.

**C. Globals at hydrateRows() call time:**  
`70f6ea6c:3-5` seeds all three globals as empty arrays before React mounts:
```js
window.LEADERBOARD_ROWS = [];
window.LEADERBOARD_ROWS_JIG = [];
window.SLATE_GAMES = [];
```
When `hydrateRows()` runs on Stage mount (`cfdd4178:102`), all globals are `[]`. JIG source chain (`jig-command.js:10-16`): `LEADERBOARD_ROWS_RAW` (undefined) → `LEADERBOARD_ROWS_JIG` (empty) → `LEADERBOARD_ROWS` (empty). All empty.

**D. Listener + missed-event guard:**  
Listener attached before event fires (see B). Missed-event guard EXISTS — `hydrateRows()` called on mount (cfdd4178:102) — would catch populated globals if event somehow fired early. But globals are always empty on cold mount (see C), so the guard never provides data on first call.

### Root Cause

**Primary:** `a6cd8ef6:39` conditional guard:
```js
if (data.leaderboard_rows?.length) {
  window.LEADERBOARD_ROWS = data.leaderboard_rows;
}
```
Only updates global when `leaderboard_rows` is non-empty. If API returns empty array or field is absent, global stays `[]`. Event still fires (line 48), `hydrateRows()` runs, reads `[]`, `setMainRows([])` — board stays blank.

**Secondary:** No loading state in UI. Initial render is always blank (no spinner, no skeleton, no "Loading…"). Board only populates when fetch resolves with non-empty data.

**Silent error path:** Fetch failure (`a6cd8ef6:50`) logs only `console.warn` — no retry, no UI indication.

### Classification
**(1) Globals-never-seeded** — not a race condition. Cause is API returning empty/absent `leaderboard_rows` (pipeline hasn't run, API error, or off-season blank slate), combined with absence of loading state. The timing architecture is correct; the data contract is the failure point.

### Cross-reference
See Item 2 — independent root cause (different payload field). The hydration path (`a6cd8ef6`) is shared but the bugs are in separate API fields (`leaderboard_rows` vs `slate_games.away`).

### Key File/Lines
- `a6cd8ef6-2b53-4016-a340-66b69a8928bd.js:35-50` — fetch, conditional guard, silent catch
- `cfdd4178-a139-4f84-b282-b84f76971c49.js:95-105` — hydrateRows, mount call, listener
- `70f6ea6c-2a16-47ac-908c-807ee1421ab6.js:3-5` — global init to empty arrays

### Status
Diagnostic complete. No fix proposed. Awaiting operator review before any cold-load fix packet.

---

## ITEM 2 — HOME @ HOME MATCHUP LABELS (diagnostic, read-only)

### Symptom
Matchup labels render `HOME @ HOME` (PHI@PHI, TEX@TEX, ATL@ATL) on both chip strip and player rows. Correct format: AWAY @ HOME.

### Investigation Findings

**A. Label builder locations:**

| Location | File | Line | Expression |
|----------|------|------|-----------|
| Game-nav chip strip | `full-slate-matrix.js` | 1080 | `{g.away} @ {g.home}` via `getFSMGames()` |
| Game dropdown select | `full-slate-matrix.js` | 1017 | `{g.away} @ {g.home} · {g.time}` |
| Player row sub-label | `full-slate-matrix.js` | 335 | `{game.away}@{game.home}` |
| Card meta line | `full-slate-matrix.js` | 551 | `` `${game.away} @ ${game.home}` `` |
| Game view header | `full-slate-matrix.js` | 365 | `<b>{game.away}</b><span>@</span><b>{game.home}</b>` |

**B. Expression analysis:**  
Every builder reads `game.away` and `game.home` as two **distinct** fields. No builder reads the same field twice. Frontend code is correct.

Player row game lookup (`full-slate-matrix.js:294`):
```js
const game = showGame ? (window.SLATE_GAMES || []).find((g) => g.id === row.gameId) : null;
```
Matches row's `gameId` against `g.id` in `window.SLATE_GAMES`.

Chip strip uses `getFSMGames()` (`full-slate-matrix.js:72-75`):
```js
const getFSMGames = () => window.SLATE_GAMES && window.SLATE_GAMES.length > 0
  ? window.SLATE_GAMES
  : [{ id: "tor-mia", away: "TOR", home: "MIA", ... }];
```
Falls back to static TOR-MIA only if `SLATE_GAMES` is empty. Since PHI/TEX/ATL appear, `SLATE_GAMES` is non-empty — fallback not active.

**C. Payload inspection (`/api/slate` → `slate_games`):**  
`window.SLATE_GAMES` is set from `data.slate_games` in `a6cd8ef6:45-47`:
```js
if (data.slate_games?.length) {
  window.SLATE_GAMES = data.slate_games;
}
```
For `PHI@PHI` to render, the payload entry must be `{ ..., away: "PHI", home: "PHI" }`. The `away` field is being set to the home team value in the API/pipeline.

### Classification
**(3) API/pipeline collapses away into home — payload itself wrong.**  
Frontend reads two distinct fields correctly. Bug is in `/api/slate` → `slate_games` construction. The Python pipeline or API serializer is setting `away` to the home team abbreviation for all games.

**Likely suspect in pipeline:** wherever `slate_games` entries are built, the away-team field is being populated with the home team value (wrong key lookup, inverted assignment, or schema mapping error).

### Cross-check with Item 1
Independent root causes. Blank board = `leaderboard_rows` empty/absent. HOME@HOME = `slate_games[].away` set to home value. Could both stem from same failed pipeline run (all outputs wrong), but the bugs are in different fields at different layers. The hydration path is shared; the faults are independent.

### Key File/Lines
- `full-slate-matrix.js:72-75` — `getFSMGames()` / SLATE_GAMES consumer
- `full-slate-matrix.js:294` — per-row game lookup via `row.gameId`
- `full-slate-matrix.js:1080` — chip strip label
- `full-slate-matrix.js:335` — player row label
- `a6cd8ef6-2b53-4016-a340-66b69a8928bd.js:45-47` — SLATE_GAMES seeding from API payload

**Next step:** Inspect Python pipeline `slate_games` construction — find where `away` is assigned. Verify `/api/slate` JSON response for one game (e.g., PHI game) directly.

### Status
Diagnostic complete. No fix proposed. Awaiting operator review before any matchup fix.

---

## ITEM 3 — NO TIME GATE TOGGLE HIDDEN (fix — committed)

### Decision
`noTimeGate` confirmed stub. `applyRoomFilters` (`0ead2d7a:101-142`) has no branch for `f.noTimeGate`. State tracked, counted as active filter, displayed as toggle — zero effect on output. Decision: hide entirely. Do NOT wire.

**Frontend has no hour-cutoff equivalent** to Streamlit's `cutoff_utc_hour`. Wiring a frontend time-gate is DEFERRED — overlaps with Exclude Started / Include Live; needs its own audit before build.

### Changes Made

| File | Change |
|------|--------|
| `fa8fdb8f-2a92-4a2c-acfe-e38e50d6e9f4.js:115` | Removed `<Toggle label="No Time Gate" ...>` from Game Context cluster |
| `0ead2d7a-98fd-4c05-9412-e8c9b12b1861.js:85` | Removed `noTimeGate: false` from `FILTER_DEFAULTS` |
| `0ead2d7a-98fd-4c05-9412-e8c9b12b1861.js:162` | Removed `if (f.noTimeGate !== d.noTimeGate) n++` from `countActiveFilters` |

### Verification
- `grep noTimeGate frontend/assets/js/*.js` → 0 matches. All references removed.
- Game Context cluster: 4 toggles remain (Exclude Started Games, Include Live Games, Confirmed Lineups Only, Pre-Lineup Pool).
- No reference errors possible — state field removed from defaults, count logic removed, UI removed.
- `applyRoomFilters` untouched for all other toggles.

### Deferred
Wiring a frontend time-gate overlaps with "Exclude Started Games" and "Include Live Games" logic. Needs audit of interaction before any build: does a time-gate add value given those two toggles already handle started/live exclusions? Cross-ref Game Context cluster doctrine when scheduling.

---

## ITEM 4 — COLD-LOAD EMPTY/DEGRADED STATE (fix)

### Decision
Implement three-state board for fullSlate lens: LOADING → EMPTY/STALE → DATA. Root cause from Item 1 diagnostic. UX fix only — does not trigger pipeline from frontend.

### Architecture
**State machine added to Stage (`cfdd4178`)**
- `fetchDone: false` — board is in LOADING state (fetch in flight)
- `fetchDone: true, sourceRows.length > 0` — DATA state (normal render, unchanged)
- `fetchDone: true, sourceRows.length === 0` — EMPTY state (actionable message)
- `fetchFailed: true` — sub-state of EMPTY; fetch threw (API unreachable)

**Event wrapper (`onDataLoaded`):** Replaces direct `hydrateRows` listener. Calls `hydrateRows()` (hydration logic unchanged), then sets `fetchDone = true` and `fetchFailed` from `e.detail._fetchFailed`.

**`hydrateRows()` unchanged** — reads globals, sets rows exactly as before.

**MasterDashboard catch (`a6cd8ef6`):** Now dispatches `hrEngineDataLoaded` with `{ _fetchFailed: true }` on fetch failure. Previously fired nothing → loading state would never resolve on error.

### Empty State Copy
| Condition | Eyebrow | Headline | Body |
|-----------|---------|----------|------|
| Pipeline not run | PIPELINE PENDING (amber) | NO SLATE DATA | "Pipeline has not run for today's slate. Trigger: POST /api/pipeline/run with X-Cron-Secret header." |
| API connection failed | BOARD OFFLINE (red) | API CONNECTION FAILED | "Could not reach HR Engine API. Check connection or refresh to retry." |

Loading state: "LOADING SLATE DATA / Fetching picks from HR Engine API…" — resolves to EMPTY or DATA, never infinite.

### Constraints Met
- No Python/JS exception text surfaced
- No fake rows/placeholder cards
- MAIN/JIG source-ownership branch untouched
- `hydrateRows()` internal logic untouched
- No None/nan coercion needed (empty state, not row display)

### Files Changed
| File | Change |
|------|--------|
| `a6cd8ef6-2b53-4016-a340-66b69a8928bd.js:50-52` | catch block dispatches `hrEngineDataLoaded` with `_fetchFailed: true` |
| `cfdd4178-a139-4f84-b282-b84f76971c49.js:95-96` | add `fetchDone`, `fetchFailed` state |
| `cfdd4178-a139-4f84-b282-b84f76971c49.js:105-111` | replace direct `hydrateRows` listener with `onDataLoaded` wrapper |
| `cfdd4178-a139-4f84-b282-b84f76971c49.js:139-170` | fullSlate branch: LOADING → EMPTY (two variants) → DATA |

### Cross-Reference
`PHASE3_REFINEMENT_DOCTRINE.md` degraded-state section: this establishes new degraded-state behavior for the fullSlate board. Pattern: three-state (loading/empty/data) with operator-actionable copy on empty. Does NOT add Python exception text (explicitly excluded by doctrine). Fetch error → "API connection failed" copy only, no stack trace or error object.

### Status
Fixed. DO NOT COMMIT until operator authorizes.

---

## ITEM 5 — HOME@HOME MATCHUP BUG FIX (data-integrity fix — applied)

### Root Cause (confirmed in Phase 1 audit)

`opponent` in the player dict is "opposing team from batter's perspective" — NOT always the visiting team.

| Batter side | `team` | `opponent` | `home_team` |
|-------------|--------|-----------|-------------|
| Home (PHI) | PHI | ATL | PHI |
| Away (ATL) | ATL | **PHI** | PHI |

`_build_slate_payload` was using `opponent` as `away` at both:
- **Site A** — `derived_game_id` / `gameId` per leaderboard row (L360–362)
- **Site B** — `slate_games[*].away`, `gid`, `teams[0]` (L459–479)

For away batters: `opponent = home team` → `away == home` → "PHI-PHI" IDs.

### Blast Radius (b) — Deeper Than Labels

| Broken | Description |
|--------|-------------|
| `slate_games[*].away` | Non-deterministic: whichever player in `players` list appears first for a game registers the entry. Away batter first → HOME@HOME display |
| `leaderboard_rows[*].gameId` | **Every** away batter had wrong `gameId` ("phi-phi") → away batters orphaned to phantom game buckets; game-card grouping broken |
| `slate_games[*].teams[0]` | Same as `away` |

| Unaffected | Why |
|------------|-----|
| Model output (Poisson / EV / edge / sizing) | Computed from `home_team` and `pitcher` in pipeline — no dependency on collapsed `away` field |
| Park factor / platoon splits / handedness | All keyed on `home_team` directly (L172, L219 pipeline.py) |
| `portfolio/correlation.py` same-game detection | Uses `opp_a == team_b or opp_b == team_a` — correct regardless of home/away order |
| Historical picks / calibration data | Model accuracy unaffected; `opponent` semantics consistent in CSVs |
| Streamlit `app.py` display | `opponent` used as "opposing team" contextually — semantically correct for display |

### Fix — `api/main.py`

Derived away team as: own team if not the home team, else opponent. Applied identically at both sites.

```python
# Correct derivation — order-independent
home = (p.get("home_team") or p.get("team") or "home").upper()
_own = (p.get("team") or "").upper()
_opp = (p.get("opponent") or "").upper()
away = (_own if _own != home else _opp) or "away"
```

**Order-independence property:** Both home batter and away batter for the same game produce identical `(away, home)` pair and `gid`. Verified by trace:

| Batter | team | opponent | home_team | → away | → home | gid |
|--------|------|----------|-----------|--------|--------|-----|
| PHI (home) | PHI | ATL | PHI | ATL | PHI | atl-phi ✓ |
| ATL (away) | ATL | PHI | PHI | ATL | PHI | atl-phi ✓ |

`seen_games` dedup on `gid` is now fully order-independent — no processing-order dependence.

### Files Changed

| File | Sites | Change |
|------|-------|--------|
| `mlb_hr_engine_v4/api/main.py` | L360–364 (Site A) | `gameId` derivation: `opponent→away` replaced with team/home_team logic |
| `mlb_hr_engine_v4/api/main.py` | L461–482 (Site B) | `slate_games` construction: `_away/_home` derived correctly; `away`, `home`, `teams` all use derived values |

### Deploy Requirement

**GitHub push does NOT auto-deploy.** After push, production requires cache flush:
```
POST /api/pipeline/run
Header: X-Cron-Secret: <secret>
```
Or wait for next scheduled cron run. Stale `slate_cache` in Supabase will serve old broken payload until flushed.

### Cross-Reference
- `wiki/architecture/pipeline-data-flow.md` — `opponent` field semantics (opposing team, not away team)
- `wiki/sessions/2026-06-18-cold-load-matchup-no-time-gate.md` Item 2 — diagnostic that identified `slate_games` as source

### Status
Fixed. Awaiting operator authorization to commit + push.
