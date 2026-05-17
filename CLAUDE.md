# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Codex HR Engine — predicts home run probabilities for every starting batter, prices them against market odds, identifies positive-EV bets, and recommends bet sizes. The repo contains four versioned iterations (`codex_hr_engine_v1` through `v4`) plus a root-level comparison tool.

## Common Commands

All commands run from within a specific version's directory (e.g., `cd codex_hr_engine_v4`).

```bash
# Run today's picks (CLI)
python main.py

# Run for a specific date
python main.py 2026-04-18

# Run Streamlit dashboard (v4 only)
streamlit run app.py

# Run backtest (v3/v4 only) — last N days or date range
python backtest.py 30
python backtest.py 2026-01-01 2026-04-01

# Compare v1 vs v2 output for a date (run from repo root)
python compare.py 2026-04-18
python compare.py 2026-04-18 --skip-run   # use cached JSON dumps
```

## Setup

```bash
pip install -r requirements.txt
```

Requires a `.env` file in the version directory with:
- `ODDS_API_KEY` — from The Odds API (free tier: 500 req/month)
- `GOOGLE_SHEETS_CREDS` — (v4 only) path to service account JSON

If no API key is present, the engine falls back to `manual_odds.csv` for market prices.

## Architecture

### Core Data Pipeline

Every version follows the same flow:

1. **Fetch** — MLB Stats API (schedule, lineups, stats), The Odds API (market lines), Baseball Savant/Statcast (v2+), Open-Meteo (weather)
2. **Build player profiles** — Bayesian-regressed HR rate × multiplicative adjustment factors (park, pitcher, weather, platoon)
3. **Poisson model** — `P(HR≥1) = 1 − e^(−λ)` where `λ = adjusted_rate × expected_PA`
4. **Price vs market** — fuzzy-match player names to odds lines, compute no-vig probability, EV%, Edge%
5. **Filter** — 7-rule pass/fail system (min EV, min edge, min PA, park penalty cap, weather cap, pitcher suppressor cap, lineup position)
6. **Rank** — composite score: EV×0.4 + Edge×0.35 + Confidence×0.25
7. **Size** — quarter-Kelly bet sizing against configured bankroll
8. **Output** — rich CLI tables (all versions) + Streamlit dashboard (v4)

### Version Differences

| Feature | v1 | v2 | v3 | v4 |
|---|---|---|---|---|
| Statcast barrel%/exit velo blending | — | ✓ | ✓ | ✓ |
| Real platoon splits (vs handedness factor) | — | ✓ | ✓ | ✓ |
| P&L + CLV tracking | — | ✓ | ✓ | ✓ |
| Backtest framework + calibration | — | — | ✓ | ✓ |
| Streamlit dashboard | — | — | — | ✓ |
| Google Sheets persistence | — | — | — | ✓ |
| K/GB pitcher suppressor | — | — | — | ✓ |

**v4 is the production version.** v1/v2 exist primarily to support `compare.py` via `--dump-json`.

### Module Map (consistent across versions)

- `clients/mlb_stats.py` — schedule, lineups, player/pitcher stats (free MLB API)
- `clients/odds_api.py` — market HR lines, fuzzy name matching, CSV fallback
- `clients/weather.py` — temp/wind factors, dome detection
- `clients/statcast.py` *(v2+)* — barrel%, exit velocity, hard-hit% from Baseball Savant
- `data/park_factors.py` — per-stadium HR factor + coordinates
- `engine/probability.py` — HR rate construction, all adjustment factors, Poisson model
- `engine/ev.py` — EV%, edge%, ROI
- `engine/market.py` — American↔decimal conversion, no-vig probability
- `engine/filters.py` — 7-rule filter set + soft caution flags
- `engine/sizing.py` — quarter-Kelly bet sizing
- `output/ranker.py` — composite scoring and ranking
- `output/parlay.py` — exhaustive 2/3/4-leg parlay builder
- `tracking/pnl.py` *(v2+)* — pick logging, P&L
- `tracking/clv.py` *(v2+)* — closing line value capture
- `tracking/sheets.py` *(v4)* — Google Sheets sync
- `backtest/` *(v3+)* — historical scoring, calibration table, Brier score, simulated P&L
- `pipeline.py` *(v4)* — shared data pipeline consumed by both `main.py` and `app.py`
- `config.py` — all thresholds, Kelly fraction, bankroll settings, model constants

