# MAIN Model Doctrine

## Summary

MAIN is the quantitative, model-driven intelligence layer of the MLB HR Engine. It derives per-batter home-run probabilities using Poisson math (`P(HR≥1) = 1 − e^(−λ)`), prices those probabilities against market odds, identifies positive-EV edges, and sizes bets via Kelly-derived logic. MAIN operates independently of JIG tactical signals and must not be contaminated by HVY pitch-mix modifiers or matchup-hunting heuristics.

## Key Points

- **Scoring formula:** `score = EV% × 0.40 + Edge% × 0.35 + Confidence × 0.25`
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
