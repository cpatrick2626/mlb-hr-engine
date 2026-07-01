# Session: OOM Incident + Cache Architecture Fix + Cron Expansion + AEI Fixes — 2026-07-01

Date: 2026-07-01
Agent: Claude Code (execution)
Owner: Operator (Kylar)
Project: MLB HR ENGINE - OPERATIONS
Risk Class: HIGH (production incident + API architecture change); MEDIUM (infra, pitch_mix, cron); LOW (AEI UI fixes)
Phase: Production incident response + architecture hardening + ops expansion
Status: COMPLETE / SHIPPED

## Scope

Production incident session. A daily-morning OOM crash loop on the Fly.io API was diagnosed and fixed via a two-part response: a 1 GB memory stopgap (`f711ff3`) followed by a root architecture fix (`8feef78`). The architecture fix is the durable change: `/api/slate` is now a **pure cache-reader** and will **never** rebuild the pipeline in-request. Pipeline execution responsibility belongs solely to the GH Actions cron.

Additional work: pitch_mix Savant streaming fix (`60a78b9`), cron cadence 2x→5x (`4c6f8dc`), stale-slate UI banner (`4bbc40d`), AEI pitcher tier bug fix + close-button anchor (`e8b4822`, `fc27578`). Vault Phase 1 doctrine completion (`8ef95e8`, `bf7757b` — see prior log entries).

---

## Commits (chronological, this session)

| Commit | Summary |
|--------|---------|
| `f711ff3` | fix(infra): bump Fly memory 512→1024 MB — stopgap while root fix prepared |
| `8feef78` | fix(api): /api/slate pure cache-reader; stale:True on miss/stale; add get_latest_picks() |
| `4bbc40d` | feat(ui): stale-slate banner — "last-good slate from [date]" when stale:true |
| `60a78b9` | fix(pitch_mix): stream Savant CSV via TextIOWrapper(utf-8-sig); max_workers 6→3 |
| `4c6f8dc` | ops(cron): GH Actions pipeline 2x/day → 5x/day (10:05/12:05/14:05/16:05/18:05 EDT) |
| `3dd6a98` | fix(aei): pitcher tier from pitcher_hr9 — first attempt (caused cross-component crash) |
| `34d7a68` | Revert `3dd6a98` — cross-component var ref caused black-screen crash |
| `e8b4822` | fix(aei): pitcher tier derived in-component from row.pitcher_hr9 (correct fix) |
| `fc27578` | fix(aei): anchor AEI close button to card via .aei-wrap position:relative |
| `8ef95e8` | docs(vault): Formula Boundaries — already documented, see log.md |
| `bf7757b` | docs(vault): TCC wiki summary — already documented, see log.md |

---

## Production Incident: /api/slate OOM Crash Loop

### Symptom

Daily-morning API crash loop on Fly.io. `/api/slate` was OOM-crashing and restarting on days when the pipeline cache was missing or stale (before the morning cron had fired). Each crash triggered a Fly.io machine restart, which re-entered the same code path — a crash loop.

### Root Cause

`/api/slate` contained a live fallback: when the Supabase cache was missing or stale, it called `load_game_data()` in-request. This triggered a full pipeline execution inside the Fly.io container — building Statcast/Savant profiles for all batters across all games. On a 512 MB shared-CPU machine, this exhausted available memory, killing the process.

### Two-Part Fix

**Part 1 — Stopgap (`f711ff3`):** Bumped Fly machine `memory_mb` from 512 to 1024 in `fly.toml`. Stopped the crash loop immediately. Deployed before the root fix as a safety measure.

**Part 2 — Root fix (`8feef78`):** Removed the `load_game_data()` live-fallback path entirely from `api/main.py`. Replaced with `get_latest_picks()` (new function in `api/cache.py`): on cache miss or stale, `/api/slate` now queries Supabase for the most-recent stored pipeline run (ordered by `date DESC LIMIT 1`) and serves that payload with `stale: True`. If no stored run exists at all, returns an empty-rows error shape. No pipeline ever runs in-request.

---

## Architecture Change — /api/slate is Now a Pure Cache-Reader (DURABLE TRUTH)

This is the most important change from this session. It permanently alters the API contract.