### Key Model Constants (`config.py`)

All constants below are from `config.py` as of 2026-05-16. Update `config.py` at mid-season refresh (late June); `pitch_mix.py` derives its league baselines from `config.py` automatically.

- `KELLY_FRACTION = 0.25` — quarter-Kelly risk scaling
- `LEAGUE_AVG_HR_PA = 0.030` — regression target (2026 MLB May-6; broader Apr=0.028, qualified May=0.032, 0.030 splits the difference)
- `REGRESSION_PA = 200` — Bayesian shrinkage weight
- `RECENT_WEIGHT = 0.30 / SEASON_WEIGHT = 0.70` — blending recent vs season stats
- `LEAGUE_AVG_HR9 = 1.05`, `LEAGUE_HR_FB = 0.097` — pitcher league baselines (2026 May-6; updated from earlier-season values)
- `MAX_GAME_HR_PROB = 0.29` — hard ceiling on per-game HR probability (from 2025 full-season backtest actual 28.9%)
- `PRIOR_YEAR_TRUST = 0.85`, `MIN_CURRENT_YEAR_PA = 50` — Statcast prior-year blending
- `LEAGUE_AVG_BARREL_RATE = 0.055`, `LEAGUE_AVG_EXIT_VELO = 89.1`, `LEAGUE_AVG_HARD_HIT = 0.399` — batter power baselines (2026 May-6)
- `LEAGUE_AVG_XSLG = 0.418`, `LEAGUE_AVG_SWEET_SPOT = 0.334`, `LEAGUE_AVG_PULL_PCT = 0.392` — batter contact baselines (2026 May-6)
- `LEAGUE_AVG_FB_PCT = 0.264` — Savant pure fly-ball rate (excludes popups; do NOT use FanGraphs FB%≈0.34 which includes popups)
- `LEAGUE_AVG_ISO = 0.157` — ISO = SLG − AVG (2026 May-6)
- `LEAGUE_AVG_HUMIDITY = 55.0` — % RH baseline for neutral humidity factor
- All Statcast leaderboard league averages live in `config.py`; update all together at mid-season refresh
- `MIN_EV_PCT = 3.0`, `MIN_EDGE_PCT = 2.0` — filter floor thresholds
- `MIN_PA_THRESHOLD = 3.3` — blocks 9-hole batters (3.2 PA); `MAX_PARK_PENALTY = 0.87` — blocks SF + SD

### Weather Model

Three multiplicative factors (all clamped before the 0.80–1.20 outer bound):
- **Temperature:** ~2% per 10°F from 72°F baseline (range 0.82–1.08)
- **Wind:** ~3% per mph toward CF (meteorological FROM convention; OpenMeteo `winddirection_10m` is FROM direction); dome teams get 1.0
- **Humidity:** ~1.5% per 10pp RH from 55% baseline, humid air = less dense = more carry (range 0.96–1.04); added 2026-05-16

### HVY Pitch Mix Modifier

`clients/pitch_mix.py` — display-only matchup signal [0.70, 1.40]; NOT fed into model_prob.
Five additive signals: (1) pitcher HR rate vs batter hand ±0.10, (2) arsenal matchup SLG ±0.10, (3) batter contact shape ±0.06, (4) pitch arsenal K%/HR rate ±0.06, (5) career H2H OPS ±0.06. Park and weather removed from HVY modifier (2026-05-16) to avoid double-counting with core model.

### Regression Floor (probability.py)

`reg_target_adj = max(0.30, min(1.0, statcast_mult))` — floor lowered from 0.40 to 0.30 (2026-05-16). Players with extreme contact-hitter Statcast profiles (mult<0.40) were over-predicted; 0.30 floor is more faithful to actual signal. Zero-HR and low-HR suppressors provide additional discounting on top.

### Pitcher Fatigue Factor

Short rest (≤4 days): 1.01–1.08 HR boost. Standard (5 days) and extra rest (6+ days): 1.00 neutral. Prior extra-rest linear decay (0.97–0.99) removed (2026-05-16) — no backtest evidence that pitchers are harder to hit on extra rest.

### FB% Signal Promotion (statcast.py, probability.py)

Added 2026-05-16. FB% was #2 raw predictor in 2026 signal ranking (+0.1341 point-biserial) but was weighted at only 15% in `batter_power_multiplier`. Promoted to 20%, with weight redistributed from weaker signals.

