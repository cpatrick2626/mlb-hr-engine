# Production Surface Truth

**Last Updated:** 2026-07-01

---

## ⚠ Correction (2026-06-22)

This document originally described two frontend surfaces. That was incomplete. **Three surfaces exist:**

1. `frontend/` (root) — static production board (Vercel)
2. `mlb_hr_engine_v4/app.py` — Streamlit operator dashboard (**ACTIVE** — not dead, not safe to delete)
3. `mlb_hr_engine_v4/frontend/` — Next.js tactical shell (MIXED/prototype)

The authoritative three-surface map is now: **`wiki/architecture/frontend-topology.md`**

app.py was omitted from this document's original "two-surface" framing. That omission was incorrect. app.py is the primary operator workflow surface (pick logging, FD slip, CLV tracking). It is NOT a candidate for deletion until a validated replacement exists.

---

## Summary

Two frontend surfaces were originally documented here. As of 2026-06-22 the full topology is three surfaces. See `wiki/architecture/frontend-topology.md` for the current authoritative map. This document is retained for the branch-canonicity record and deployment surface details below.

---

## ⚠ AGENT WARNING — TWO `frontend/` TREES EXIST (2026-06-23)

This repo has **two directories named `frontend/`**. Two agents have analyzed the wrong tree and produced incorrect doctrine. This block is the authoritative disambiguation.

| Tree | Path | Type | Deploys to Vercel? |
|------|------|------|--------------------|
| **LIVE PRODUCTION** | `frontend/` (repo root) | Static HTML + CDN React 18 + `@babel/standalone` — **no build step** | **YES** — Vercel Root Dir = `frontend` |
| **DEAD PROTOTYPE** | `mlb_hr_engine_v4/frontend/` | Next.js 14 (`app/page.tsx`) | **NO** |

Root `frontend/` is NOT a Next.js app. It loads React 18 + Babel from unpkg CDN and transpiles JSX bundles at runtime via `<script type="text/babel">`. The named live component bundles are: `hr-threat-zone.js`, `jig-command.js`, `full-slate-matrix.js`, `escalation-feed.js`, `slate-command-strip.js`, `pitcher-vulnerability-strip.js` — all in `frontend/assets/js/`. Existence confirmed 2026-06-23.

**Authoritative full topology:** `wiki/architecture/frontend-topology.md`

---

## Frontend Surface Map

| Path | Type | Status | Data |
|------|------|--------|------|
| `frontend/` (repo root) | Static production frontend | **PRODUCTION** | Real API data via `/api/slate` |
| `mlb_hr_engine_v4/frontend/` | Next.js prototype | **PROTOTYPE / DESIGN ITERATION** | Mock data |

### Rules

- `frontend/` (root) is the production operator surface.
- `mlb_hr_engine_v4/frontend/` is a design-iteration prototype. As of 2026-06-08 it is standalone — no Python runtime, no FastAPI, no Fly.io deployment invokes it.
- Do not treat prototype component logic as production truth.
- Do not treat prototype mock data shapes as production API contracts.
- Layout and visual hierarchy from the prototype shell may be used as layout reference only (see `app-shell-layout.md`).

---

## Branch Canonicity

| Branch | Status |
|--------|--------|
| `main` | **Canonical active working branch** — MLB HR ENGINE operations |
| `master` | Stale unless specifically revalidated |

**Confirmed by operator: 2026-06-08.**

Any documentation, doctrine, or instruction referencing `master` as the active branch is stale and should be updated to `main` when encountered.

Exception: a future audit may confirm that a specific `master` commit contains unique history not merged to `main`. Until that audit occurs, treat `master` references as stale.

---

## FastAPI + Deployment Surface

- FastAPI service: `mlb_hr_engine_v4/api/main.py`
- Deployed to Fly.io (`fly.toml`, `Dockerfile` at repo root)
- Root `frontend/` static assets are served from the same deployment
- `mlb_hr_engine_v4/frontend/` (Next.js) is NOT deployed to Fly.io

---

## Stale / Orphan Deployment Files (2026-06-12)

The following files exist in the repo but are **stale/orphaned** and **must not be used for deployment**:

| File | Reason |
|------|--------|
| `mlb_hr_engine_v4/Dockerfile` | Multi-stage build, pinned 3.12.13, no `--workers` flag, `COPY` path expects `cwd = v4/`. Not referenced by any workflow, script, or doc. |
| `mlb_hr_engine_v4/fly.toml` | Same app name (`mlb-hr-api`), empty `[build]` block, conflicting `memory_mb` vs `memory`, `auto_stop_machines` as string vs root's bool. Not referenced by any workflow, script, or doc. |

**Canonical deployment files** are at the repo root only:
- `Dockerfile` (root)
- `fly.toml` (root)

