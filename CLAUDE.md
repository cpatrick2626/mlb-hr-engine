# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 1. Project Overview

MLB HR Engine — predicts per-batter home-run probabilities for each day's starting lineups, prices them against market odds, identifies positive-EV bets, and recommends bet sizes. Outputs flow into a Streamlit operator dashboard and (separately) a FastAPI service.

Four versioned iterations live side-by-side: `mlb_hr_engine_v1` → `mlb_hr_engine_v4`. v4 is the active line of development. v1–v3 are retained for backtesting comparisons and historical reproducibility.

## 2. Current Production Version

`mlb_hr_engine_v4` is the production version. New work happens there. v1/v2/v3 should not be modified except for narrow comparison/backtest needs.

## 3. Quick Setup

```bash
pip install -r mlb_hr_engine_v4/requirements.txt           # dashboard + CLI deps
pip install -r mlb_hr_engine_v4/requirements-api.txt       # FastAPI service deps (separate)
```

A `.env` file is expected inside each version directory (e.g. `mlb_hr_engine_v4/.env`). `.env.example` files are committed as templates. See section 11 for variables and loading behavior.

## 4. Common Commands

All `main.py` / `app.py` commands are run from inside a specific version directory.

```bash
# CLI: today's picks
cd mlb_hr_engine_v4 && python main.py

# CLI: specific date
cd mlb_hr_engine_v4 && python main.py 2026-04-18

# Streamlit dashboard (v4 only)
cd mlb_hr_engine_v4 && python -m streamlit run app.py

# Backtest (v3/v4): last N days, or date range
cd mlb_hr_engine_v4 && python backtest.py 30
cd mlb_hr_engine_v4 && python backtest.py 2026-01-01 2026-04-01

# FastAPI service (local)
cd mlb_hr_engine_v4 && python -m uvicorn api.main:app --host 0.0.0.0 --port 8080
```

Analysis and ops scripts live under `mlb_hr_engine_v4/scripts/`:

```bash
# Analysis (calibration, CLV, portfolio, market inefficiency, etc.)
python mlb_hr_engine_v4/scripts/analysis/analyze_calibration.py
python mlb_hr_engine_v4/scripts/analysis/analyze_clv.py
python mlb_hr_engine_v4/scripts/analysis/analyze_portfolio.py
python mlb_hr_engine_v4/scripts/analysis/optimize_daily.py
python mlb_hr_engine_v4/scripts/analysis/compare.py 2026-04-18

# Daily ops
python mlb_hr_engine_v4/scripts/ops/ops_daily.py
python mlb_hr_engine_v4/scripts/ops/settle_pick_tracker.py

# Monitoring (root)
python monitoring_dashboard.py
```

### Windows vs cross-platform invocation

The repo is primarily developed on Windows.

Windows-only helpers (do not assume they work elsewhere):
- `py -3.12 <script>.py` — Windows Python launcher convention used in doctrine docs
- `run_ops_daily.bat` — bat launcher for daily ops
- `schedule_task.ps1` — PowerShell scheduler script

Cross-platform equivalents:
- `python <script>.py`
- `python -m streamlit run app.py`
- `python -m uvicorn api.main:app ...`

## 5. Version / Directory Map

| Version | Statcast | Real platoon | P&L + CLV | Backtest | Streamlit | API | Sheets | Portfolio mgmt |
|---|---|---|---|---|---|---|---|---|
| `mlb_hr_engine_v1` | — | — | — | — | — | — | — | — |
| `mlb_hr_engine_v2` | ✓ | ✓ | ✓ | — | — | — | — | — |
| `mlb_hr_engine_v3` | ✓ | ✓ | ✓ | ✓ | — | — | — | — |
| `mlb_hr_engine_v4` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## 6. Architectural Invariants

These invariants must hold across changes. Do not break them without explicit operator authorization.

- The core data pipeline is: Fetch → build profiles → Poisson `P(HR≥1) = 1 − e^(−λ)` → price vs market → filter → rank → size → output. Reorder only with intent.
- `config.py` is the single source of truth for thresholds, weights, league baselines, and tuning values. Do not duplicate constants into documentation.
- Streamlit dashboard (`app.py`) and FastAPI service (`api/main.py`) are independent operational surfaces. They share `pipeline.py` and `config.py`; they do not share session state, auth, or caching.
- `pipeline.py` is consumed by both `main.py` and `app.py`. Treat it as the canonical data-assembly entrypoint.
- Routing, session_state, cache, and Streamlit UI scaffolding are considered closed surfaces. See `PHASE3_REFINEMENT_DOCTRINE.md`.
- Versioned directories (`mlb_hr_engine_v1`..`v4`) are intentionally separate trees. Do not collapse, share modules between them, or refactor across versions.