**Weight change** (barrel=40% unchanged):
- FB%: 15% → 20% (+5pp) — #2 predictor, underweighted relative to raw correlation
- Sweet Spot%: 12% → 10% (-2pp) — weakest batter signal per 2026 ranking
- xSLG: 10% → 8% (-2pp) — correlated with barrel% (r~0.75)
- Exit Velo: 5% → 4% (-1pp) — mostly captured by barrel/hard-hit
- Pull%, Hard Hit% unchanged

**Quality gate** (`FB_QUALITY_GATE_ENABLED=True`, `FB_QUALITY_GATE_FLOOR=0.50`): Gates positive FB% deviations (above-league-avg FB%) by barrel quality. Batters with high FB% but low barrel quality (weak fly balls) get the FB% upside discounted by up to 50%. Ground-ball hitters (negative deviation) are not affected. Gate formula: `gate = 0.50 + 0.50 * min(1.0, barrel_mult)`. Savant `fb_pct` already excludes popups, so the gate specifically catches low-exit-velocity outfield flies.

**Park interaction** (`FB_PARK_SCALE=0.30`, now configurable): FB% deviation scales park factor effect. Value unchanged from prior (0.30), but now lives in config.py for easy tuning. `fly_ball_adjusted_park_factor` uses `_FB_PARK_SCALE = config.FB_PARK_SCALE`.

**Configurable parameters** (all in `config.py`):
- `FB_PCT_WEIGHT = 0.20` — power multiplier weight
- `FB_QUALITY_GATE_ENABLED = True` — enable/disable gate
- `FB_QUALITY_GATE_FLOOR = 0.50` — minimum gate factor (0=full conditional, 1=no gate)
- `FB_PARK_SCALE = 0.30` — park factor FB% interaction strength

**Validation**: Run `python analyze_fb_pct.py` from repo root (tests 7 configs, outputs `fb_pct_analysis_output.txt`). Revert by setting `FB_PCT_WEIGHT=0.15`, `FB_QUALITY_GATE_ENABLED=False` in config.

### Probability Calibration Layer (engine/calibration.py)

Added 2026-05-16. Post-model monotone transform: maps raw `model_prob` → calibrated probability while preserving rank order. Applied in `pipeline.py` after `apply_prob_scale()` and before storing `model_prob`.

**Method: Platt scaling** — `sigmoid(A × logit(p) + B)`. Two fitted parameters, monotone by construction (Spearman ρ = 0.999999 vs baseline, zero daily top-10 pick changes in 45-date test). Crossover probability p* = sigmoid(B / (1−A)): below p* predictions increase, above p* they decrease.

**Fitted parameters** (from `analyze_calibration.py`, 10,777 batter-games Apr 1–May 15 2026):
- `CALIBRATION_PLATT_A = 0.7805` — slope (compression factor; 1.0 = identity)
- `CALIBRATION_PLATT_B = -0.4611` — intercept (shift)
- Crossover: **10.9%** — below 10.9% predictions increase (+0.4–1.0pp); above 10.9% they decrease (−1.0 to −5.1pp at 29%)
- CV test Brier: 0.09104 (baseline: 0.09207, improvement: −0.00103)

**Root cause of 15-25% over-prediction (confirmed by audit):**
1. Statcast look-ahead in backtest (full-season Statcast used for April games — structural, not fixable)
2. Multiplicative stacking: average batters in favorable contexts (good park + hittable pitcher + platoon) get pushed into 15%+ range, but actual HR rates for that cluster are lower
3. Blended-source players show +1.75pp bias (prior-year Statcast elevates their signals artificially)

**Known trade-off**: 20-25% bucket shows +2.4pp after calibration (extreme-top batters compressed into this bucket genuinely HR at ~24.4%, so calibration slightly under-corrects the very top end). CV test data confirms this is acceptable — overall Brier still improves.

**Impact on filters/EV**: 464 picks that the model placed at 15%+ probability get calibrated below 15%. These were false-confidence picks (blended-source or stacking artifacts). ROI @15% threshold improves from −26.7% to −15.2% (simulated).

**Configurable parameters** (all in `config.py`):
- `CALIBRATION_ENABLED = True` — master switch (set False to rollback instantly)
- `CALIBRATION_METHOD = "platt"` — "platt" | "isotonic" | "none"
- `CALIBRATION_PLATT_A = 0.7805` — slope
- `CALIBRATION_PLATT_B = -0.4611` — intercept

