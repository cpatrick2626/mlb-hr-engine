# Build Log and Spec Status

**Last Updated:** 2026-06-08

---

## Summary

Baseline audit (2026-06-08) identified missing and empty files that future agents must not assume exist or contain valid content.

Production validation was also recorded on 2026-06-08 for the live MAIN/JIG/JIG Builder frontend behavior after the Full Slate ordering fix and the JIG Builder source-routing fix.

---

## Production Validation Status

### Scope

- Room: `Obsidian Governance Update`
- Phase: Post-production validation documentation
- Risk: LOW
- Surface validated: live production only
- Frontend: `https://mlb-hr-engine-one.vercel.app`
- API: `https://mlb-hr-api.fly.dev/api/slate`

### Result

- Page loaded: yes
- Data loaded: yes
- Crash-level JavaScript exception observed: no
- Nonblocking 404 observed: `/.image-slots.state.json`
- App-load failure observed: no
- Data-load failure observed: no

### API Snapshot

- MAIN count: `184`
- MAIN top 3: Luke Raley, Dominic Canzone, Casey Schmitt
- JIG count: `184`
- JIG top 3: Yordan Alvarez, Collin Price, Kyle Schwarber

### Live UI Validation

- MAIN Full Slate count: `184 / 184`
- MAIN Full Slate top 3 matched API `leaderboard_rows`: yes
- JIG Full Slate count: `184 / 184`
- JIG Full Slate top 3 matched API `leaderboard_rows_jig`: yes
- JIG Full Slate mirrored MAIN: no
- JIG Builder count: `184 / 184`
- JIG Builder validated in PLAYER VIEW: yes
- JIG Builder matched JIG-side source / API `leaderboard_rows_jig`: yes
- JIG Builder mirrored MAIN: no

### Verdict

- MAIN/JIG Full Slate production fix validated: yes
- JIG Builder Phase A production fix validated: yes
- MAIN live order equals API MAIN order: yes
- JIG live order equals API JIG order: yes
- JIG Builder player-source live equals API JIG, not MAIN: yes

### Commits Recorded

1. `a4c4cc8` — `fix(frontend): preserve main jig full slate order`
   - `frontend/assets/js/full-slate-matrix.js`
   - `frontend/assets/js/cfdd4178-a139-4f84-b282-b84f76971c49.js`
2. `08d7051` — `fix(frontend): route jig builder to jig source`
   - `frontend/assets/js/jig-command.js`

### Push Result

- Push succeeded: `c1833c9..08d7051 main -> main`
- Validation-time repo state recorded as:
  - `main` synced with `origin/main`
  - working tree clean

### Technical Summary

1. Full Slate bug
   - Stage already had separate `mainRows` and `jigRows`.
   - The actual bug was `FullSlateMatrix` forcing incoming rows through default `hrprob` sort.
   - Fix preserved incoming API order by default while preserving explicit operator sort behavior.
2. Hydration bug
   - Stage could miss `hrEngineDataLoaded`.
   - `mainRows` / `jigRows` could stay empty.
   - Fix added `hydrateRows()` so Stage seeds from globals on mount and still listens for `hrEngineDataLoaded`.
3. JIG Builder Phase A
   - JIG Builder previously used `window.LEADERBOARD_ROWS`, which meant MAIN rows.
   - Fix changed source priority to:
     1. `window.SLATE_ROWS_RAW`
     2. `window.RAW_SLATE_ROWS`
     3. `window.LEADERBOARD_ROWS_RAW`
     4. `window.LEADERBOARD_ROWS_JIG`
     5. `window.LEADERBOARD_ROWS` only as commented degraded last-resort fallback
   - No raw globals are currently exposed, so Phase A presently resolves to JIG-side rows.
   - This is a stopgap, not full raw-workspace doctrine compliance.

### Outstanding Future Work

1. JIG Builder Phase B — **DEFERRED (operator decision 2026-06-08)**
   - Raw-workspace UI cleanup
   - Reduce formula-first language where needed
   - Avoid implying JIG Builder is fully raw while it still uses JIG-side scored rows
   - **Do not modify JIG Builder UI unless operator explicitly reopens Phase B.**
   - See session [[2026-06-08-jig-builder-phase-b-deferred]]
2. JIG Builder Phase C — **FUTURE ONLY / HIGH RISK**
   - HIGH-risk backend/API raw data surface audit if true raw unscored slate rows are required
   - Current `/api/slate` payload exposes only `leaderboard_rows`, `leaderboard_rows_jig`, `slate_games`, and `generated_at`
   - Requires separate authorized assignment with explicit operator authorization before any work begins
3. JIG Top Targets
   - Previously audited adjacent issue: JIG Top Targets hard-coded `mainRows`
   - **RESOLVED** — fixed and production-validated 2026-06-08
   - See session [[2026-06-08-jig-top-targets-production-validation]]

---

## JIG Top Targets Production Validation Status

**Last validated:** 2026-06-08

### Source Fix Confirmed

- File: `frontend/assets/js/cfdd4178-a139-4f84-b282-b84f76971c49.js` lines 145–146
- `const targetSourceRows = engine.id === "jig" ? jigRows : mainRows;`
- MAIN Top Targets → `mainRows`. JIG Top Targets → `jigRows`. ELITE/EDGE filter unchanged.

### API Snapshot

- MAIN raw count: `176`
- JIG raw count: `176`
- MAIN Top Targets after filter: `69`
- JIG Top Targets after filter: `69`

### Live UI Validation

- MAIN Top Targets count: `69 / 69` — top 1: Colton Cowser
- JIG Top Targets count: `69 / 69` — top 1: Collin Price
- MAIN/JIG Top Targets no longer mirror: yes
- MAIN Full Slate operational: yes
- JIG Full Slate operational: yes
- JIG Builder operational: yes

### Verdict

- JIG Top Targets production source fix validated: **yes**
- Repo synced with `origin/main` at validation time. Working tree clean.

### Commit

- `9962d27` — generic vault backup message (do not rewrite history)

### Outstanding

- JIG Builder Phase B — raw-workspace UI cleanup — **DEFERRED (operator decision 2026-06-08)** — do not prioritize unless operator reopens
- JIG Builder Phase C — backend/API raw data surface audit (HIGH risk) — future only
- Commit hygiene note: fix landed under vault backup message

---

## Build Log Status

| File | Status | Notes |
|------|--------|-------|
| `latest.md` | **MISSING** | Expected build log; file does not exist as of 2026-06-08 audit |
| `TASK-001-build-log.md` | **Current fallback** | Use this until `latest.md` is re-created |

### Rule

When referencing build log state, check `TASK-001-build-log.md` until `latest.md` is confirmed present and current.

Do not assume `latest.md` exists. Verify before referencing it.

---

## Empty Spec Placeholders

The following spec files exist but contain **0 bytes**. They are structural placeholders only.

| File | Status |
|------|--------|
| `mlb_hr_engine_v4/Docs/01_SPECS/product-spec.md` | **0 bytes — empty placeholder** |
| `mlb_hr_engine_v4/Docs/01_SPECS/ui-system.md` | **0 bytes — empty placeholder** |
| `mlb_hr_engine_v4/Docs/01_SPECS/architecture.md` | **0 bytes — empty placeholder** |

### Rule

Do not cite these files as authoritative sources. They contain no content. Any agent that reads them will find nothing. Until they are populated by an authorized task, treat them as gaps.

If a future task populates these files, update this note.

---

## Cross-References

- [Room Governance](room-governance.md)
- [Obsidian Governance Doctrine](OBSIDIAN_GOVERNANCE_DOCTRINE.md)
