# MLB HR Engine v4 — Architecture Specification

**Version:** 1.0
**Date:** 2026-06-09
**Status:** AUTHORITATIVE
**Scope:** mlb_hr_engine_v4 production system
**Sources:** AGENTS.md, MASTER_TCC_DOCTRINE.md, PHASE3_REFINEMENT_DOCTRINE.md, ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md, Docs/03_LLM_WIKI/system_governance/mlb_hr_engine_operating_doctrine.md, CLAUDE.md, fly.toml, Dockerfile, verified directory inspection

---

## 1. Production Surfaces

Four independent operational surfaces. No runtime cross-dependency.

| Surface | Entry Point | Runtime | Deployment |
|---------|-------------|---------|------------|
| Streamlit Dashboard | `app.py` | Python / Streamlit | Local operator machine |
| FastAPI Service | `api/main.py` | Python / uvicorn | Fly.io (`mlb-hr-api`, region `iad`) |
| CLI Pick Runner | `main.py` | Python | Local / GitHub Actions |
| Static Frontend | `frontend/index.html` | Static HTML / JavaScript | Vercel — https://mlb-hr-engine-one.vercel.app |

**Frontend disambiguation:**
- `frontend/` (repo root) — production static frontend. Deployed to Vercel. Entry point: `frontend/index.html`.
- `mlb_hr_engine_v4/frontend/` — Next.js design-iteration prototype. Standalone. No Python runtime invokes it. No Fly.io or Vercel deployment builds it. Not a production surface as of 2026-06-09.

Do not conflate these two surfaces.

---

## 2. Frontend Ownership

### 2.1 Streamlit Dashboard (operator surface)

- **Owner:** `app.py` — Streamlit orchestrator
- **Responsibility:** render pick cards, TCC controls, Full Slate, JIG, portfolio optimizer, sidebar tray, P&L summary
- **Session state:** owned exclusively by `app.py` orchestrator; no external module may write orchestrator-owned keys
- **Cache:** `@st.cache_data` / `@st.cache_resource` — owned by `app.py` and `pipeline.py`
- **UI components:** `filter_controls.py`, `components/sub_room_rail.py`, `strategies_ui.py`
- **Navigation state:** `nav_state.py`, `navigation_continuity.py`
- **Investigation state:** `investigation_state.py`

### 2.2 Static Frontend (production — Vercel)

- **Owner:** `frontend/` (repo root)
- **Status:** production — deployed to Vercel
- **Entry point:** `frontend/index.html`
- **Runtime:** Static HTML / JavaScript (no build step required)
- **Production URL:** https://mlb-hr-engine-one.vercel.app
- **Relationship to Fly.io API:** static frontend may call FastAPI endpoints at `mlb-hr-api.fly.dev`; no shared session state or auth

### 2.3 Next.js Prototype (design iteration only)

- **Owner:** `mlb_hr_engine_v4/frontend/`
- **Status:** design iteration — standalone, not wired to any Python runtime, not deployed
- **Canonical TSX components:** `mlb_hr_engine_v4/frontend/components/`
- **Build entry:** `mlb_hr_engine_v4/frontend/app/page.tsx`
- **Archived pre-rebuild components:** `mlb_hr_engine_v4/_archive/components_hr_pre_rebuild/`

---

## 3. Backend Ownership

### 3.1 Core Engine (`engine/`)

| Module | Responsibility | Protected |
|--------|---------------|-----------|
| `engine/probability.py` | Produces `model_prob` — calibrated per-batter-game HR probability | YES |
| `engine/calibration.py` | Platt scaling, context moderation, confidence tier calibration | YES |
| `engine/ev.py` | EV%, Edge% vs sportsbook no-vig | YES |
| `engine/market.py` | No-vig probability extraction from sportsbook lines | YES |
| `engine/filters.py` | JIG filter application, threshold gates | YES |
| `engine/sizing.py` | Fractional Kelly bet sizing | YES |
| `engine/vig.py` | Vig calculation utilities | YES |
| `engine/trust.py` | Trust-state ladder: FULL / DEGRADED / RESTRICTED / BLOCKED | YES |

### 3.2 Data Clients (`clients/`)