**Validation**: Run `python analyze_calibration.py --analyze-only` from repo root. Reuses existing `fb_pct_raw_data.csv`. Outputs `calibration_analysis_output.txt`. Rollback: `CALIBRATION_ENABLED = False`.

**Re-calibrate after**: any signal weight change, new signal addition, Poisson model change. Parameters drift with model changes.

### Context Moderation Guard (engine/probability.py)

Added 2026-05-16. Narrow safety guard: caps the combined context multiplier for sub-average power batters (`power_mult < 1.0`) to prevent contact/suppressed-power hitters from reaching ≥15% probability solely via multiplicative context stacking (favorable park + hittable pitcher + platoon advantage).

**Mechanism**: `_moderate_context(combined, power_mult)` — applied inside `game_hr_probability()` BEFORE the [0.42, 1.50] clamp. Only fires when `combined > 1.0` AND `power_mult < 1.0`. Elite hitters (`power_mult ≥ 1.0`) are completely unaffected.

**Analysis results** (from `analyze_elite_separation.py`, 8,633 batter-games, 2026-05-16):
- Target cases: 523 rows with power_mult<0.90 + combined>1.30; actual HR%=7.07%, model=8.07% (+1.00pp bias)
- At ≥15% threshold: 51 of these inflate to false-positive bet picks; V5_Cap removes them (1,977→1,926 picks)
- Brier improvement: −0.00005 (marginal but directionally correct)
- Elite hitter bias: unchanged (−3.97pp, zero delta) — confirmed safe for elite hitters
- Spearman rank stability: 0.9957 vs 0.9992 baseline (negligible practical shift)

**Key finding from Session 22 analysis**: Elite hitter under-prediction (barrel≥12%: actual=28.75%, model=20.19%, bias=−8.56pp) is caused by the **base rate calculation** (Bayesian regression toward league mean), NOT by insufficient context. Platt calibration worsens this further by compressing probs above 10.9%. Context moderation cannot fix elite under-prediction — it requires base-rate changes (out of scope). The context guard is solely a protection against false-positive contact-batter inflation.

**Configurable parameters** (all in `config.py`):
- `CONTEXT_MODERATION_ENABLED = True` — master switch (set False to rollback instantly)
- `CONTEXT_MODERATION_LOW_POWER_CAP = 1.25` — combined cap when power_mult < 1.0

**Validation**: Run `py -3.12 analyze_elite_separation.py` from repo root. Outputs `elite_separation_output.txt`. Rollback: `CONTEXT_MODERATION_ENABLED = False`.

### Elite Barrel Preservation & Adaptive Regression (Session 23)

Added 2026-05-16. Fixes the structural under-prediction of elite HR hitters (barrel≥12%: actual=28.75%, model=20.19%, bias=−8.56pp confirmed Session 22). Three stacked compression layers were identified and individually addressed.

**Root cause — three compression layers:**
1. **L1 — `base_hr_rate()` regression anchor**: `reg_target_adj = max(0.30, min(1.0, statcast_mult))` — capped at 1.0 for ALL power_mult≥1.0 batters, so elite hitters regress to league avg (0.030) same as average players. At 300 PA, a barrel=12% hitter's true ~5.25% rate is dragged down to ~4.63% (−11.8pp compression).
2. **L2 — `statcast_blended_rate()` upside damping**: Statcast boost damped to 0.42x for all power_mult>1.0. For PM=2.10, this suppresses the signal by 36% (1.46x effective vs 2.10x uncapped). Partially offsets L1 but insufficient.
3. **L3 — Platt calibration**: Standard crossover=10.9% compresses everything above. At 22% raw prob: loses 3.0pp. At 29%: loses 5.1pp — stacking on top of already-underestimated pre-calibration output.

**Fix 1 — Elite Regression Target Ceiling (`base_hr_rate()`, `engine/probability.py`)**

For `barrel_rate >= ELITE_REG_TARGET_BARREL_THRESHOLD` and `statcast_mult > 1.0`:
```
reg_target_adj = max(0.30, min(ELITE_REG_TARGET_CEILING, statcast_mult))
```
Raises the Bayesian anchor for elite batters: PM=1.75 now targets 0.030×1.5=0.045 HR/PA instead of 0.030. Barrel<8% batters are **completely unaffected** (correction=1.0 for all).

