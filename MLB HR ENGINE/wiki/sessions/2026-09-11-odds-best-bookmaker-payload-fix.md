# Odds Best-Bookmaker Payload Fix - 2026-09-11

Status: **STAGE 2 FIX RECORD**

## Failure

The pipeline matched valid player props and stored the best line in `best_american` and `best_bookmaker`. The API payload builder read only `fanduel_american`, so events with BetRivers, William Hill, or another non-FanDuel line published null odds and null implied probability, edge, and EV.

## Fix

`api/main.py` now prefers `fanduel_american` and falls back to `best_american`. It publishes `odds_bookmaker` so the selected source is explicit. The existing implied probability, edge, and EV calculations run against the selected line. Players with neither field remain null.

No fetch, matching, scoring, `model_prob`, MAIN/JIG, calibration, tier, or pipeline behavior changed.

## Validation

- Regression coverage verifies FanDuel preference, BetRivers fallback, and no-line null behavior.
- Production deployment is gated on scoped commits being pushed first.
- Live `/api/slate` verification must use a newly generated slate payload; previously stored cached rows remain unchanged until the next pipeline write.