| Module | Responsibility |
|--------|---------------|
| `clients/mlb_stats.py` | MLB Stats API — lineups, game schedule, rosters |
| `clients/statcast.py` | Baseball Savant / Statcast — barrel%, exit velo, FB%, xSLG |
| `clients/odds_api.py` | The Odds API — sportsbook lines, market odds |
| `clients/weather.py` | Weather data — temperature, wind, humidity |
| `clients/pitch_mix.py` | Pitcher pitch-mix data — HVY modifier source |
| `clients/arsenal.py` | Pitcher arsenal data |
| `clients/pull_air.py` | Pull air% stat client |
| `clients/session_utils.py` | Session-scoped utility helpers |

### 3.3 Pipeline (`pipeline.py`)

Canonical data-assembly entrypoint. Consumed by both `app.py` and `main.py`.

**Pipeline sequence (invariant):**
```
Fetch → Build batter profiles → Poisson P(HR≥1) = 1 − e^(−λ) → Price vs market → Filter → Rank → Size → Output
```

Reorder only with explicit operator authorization.

### 3.4 Portfolio Layer (`portfolio/`)

| Module | Responsibility |
|--------|---------------|
| `portfolio/metrics.py` | Portfolio performance metrics |
| `portfolio/correlation.py` | Pick correlation estimation |
| `portfolio/exposure.py` | N_eff, HHI, fragility score, concentration tracking |
| `portfolio/sizing.py` | Portfolio-level sizing constraints |
| `portfolio/optimizer.py` | Portfolio optimizer — selects and constrains pick set |

### 3.5 Output Layer (`output/`)

| Module | Responsibility |
|--------|---------------|
| `output/ranker.py` | Pick ranking — MAIN composite score |
| `output/parlay.py` | Parlay builder (2/3/4-leg exhaustive) |
| `output/display.py` | Display formatting utilities |

---

## 4. API Ownership (`api/`)

| Module | Responsibility |
|--------|---------------|
| `api/main.py` | FastAPI app — read endpoints (picks, strategies, runs); pipeline trigger endpoint | Protected routing |
| `api/auth.py` | Supabase JWT authentication gate | Protected |
| `api/cache.py` | API-layer cache management | Protected |
| `api/cron.py` | GitHub Actions cron trigger; also calls `load_dotenv()` for local dev |

**Auth model:** Read endpoints gated by Supabase JWT. Pipeline trigger gated by `X-Cron-Secret` header.

**API does NOT:**
- Serve `frontend/` assets
- Share session state with Streamlit
- Share auth or caching with Streamlit

---

## 5. Deployment Architecture

### 5.1 FastAPI Service — Fly.io

```
App name:    mlb-hr-api
Region:      iad (Washington D.C.)
Runtime:     Python 3.12-slim, uvicorn, single worker, port 8080
CPU:         shared, 1 vCPU
Memory:      512 MB (memory_mb = 512, per fly.toml — pipeline needs ~300 MB; 512 gives headroom)
Volume:      mlb_tracking → /app/tracking (persistent across deploys)
HTTPS:       forced
Auto-stop:   true (scale to zero)
Auto-start:  true
Min machines: 0
```