These are the only files used by the `mlb-hr-api` Fly.io app.

**Operator note:** Archive or deletion of `mlb_hr_engine_v4/Dockerfile` and `mlb_hr_engine_v4/fly.toml` is pending separate authorization. No cleanup was performed in this update.

*Surfaced by 2026-06-12 production sanity check. Dated entry: 2026-06-12.*

---

## Mandatory Documentation Gate

All agents working in this repo must apply the documentation gate before finalizing any task.

Full rule: `AGENTS.md § Mandatory Obsidian/Wiki Documentation Gate`

Summary: if the work changed or discovered anything affecting production surfaces, UI, deployment, MAIN/JIG behavior, formulas, API payloads, architecture, doctrine, or operator workflow — update the wiki before final reporting. If not, state explicitly "No wiki update needed because [reason]." Never silently skip the checkpoint.

---

---

## Slip Architecture (Live — 2026-06-26)

### window.__hrSlip — Shared Slip State

`frontend/assets/js/slip-state.js` is the architectural backbone for all add-to-slip. A single JavaScript global manages the active ticket legs. See [Session State Map](../architecture/session-state-map.md) for the full API.

### Ticket Command Slip Card (ticket-command.js)

The live slip card displays current ticket legs with real data:
- Player name, team, HR prob (decimal model_prob), tier, barrel%, hard hit%, pitcher
- "SAMPLE" tags on panels not yet wired to real data (probability engine, grade, confidence, payout)
- Empty fields hidden (no NULL placeholder display)
- Mobile + desktop responsive

**Integrity rule:** No fabricated numbers. "SAMPLE" is the explicit contract for non-real panels.

### Persistent Top-Bar Slip Button (slip-btn.js)

"SLIP · N" button appears left of the account auth chip when legs ≥ 1. Opens the shared slip overlay from any page. Uses `window.__hrSlip.subscribe()` for reactive count updates. SlipOverlayHost is a centralized single mount (no per-component duplicate overlays).

### Add-to-Slip Surface Map

| Surface | Board | Wired? |
|---------|-------|--------|
| HR Threat Zone | MAIN | YES |
| Full Slate Matrix | MAIN/JIG | YES |
| JIG Command | JIG | YES |
| All Batters Leaderboard | MAIN | YES |
| Strategy Rail | MAIN | YES |
| Command Tab | MAIN + JIG | YES |
| Escalation Feed | MAIN | YES |
| **LIVE Targets Banner** | MAIN | **NO — intentional block** |

**LIVE Targets Banner block:** Hardcoded mock data, no real `player_id`. Wiring would corrupt calibration data. Must not be wired until banner is connected to real API rows.

---

## Authentication (Live — 2026-06-26)

### Auth System Summary

- **JWT validation:** ES256/JWKS (Supabase issues ES256; original HS256 was incorrect). See [Supabase Schema](../architecture/supabase-schema.md) for implementation detail.
- **Write-endpoint gating:** `require_auth` (login required) and `require_beta` (beta_users membership required)
- **Per-user ownership:** `user_id` stamped on all write paths (tickets, legs)
- **Frontend:** `auth.js` provides Supabase login modal, email-confirm flow, invite redemption (beta_invites → beta_users), auth chip in topbar

### Live Auth Bundles

| File | Purpose |
|------|---------|
| `frontend/assets/js/auth.js` | Login modal, invite redemption, auth chip |
| `frontend/assets/js/slip-btn.js` | Auth-aware slip button (requires login to add legs) |

---

## Matchup Cell & TM Surface (2026-06-28)

The production `frontend/` Full Slate matchup cell was reframed and a True Matchup gauge added. Canonical truth for the matchup cell:

| Element | Source field | Notes |
|---------|--------------|-------|
| TM gauge | `true_matchup_score` (0–100) | Labeled "TM"; honest 0–100 arc (no rescale); fixed band colors. See `true-matchup-score.md`. |
| HR PROB | `hrprob` (×100) | Headline number; the real predictive HR %. |
| BATTER EDGE | `arsenal_edge_score` (0–10) | Displayed raw, unsigned. Renamed display of the arsenal-edge exploit score. |
| SIGNAL | `arsenal_edge_confidence` (0–1 → %) | Full-arsenal exploit confidence. Same field shown as EXPLOIT CONF in AEI. |

- Removed from the slate cell: "Elite/Strong/Neutral Matchup" text and the key pitch label. Key pitch lives only in the Arsenal Edge Intel modal.
- The TM gauge reads `row.true_matchup_score` directly — no client-side recomputation (single source of truth).

## Arsenal Edge Intel (AEI) (2026-06-28)