**Before (`8feef78~1`):**
```
GET /api/slate
  → try Supabase cache (today, ≤12 h)
  → if miss/stale → load_game_data() in-request  ← OOM path
  → on exception → empty rows
```

**After (`8feef78`):**
```
GET /api/slate
  → try Supabase cache (today, ≤12 h) → stale: False
  → if miss/stale → get_latest_picks() (last-good row, any date) → stale: True
  → if DB empty (pipeline never run) → empty rows, stale: True
```

**Invariant established:** `/api/slate` NEVER runs the pipeline. Pipeline execution belongs exclusively to `POST /api/pipeline/run` (GH Actions cron). The `stale` boolean is now a first-class field in the payload contract.

### Payload Changes

| Condition | `stale` | `from_cache` | `cache_age_minutes` |
|-----------|---------|--------------|---------------------|
| Fresh cache (today, ≤12 h) | `False` | `True` | minutes since run |
| Stale/miss → last-good served | `True` | `True` | `None` |
| DB empty (pipeline never run) | `True` | `False` | — |

### `cache.py` Addition

`get_latest_picks()` — queries `pipeline_runs` table, `ORDER BY date DESC LIMIT 1`. No date filter — returns the most-recent stored payload regardless of date. Returns `None` if the table is empty.

---

## Stale-Slate UI Banner (`4bbc40d`)

Completes the graceful-degradation loop for the architecture fix. When `/api/slate` returns `stale: true`, the frontend renders a banner: **"last-good slate from [date]"**. Implemented in `a6cd8ef6-...js` (master dashboard bundle) + CSS in `index.html`. Users see honest data-freshness state; stale data is never silently presented as current.

Files changed: `frontend/assets/js/a6cd8ef6-....js` (+42 lines), `frontend/index.html` (+44 lines).

---

## Pitch Mix Efficiency Fix (`60a78b9`)

`mlb_hr_engine_v4/clients/pitch_mix.py` — Savant CSV was fetched as `response.content` (full in-memory bytes) then decoded. Changed to streaming: `requests.get(..., stream=True)` + `TextIOWrapper(response.raw, encoding='utf-8-sig', errors='replace')` with `decode_content=True`. Also reduced `max_workers` from 6 to 3 in the concurrent pitcher-fetch executor.

**Result:** Cuts peak memory during cron runs (both from streaming and fewer parallel workers). Parse output is identical — no change to pitch stats shape, field names, or values. Production model behavior unchanged.

---

## Cron Cadence: 2x/day → 5x/day (`4c6f8dc`)

`.github/workflows/daily_pipeline.yml` updated from 2 schedule entries to 5.

| UTC cron | EDT (UTC−4, summer) | EST (UTC−5, winter) |
|----------|---------------------|---------------------|
| `5 14 * * *` | 10:05 AM | 9:05 AM |
| `5 16 * * *` | 12:05 PM | 11:05 AM |
| `5 18 * * *` | 2:05 PM | 1:05 PM |
| `5 20 * * *` | 4:05 PM | 3:05 PM |
| `5 22 * * *` | 6:05 PM | 5:05 PM |

**Rationale:** Staggered MLB game times (early/afternoon/evening) mean probable pitchers post at different times through the day. More frequent refreshes shrink the TBD-pitcher window and keep pitcher data fresher for evening starts.

**DST caveat:** GitHub Actions cron is fixed UTC — no automatic DST adjustment. During winter (EST, UTC−5), all five runs fire 1 hour earlier in Eastern Time than the EDT column shows. The comments in the workflow file show EDT times; remember to mentally shift by +1 h when evaluating winter timing.

---

## AEI Fixes (`e8b4822`, `fc27578`)

### Pitcher Vulnerability Tier Bug (`e8b4822`)

**Bug:** The PITCHER VULNERABILITY tier label inside the Arsenal Edge Intel component was reading `row.tier` — the **batter's** model tier — instead of any pitcher-specific field. This produced phantom "EDGE" labels for TBD pitchers (inheriting the batter's tier) and wrong tiers for all pitchers.

**First attempt (`3dd6a98`):** Fixed the field read but introduced a cross-component variable reference. Caused a black-screen JavaScript crash. Reverted immediately (`34d7a68`).

