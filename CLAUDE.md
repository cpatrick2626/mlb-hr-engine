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

### compare.py (root)

Runs both v1 and v2 engines for the same date, diffs their outputs, and displays probability shifts, EV changes, and pick-set divergence in rich tables. Reads/writes `compare_v1.json` / `compare_v2.json` when `--dump-json` is passed to the individual engines.