**Required Fly.io secrets:**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_JWT_SECRET`
- `ODDS_API_KEY`
- `CRON_SECRET`

### 5.2 Streamlit Dashboard — Local

Run from inside `mlb_hr_engine_v4/`:
```
python -m streamlit run app.py
```

Reads from `mlb_hr_engine_v4/.env`. Falls back to `st.secrets` (Streamlit Cloud or `.streamlit/secrets.toml`).

### 5.3 CLI Runner — Local / GitHub Actions

```
python main.py           # today's picks
python main.py 2026-04-18   # specific date
```

### 5.4 Static Frontend — Vercel

- **Root path:** `frontend/` (repo root)
- **Entry point:** `frontend/index.html`
- **Production URL:** https://mlb-hr-engine-one.vercel.app
- **Runtime:** Static HTML / JavaScript — no build step, no Node.js runtime required
- **Relationship to Fly.io API:** frontend may call FastAPI read endpoints; no shared secrets, session state, or auth are deployed at the Vercel layer
- **vercel.json:** No `vercel.json` present in repo as of 2026-06-09 (Vercel auto-detects static site from `frontend/index.html`)

---

## 6. Configuration — Source of Truth

`config.py` is the single source of truth for:
- Model thresholds and signal weights
- League baselines
- Calibration parameters
- Rollback feature flags
- Kelly fraction
- Park factor constants

**Never duplicate constants from `config.py` into documentation.**

### 6.1 Rollback Flags (current)

| Flag | Module | Rollback Value | Effect |
|------|--------|---------------|--------|
| `CALIBRATION_ENABLED` | `config.py` | `False` | Disables Platt calibration |
| `ELITE_REG_TARGET_ENABLED` | `config.py` | `False` | Disables regression ceiling for barrel≥8% |
| `ELITE_PLATT_ENABLED` | `config.py` | `False` | Disables elite tier Platt |
| `CONTEXT_MODERATION_ENABLED` | `config.py` | `False` | Disables low-power context cap |
| `FB_QUALITY_GATE_ENABLED` | `config.py` | `False` | Disables FB% quality gate |
| `DYNAMIC_VIG_ENABLED` | `config.py` | `False` | Falls back to fixed `VIG_FACTOR=7.5%` |
| `PITCHER_FACTOR_SCALE` | `config.py` | `1.0` | Removes pitcher factor attenuation |

---

## 7. Protected Systems

These systems must not be modified without explicit operator authorization.

### 7.1 Hard-Protected Runtime Files

| File | Protection Reason |
|------|------------------|
| `engine/probability.py` | Core `model_prob` calculation — no deployment logic, no tactical signals |
| `engine/calibration.py` | Platt parameters — no AI auto-adjustment |
| `engine/filters.py` | JIG filter thresholds — no changes below n=200 settled picks |
| `config.py` numerical constants | Model parameters — require operator approval + calibration re-run |
| `tracking/pick_tracker.py` schema | Deterministic `pick_id` dedup depends on this schema |
| `api/main.py` routing | API routing architecture — closed surface |
| `api/cache.py` | Cache management — closed surface |

### 7.2 Protected Architectural Surfaces (PHASE3_REFINEMENT_DOCTRINE)

- Routing architecture
- `session_state` ownership and hydration sequence
- Cache ownership and invalidation rules
- Full Slate orchestrator logic
- Modal architecture
- MAIN/JIG identity boundaries

---

## 8. Session-State Ownership Rules

Defined in `MASTER_TCC_DOCTRINE.md` and `PHASE3_REFINEMENT_DOCTRINE.md`.

**Ownership model:**
- `app.py` orchestrator owns all hydration-level keys
- Each engine namespaces its own TCC keys
- Deployment layer owns `deployment_*` prefixed keys only
- No external module may write to orchestrator-owned keys

**TCC Key Namespacing:**

| Engine | Key Prefix | Example |
|--------|-----------|---------|
| MAIN | `tac_` | `tac_min_barrel` |
| JIG | `jig_tac_` | `jig_tac_min_barrel` |
| Full Slate | `fs_tac_` | `fs_tac_min_barrel` |
| Deployment | `dep_tac_` | `dep_tac_min_barrel` |

**Hard rules:**
- MAIN reads only `tac_*` keys
- JIG reads only `jig_tac_*` keys
- Cross-key reads are a contamination violation
- Deployment layer reads orchestrator state; never writes to it

---

## 9. Cache Ownership Rules

- Streamlit `@st.cache_data` / `@st.cache_resource` owned by `app.py` and `pipeline.py`
- API cache managed by `api/cache.py` — isolated from Streamlit
- `capture_closing_lines.py` is a standalone script — does not share app cache context
- Card HTML cache invalidates on new `slate_ts`
- `_tac_filter_fp` fingerprint invalidates on `slate_ts` change
- P&L sidebar cached at 5-minute TTL
- Cache key namespace must stay separate between engines (contamination risk)

---

## 10. MAIN / JIG Boundaries

Defined in `AGENTS.md` and `mlb_hr_engine_operating_doctrine.md`.

### 10.1 MAIN — Quantitative Deployment Engine

**Location:** `engine/probability.py`, `engine/calibration.py`, `clients/`, `data/`

**Responsibility:** Produce `model_prob` — calibrated per-batter-game HR probability.

**Permitted inputs:** MLB Stats API data, Statcast data, park factors, weather, pitcher stats, lineup position.

**Scoring formula:**
```
score = EV% × 0.40 + Edge% × 0.35 + Confidence × 0.25
```

**Not permitted:** Market data, EV, user preferences, display logic, tactical signals in `model_prob`.

### 10.2 JIG — Tactical Exploit Engine

**Location:** `engine/ev.py`, `engine/market.py`, `engine/filters.py`, `engine/sizing.py`

**Responsibility:** Compare `model_prob` to sportsbook no-vig probability. Compute EV%, Edge%, apply filter rules, size bets via fractional Kelly.

**Permitted inputs:** `model_prob`, sportsbook odds, configured thresholds from `config.py`.

**Not permitted:** Direct access to raw Statcast data, park factors, pitcher stats — all probability adjustment must occur in MAIN first.

### 10.3 STRATEGY Layer

**Location:** `portfolio/`, `output/ranker.py`, `output/parlay.py`, `clients/pitch_mix.py`

**Responsibility:** Select, rank, and display picks. Apply portfolio constraints. Generate tactical context signals. Drive UX output.

**Influence boundary:** May influence pick selection and display ranking. Must not alter `model_prob`, EV%, or Edge%.

### 10.4 Cross-Engine Isolation Rules (permanent)

- No shared scoring — MAIN composite score and JIG HVY modifier are computed independently; never merged
- No key cross-read — MAIN reads only `tac_*`; JIG reads only `jig_tac_*`
- No formula inheritance across engines
- `_apply_tactical_filters()` (MAIN) and JIG's equivalent are separate functions
- No shared `model_prob` — JIG operates without model probability
- Full Slate All Players mode must never apply MAIN scoring to JIG picks or vice versa

---

## 11. HVY Modifier Boundaries

Defined in `mlb_hr_engine_operating_doctrine.md` Section 3, `AGENTS.md`.

**HVY modifier is display-only.** Range [0.70, 1.40].

**Hard rules:**
- Must not be injected into `model_prob` calculation
- Must not be folded into MAIN model probability
- Park and weather factors are already in MAIN — do not double-count in HVY (removed in Session 22)
- Labeled "Tactical Signal" or equivalent in UX — must not appear to be a probability
- Resides in STRATEGY layer (`clients/pitch_mix.py`) for display context

**In TCC:**
- `min_hvy_score` filter: applies to JIG and Full Slate only — NOT MAIN scoring
- JIG reads `jig_tac_min_hvy_score`; MAIN does not read this key

---

## 12. Source-of-Truth Files

| Concern | Authoritative File |
|---------|-------------------|
| Model parameters, thresholds, weights | `config.py` |
| MAIN/JIG doctrine | `AGENTS.md` |
| TCC architecture and filter vocabulary | `MASTER_TCC_DOCTRINE.md` |
| Deployment, FD slip, CLV, tracking | `ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md` |
| Runtime UX refinement boundaries | `PHASE3_REFINEMENT_DOCTRINE.md` |
| System-wide operating doctrine | `Docs/03_LLM_WIKI/system_governance/mlb_hr_engine_operating_doctrine.md` |
| Deployment infrastructure | `fly.toml`, `Dockerfile` |
| Implementation conventions | `CLAUDE.md` (project-level) |
| Pick tracking schema | `tracking/pick_tracker.py` |
| Park factors | `data/park_factors.py` |

---

## 13. Data Sources

### 13.1 External APIs

| Source | Client | Data Type | Fallback |
|--------|--------|-----------|---------|
| MLB Stats API | `clients/mlb_stats.py` | Lineups, schedules, rosters, game results | None (required for pick generation) |
| Baseball Savant / Statcast | `clients/statcast.py` | barrel%, exit velo, FB%, xSLG, pull% | Blended/prior-season (labeled BLENDED/PRIOR) |
| The Odds API | `clients/odds_api.py` | Sportsbook lines | `manual_odds.csv` (if key unset) |
| Weather API | `clients/weather.py` | Temperature, wind, humidity | — REQUIRES FUTURE AUDIT — |
| Pitch Mix (Savant) | `clients/pitch_mix.py` | Pitcher arsenal, pitch-type rates, HVY modifier | Graceful fallback; never fabricate |

### 13.2 Static Reference Data

| File | Contents |
|------|---------|
| `data/park_factors.py` | Park HR factors, dome detection |
| `data/odds_cache.json` | Odds API response cache |

### 13.3 Sportsbook Priority Order

For edge assessment (sharpest = most efficient):
```
Pinnacle > Circa > BetOnlineAG > BetRivers > Caesars > DraftKings > FanDuel > Fanatics
```

---

## 14. Persistence Layer

### 14.1 Local CSV Files (`tracking/`)

| File | Contents | Schema Owner |
|------|---------|-------------|
| `tracking/pick_tracker.csv` | All pick records — model_prob, EV, sizing, deployment, settlement | `tracking/pick_tracker.py` |
| `tracking/picks_log.csv` | Daily picks log | — REQUIRES FUTURE AUDIT — |
| `tracking/clv_log.csv` | CLV calculations per pick | `tracking/clv.py` |
| `tracking/line_snapshots.csv` | Opening/closing line snapshots | `tracking/line_snapshots.py` |
| `tracking/line_movement_log.csv` | Line movement history | `tracking/line_movement.py` |
| `tracking/results.csv` | Settled game results | — REQUIRES FUTURE AUDIT — |

**Pick ID:** Deterministic `SHA1[:12]` of `(date, player, source_tab)` — dedup depends on this. Never change.

**Deployment write rule:** `pick_tracker.csv` write triggered only at Checkpoint 4 confirmation. No pre-confirmation writes to DEPLOYED state.

### 14.2 Fly.io Volume

Persistent volume `mlb_tracking` mounted at `/app/tracking` — survives deploys and machine restarts. Contains same CSV files as above when running in production API context.

### 14.3 Supabase (Cloud)

Used by FastAPI service only. Three required secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`.