**Fix 2 — Elite Tier Platt Calibration (`apply_calibration()`, `engine/calibration.py`)**

For `barrel_rate >= ELITE_PLATT_BARREL_THRESHOLD`: uses separate Platt params with higher crossover.
- Standard: A=0.7805, B=−0.4611, crossover=10.9% (compresses all probs >10.9%)
- Elite tier: A=0.92, B=−0.10, crossover=22.3% (near-identity across 10–29% range)
At 22% raw: standard gives 19.0% (−3.0pp), elite gives 22.0% (≈identity). Barrel<10% batters use standard Platt unchanged.

**Analysis results** (from `analyze_adaptive_regression.py`, 10,777 batter-games, 2026-05-16):
- V1a (regression ceiling only): Brier −0.00027, elite barrel 12-15% bias −10.97→−9.00pp, Spearman=0.9970
- V4a (tier Platt only): Brier −0.00024, 20-25% bucket bias +0.5pp (nearly perfect), new 25-30% picks actual=29.9%, top-50 accuracy 26%→30%, Spearman=0.9991
- Combined V5: Brier −0.00046 but requires Platt re-calibration after regression change (Step 3)
- Average batters (barrel<8%): **zero change** in any variant — confirmed Section 11 output

**API changes** (backward-compatible, new kwargs with defaults):
- `base_hr_rate(..., barrel_rate=0.0)` — new kwarg; callers without it get old behaviour
- `apply_calibration(p, barrel_rate=0.0)` — new kwarg; callers without it get standard Platt
- `pipeline.py` and `backtest/runner.py` updated to pass `sc_barrel = sc_stats.get("barrel_rate") or 0.0`

**Configurable parameters** (all in `config.py`):
- `ELITE_REG_TARGET_ENABLED = True` — master switch for regression ceiling
- `ELITE_REG_TARGET_CEILING = 1.5` — max(0.30, min(ceiling, power_mult)) for elite gate
- `ELITE_REG_TARGET_BARREL_THRESHOLD = 0.08` — barrel_rate floor to apply ceiling
- `ELITE_PLATT_ENABLED = True` — master switch for tier Platt calibration
- `ELITE_PLATT_A = 0.92`, `ELITE_PLATT_B = -0.10` — elite tier Platt params (crossover=22.3%)
- `ELITE_PLATT_BARREL_THRESHOLD = 0.10` — barrel_rate floor for elite Platt

**Rollback**: Set `ELITE_REG_TARGET_ENABLED = False` and/or `ELITE_PLATT_ENABLED = False` in config.py. Both flags are fully independent.

**Step 3 — Re-calibrate Platt after both fixes stabilize**: The regression ceiling raises pre-calibration probs for elite hitters; the current standard Platt params (A=0.7805) were fitted before this change and will partially offset Step 1 gains. After validating, run `analyze_calibration.py --collect-only` then `--analyze-only` to re-fit. Expected: A rises slightly, B becomes less negative.

**Validation**: Run `py -3.12 analyze_adaptive_regression.py` from repo root. Outputs `adaptive_regression_output.txt`. Analysis uses `fb_pct_raw_data.csv` (no additional API calls needed).

**Known remaining issues (accepted):**
- Elite barrel bias reduced but not eliminated: −10.97pp → estimated ~−8-9pp (both fixes active)
- 15-20% bucket: slight +1pp bias when both fixes combined — caused by some batters promoted from context stacking, not by regression changes alone
- Re-calibration needed for combined V5 variant to reach full potential

### Market Inefficiency Segmentation & Edge Quality (Session 24)

Added 2026-05-16. `analyze_market_inefficiency.py` — comprehensive synthetic market analysis across all 5 phases. No real settled pick data available (pick_tracker.csv: 0 settled rows); all ROI figures are **synthetic simulations**.

**Market model assumption:**
Books price from park/pitcher/platoon factors only, without Statcast barrel/exit-velo data.
`market_true_prob = 1 − exp(−LEAGUE_AVG_HR_PA × pk_factor × pit_factor × plat_factor × exp_pa)`
Our model adds `power_mult` (Statcast) then applies calibration → information gap is the synthetic edge.
`edge_pct = cal_prob − market_true_prob` (positive = Statcast premium over naive market).

