# Build Log and Spec Status

**Last Updated:** 2026-06-10

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

---

## Option A Tier Threshold Production Validation

**Last validated:** 2026-06-10

### Scope

- Room: `Obsidian Governance Update`
- Phase: Document Option A Tier Threshold Production Validation
- Risk: LOW
- Surface validated: live production only
- API: `https://mlb-hr-api.fly.dev`

### Commits

1. `f3969b1` — `tune(config): tighten full slate tier thresholds`
   - File: `mlb_hr_engine_v4/config.py` only
   - `FS_TIER_THRESHOLDS`: APEX 0.20, ELITE 0.16, EDGE 0.11, SIGNAL 0.07, WATCH 0.04, COLD 0.00
2. `ffa156c` — `fix(frontend): align full slate fanduel search links`
   - File: `frontend/assets/js/full-slate-matrix.js` only
   - `fsmFanduelUrl` pattern: `https://sportsbook.fanduel.com/search?query=<encoded player name> home run`

### Fly.io Deploy

- Result: success — Image `deployment-01KTT1166HZRBB8WWAF2R1JBWM`, Machine `7841255a9d2e28`

### API Snapshot

- `generated_at`: `2026-06-11T00:32:25`
- `from_cache`: false
- MAIN rows: `198`, JIG rows: `198`

### Tier Distribution

| Tier   | Count | % of 198 |
|--------|-------|----------|
| APEX   | 18    | 9.1%     |
| ELITE  | 17    | 8.6%     |
| EDGE   | 59    | 29.8%    |
| SIGNAL | 65    | 32.8%    |
| WATCH  | 32    | 16.2%    |
| COLD   | 7     | 3.5%     |

- Top Targets eligible (ELITE + EDGE): 76 / 198

### Verdict

- Option A tiers active in production: **yes**
- No legacy AVG / WEAK in `row.tier`: **yes**
- FanDuel search URL fix live: **yes**
- MAIN Full Slate label (TIER): **yes**
- JIG Full Slate / Builder label (MODEL TIER): **yes**
- Fly.io healthy: **yes**

See session [[2026-06-10-option-a-tier-threshold-production-validation]] for full detail.

---

---

## Tier Ranking Room Foundation

**Completed:** 2026-06-11

### Scope

- Room: `Tier Ranking Room`
- Phase: Foundation completion
- Risk: LOW
- Documentation session only

### Commits Recorded

| Commit | Message | Deliverable |
|--------|---------|-------------|
| `1b46e48` | `fix(app): migrate main tier displays to full slate tiers` | Tier vocabulary migration — MAIN |
| `394172c` | `fix(app): migrate jig displays to model tier labels` | JIG MODEL TIER migration |
| `c00cf05` | `fix(frontend): clarify jig model tier labels` | Frontend JIG label cleanup |
| `3de3d89` | `docs(doctrine): clarify jig tier display inheritance` | JIG row.tier inheritance doctrine |
| `f13b02f` | `fix(api): read tier thresholds from config` | API config-sourced thresholds |
| `10b1d25` | `feat(ranking): stamp model tier rank` | `model_tier_rank` field foundation |
| `3149d18` | `feat(app): show model tier rank on main surfaces` | APEX #1 / ELITE #1 display |
| `9231895` | `docs(doctrine): establish primary ranking doctrine` | Primary Ranking Doctrine codified |
| `61137c9` | `feat(app): add apex reason stack` | APEX Reason Stack Phase 1 |
| `de2fb52` | `fix(app): refine apex reason stack badges` | Reason Stack Phase 1.5 cleanup |

### Final Doctrine Summary

- `model_tier_rank` = HR Threat Rank — pure model probability, no market contamination
- `APEX #1` = highest engine-estimated HR probability; not "best bet", not "highest EV"
- Odds, EV, edge, sportsbook lines — display-only; never influence primary rank
- Bet Value Rank (Deploy Score) — deferred, not yet implemented
- JIG excluded from Bet Value Rank when eventually implemented

### Reason Stack Status

| Phase | Status |
|-------|--------|
| Phase 1 — APEX drivers display | Complete (`61137c9`) |
| Phase 1.5 — Badge cleanup | Complete (`de2fb52`) |
| Phase 2 | Deferred — not yet defined |

### Next Phase

Live APEX Trust Review. No ranking changes until n≥200 settled picks. Observe APEX tier outcomes. Initiate calibration review as separate authorized assignment when sample accumulates.

See session [[wiki/sessions/2026-06-11-tier-ranking-foundation-completion]] for full detail.

---

## Cross-References

- [Room Governance](room-governance.md)
- [Obsidian Governance Doctrine](OBSIDIAN_GOVERNANCE_DOCTRINE.md)