Schema details: — REQUIRES FUTURE AUDIT — (consult `supabase/` directory)

### 14.4 Google Sheets Sync

Optional. `tracking/sheets.py`. Requires `GOOGLE_SHEETS_CREDS` env var (path to service-account JSON).

### 14.5 Adaptive Learning State

| File | Contents |
|------|---------|
| `tracking/learned_adjustments.json` | Active learned adjustments |
| `tracking/learned_adjustments.ARCHIVE-2026-05-29.json` | Archived prior adjustments |

---

## 15. Backtest Layer (`backtest/`)

| Module | Responsibility |
|--------|---------------|
| `backtest/runner.py` | Historical replay entrypoint |
| `backtest/calibration.py` | Brier score, calibration analysis |
| `backtest/outcomes.py` | Game outcome processing |
| `backtest/feature_importance.py` | Signal ranking analysis |

**Known limitation (accepted):** Statcast data is full-season in backtest (not point-in-time). Documented look-ahead. Do not "fix" by adding more look-ahead to live mode.

---

## 16. Daily Operational Sequence

```
1. ops_daily.py          — settle + integrity + drift + CLV
2. main.py               — generate today's picks
3. optimize_daily.py     — filter to portfolio
4. ~30min pre-game:      capture_closing_lines.py
5. Weekly:               monitoring_dashboard.py
```

