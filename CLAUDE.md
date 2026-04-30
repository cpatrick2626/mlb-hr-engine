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

- `KELLY_FRACTION = 0.25` — quarter-Kelly risk scaling
- `LEAGUE_AVG_HR_PA = 0.028` — regression target (2026 YTD; revisit mid-May)
- `REGRESSION_PA = 200` — Bayesian shrinkage weight
- `RECENT_WEIGHT = 0.30 / SEASON_WEIGHT = 0.70` — blending recent vs season stats
- `LEAGUE_AVG_HR9 = 1.09`, `LEAGUE_HR_FB = 0.106` — pitcher league baselines (2026 YTD)
- `MAX_GAME_HR_PROB = 0.31` — hard ceiling on per-game HR probability (calibration-backed)
- `PRIOR_YEAR_TRUST = 0.85`, `MIN_CURRENT_YEAR_PA = 50` — Statcast prior-year blending
- All Statcast leaderboard league averages (barrel%, exit velo, hard hit%, etc.) live in `config.py`; update all together at mid-season refresh
- `MIN_EV_PCT = 3.0`, `MIN_EDGE_PCT = 2.0` — filter floor thresholds
- `MIN_PA_THRESHOLD = 3.3` — blocks 9-hole batters (3.2 PA); `MAX_PARK_PENALTY = 0.87` — blocks SF + SD

### compare.py (root)

Runs both v1 and v2 engines for the same date, diffs their outputs, and displays probability shifts, EV changes, and pick-set divergence in rich tables. Reads/writes `compare_v1.json` / `compare_v2.json` when `--dump-json` is passed to the individual engines.