## 7. MAIN vs JIG Doctrine

Authoritative source: `AGENTS.md`.

- MAIN and JIG are separate intelligence layers.
- MAIN is quantitative / model-driven (EV, Edge, model probability, Poisson-derived).
- JIG is tactical / matchup-driven (arsenal, HVY pitch-mix signal, environmental hunting).
- MAIN and JIG must not be merged.
- MAIN and JIG use separate filters, separate scoring, and separate operational intent. The HVY pitch-mix modifier is display-only on the JIG side and must not be folded into MAIN's model probability.
- Preserve MAIN/JIG isolation unless the operator explicitly authorizes a scoped change.
- Do not introduce hidden composite scoring that blends tactical/HVY signals and model scoring.
- TCC (Tactical Control Center) orchestrates; it does not compute. See `MASTER_TCC_DOCTRINE.md`.

## 8. Deployment Summary

Two surfaces deploy independently.

**Streamlit dashboard (`mlb_hr_engine_v4/app.py`)**
- Operator-facing dashboard.
- Run locally with `python -m streamlit run app.py` from inside `mlb_hr_engine_v4/`.
- Reads from `mlb_hr_engine_v4/.env` (or Streamlit secrets — see section 11).

**FastAPI service (`mlb_hr_engine_v4/api/main.py`)**
- Read endpoints (picks, strategies, runs) gated by Supabase JWT auth.
- Pipeline trigger endpoint gated by `X-Cron-Secret` header. Normal pipeline runs come from GitHub Actions cron (`api/cron.py`); the manual endpoint is a fallback.
- Containerized via the root `Dockerfile` (Python 3.12-slim, uvicorn, single worker on port 8080).
- Deployed to Fly.io. `fly.toml` declares:
  - `app = "mlb-hr-api"`, `primary_region = "iad"`
  - `auto_stop_machines = true`, `auto_start_machines = true`, `min_machines_running = 0`
  - Shared CPU, 512 MB
  - Volume `mlb_tracking` mounted at `/app/tracking` to persist pick/CLV CSVs across deploys
- API dependencies live in `mlb_hr_engine_v4/requirements-api.txt` (FastAPI + uvicorn + supabase + python-jose; no Streamlit/rich/gspread).