**Correct fix (`e8b4822`):** Derive the pitcher vulnerability tier **in-component** from `row.pitcher_hr9` using a local threshold function — no cross-component variable reference:

| `pitcher_hr9` | Displayed tier |
|---------------|----------------|
| ≥ 1.45 | **HR TARGET** |
| ≥ 1.05 | **VULNERABLE** |
| < 1.05 | **TOUGH** |
| `null` / TBD | `—` (no label) |

**Labels relabeled:** Left AEI panel → **PITCHER VULNERABILITY**; right panel → **BATTER THREAT TIER**. Both now accurately describe what they display.

**File:** `frontend/assets/js/full-slate-matrix.js` (+6/−2 lines).

### AEI Close Button Anchor (`fc27578`)

**Bug:** The AEI modal close button (`×`) was escaping its card container and rendering at the viewport corner.

**Fix:** Added `position: relative` to `.aei-wrap` in `frontend/index.html` (+1 line). Matches the `.fsm-card--h2h` pattern used elsewhere in the stylesheet. Close button now sits top-right of the AEI card as intended.

---

## Vault Phase 1 Completion (Reference)

Five doctrine pages completed this session (separate log entries — see `wiki/log.md`):

| Page | Commit | Status |
|------|--------|--------|
| `doctrine/ticket-slip-system.md` | `d8c2c00` | Code-verified; build-slip LIVE, settlement/analytics NOT BUILT |
| `doctrine/full-slate-matrix.md` | `09e183c` | Code-verified; MAIN board LIVE |
| `doctrine/odds-clv.md` | `733a43f` | Code-verified; ODDS column flagged SYNTHETIC |
| `doctrine/tcc-command-center.md` | `bf7757b` | Code-verified; COMMAND tab LIVE; overlay partly mock |
| `doctrine/formula-boundaries.md` | `8ef95e8` | Code-verified; formula→file:line map confirmed |

---

## Invariants Preserved

- MAIN/JIG separation intact; scoring/probability formulas unchanged
- `model_tier_rank` and `jigScore` ordering unchanged
- Pipeline execution: GH Actions cron only — **new invariant established this session**
- `config.py` thresholds unchanged
- AEI fixes are display-only; no model math involved

---

## Known Follow-Ups

1. **AEI threshold alignment:** In-component pitcher tier thresholds (`1.45` / `1.05` HR/9) do not match `config.py`'s pitcher factor buckets (`[1.50, 1.20, 1.00, 0.80]`). Should align or document intentional divergence. **Flagged — not fixed this session.**

2. **Honest-UI backlog (pre-existing):**
   - Production board ODDS column is synthetic (model-derived, not real market odds) — documented in `doctrine/odds-clv.md`
   - Ticket slip SAMPLE panels (probability engine, grade, confidence, payout) — scaffolded but not yet wired to real data
   - `CommandCenter` overlay: garbled `"LYAR TREKRM MODE"` placeholder in `VisibilityPanel`; hardcoded `"SYSTEM LOAD: 14%"` / `"Active Filters: 12"` / `"UPDATE TIMER: 28s"` remain mock

3. **pitch_mix batter-side socket not closed on exception path** — pre-existing issue, not worsened by `60a78b9`. Not a blocker; flagged for cleanup in a future session.

---

## Files Touched By This Documentation Session

- `MLB HR ENGINE/wiki/sessions/2026-07-01-oom-incident-cache-fix-cron-aei.md` (this file — new)
- `MLB HR ENGINE/wiki/doctrine/production-surface-truth.md` (updated — /api/slate pure cache-reader contract)
- `OPS_DAILY_SETUP.md` (updated — GH Actions pipeline cron cadence section added)
- `MLB HR ENGINE/wiki/log.md` (appended)
- `MLB HR ENGINE/wiki/sessions/_Index_of_sessions.md` (appended)

## Post-session maintenance

- Graphify: graph rebuilt this session (`/graphify mlb_hr_engine_v4 --update`) — FRESH as of 2026-07-01 (3 changed files: `api/cache.py`, `api/main.py`, `clients/pitch_mix.py`).