The matchup-gauge detail modal is `FsmArsenalEdgeIntel` (three panels: PITCHER ARSENAL | ARSENAL EDGE VERDICT | BATTER DAMAGE PROFILE). It replaced `FsmPitchMix`, which is preserved unrouted in `frontend/assets/js/full-slate-matrix.js` as a rollback path.

- Verdict headlines the arsenal-edge read (label + score + EXPLOIT CONF from `arsenal_edge_confidence`); raw per-pitch HR/PA is per-pitch context only, not the headline.
- ~146 `aei-*` references in `full-slate-matrix.js` + AEI CSS in `index.html`. Any future edit to that file must preserve the AEI surface.
- All displayed values trace to real served fields. No invented numbers. Scoring untouched.

## Full Slate Mobile Card View (2026-06-28)

At ≤768px the Full Slate `.fsm-table` becomes stacked per-player cards via a CSS `@media (max-width: 768px)` block in `index.html` (CSS-grid card: tier+roles | name | TM gauge header, then a 6-column labeled stat-tile grid using `data-label`, with a `+N MORE STATS` expander toggling `is-expanded` / `fsm-cell--extra`). Desktop (>768px) renders the normal table unchanged.

- Follows the established `-desktop` / `-mobile` (or media-query swap) convention used by HR Threat Zone, Pitcher Vulnerability, Escalation Feed, TCS.
- The matrix JS emits the required hooks (`data-label`, `fsm-cell--extra`, `fsm-expandcell`/`fsm-expandbtn`, `fsm-roles`) — these were added to the live matrix (the prototype handoff matrix had them but lacked the AEI work; the live file is canonical).
- Open follow-up: role badges render below the tier chip rather than clustered beside it (`.fsm-roles` JSX wrap pending) — cosmetic only.

## Slate Sort & Filter Controls (2026-06-28)

A control bar on the Full Slate: **RANK** (sort/default — restores canonical `model_tier_rank` via existing `onSort`/`setSortState`), and **TM** / **HR PROB** as role-style filter toggles (independent on/off; AND-intersection when both on). Fixed thresholds: TM ≥ 60, `hrprob` ≥ 15. All view-level — MAIN ranking is never altered; filtering and sorting are independent and reversible. See `true-matchup-score.md` for thresholds.

---

## /api/slate Contract — Pure Cache-Reader (2026-07-01)

**Established by commit `8feef78`. This is a permanent architecture invariant.**

`/api/slate` is a **pure cache-reader**. It never runs the pipeline in-request.

### Decision record

Before `8feef78`, `/api/slate` had a live fallback: if the Supabase cache was missing or stale, it called `load_game_data()` inside the request handler. On a 512 MB Fly.io machine this triggered a full Statcast/Savant pipeline build, exhausting memory and causing a daily-morning OOM crash loop. The live-fallback path was removed entirely.

### Current behavior

| Condition | Response |
|-----------|----------|
| Supabase cache fresh (today, ≤12 h) | Serve cached payload — `stale: false` |
| Cache miss or stale | `get_latest_picks()` → serve most-recent stored run — `stale: true, cache_age_minutes: null` |
| DB empty (pipeline never run) | Empty rows + error message — `stale: true` |

### Payload contract additions (as of 8feef78)

- `"stale": bool` — first-class field on every `/api/slate` response. `false` = data is from today's run. `true` = serving last-good cache from a prior date (or DB empty).
- `"cache_age_minutes": int | null` — `null` when serving a stale last-good payload.

### `api/cache.py` — `get_latest_picks()`

New function added by `8feef78`. Queries `pipeline_runs` table, `ORDER BY date DESC LIMIT 1`, no date filter. Returns the most-recent stored payload regardless of date. Returns `None` if table is empty.

### Pipeline execution invariant

**Pipeline runs belong exclusively to `POST /api/pipeline/run` (GH Actions cron). No request handler may call `load_game_data()` or any pipeline entrypoint.** Any future `/api/*` endpoint that needs fresh data must read from `pipeline_runs` via `cache.py`.

### Stale-slate UI banner

Commit `4bbc40d`: when `stale: true` is received, the frontend renders **"last-good slate from [date]"**. Implemented in `a6cd8ef6-....js` + `index.html`. Honest state is always surfaced to the user.

### Infra note

Fly.io memory was also bumped 512 MB → 1024 MB (`f711ff3`, `fly.toml`) as a stopgap before the root fix landed. The memory bump remains in place.

---

## Cross-References

- [App Shell Layout](app-shell-layout.md)
- [Visual Design Doctrine](visual-design-doctrine.md)
- [Room Governance](room-governance.md)
- [Obsidian Governance Doctrine](OBSIDIAN_GOVERNANCE_DOCTRINE.md)
