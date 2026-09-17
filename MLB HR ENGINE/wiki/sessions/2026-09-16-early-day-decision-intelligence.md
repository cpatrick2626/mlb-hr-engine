# Early-Day Decision Intelligence

Date: 2026-09-16

Code commit: `b032788` (`feat(early-day): add decision intelligence`)

Code state: committed locally, not pushed, not deployed

## Purpose

Early-Day Decision Intelligence makes Full Slate useful before sportsbook HR markets are available. It adds deterministic fair-price and buy-price context without changing MAIN qualification, ranking, tiers, JIG, HVY, calibration, or the existing odds/edge/EV fields.

## Payload fields

Current-probability pricing:

- `fair_odds`
- `buy_odds_5`
- `buy_odds_10`

Projected-probability pricing:

- `fair_odds_projected`
- `buy_odds_5_projected`
- `buy_odds_10_projected`
- `edge_projected_vs_actual`
- `ev_pct_projected_vs_actual`

Market and decision context:

- `market_state`
- `market_observed_at`
- `decision_action`

## Deterministic market math

Fair odds are the American odds implied by the selected probability. Buy prices are the minimum integer American odds that meet the requested expected-value threshold.

- At `p = .188`, fair odds are approximately `+432`, the +5% buy price is approximately `+459`, and the strict +10% integer buy price is `+486`.
- `+485` is below 10% EV. `+486` clears 10% EV.
- At `p = .60`, fair odds are `-150` and the +10% buy price is `-120`.

## Current and projected semantics

- A confirmed player's `decision_action` uses `model_prob`.
- An unconfirmed player with `model_prob_projected` uses that projected probability.
- An unconfirmed player without `model_prob_projected` has `decision_action = null`. Current FAIR and CURRENT BUY may still display as context, but no WATCH action is allowed.
- `edge_projected_vs_actual` and `ev_pct_projected_vs_actual` compare `model_prob_projected` with the same real selected sportsbook quote used by the current market fields. They do not replace current EDGE or EV.

## Market state and quote time

Reachable states are:

- `LIVE_MARKET`
- `PRE_MARKET`
- `MARKET_UNKNOWN`

`STALE_MARKET` and `PROJECTED_MARKET` are defined for display but are not currently emitted. There is no `NO_MARKET` state.

`market_observed_at` comes from the selected sportsbook quote's `last_update`. The API does not substitute a generated or runtime timestamp.

## Full Slate presentation

- Confirmed: FAIR / BUY +10
- Unconfirmed with a projection: PROJ FAIR / PROJ BUY +10
- Unconfirmed without a projection: CURRENT FAIR / CURRENT BUY +10

Full Slate renders `decision_action` and market context additively. Existing ODDS, BOOK, IMP, EDGE, and EV remain authoritative.

## BetRivers Beta

BetRivers Beta is deferred. No trained Beta artifact or projected BetRivers range is shipped. Current selected-book quotes may come from BetRivers, but that is real observed market data, not a projected range.

## Protected boundaries

The implementation does not change:

- MAIN probability, ranking, or tiers
- JIG scoring or order
- HVY
- calibration
- `config.py` thresholds
- existing odds, implied probability, edge, or EV semantics

Market prices do not influence MAIN probability, qualification, ranking, or tiers. FAIR and BUY fields are display and decision context only.

## Validation

Claude implementation validation passed. Codex independent verification passed after one doctrine correction. Final focused verification recorded:

- market math: PASS
- decision semantics: PASS
- frontend CASE C: PASS
- current market parity: PASS
- MAIN parity: PASS
- JIG parity: PASS
- HVY parity: PASS
- requested tests: 122 passed
- `git diff --check`: PASS

This checkpoint does not claim that Stage 2 was pushed or deployed.
