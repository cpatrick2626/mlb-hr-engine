# MLB HR Prop Betting Engine — Setup

## 1. Install Python

If Python isn't installed, download from https://python.org/downloads (3.11+).
Check the "Add Python to PATH" box during install.

## 2. Install Dependencies

```bash
cd "mlb_hr_engine"
pip install -r requirements.txt
```

## 3. Configure API Keys

```bash
copy .env.example .env
```

Then edit `.env` and add:
- `ODDS_API_KEY` — get a free key at https://the-odds-api.com (500 req/month free tier)
- `BANKROLL` — your betting bankroll in dollars (default: 1000)

The engine works without an Odds API key — it will still show model probabilities for all batters, but EV%, Edge%, and bet sizing require market odds.

## 4. Run

```bash
cd "mlb_hr_engine"
python main.py
```

To run for a specific date:
```bash
set TARGET_DATE=2025-04-20 && python main.py    # Windows
TARGET_DATE=2025-04-20 python main.py           # Mac/Linux
```

## Output

The engine prints three sections:

### TOP HR BETS (EV-Ranked)
Only bets that pass all filters:
- EV ≥ +5%
- Edge ≥ +3%
- Expected PA ≥ 3.5
- Park factor not a strong suppressor (< 0.85)
- Weather not strongly negative (< 0.88)
- Not facing an elite HR suppressor pitcher (factor < 0.75)

| Column    | Description |
|-----------|-------------|
| Model%    | Engine's true HR probability (Poisson model) |
| Mkt%      | No-vig market implied probability |
| Edge      | Model% − Market% |
| EV%       | Expected profit per $100 risked |
| Bet $     | Quarter-Kelly recommended bet size |
| Conf      | Confidence score 0–100 (sample size + signal quality) |
| Score     | Composite rank score (EV×0.4 + Edge×0.35 + Conf×0.25) |

### MODEL PROBABILITIES
All batters in today's games ranked by model HR%, regardless of filters.
Useful for spotting value even if no qualifying bets exist.

### BEST PARLAY
Top 2–3 leg combination from qualified picks, ranked by combined EV%.
Uses 1/8 Kelly sizing (more conservative than single-leg bets).

## System Architecture

```
Data Sources
  ├── MLB Stats API (free)     → schedule, lineups, player/pitcher stats
  ├── The Odds API (key req'd) → market HR prop lines
  └── Open-Meteo (free)       → game-time weather at each stadium

Pipeline
  1. Pull schedule + lineups
  2. Build player HR rate (weighted: 65% recent 30d + 35% season, Bayesian regression)
  3. Apply adjustments: park × pitcher × weather × handedness
  4. P(HR≥1) = 1 − e^(−λ),  λ = adjusted_rate × expected_PA
  5. Match to market odds (fuzzy name matching)
  6. Compute EV%, Edge%, Kelly bet size
  7. Apply 7-rule filter set
  8. Rank by composite score
  9. Build optimal parlay from top picks
```

## Key Formulas

**Base HR Rate** (Bayesian regressed):
```
regressed = (HR + 200 × 0.033) / (PA + 200)
rate = 0.65 × recent_blended + 0.35 × regressed_season
```

**Game Probability** (Poisson):
```
λ = rate × park_factor × pitcher_factor × weather_factor × handedness_factor × expected_PA
P(HR) = 1 − e^(−λ)
```

**EV%**:
```
EV% = [p × (decimal_odds − 1) − (1 − p)] × 100
```

**Edge%**:
```
Edge% = (model_prob − no_vig_market_prob) × 100
```

**Kelly bet size**:
```
f* = (b·p − q) / b          (full Kelly)
f  = f* × 0.25              (quarter Kelly)
bet = min(f × bankroll, 5% × bankroll)
```
