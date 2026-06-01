# Codex HR Engine â€” Setup

## 1. Install Python

If Python isn't installed, download from https://python.org/downloads (3.11+).
Check the "Add Python to PATH" box during install.

## 2. Install Dependencies

```bash
cd "codex_hr_engine_v2"
pip install -r requirements.txt
```

## 3. Configure API Keys

```bash
copy .env.example .env
```

Then edit `.env` and add:
- `ODDS_API_KEY` â€” get a free key at https://the-odds-api.com (500 req/month free tier)
- `BANKROLL` â€” your betting bankroll in dollars (default: 1000)

The engine works without an Odds API key â€” it will still show model probabilities for all batters, but EV%, Edge%, and bet sizing require market odds.

## 4. Run

```bash
cd "codex_hr_engine_v2"
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
- EV â‰¥ +5%
- Edge â‰¥ +3%
- Expected PA â‰¥ 3.5
- Park factor not a strong suppressor (< 0.85)
- Weather not strongly negative (< 0.88)
- Not facing an elite HR suppressor pitcher (factor < 0.75)

| Column    | Description |
|-----------|-------------|
| Model%    | Engine's true HR probability (Poisson model) |
| Mkt%      | No-vig market implied probability |
| Edge      | Model% âˆ’ Market% |
| EV%       | Expected profit per $100 risked |
| Bet $     | Quarter-Kelly recommended bet size |
| Conf      | Confidence score 0â€“100 (sample size + signal quality) |
| Score     | Composite rank score (EVÃ—0.4 + EdgeÃ—0.35 + ConfÃ—0.25) |

### MODEL PROBABILITIES
All batters in today's games ranked by model HR%, regardless of filters.
Useful for spotting value even if no qualifying bets exist.

### BEST PARLAY
Top 2â€“3 leg combination from qualified picks, ranked by combined EV%.
Uses 1/8 Kelly sizing (more conservative than single-leg bets).

## System Architecture

```
Data Sources
  â”œâ”€â”€ MLB Stats API (free)     â†’ schedule, lineups, player/pitcher stats
  â”œâ”€â”€ The Odds API (key req'd) â†’ market HR prop lines
  â””â”€â”€ Open-Meteo (free)       â†’ game-time weather at each stadium

Pipeline
  1. Pull schedule + lineups
  2. Build player HR rate (weighted: 65% recent 30d + 35% season, Bayesian regression)
  3. Apply adjustments: park Ã— pitcher Ã— weather Ã— handedness
  4. P(HRâ‰¥1) = 1 âˆ’ e^(âˆ’Î»),  Î» = adjusted_rate Ã— expected_PA
  5. Match to market odds (fuzzy name matching)
  6. Compute EV%, Edge%, Kelly bet size
  7. Apply 7-rule filter set
  8. Rank by composite score
  9. Build optimal parlay from top picks
```

## Key Formulas

**Base HR Rate** (Bayesian regressed):
```
regressed = (HR + 200 Ã— 0.033) / (PA + 200)
rate = 0.65 Ã— recent_blended + 0.35 Ã— regressed_season
```

**Game Probability** (Poisson):
```
Î» = rate Ã— park_factor Ã— pitcher_factor Ã— weather_factor Ã— handedness_factor Ã— expected_PA
P(HR) = 1 âˆ’ e^(âˆ’Î»)
```

**EV%**:
```
EV% = [p Ã— (decimal_odds âˆ’ 1) âˆ’ (1 âˆ’ p)] Ã— 100
```

**Edge%**:
```
Edge% = (model_prob âˆ’ no_vig_market_prob) Ã— 100
```

**Kelly bet size**:
```
f* = (bÂ·p âˆ’ q) / b          (full Kelly)
f  = f* Ã— 0.25              (quarter Kelly)
bet = min(f Ã— bankroll, 5% Ã— bankroll)
```