---

## 17. Versioned Directory Isolation

v1–v4 live side-by-side. Each version tree is self-contained.

| Version | Status |
|---------|--------|
| `mlb_hr_engine_v4` | Production — all new work here |
| `mlb_hr_engine_v1` | Historical reference only |
| `mlb_hr_engine_v2` | Historical reference only |
| `mlb_hr_engine_v3` | Historical reference only |

**Hard rule:** Do not collapse, share modules between, or cross-import across versioned directories.

---

## 18. Unresolved Items (REQUIRES FUTURE AUDIT)

| Item | Gap | Priority |
|------|-----|---------|
| Supabase schema | Table names, column definitions, RLS policies not documented here | Medium |
| Weather API provider | Specific API provider for `clients/weather.py` not confirmed | Low |
| `tracking/results.csv` schema | Column definitions not verified | Low |
| `tracking/picks_log.csv` schema | Relationship to `pick_tracker.csv` unclear | Medium |
| `supabase/` directory contents | Not inspected during this audit | Medium |
| `strategies/` directory | Strategy definition files not inventoried | Low |
| `_design/` directory | Contents and status not inspected | Low |
| Fly.io memory — RESOLVED | `memory_mb = 512` confirmed via `fly.toml`. No discrepancy. Previous references to 1 GB or 256 MB were fabricated. | Closed |
| Adaptive learning loop (`tracking/auto_learn.py`, `tracking/adaptive_weights.py`) | Interaction with `model_prob` pipeline not confirmed | Medium |

---

*Source mapping summary and unresolved items follow below this document's main body. Treat this architecture.md as living spec — update on any protected-surface change.*