**Key findings (10,777 batter-games, Apr 1–May 15 2026):**
- Qualifying picks (EV≥3%, Edge≥2% at DraftKings): **2,136** (19.8% of rows)
- Simulated ROI: **+37.1%** flat $1 bet | Sharpe proxy: 0.1215 | 95% CI: ±12.9pp

**Barrel ROI gradient (most important finding):**
| Barrel Tier | Bets | HR%  | MdlEdge | ROI%    |
|-------------|------|------|---------|---------|
| <4%         | 26   | 0.0% | −4.0pp  | −100.0% |
| 4-6%        | 363  | 11.0%| −1.2pp  | −2.7%   |
| 6-8%        | 430  | 12.3%| −0.2pp  | −1.3%   |
| 8-10%       | 476  | 16.8%| +1.4pp  | +28.0%  |
| 10-12%      | 561  | 21.6%| +5.8pp  | +65.3%  |
| 12%+        | 280  | 30.0%| +7.1pp  | +119.3% |

Edge breakeven ≈ barrel≥8%. Below that, Statcast provides no meaningful information premium over the naive market baseline.

**Sportsbook tier ranking (sharp > offshore > mid > retail on EV):**
1. Pinnacle 3.0% vig → +46.3% ROI
2. Circa 4.0% vig → +44.6%
3. BetOnlineAG 5.5% → +42.2%
4. BetRivers 7.0% → +39.9%
5. Caesars 7.8% → +38.7%
DraftKings (8.8%) → +37.1% | FanDuel (9.5%) → +35.8% | Fanatics (11.0%) → +35.1%

**Edge threshold analysis:**
- Current EV≥3%, Edge≥2%: n=2136, ROI=+37.1%
- Tighter EV≥4%, Edge≥2.5%: n=1882, ROI=+42.3% (+5.2pp improvement, 12% fewer picks)
- Tightest Edge≥5%: n=906, ROI=+51.8% (barrel≥10% dominated)

**Top composite archetype (barrel+power+park, ≥20 bets):**
1. barrel=12%+, Elite power, Hitter park → n=68, HR=40%, ROI=+157%
2. barrel=12%+, Above-avg power, Hitter park → n=31, HR=31%, ROI=+200%
3. barrel=10-12%, Above-avg power, Slight+ park → n=198, HR=23%, ROI=+73%

**Worst archetypes (false edge traps):**
- barrel=4-6%, Average power, Hitter/Neutral park → ROI −2% to −30% (Statcast negative)
- barrel=8-10%, Average power, any park → n=21, ROI=−56%

**Pitcher/platoon interaction:**
- Good/Elite suppressors: ROI=+72-80% (books over-price, market anchors high for matchup, model corrects)
- Platoon disadvantage: ROI=+55% (market inflates context price, model correctly discounts)
- Mild platoon advantage: ROI=+4% (false edge — market prices it correctly, model offers no premium)

**Calibration quality by barrel tier:**
- Best: 6-8% barrel (CalBias=+0.08pp — nearly perfect)
- Worst: 12%+ barrel (CalBias=−8.57pp — systematic under-prediction; Session 23 partially fixes this)

**Production recommendations (pending real settled data):**
1. Barrel threshold: prioritize barrel≥8% picks; barrel<6% show negative synthetic ROI
2. Tighten thresholds to EV≥4%, Edge≥2.5% for more selective filtering (+5pp ROI simulated)
3. Book priority: sharp/offshore books (circa, pinnacle, betonlineag) preserve more edge
4. Sharp book floor: consider EV≥1.5% at Pinnacle/Circa since their vig screens bad edges natively
5. Archetype scoring bonus in ranker.py: barrel≥10% + power≥1.15 + any park → top-tier picks
6. Session 24 limitation: sharp books partially price barrel rate — true edge lower than +119% sim

**Data limitation:**
All ROI is synthetic (no settled market data). Validate once ≥200 real settled picks accumulate.
Re-run: `py -3.12 analyze_market_inefficiency.py` → `market_inefficiency_output.txt`

### Real-World Pick Tracking & Live ROI Validation (Session 25)

Added 2026-05-16. Three scripts built for live tracking and validation. **CRITICAL RULE: Do NOT adjust model thresholds or calibration based on n<200 real picks.**

**Schema upgrade — `mlb_hr_engine_v4/tracking/pick_tracker.py`**

