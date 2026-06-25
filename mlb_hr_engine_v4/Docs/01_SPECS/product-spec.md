# MLB HR Engine v4 — Product Specification

**Version:** 1.0  
**Date:** 2026-06-09  
**Status:** AUTHORITATIVE  
**Scope:** mlb_hr_engine_v4 production system  
**Sources:** AGENTS.md, MASTER_TCC_DOCTRINE.md, FULL_SLATE_UX_DOCTRINE.md, PHASE3_REFINEMENT_DOCTRINE.md, ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md, OPS_DAILY_SETUP.md, architecture.md, wiki/doctrine/*, wiki/doctrine/app-shell-layout.md, wiki/doctrine/production-surface-truth.md, wiki/doctrine/mobile-architecture-v2.md  
**Mobile Architecture V2:** `MLB HR ENGINE/wiki/doctrine/mobile-architecture-v2.md` — persisted 2026-06-09. Authoritative mobile and responsive layout doctrine for production frontend shell.

---

## 1. Product Purpose

MLB HR Engine (v4) is an operator-facing quantitative intelligence system for MLB home run prop betting.

It performs five functions:
1. **Predict** — Computes per-batter, per-game HR probabilities using Poisson math calibrated on Statcast data
2. **Price** — Prices model probabilities against live sportsbook lines to identify positive-EV edges
3. **Filter** — Applies configurable threshold gates to surface only deployable picks
4. **Size** — Recommends Kelly-derived bet sizes based on edge magnitude and bankroll
5. **Track** — Logs deployment decisions, captures CLV, settles results, and archives historical performance

The system is not a general sports analytics tool, a prediction dashboard for public consumption, or a live betting interface. It is an operational decision-support layer for a single disciplined operator.

---

## 2. Operator Persona

**Primary operator + accepted multi-user direction (2026-06-25).** See Section 15.1.

The operator:
- Is the system owner and sole user
- Has domain knowledge of MLB, Statcast metrics, and sports betting math
- Makes daily deployment decisions on MLB HR props (primarily FanDuel)
- Requires operational clarity, not entertainment
- Works under time pressure during pre-game windows
- Uses the system as a deliberation layer — the slip is built before touching a sportsbook
- Treats CLV and P&L as separate, non-interchangeable performance measures

The operator's primary trust signals are data freshness, model calibration, and filter transparency. Any feature that obscures these signals is harmful.

---

## 3. Operational Goals

### Primary goals (define success)

| Goal | Measure |
|------|---------|
| Generate positive-EV picks | EV% > 0 on deployed picks; ROI positive over rolling 100 picks |
| Execute at market-sharp timing | Average CLV > 0 across session |
| Maintain model calibration | Brier score / calibration buckets within tolerance (see monitoring_dashboard.py) |
| Enforce deployment discipline | N_eff ≥ 3.0, no single pick > 20% session bankroll |
| Complete daily lifecycle | ops_daily.py runs, settlement resolves, CLV captured |

### Secondary goals (support primary)

- Identify JIG tactical exploits (arsenal mismatches) that MAIN may underweight
- Surface favorable environmental conditions (park, wind, temp) before game lock
- Maintain historical record for long-run calibration and override audit

---

## 4. MAIN Workflow — SCAN → QUALIFY → DEPLOY

MAIN is the quantitative, model-driven intelligence layer.

### 4.1 SCAN

Operator opens MAIN in the Streamlit dashboard. Picks are loaded from `pipeline.py`.

Scan mode: Full Slate tab → All Players mode. All batters visible across all games, sorted by batting order within each game. TCC filters highlight but do not remove.

Purpose: situational awareness across the full slate. Identify game count, urgency states, and environmental signals before narrowing.

### 4.2 QUALIFY

Operator applies TCC filters (Barrel%, HH%, xSLG, ISO, EV%, Edge%, Model Prob) to narrow the pool.

TCC filter layers:
- **Profile gate:** raw Statcast thresholds (Barrel, HH, xSLG, ISO, Pull Air, HR Window)
- **Market gate:** EV%, Edge%, Model Probability (MAIN-only)

Preset postures (defined in `filter_controls.py`):
- `Operational` — no batter-profile floors; EV/Edge gates qualify picks (default)
- `Selective` — Barrel ≥ 5%, HH ≥ 35%; restricts to power-contact profile
- `Elite Only` — Barrel ≥ 8%, HH ≥ 40%, EV ≥ 2%, Edge ≥ 1.5%

Picks ranked by composite score:
```
score = EV% × 0.40 + Edge% × 0.35 + Confidence × 0.25
```

Operator reviews Pre-Lineup Pool and confirmed starters separately. Cross-checks JIG targets against MAIN qualifiers.

### 4.3 DEPLOY

Operator constructs FanDuel slip via the Deployment layer:
- Reviews full pick queue before any deployment action (sequential, not bulk)
- Assigns slip category (Single / Tactical Double / Stack / Longshot / Controlled Volatility)
- Confirms sizing via Kelly output
- Passes four review checkpoints
- Logs deployment at Checkpoint 4 (`pick_tracker.csv` write)

The slip documents deliberation. FanDuel executes it. The two actions are physically separated.

---

## 5. JIG Workflow — MATCHUP → CONFIRM → EXPLOIT

JIG is the tactical, matchup-driven intelligence layer. Independent of MAIN. Uses separate scoring, separate filters, separate output.

### 5.1 MATCHUP

Operator opens JIG. Full universe scan with `All Tactical` preset.

Purpose: identify pitcher arsenal vulnerabilities and HVY pitch-mix modifier distribution. High-modifier targets surfaced before lineup confirmation.

JIG signals:
- HVY pitch-mix modifier — display-only; range [0.70, 1.40]; derived from `clients/pitch_mix.py`
- Arsenal exploitation — slot-specific pitcher vulnerability vs batter profile
- HR environment targeting — park, wind, temp weighted explicitly (not just as multipliers)

JIG picks ranked by HVY modifier descending. JIG scoring is not EV-driven.

### 5.2 CONFIRM

Operator validates environmental and handedness edges for top JIG targets. Checks:
- Pitcher lineup confirmation (TBD pitcher = reduced confidence)
- Weather conditions (wind direction/speed, temp)
- Park factor (extreme only — neutral suppressed)
- Handedness split vs pitcher arsenal

TCC filters for JIG:
- `All Tactical` — full universe, broad matchup exploration (default)
- `Selective` — Barrel ≥ 5%, modifier ≥ 100%; neutrals filtered out
- `Matchup+` — Barrel ≥ 6%, modifier ≥ 110%, HVY ≥ 40; elite exploit only

### 5.3 EXPLOIT

Operator stacks confirmed JIG signals. Aggressive posture: narrowed pool, stricter matchup thresholds, higher positional concentration acceptable when signals converge.

JIG targets that also qualify under MAIN become highest-conviction plays. Operator synthesizes — the system does not auto-merge.

---

## 6. MAIN/JIG Separation Doctrine

These rules are architectural invariants. Violation requires explicit operator authorization and doctrine update.

| Rule | Statement |
|------|-----------|
| Separate scoring | MAIN uses `EV% × 0.40 + Edge% × 0.35 + Confidence × 0.25`. JIG uses separate tactical scoring. No shared formula. |
| Separate filters | MAIN filters are model-supportive and broader. JIG filters are aggressive and matchup-specific. Never identical. |
| HVY signal isolation | HVY pitch-mix modifier is display-only on JIG side. Never folded into MAIN model probability or λ. |
| Separate output | MAIN and JIG produce separate pick lists. No composite/blended list without new explicit doctrine. |
| No hidden blending | No hidden composite scoring that mixes tactical/HVY signals with model scoring. Any blend must be explicit, documented, and operator-authorized. |
| TCC orchestrates only | TCC exposes filter controls. It does not compute MAIN or JIG scores. It does not alter model_prob, EV%, or Edge%. |
| Separate key namespaces | MAIN uses `tac_*` keys. JIG uses `jig_tac_*` keys. Cross-engine key reads are contamination. |

**What counts as contamination:**
- Feeding JIG tactical scores into MAIN's λ
- Using HVY modifier as a MAIN multiplier
- Running identical filters on both layers
- Producing a single merged pick list without operator authorization
- Injecting JIG signals into `pipeline.py` probability construction

---

## 7. User Workflows

### 7.1 Daily Pre-Game Workflow

```
1. CONFIRM SLATE
   Full Slate tab → All Players mode
   Verify game count, urgency states, weather impacts

2. ASSESS BATTLEFIELD (JIG)
   Open JIG → All Tactical preset
   Scan HVY modifier distribution
   Identify high-modifier targets before lineup confirmation

3. QUALIFY PICKS (MAIN)
   Open MAIN → Operational preset
   Review Pre-Lineup Pool and confirmed starters
   Apply Selective or Elite Only preset for deployment

4. NARROW FOR DEPLOYMENT
   Apply market gate (EV ≥ N%, Edge ≥ N%)
   Activate Portfolio Optimizer if deploying real capital
   Cross-check JIG targets vs MAIN picks

5. BUILD SLIP
   Assign picks to FD slip categories
   Verify N_eff and exposure before any deployment
   Confirm sizing via Kelly output

6. LOG AND TRACK
   Log to pick tracker at Checkpoint 4 (sportsbook field populated)
   Capture opening lines for CLV
   Run capture_closing_lines.py ~30 min before first pitch
```

### 7.2 Post-Game / Settlement Workflow

See Section 11.

### 7.3 Portfolio Optimizer Workflow

1. Enable Portfolio Optimizer in sidebar
2. Select optimizer preset
3. Optimizer filters pick set to maximize N_eff and minimize fragility
4. Rejected picks visible in expandable panel
5. Approved picks flow to slip construction

Optimizer EV/edge thresholds: not to be tuned until n ≥ 200 settled optimized picks with CLV data.

---

## 8. Feature Inventory

### 8.1 Core Intelligence Surfaces

| Feature | Surface | Module |
|---------|---------|--------|
| MAIN pick generation | Streamlit dashboard | `pipeline.py`, `engine/probability.py` |
| JIG tactical picks | Streamlit dashboard | `engine/filters.py`, `clients/pitch_mix.py` |
| Full Slate battlefield view | Streamlit dashboard | `app.py` |
| TCC filter controls | Streamlit dashboard | `filter_controls.py` |
| Portfolio Optimizer | Streamlit dashboard | `portfolio/optimizer.py` |
| Backtest runner | CLI | `backtest.py`, `backtest/` |

### 8.2 Pick Construction Signals

| Signal | Source | Engine |
|--------|--------|--------|
| Model HR probability (`model_prob`) | `engine/probability.py` | MAIN |
| Poisson λ | Batter base score × pitcher factor × env multipliers | MAIN |
| EV% vs market | `engine/ev.py` | MAIN |
| Edge% vs market | `engine/ev.py` | MAIN |
| Composite score | `output/ranker.py` | MAIN |
| Kelly bet size | `engine/sizing.py` | MAIN |
| HVY pitch-mix modifier | `clients/pitch_mix.py` | JIG (display) |
| Escalation tier | `output/ranker.py` / Full Slate logic | Both |

### 8.3 Batter Profile Inputs (λ construction)

- Barrel% (`barrel_pct` from Statcast)
- ISO, HR/FB, xSLG
- Exit velocity / Hard Hit%
- Pull Air%
- Platoon splits

### 8.4 Pitcher Vulnerability Inputs

- HR/9
- Barrel% Allowed
- xFIP
- Pitch arsenal (FB%, slider%, changeup%)
- HVY modifier components (JIG context only)

### 8.5 Environmental Multipliers

- Park factor (HR-specific, per `data/park_factors.py`)
- Wind speed/direction
- Temperature
- Humidity (extreme only)
- Handedness (H2H, platoon)

### 8.6 Operational Tools

| Tool | Trigger | Output |
|------|---------|--------|
| `ops_daily.py` | 8:00 AM daily (Task Scheduler) | Settlement, integrity check, CLV, ROI report |
| `capture_closing_lines.py` | Manual ~30 min pre-game | Closing lines → CLV computation |
| `optimize_daily.py` | Manual after picks generated | Portfolio-filtered pick set |
| `monitoring_dashboard.py` | Weekly | Full health dashboard, calibration drift |
| `analyze_calibration.py` | After threshold changes or n=500 milestone | Calibration bucket analysis |
| `settle_pick_tracker.py` | Via `ops_daily.py` Phase 1 | `hr_result` written for past picks |

### 8.7 Tracking & Persistence

| File | Purpose |
|------|---------|
| `tracking/pick_tracker.csv` | All pick records — model, deployment, settlement |
| `tracking/clv_log.csv` | CLV per pick |
| `tracking/line_snapshots.csv` | Opening/closing line snapshots |
| `tracking/line_movement_log.csv` | Line movement history |

### 8.8 API Surface (read-only external access)

- FastAPI service (`api/main.py`) on Fly.io
- Endpoints: picks, strategies, runs (Supabase JWT gated)
- Pipeline trigger: `POST /api/pipeline/run` (X-Cron-Secret gated)
- Static frontend on Vercel (`frontend/index.html`) may call FastAPI read endpoints

---

## 9. Deployment Workflow

Full doctrine: `ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md`

### 9.1 Pick Lifecycle States (sequential — no reversals)

```
QUALIFIED → SHORTLISTED → STAGED → REVIEWING → DEPLOYED → LIVE → SETTLED → REVIEWED → ARCHIVED
```

Non-standard: `ABANDONED` (removed before Checkpoint 4), `VOID` (DNP / game cancelled).

### 9.2 Deployment Confidence Tiers

| Tier | Conditions | Sizing |
|------|-----------|--------|
| CORE DEPLOYMENT | FIRE escalation, Suppression ≤ LOW, Barrel ≥ 10% | Full quarter-Kelly |
| HIGH CONVICTION | FIRE/STRONG, Suppression ≤ MODERATE, Barrel ≥ 8% | Full quarter-Kelly |
| TACTICAL EXPOSURE | STRONG/WATCH, Suppression ≤ MODERATE, Barrel ≥ 6% | Half quarter-Kelly |
| VOLATILITY EXPOSURE | Any escalation, odds ≥ +300 | Fixed floor (≤ 1% session bankroll) |
| WATCHLIST ONLY | Fails one exposure/governance check | None deployed |
| NO DEPLOYMENT | LOCKDOWN suppression or trust BLOCKED | None; no override |

**Hard rule:** Confidence tier does not auto-scale bankroll aggressively. CORE picks get a full quarter-Kelly unit — not more.

### 9.3 FD Slip Categories

| Category | Intent |
|----------|--------|
| SINGLE DEPLOYMENTS | Independent picks, no correlated risk |
| TACTICAL DOUBLES | Explicit correlation; intent documented |
| ESCALATION STACKS | N_eff impact shown before first leg added |
| LONGSHOT EXPOSURE | Capped unit; annotated; tracked separately |
| CONTROLLED VOLATILITY | Experimental; tracked separately from primary ROI |

Category assignment is always operator-initiated. No auto-assignment.

### 9.4 Review Checkpoints (four — non-skippable)

Deployment action at Checkpoint 4 triggers `pick_tracker.csv` write. No pre-confirmation DEPLOYED write.

### 9.5 Exposure Governance

| Dimension | Alert | Hard Gate |
|-----------|-------|-----------|
| Team concentration | 20% | 35% |
| Same-game concentration | 35% | 50% |
| Pitcher target count | 4 picks | 5 picks |
| N_eff | < 3.0 | < 2.0 |
| Session saturation | 60% | 90% |
| Fragility composite | > 50 | > 70 |
| Single pick exposure | — | 20% session bankroll |

### 9.6 Deployment Pacing Rules

- Full queue must render before deployment controls activate
- No "deploy all" control — each pick requires individual review
- Session bankroll confirmed before first deployment; not adjustable mid-session
- After each deployment: portfolio exposure updates before next pick presents

### 9.7 Execution Handoff

The slip is a human-readable execution summary. The operator carries it to FanDuel manually. No sportsbook API integration.

---

## 10. Tracking Workflow

Full doctrine: `ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md` Sections 4, 7

### 10.1 CLV Tracking

CLV measures timing quality, independent of outcomes.

```
CLV = close_no_vig_pct − deploy_no_vig_pct
```

Positive CLV = entry was sharper than close. Negative CLV = close moved against pick.

Four timestamps per deployed pick: OPENING, DEPLOYED, CURRENT, CLOSING.

Six timing states: EARLY STRIKE / MARKET DRIFT / LATE STEAM / PRICE COLLAPSE / VALUE RECOVERED / DEAD ENTRY

CLV and P&L are **never combined** into a single performance score. Separate panels. Separate analysis.

### 10.2 CLV Capture Workflow

1. `capture_closing_lines.py` runs ~30 min before first pitch
2. Fetches current odds from The Odds API for all deployed picks
3. Stores `snapshot_type=closing` in `line_snapshots.csv`
4. Computes CLV, writes to `pick_tracker.csv`
5. If run manually after deadline: tagged `snapshot_type=manual`, flagged `post_deadline=True`

### 10.3 Tracking Dashboard Hierarchy

Primary (always visible): Session P&L, CLV average, settled count, open positions  
Secondary (below fold): Escalation tier breakdown, barrel tier ROI, slip category performance, book performance  
Tertiary (drill-down): Individual pick timelines, override performance, calibration drift, portfolio fragility history

---

## 11. Settlement Workflow

### 11.1 Settlement Sequence

1. `settle_pick_tracker.py` (via `ops_daily.py` Phase 1) runs daily at 8:00 AM targeting prior day
2. Fetches game results from MLB Stats API game log
3. Writes `hr_result`: 0 (miss), 1 (hit), or `void` (DNP / game cancelled)
4. Computes P&L: `bet_dollars × payout factor`
5. Void picks: P&L = $0; excluded from timing efficiency analysis

### 11.2 Manual Settlement Override

```
python ops_daily.py 2026-05-17   # settle specific past date
python ops_daily.py --skip-settle   # skip settlement phase
```

### 11.3 Post-Slate Review (7 steps — non-skippable)

```
1. OUTCOME SUMMARY     — settled count, P&L, void count
2. PREDICTION REVIEW   — tier accuracy, model probability vs outcome
3. EXECUTION REVIEW    — CLV by pick, timing grade, deployment pacing
4. EXPOSURE REVIEW     — fragility score, concentration outcomes
5. DISCIPLINE REVIEW   — override audit, pacing adherence
6. LEARNING CAPTURE    — operator notes, flags for archive
7. ARCHIVE             — confirm all picks moved to ARCHIVED state
```

Prediction quality and execution quality are assessed in separate sections. A session without completed review is an unlearned session.

### 11.4 Variance Context

Every post-session P&L report includes variance context:
```
Expected value at deployment
Variance delta
N_eff this session
Estimated variance band (68% confidence)
Assessment: WITHIN/OUTSIDE EXPECTED VARIANCE
```

Purpose: prevent model adjustment after single-session outcomes.

---

## 12. Daily Operations Lifecycle

Full reference: `OPS_DAILY_SETUP.md`

| Time | Action | Trigger | Command |
|------|--------|---------|---------|
| 8:00 AM | ops_daily.py — settle + integrity + drift + CLV + ROI | Auto (Task Scheduler) | `run_ops_daily.bat` |
| Before picks | Generate today's picks | Manual | `python main.py` |
| After picks | Portfolio optimizer | Manual | `python scripts/analysis/optimize_daily.py` |
| ~30 min pre-game | Capture closing lines for CLV | Manual | `python capture_closing_lines.py` |
| Weekly | Full health dashboard | Manual | `python monitoring_dashboard.py` |

### 12.1 ops_daily.py Phases

| Phase | Action | Output |
|-------|--------|--------|
| 1 | Settle yesterday via MLB Stats API | `pick_tracker.csv` |
| 2 | Data integrity check | Warnings in log |
| 3 | Calibration drift monitor (9 dimensions) | Warnings in log |
| 4 | CLV capture | `pick_tracker.csv`, `line_snapshots.csv` |
| 5 | CLV summary | Report |
| 6 | ROI snapshot | Report |

Reports saved: `reports/daily_YYYY-MM-DD.txt`. Auto-deleted after 90 days.

### 12.2 Calibration Recheck Triggers

Re-run `analyze_calibration.py` when:
- Settled picks cross 500 (from current 262 as of 2026-06-09)
- 12–15% calibration bucket bias exceeds +4pp at n ≥ 50
- Any signal weight change
- Session 23 regression ceiling has been live ≥ 100 new real picks

Do not re-calibrate Platt parameters (a, b) without a new CV-fitted run.

---

## 13. Production Behavior

### 13.1 Four Independent Operational Surfaces

| Surface | Entry Point | Deployment |
|---------|-------------|------------|
| Streamlit Dashboard (operator) | `app.py` | Local operator machine |
| FastAPI Service | `api/main.py` | Fly.io (`mlb-hr-api`, region `iad`) |
| CLI Pick Runner | `main.py` | Local / GitHub Actions |
| Static Frontend | `frontend/index.html` | Vercel |

No runtime cross-dependency between surfaces. Streamlit and FastAPI share `pipeline.py` and `config.py` but not session state, auth, or caching.

### 13.2 Pipeline Sequence (invariant)

```
Fetch → Build batter profiles → Poisson P(HR≥1) = 1 − e^(−λ) → Price vs market → Filter → Rank → Size → Output
```

Reorder only with explicit operator authorization.

### 13.3 Degraded-State Behavior

| Degraded State | Behavior |
|----------------|---------|
| No odds (API failure) | Cards render muted; EV/Edge pills show "—"; model signals intact |
| No lineup (unconfirmed) | Urgency shows "PROJECTED" in blue; pick not hidden |
| No Statcast data | Fallback to blended/prior; labeled BLENDED or PRIOR |
| Prior-year pitch data | Pitcher label shows "(PRIOR YEAR)" |
| Stale API cache | Warning logged; validation skips/warns |

Never remove cards from display solely due to missing one data source. Never show raw Python exception text. Never show "None" or "nan" as a displayed value — coerce to "—".

### 13.4 Trust-State Ladder

Four states: FULL / DEGRADED / RESTRICTED / BLOCKED  
Governed by `engine/trust.py`.  
Trust-state refreshed at each queue expansion. Stale trust-state (> 15 min without refresh) triggers DEGRADED floor.

### 13.5 Fly.io Service Behavior

```
Auto-stop: true (scale to zero when idle)
Auto-start: true
Min machines: 0
Memory: 512 MB (pipeline needs ~300 MB)
Persistent volume: mlb_tracking → /app/tracking (survives deploys)
```

### 13.6 GitHub Actions Cron

Normal pipeline runs triggered via `api/cron.py`. Manual trigger via `POST /api/pipeline/run` (X-Cron-Secret gated) is a fallback only.

---

## 14. Product Scope Boundaries

### What this product IS

- Single-operator quantitative HR prop betting tool
- Statistical model + market pricing + deployment workflow
- Pick tracking, CLV measurement, and settlement logging
- Operator dashboard for daily pre-game decision-making
- Historical performance intelligence for calibration and improvement

### What this product IS NOT

- A public-facing betting advice platform
- A DFS (daily fantasy sports) tool
- A live in-game betting tool
- A general sports prediction engine
- A real-money execution layer (no sportsbook API integration)
- A social or sharing platform

---

## 15. Non-Goals

The following are explicitly out of scope. Do not implement without new doctrine and operator authorization.

| Non-Goal | Reason |
|----------|--------|
| Mobile-native optimization | Desktop is primary; mobile is a degraded access mode. No mobile-specific CSS, touch controls, or PWA configuration. |
| DFS lineup optimization | Different product. Different math. Different output. |
| Live in-game betting | No live score feed, no in-play model. Pre-game picks only. |
| Automated sportsbook execution | Deliberation layer and execution platform are intentionally separated. |
| Combined MAIN+JIG merged output | MAIN/JIG separation is an architectural invariant. A merged list requires new explicit doctrine. |
| Dynamic AI-driven preset suggestions | TCC presets are static, transparent threshold bundles. No AI auto-tuning of filters. |
| Sound / push notifications | Not in scope. Future `spec_operational_audio_future_doctrine.md` if ever authorized. |
| Streaming / real-time score tracking | Play-by-play is a different product surface. |
| Non-MLB sports | Engine is MLB-specific (Statcast, park factors, HR Poisson math). |
| "Responsible gambling" / limit features | Not relevant to single professional operator context. |
| Automatic model recalibration | Platt parameters require CV-fitted runs, not auto-adjustment. |

---

## 15.1 Multi-User Direction (Accepted 2026-06-25)

The system supports multiple users (operator + friends). Each user deploys and tracks their own picks. Auth is Supabase JWT (`api/auth.py`), which already gates all read endpoints.

**Phased build:**
1. **Phase 1 (write-endpoint gate):** `POST /api/tickets/leg` and `POST /api/tickets/complete` gated behind existing `require_auth`. No schema change required.
2. **Phase 2 (per-user schema):** Add `user_id` column to tickets/legs tables. Update `cache.py` to stamp `user.get("sub")`. Add Supabase RLS policies for per-user data isolation.
3. **Phase 3 (friend access):** Friend signup/login flow + token-authenticated frontend ticket capture.

**Invariants unchanged:** MAIN/JIG separation, scoring formulas, calibration parameters, pipeline sequence, and all other architectural invariants are unaffected by multi-user support.

---

## 16. Production Frontend Shell Architecture

**Source:** `wiki/doctrine/app-shell-layout.md`, `wiki/doctrine/production-surface-truth.md`, `wiki/doctrine/mobile-architecture-v2.md`  
**Mobile Architecture V2:** `MLB HR ENGINE/wiki/doctrine/mobile-architecture-v2.md` — persisted 2026-06-09. Canonical mobile and responsive layout doctrine. Covers shell zone hierarchy, navigation model, breakpoint behavior, progressive disclosure, MAIN/JIG separation on mobile, production fix preservation, and stale elements not to copy. See that document for full mobile doctrine.

### 16.1 Canonical Shell Zones

| Zone | Component | Role |
|------|-----------|------|
| Top | TopBar | Branding, date, status strip |
| Navigation | engine-lens nav | Switch between MAIN and JIG engine surfaces and their lens views |
| Banner | LiveTargets | Live HR threat summary, escalation badges |
| Center | Stage | Central viewport — primary operator action surface |
| Right | RightRail | Secondary intelligence panel |
| Left/overlay | NavPanel | Navigation and view control |
| Right/secondary | StrategyRail | Strategy and bet-sizing context |

### 16.2 Navigation Model

Navigation is **engine → lens**. Top-level switch: MAIN engine vs JIG engine. Within each engine: lens views (Full Slate, Leaderboard, Matchup, etc.).

Engine identity colors are doctrine-locked:

| Engine | Identity Color |
|--------|---------------|
| MAIN | Red |
| JIG | Cyan |

Do not swap or blend engine identity colors.

### 16.3 Workflow-First Navigation

The shell presents engine surfaces in operational workflow order. MAIN workflow (SCAN → QUALIFY → DEPLOY) drives lens ordering within the MAIN surface. JIG workflow (MATCHUP → CONFIRM → EXPLOIT) drives JIG lens ordering.

### 16.4 Command-Center Hierarchy

The command strip (TopBar + LiveTargets) anchors the operator view at all times. It is never scrolled away from. It communicates:
- Slate state and game count
- Active escalation counts (Critical / Dangerous / Elevated)
- Pipeline freshness (last sync timestamp)
- Active environmental threats

Per FULL_SLATE_UX_DOCTRINE.md, the operator's full-slate reconnaissance should complete in under 90 seconds for a 12-game slate. The command-center hierarchy supports this by surfacing Critical and Dangerous escalations above the fold without operator action.

### 16.5 Claude Design Preservation Rules

Architecture closed surfaces that must not be modified without explicit operator authorization:
- Engine-lens navigation routing
- `session_state` ownership and hydration sequence
- Cache ownership and invalidation rules
- Full Slate orchestrator logic
- Modal architecture
- MAIN/JIG identity boundaries (colors, scoring, filter namespaces)

These rules apply to both the Streamlit dashboard (`app.py`) and the static production frontend (`frontend/`). The two surfaces are isolated and do not share session state, auth, or cache.

### 16.6 ui-system.md Readiness Assessment

**Status:** `mlb_hr_engine_v4/Docs/01_SPECS/ui-system.md` is **READY TO RECONSTRUCT** after `product-spec.md` and `mobile-architecture-v2.md` are committed.

Prerequisite sources now available:
- `product-spec.md` (this file) — Section 16 shell architecture and zone doctrine
- `wiki/doctrine/mobile-architecture-v2.md` — mobile breakpoints, progressive disclosure, touch targets, token inventory

When `ui-system.md` is populated, audit `mobile-architecture-v2.md` against formalized token set and update any diverging values. Until then, `wiki/doctrine/visual-design-tokens.md` is authoritative for token values.

**Do not claim implementation is authorized.** ui-system.md reconstruction is a documentation task only.

---

## 18. Config Authority

`config.py` is the single source of truth for:
- Model thresholds and signal weights
- League baselines
- Calibration parameters
- Rollback feature flags
- Kelly fraction
- Park factor constants

**Never duplicate numeric constants from `config.py` into this document or any documentation.** Values in docs drift; values in code are live.

---

## 18. Protected Surfaces

These surfaces must not be modified without explicit operator authorization:

- `engine/probability.py` — core `model_prob` calculation
- `engine/calibration.py` — Platt parameters
- `engine/filters.py` — JIG filter thresholds
- `config.py` numerical constants — model parameters
- `tracking/pick_tracker.py` schema — deterministic `pick_id` dedup depends on it
- `api/main.py` routing — closed surface
- `api/cache.py` — closed surface
- MAIN/JIG identity boundaries
- `session_state` ownership and hydration sequence
- Routing architecture
- Cache ownership and invalidation rules
- Full Slate orchestrator logic

---

*End of product specification.*  
*No runtime files modified. No commits made.*  
*Authority: Claude Code (Reconciliation) · 2026-06-09*  
*Mobile Architecture V2 (Claude Design Preservation Version) persisted at `MLB HR ENGINE/wiki/doctrine/mobile-architecture-v2.md`. Section 16 updated to cite canonical source.*
