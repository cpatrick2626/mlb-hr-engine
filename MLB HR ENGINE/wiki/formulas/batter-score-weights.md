# Batter Score Weights

## Summary

The batter base score is assembled from Statcast and derived metrics, each weighted by predictive value for home-run probability. This table defines the weight allocation for the batter component of the λ calculation. All weights are relative to the batter base score (100%). The resulting batter score feeds into the Poisson λ alongside pitcher vulnerability (28%) and environmental multipliers.

## Batter Base Score (100%)

| Metric | Weight | Notes |
|--------|--------|-------|
| Barrel% | 20% | Primary power quality signal |
| ISO | 15% | Isolated power; raw hit quality |
| HR/FB | 12% | Direct HR rate on fly balls |
| xSLG | 10% | Expected slugging; contact quality |
| Avg EV | 7% | Average exit velocity |
| Hard Hit% | 6% | % balls hit 95+ mph |
| Sweet Spot% | 6% | Launch angle 8-32° contact quality |
| Pull% | 5% | Pull tendency; park/wind interaction |
| Launch Angle | 4% | Optimal LA for HR production |
| xwOBA | 2% | Expected weighted on-base average |
| SwStr% | −2% | Swing-and-miss rate (negative — penalizes contact issues) |
| K% | −1% | Strikeout rate (negative — penalizes at-bat quality) |
| **Total** | **100%** | |

## Key Points

- Negative weights (SwStr%, K%) reduce the batter score — they do not add to it.
- Weights are calibrated values in `config.py`. Do not hardcode or duplicate here for operational use.
- This table is for wiki documentation and understanding. The authoritative source is always `config.py`.
- The batter base score is then modified by pitcher vulnerability (28% of base score) and environmental multipliers.

## Cross-References

- [Pitcher Vulnerability](pitcher-vulnerability.md)
- [Environmental Multipliers](environmental-multipliers.md)
- [Pipeline Data Flow](../architecture/pipeline-data-flow.md)
- [MAIN Model Doctrine](../doctrine/main-model-doctrine.md)
