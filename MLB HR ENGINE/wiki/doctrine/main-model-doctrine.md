# MAIN Model Doctrine

## Summary

MAIN is the quantitative, model-driven intelligence layer of the MLB HR Engine. It derives per-batter home-run probabilities using Poisson math (`P(HR≥1) = 1 − e^(−λ)`), prices those probabilities against market odds, identifies positive-EV edges, and sizes bets via Kelly-derived logic. MAIN operates independently of JIG tactical signals and must not be contaminated by HVY pitch-mix modifiers or matchup-hunting heuristics.

## Key Points

- **score (current):** `score = model_prob` — compatibility alias; unchanged. Do not redefine.
- **model_tier_rank:** HR Threat Rank — `<TIER> #<N>` (e.g., `APEX #1`). Ranks by model_prob within each FS tier.
- **bet_value_score (future — NOT YET IMPLEMENTED):** Deploy Score. Approved formula: `(ev_pct × 0.55 + edge_pct × 0.45) × (0.50 + 0.50 × (confidence / 100))`. Additive-only field; must not replace score, rank, model_prob, or model_tier_rank. JIG excluded.
- **Core pipeline:** Fetch → build profiles → Poisson P(HR≥1) → price vs market → filter → rank → size → output
- **λ derivation:** Combines batter base score (Barrel%, ISO, HR/FB, xSLG, etc.) with pitcher vulnerability (HR/9, Barrel% Allowed, xFIP) and environmental multipliers (platoon, park, wind, temp, H2H)
- **Market pricing:** Model probability vs no-vig implied probability = edge. Positive edge + minimum confidence threshold = pick candidate.
- **Filter logic:** MAIN filters use model-supportive thresholds — broader, not aggressive. JIG filters are separate.
- **Output:** Ranked pick list with EV%, Edge%, Confidence, recommended bet size.
- **config.py is authoritative** for all thresholds, weights, and calibration constants. Do not duplicate here.

## What MAIN Does NOT Compute

- Arsenal hunting or pitch-mix exploitation signals (JIG owns this)
- HVY pitch-mix modifier (JIG display-only — never folded into MAIN)
- Tactical matchup escalation (JIG owns this)
- Any composite that blends JIG signals with MAIN probability

## Protected Surfaces

- `config.py` — single source of truth for all thresholds and weights
- `pipeline.py` — canonical data-assembly entrypoint
- `engine\*` — model computation layer (HIGH risk, operator auth required)

## Data Integrity Rule

Never fabricate Statcast, Savant, or model inputs. If data is
unavailable, display `--` and report as a data gap. No threshold or
calibration changes from n<200 settled picks without explicit operator
authorization.

## Primary Ranking Doctrine

**Final operator decision (2026-06-11):** Primary tier ranking is pure HR Threat Rank. No market data, EV, odds, or edge may contaminate primary rank.

- **`model_tier_rank` = HR Threat Rank** — pure model probability, always.
- **APEX #1** = highest engine-estimated HR probability in APEX tier. Not "best bet." Not "highest EV."
- **ELITE #1 / EDGE #1** = highest HR probability within each respective tier. Not market rank.
- **Odds, EV, edge, and sportsbook lines** are display-only context. They never influence `model_prob`, `model_tier_rank`, tier classification, or the primary sort key.
- **Bet Value Rank (Deploy Score)** is deferred. When implemented, it must be an additive-only secondary layer, selectable by the operator. It must not replace or re-sort primary rank.
- **Market value as a sort option** may be added in the future only with explicit operator authorization and a separate doctrine update.

## MAIN Doctrine Reform

- **Market data is display-only:** market fields never gate player qualification in MAIN.
- **Projected market values:** projected market-facing values derive from `model_prob`.
- **Layer 1 filter chain:** 3 market-dependent gates removed.
- **Qualification order:** model qualifies first; market context displays after.

## Cross-References

- [JIG Tactical Doctrine](jig-tactical-doctrine.md) — the separated tactical layer
- [MAIN/JIG Separation Rules](main-jig-separation.md) — invariants preventing contamination
- [Batter Score Weights](../formulas/batter-score-weights.md) — full weight table
- [Pitcher Vulnerability](../formulas/pitcher-vulnerability.md) — full vulnerability weight table
- [Environmental Multipliers](../formulas/environmental-multipliers.md) — multiplier table
- [Pipeline Data Flow](../architecture/pipeline-data-flow.md) — how data flows through pipeline.py
