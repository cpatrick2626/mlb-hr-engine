---
title: Market Inefficiency - Overview
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Market Inefficiency — Overview

## Core Concept

Market inefficiency exists when sportsbooks price HR props using a subset of the available predictive information. The MLB HR ENGINE's information premium comes primarily from Statcast barrel rate — books approximate HR probability from park, pitcher, and platoon factors but do not systematically incorporate barrel data. This creates a structural edge for barrel-qualified batters that erodes only when books integrate the same Statcast signals.

## Tactical Signals

- **EV% (Expected Value)**: `(model_prob × decimal_odds) - 1` — primary deployment gate signal
- **Edge%**: `model_prob - no_vig_market_prob` — information premium over book's true probability
- **CLV (Closing Line Value)**: model price vs closing no-vig probability — sharp betting metric
- **Odds drift**: opening → closing line movement; positive drift = market moving toward model = confirmation
- **Stale lines**: book has not updated for lineup, weather, or injury information → edge decay pending
- **Vig tier**: lower-vig books preserve more of the theoretical edge (Pinnacle > Circa > mid-tier > retail)

## Escalation Conditions

- EV% ≥ 5.0% → +1 danger layer (confirmed market mismatch)
- EV% ≥ 8.0% → +2 danger layers (significant mispricing)
- Edge% ≥ 4.0% → strong model-vs-market premium
- CLV positive (avg > 0 pp) → model is consistently sharper than closing line
- Book slow to react to lineup scratch or weather update → stale line opportunity

## Failure Conditions

- EV% below `MIN_EV_PCT = 3.0%` → pick blocked regardless of barrel quality
- Edge% below `MIN_EDGE_PCT = 2.0%` → insufficient model premium
- Barrel < 4% → EV% is a false positive; barrel generates no real information premium
- Barrel 4–6% → synthetic ROI negative even at positive EV%; do not deploy
- CLV negative (avg < −1.0 pp) → model consistently softer than closing line → edge decay

## MLB HR ENGINE Usage

EV% computed in `engine/ev.py`. Market prob from `clients/odds_api.py` (no-vig conversion). Edge% = `model_prob - no_vig_market_prob`. CLV tracked in `tracking/clv.py`. Drift monitored in `tracking/drift_monitor.py`. Book vig tiers embedded in `engine/vig.py` `no_vig_prob_for_book()`. Live ROI analysis via `analyze_live_roi.py`.

## Related Doctrine Links

- [[Barrel_Quality/overview]] — barrel ≥ 8% is breakeven point for positive synthetic ROI
- [[Confidence_Tiering/overview]] — EV/Edge fire danger layers that feed tier assignment
- [[HR_Threat_Escalation/overview]] — market EV is one of five danger layer inputs
- [[Hard_Hit_Danger/overview]] — power quality determines whether market edge is real or artifact
