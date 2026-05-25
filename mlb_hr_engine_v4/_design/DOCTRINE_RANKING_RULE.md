# Doctrine — Ranking & Tier Calculation Rule

Status: LOCKED · 2026-05-25
Authority: Operator clarification during design session

## Rule

Tier assignments, rank order, and any sorted player list on MAIN surfaces are computed from model HR probability and model-derived metrics only. Market data (FanDuel HR prop odds, implied market probability) is shown as a column for operator reference but never participates in tier or rank calculation.

## What drives ranking

- Model HR probability (engine's computed prediction)
- Model confidence
- Poisson-derived probability components
- Other model outputs per config.py thresholds

## What does NOT drive ranking

- FanDuel or other sportsbook HR prop odds
- Implied market probability derived from odds
- Edge (model probability minus market implied probability)
- EV (expected value calculation)
- Public sentiment, ownership, or any external betting signal

## Where market data DOES live

Market data is displayed alongside model output, not as a ranking input:

- FanDuel column on every Full Slate row (operator sees the market price)
- Implied market probability as an optional display column (informational only)
- Edge metric computed after ranking, used for portfolio/deployment decisions (Room 05)
- EV calculation computed after ranking, used for slip sizing decisions

## Operational workflow this enables

The SCAN to QUALIFY to DEPLOY workflow on MAIN side:

1. SCAN — Operator sees model-ranked tiers (model says "these are most likely to homer")
2. QUALIFY — Operator inspects matchup, environment, lineup state via Batter Card, Pitch Mix, etc.
3. DEPLOY — Operator references market data (Edge column) to identify where market disagrees with model; that's where positive-EV bets hide

If market data were part of the ranking calculation, this workflow collapses: the operator can no longer use disagreement between model and market as a deployment signal, because the ranking already absorbed the market info.

## Implementation enforcement

When pipeline.py is implemented for any MAIN-side surface, the ranking pipeline must be:

1. pipeline.py computes model_hr_prob from model inputs ONLY (no market inputs in this step)
2. model_hr_prob is mapped to tier via thresholds in config.py (thresholds are model-domain, not market-domain)
3. Market data fetched separately and joined into display row at the very last step (presentation layer, not ranking layer)
4. Edge = model_hr_prob minus market_implied_prob (computed for display only, never feeds back into rank)
5. EV = derived metric for portfolio decisions (used in Room 05 / Deployment surfaces, not in MAIN ranking)

## Relationship to existing MAIN/JIG separation rule

This rule complements the existing doctrine invariant:

"MAIN is quantitative/model-driven: EV, Edge, model probability, Poisson-derived probability. The HVY pitch-mix modifier is display-only on the JIG side and must not be folded into MAIN model probability."

Updated mental model:

Market HR odds and implied market probability are display-only on MAIN and must not be folded into model probability or tier ranking. EV and Edge are derived from model probability plus market data, used downstream for portfolio decisions, not for ranking.

## Verification questions for code review

When reviewing any new MAIN-side ranking code, ask:

1. Does the ranking function take market data as input? (Should be NO)
2. Does the tier-assignment function reference market data? (Should be NO)
3. Is model_hr_prob computed before any market data is joined? (Should be YES)
4. Is market data joined only at the display/presentation step? (Should be YES)
5. Are Edge and EV derived AFTER ranking is final? (Should be YES)

If any answer is wrong, the ranking pipeline violates this doctrine.

## Cross-references

- MASTER_TCC_DOCTRINE.md — TCC orchestration rules
- config.py — model thresholds and tier cutoffs (single source of truth)
- pipeline.py — canonical data assembly entrypoint
- DESIGN_FULL_SLATE_MATRIX.md — primary MAIN surface, tier system documented there
