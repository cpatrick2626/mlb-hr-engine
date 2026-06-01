# Environmental Multipliers

## Summary

Environmental multipliers are applied after the base score (batter score × pitcher vulnerability) is assembled. They adjust the final λ for situational conditions: handedness edges, park factors, wind, temperature, historical matchup data, and game context. The dome rule is a hard override: dome games nullify wind and temperature multipliers entirely.

## Environmental Multipliers (applied after base score)

| Factor | Range | Notes |
|--------|-------|-------|
| Platoon Split | ×0.90 – ×1.12 | Handedness advantage/disadvantage (batter vs pitcher hand) |
| Park Factor | ×0.88 – ×1.14 | HR park factor for home ballpark |
| Wind | ×0.93 – ×1.09 | Wind speed/direction toward or away from HR zones |
| Temperature | ×0.93 – ×1.03 | Air density effect on ball carry |
| Time Through Order | ×1.00 – ×1.03 | Pitcher fatigue escalation (1st/2nd/3rd time through order) |
| H2H This Season | ×0.93 – ×1.14 | Head-to-head this season performance |
| H2H Career | ×0.94 – ×1.08 | Head-to-head career performance |

### Dome Rule
**Dome games nullify wind and temperature multipliers.** Both revert to ×1.00 for dome/retractable-roof-closed games. Park factor still applies.

## Key Points

- Multipliers are applied multiplicatively in sequence, not additively.
- H2H This Season has the widest range (×0.93 – ×1.14), reflecting the strongest situational signal.
- Platoon split is one of the most consistently predictive multipliers across sample sizes.
- Time Through Order captures pitcher fatigue — increases incrementally, not dramatically.
- All multiplier values calibrated in `config.py`. This table is wiki documentation only.
- JIG weights these multipliers explicitly in pick selection (not just as post-processing). See [JIG Tactical Doctrine](../doctrine/jig-tactical-doctrine.md).

## Cross-References

- [Batter Score Weights](batter-score-weights.md)
- [Pitcher Vulnerability](pitcher-vulnerability.md)
- [Pipeline Data Flow](../architecture/pipeline-data-flow.md)
- [MAIN Model Doctrine](../doctrine/main-model-doctrine.md)
- [JIG Tactical Doctrine](../doctrine/jig-tactical-doctrine.md)
