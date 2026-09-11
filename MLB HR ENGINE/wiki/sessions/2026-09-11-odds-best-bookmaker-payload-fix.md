# Odds Best-Bookmaker Payload Fix - 2026-09-11

Status: **DEPLOYED / VERIFIED**

## Failure

The pipeline matched valid player props and stored the best line in `best_american` and `best_bookmaker`. The API payload builder read only `fanduel_american`, so events with BetRivers, William Hill, or another non-FanDuel line published null odds and null implied probability, edge, and EV.

## Fix

`api/main.py` now prefers `fanduel_american` and falls back to `best_american`. It publishes `odds_bookmaker` so the selected source is explicit. The existing implied probability, edge, and EV calculations run against the selected line. Players with neither field remain null.

No fetch, matching, scoring, `model_prob`, MAIN/JIG, calibration, tier, or pipeline behavior changed.

## Validation

- Regression coverage verifies FanDuel preference, BetRivers fallback, and no-line null behavior.
- Code commit `cf67df0` and wiki commit `d12fdbd` were pushed before deployment.
- Live `/api/slate` verification must use a newly generated slate payload; previously stored cached rows remain unchanged until the next pipeline write.

The post-deploy daily pipeline completed successfully from pushed SHA `d12fdbd`: 88 odds lines and 88/410 player matches. The refreshed `/api/slate` contains 88 odds rows, all from BetRivers for this run, plus 322 genuine no-line rows. Examples include Rafael Flores Jr. `+510` (BetRivers), implied probability `0.1639`, edge `0.0478`, and EV `29.14%`; Pete Crow-Armstrong `+300` (BetRivers), implied probability `0.25`, edge `-0.0178`, and EV `-7.12%`. A no-line row remains null across all odds fields.