Required Fly.io secrets (set via `fly secrets set KEY=value`):
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_JWT_SECRET`
- `ODDS_API_KEY`
- `CRON_SECRET`

For the full deployment + slip-tracking doctrine see `ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md`.

## 9. Module Map (`mlb_hr_engine_v4/`)

Top-level entrypoints:
- `app.py` — Streamlit dashboard
- `main.py` — CLI pick runner
- `pipeline.py` — shared data-assembly pipeline (consumed by both `app.py` and `main.py`)
- `backtest.py` — historical replay entrypoint
- `config.py` — single source of truth for parameters, thresholds, baselines, calibration values

Subdirectories (only those that exist are listed):
- `api/` — FastAPI service (`main.py`, `auth.py`, `cache.py`, `cron.py`)
- `assets/` — static assets used by the dashboard
- `backtest/` — historical scoring framework, calibration, Brier score, simulated P&L
- `clients/` — external data clients: MLB Stats API, The Odds API, Baseball Savant/Statcast, weather, pitch mix
- `components/` — Streamlit UI components
- `data/` — static reference data (park factors, coordinates)
- `Docs/` — additional engine documentation
- `engine/` — probability construction, EV/edge math, market/no-vig, filters, sizing, calibration
- `frontend/` — frontend assets/code
- `output/` — ranking, parlay building, formatters
- `portfolio/` — portfolio-management layer: `metrics.py`, `correlation.py`, `exposure.py`, `sizing.py`, `optimizer.py`
- `reports/` — generated daily reports
- `scripts/analysis/` — analysis tools (calibration, CLV, portfolio, market inefficiency, comparison, audits)
- `scripts/ops/` — operational scripts (`ops_daily.py`, `settle_pick_tracker.py`)
- `strategies/` — strategy definitions
- `supabase/` — Supabase-related assets
- `tests/` — test suite
- `tracking/` — pick log, CLV log, line snapshots, drift monitor, data integrity, sheets sync

Note: the same `clients/`, `engine/`, `output/`, `data/`, `tracking/`, `backtest/` module names also exist (with reduced surface area) in v1/v2/v3. Treat each version's tree as self-contained.

## 10. Frontend Surface (Next.js Prototype)

`mlb_hr_engine_v4/frontend/` is a Next.js 14 prototype surface used for design iteration of HR threat card components and related tactical UI. As of 2026-05-25 it is **standalone**: no Python runtime, FastAPI service, or Fly.io deployment invokes it. Streamlit (`app.py`) and Next.js (`frontend/`) are isolated operational surfaces with no runtime cross-dependency.

### Canonical paths

- **Frontend root:** `mlb_hr_engine_v4/frontend/`
- **Active TSX components:** `mlb_hr_engine_v4/frontend/components/`
- **Build entry:** `mlb_hr_engine_v4/frontend/app/page.tsx`
- **TypeScript config:** `mlb_hr_engine_v4/frontend/tsconfig.json` (path alias `@/*` resolves to `./*`, scoped inside `frontend/`)
- **Build artifacts:** `mlb_hr_engine_v4/frontend/.next/`

### Local development (Next.js, when needed)

Do NOT run these unless the operator explicitly authorizes a frontend session. Default assumption is that the frontend is dormant.

### Surface isolation rules

- Streamlit dashboard (`app.py`) does NOT import, consume, or render `.tsx` files. Confirmed by C-001 audit and X-001 investigation.
- FastAPI service (`api/main.py`) does NOT serve `frontend/` assets.
- Fly.io deployment (`fly.toml`, `Dockerfile`) does NOT build `frontend/`.
- Next.js components do NOT call Python runtime directly. Any future bridge must go through the FastAPI service contract (and require a separate doctrine update).
- session_state, cache, auth, and routing are NOT shared between Streamlit and Next.js.

### Archived legacy components

On 2026-05-25, the pre-rebuild `mlb_hr_engine_v4/components/hr/*.tsx` files were archived to `mlb_hr_engine_v4/_archive/components_hr_pre_rebuild/hr/`. These were the May 23 "tactical HR threat card system" originals, superseded by the May 24 "MAIN HR-threat-first rebuild" inside `frontend/components/hr/`. The archived versions had zero importers and were not doctrine-aligned (missing corner brackets, pulse animations, semantic green barrel palette, etc.). See `mlb_hr_engine_v4/_archive/components_hr_pre_rebuild/README.md` for restoration steps and full audit trail.

### Future integration (not yet specified)

If `frontend/` is wired into production (Fly.io deployment, FastAPI integration, replacement of Streamlit operator dashboard, etc.), the following doctrine items MUST be updated in the same change:

- This section
- `AGENTS.md` (platform identity)
- `MASTER_TCC_DOCTRINE.md` (orchestration scope if TCC extends to Next.js)
- `FULL_SLATE_UX_DOCTRINE.md` (if Full Slate renders on Next.js)
- `ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md` (if deployment surface changes)
- Deployment configs (`fly.toml`, `Dockerfile`)

Until then, treat `frontend/` as design iteration only.

### Audit trail

- 2026-05-25 C-001 doctrine audit (Steps 1-6) first identified `frontend/` and root `components/hr/*.tsx` as undocumented
- 2026-05-25 X-001 frontend investigation confirmed `frontend/` as canonical, root `components/hr/` as orphaned
- 2026-05-25 X-002 archival moved root `components/hr/` to `_archive/components_hr_pre_rebuild/`
- 2026-05-25 X-005 first push to origin committed and synced (commits f420411, 35cb365, 08adcf8)

## 11. Environment Variables

**Where `.env` lives**

Each version directory carries its own `.env` (e.g. `mlb_hr_engine_v4/.env`) alongside an `.env.example` template. Do not commit the real `.env`.

**How it is loaded**

`mlb_hr_engine_v4/config.py` calls `load_dotenv()` with no path argument. `python-dotenv` searches the current working directory and walks upward. Practical consequences:

- Running `python main.py` or `python -m streamlit run app.py` from inside `mlb_hr_engine_v4/` finds `mlb_hr_engine_v4/.env`. This is the supported invocation.
- Running scripts from the repo root with `python mlb_hr_engine_v4/scripts/...` runs in the repo-root cwd; `load_dotenv()` will not find `mlb_hr_engine_v4/.env` from the parent. Before running root-level or cross-directory scripts, either `cd` into the relevant version directory or set the variables in the shell environment.
- The FastAPI service reads secrets from the process environment (Fly.io secrets, GitHub Actions secrets, or local export). It does not depend on a checked-in `.env` in production. `api/cron.py` additionally calls `load_dotenv()` for local dev convenience.
- The Streamlit dashboard has a fallback path: `config._secret()` reads from `st.secrets` first, then falls back to env/`.env`. Streamlit Cloud or local `.streamlit/secrets.toml` can supply variables without a `.env`.
- For ambiguous entrypoints (custom analysis scripts, ad-hoc utilities), inspect the specific entrypoint before running.

**Common variables** (consult `config.py` and `api/auth.py` for the authoritative list)
- `ODDS_API_KEY` — The Odds API key (free tier 500 req/month). Falls back to `manual_odds.csv` if unset.
- `BANKROLL` — bankroll dollars for sizing math.
- `TARGET_DATE` — optional override; `None` means use today.
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET` — required by the API service.
- `CRON_SECRET` — required to call `POST /api/pipeline/run`.
- `GOOGLE_SHEETS_CREDS` — path to service-account JSON, only if Sheets sync is in use.

## 12. Reference Docs

Durable in-repo references. Consult these before changing related surfaces.

- `AGENTS.md` — MAIN vs JIG doctrine; pitch-mix integrity rules; scoring rules; UI/workflow rules. Read first.
- `MASTER_TCC_DOCTRINE.md` — Tactical Control Center doctrine. TCC orchestrates; does not compute. Defines what the operator sees and acts on.
- `FULL_SLATE_UX_DOCTRINE.md` — Full Slate battlefield UX, escalation hierarchy, game-card doctrine. Planning/architecture only.
- `PHASE3_REFINEMENT_DOCTRINE.md` — Runtime-aware UX refinement boundaries. Architecture, orchestration, session_state ownership, hydration, and routing are explicitly CLOSED surfaces.
- `ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md` — Governing doctrine for deployment, FD slip building, tracking systems.
- `OPS_DAILY_SETUP.md` — Daily ops scheduling guide (Windows paths, `run_ops_daily.bat`, Task Scheduler setup, log/report layout).
- `vault_architecture_audit.md` — Snapshot of repo folder hierarchy and config/skill layout (dated; verify against current tree).
- `ANALYSIS_INDEX.md` — Index of older analysis/optimization documents.
- `SETUP.md` (inside each version directory) — version-specific setup notes.

Historical session/changelog material lives in the `OPTIMIZATION_RESULTS_*.md`, `MLB_HR_ENGINE_V4_OPTIMIZATION_ANALYSIS.md`, and `FIX*_VALIDATION_REPORT.md` files at the repo root, and in `mlb_hr_engine_v4/Docs/`. Treat those as frozen artifacts; do not rely on them for current parameter values.

## 13. Validation / Safety Rules

- Read `config.py` directly for current model parameters. Do not infer parameter values from this file or older doctrine documents — they drift.
- Re-run the relevant analysis script under `mlb_hr_engine_v4/scripts/analysis/` after any change that touches signal weights, calibration, regression anchors, filter thresholds, or pitcher/park multipliers. Outputs are written next to the scripts as `*_output.txt`.
- New `.env`-dependent scripts: confirm the script's cwd before recommending an invocation pattern; `load_dotenv()` is cwd-sensitive (see section 11).
- Never fabricate Statcast/Savant data. Fall back gracefully when input is incomplete; preserve real provider integrity. (`AGENTS.md` § Pitch Mix Rules.)
- Do not adjust model thresholds or calibration based on small samples. The operator's stated rule is no threshold/calibration changes from n<200 settled real picks; verify in current ops docs before any such change.

## 14. What Not To Do

- Do not merge MAIN and JIG. Do not blend the HVY pitch-mix signal into MAIN model probability.
- Do not duplicate model constants, calibration parameters, or league baselines into documentation. They live in `config.py`.
- Do not rewrite runtime code in response to documentation tasks. Doctrine changes are doctrine changes.
- Do not collapse or cross-import between versioned directories (`mlb_hr_engine_v1..v4`).
- Do not modify routing, session_state, cache, or Streamlit UI scaffolding without explicit authorization. These are closed surfaces per `PHASE3_REFINEMENT_DOCTRINE.md`.
- Do not assume `py -3.12` works on macOS/Linux. Use `python` (and confirm a 3.12 interpreter when scripts require it).
- Do not invent deployment behavior beyond what `Dockerfile` and `fly.toml` actually declare.
- Do not commit `.env` files or any file containing real secrets.