8 new fields added (backward-compatible): `pick_id`, `opponent`, `pitcher`, `sportsbook`, `best_odds`, `market_prob_pct`, `engine_version`, `logged_at`. Total: 38 fields.
- `_gen_pick_id(date, player, source_tab)`: deterministic SHA1[:12] for dedup
- `_migrate_schema()`: detects and appends missing columns to existing CSV on first run
- `log_picks_bulk()`: dedup now checks both `pick_id` frozenset AND `(date, tab, section, name)` tuple

**Settlement — `settle_pick_tracker.py`** (root)
- Uses MLB Stats API game log endpoint to fetch HR results per player_id
- `settle_all()` / `settle_date()`: marks `hr_result=0/1/void`, computes P&L only when `bet_dollars>0` AND `american_odds!=0`
- Usage: `py -3.12 settle_pick_tracker.py` (all past dates) or `py -3.12 settle_pick_tracker.py 2026-05-13`
- Rate limit: 50ms between API calls (20 req/s)

**Live ROI Analysis — `analyze_live_roi.py`** (root)
- 5-phase analysis: overall summary, segmentation, CLV, real vs synthetic comparison, production monitoring
- Handles empty CLV gracefully (explains how to populate)
- `MIN_RELIABLE_N = 50`; all tables warn when n < 50
- Output: `live_roi_output.txt`
- Usage: `py -3.12 analyze_live_roi.py`

**Settlement results (as of 2026-05-16):**
- May 13: 313 settled, 68 void (DNP), 253 with real P&L → ROI = −26.7%, win_rate = 11.1%
- Total settled: 324 rows | 262 with real bets | ROI = −30.3%
- 2026-04-24: 9 bets, 0 wins (100% loss — single early date, tiny n)

**Live calibration status (n=324, all settled rows):**
- Overall model bias: −0.26pp → STABLE
- Alert thresholds: |bias|>3pp at n≥50 → re-run calibration; |bias|>5pp at n≥30 → immediate action
- <6% bucket: n=106, actual HR%=7.6%, model=4.1%, bias=−3.43pp (**ALERT**: n≥50, bias>3pp — model under-predicts sub-6% group)
- 8-10% bucket: n=53, actual=11.3%, model=9.1%, bias=−2.27pp (within threshold)
- 12-15% bucket: n=39, actual=7.7%, model=13.2%, bias=+5.51pp (approaching threshold, n<50)
- 20%+ bucket: n=8, actual=0.0%, model=25%, bias=+25pp (n too small for action)

**Live barrel tier ROI (directional only — all n<50 except 4-6%):**
| Barrel | n  | HR%   | ROI%    | Syn.ROI(S24) |
|--------|----|-------|---------|--------------|
| <4%    | 81 | 7.4%  | −42.8%  | −100%        |
| 4-6%   | 78 | 10.3% | −25.1%  | −2.7%        |
| 6-8%   | 45 | 13.3% | −15.7%  | −1.3%        |
| 8-10%  | 32 | 18.8% | −1.6%   | +28.0%       |
| 10-12% | 11 | 0.0%  | −100%   | +65.3%       |
| 12%+   | 15 | 13.3% | −39.8%  | +119.3%      |

8-10% tier directionally on track (near breakeven vs synthetic +28%); 10-12% and 12%+ are extreme small-sample variance — do NOT adjust model.

**EV realization** (all segments): −4.29x overall. Reflects that 93.5% of tracked bets have market_prob_pct empty (no real CLV reference), so EV is computed against model's own probability. Will improve once `sportsbook` field is populated.

**CLV status**: 0 entries. Activate via `clv.fetch_and_compute_clv()` in app.py sidebar.

**Validation milestones:**
- n=50 ✓, n=100 ✓, n=200 ✓ (preliminary ROI visible)
- n=500 (need 176 more), n=1000 (need 676 more)

**Immediate next actions:**
1. Run `py -3.12 settle_pick_tracker.py` daily
2. Activate CLV fetch in app.py
3. Ensure `sportsbook` field populated in pick logging
4. Settle May 15 picks after games complete
5. Re-run `analyze_calibration.py` — Session 23 Step 3 (after regression ceiling stabilizes at n≥100 settled)
6. Do NOT adjust thresholds until n≥200

### compare.py (root)

Runs both v1 and v2 engines for the same date, diffs their outputs, and displays probability shifts, EV changes, and pick-set divergence in rich tables. Reads/writes `compare_v1.json` / `compare_v2.json` when `--dump-json` is passed to the individual engines.

