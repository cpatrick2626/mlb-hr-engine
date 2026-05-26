# Pipeline Data Flow

## Summary

`pipeline.py` is the canonical data-assembly entrypoint for the MLB HR Engine. It is shared between `app.py` (Streamlit dashboard) and `main.py` (CLI). Both surfaces consume `pipeline.py` independently — they do not share session state, auth, or caching. The pipeline executes a fixed sequence: fetch external data → build batter/pitcher profiles → compute Poisson probability → price against market → filter → rank → size → output.

## Key Points

### Canonical Pipeline Sequence

1. **Fetch** — MLB Stats API (lineups, rosters), The Odds API (market lines), Baseball Savant/Statcast (batter/pitcher stats), weather, pitch mix
2. **Build Profiles** — per-batter profile assembly: Barrel%, ISO, HR/FB, xSLG, Avg EV, Hard Hit%, Sweet Spot%, Pull%, Launch Angle, xwOBA, SwStr%, K%
3. **Pitcher Vulnerability** — per-pitcher: HR/9, Barrel% Allowed, xFIP, Recent HR/9, Hard Hit% Allowed, GB%
4. **λ Calculation** — combines batter base score × pitcher vulnerability × environmental multipliers
5. **Poisson P(HR≥1)** — `1 − e^(−λ)`
6. **Market Pricing** — model probability vs no-vig implied probability → EV%, Edge%
7. **Filter** — MAIN filters (model-supportive, broader) applied separately from JIG filters
8. **Rank** — by composite score (`EV% × 0.40 + Edge% × 0.35 + Confidence × 0.25`)
9. **Size** — Kelly-derived bet sizing using bankroll from config
10. **Output** — ranked pick list with full metadata

### Key Constraints
- `pipeline.py` is consumed by both `app.py` and `main.py`. Changes affect both surfaces.
- `config.py` is the single source of truth for all thresholds, weights, and baselines used in the pipeline.
- JIG scoring runs through a separate path — pipeline.py does not inject JIG signals into MAIN probability construction.
- Do not reorder pipeline stages without explicit operator authorization.

## Cross-References

- [MAIN Model Doctrine](../doctrine/main-model-doctrine.md)
- [JIG Tactical Doctrine](../doctrine/jig-tactical-doctrine.md)
- [Batter Score Weights](../formulas/batter-score-weights.md)
- [Pitcher Vulnerability](../formulas/pitcher-vulnerability.md)
- [Environmental Multipliers](../formulas/environmental-multipliers.md)
- [Session State Map](session-state-map.md)
- [Cache Ownership Map](cache-ownership-map.md)
