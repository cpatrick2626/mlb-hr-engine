# JIG Tactical Doctrine

## Summary

JIG is the tactical, matchup-driven intelligence layer of the MLB HR Engine. It operates independently of MAIN's Poisson/EV model, using arsenal analysis, pitch-mix exploitation, handedness edges, and HR environment targeting to identify high-upside situational bets. JIG is NOT purely EV-driven — it prioritizes tactical signal quality, matchup conditions, and pitcher vulnerability to specific batter profiles.

## Key Points

- **HVY pitch-mix signal:** JIG's flagship tactical signal. Identifies when a pitcher's heavy pitch-mix (high usage of a pitch type) creates exploitable matchup conditions for specific batter profiles. **Display-only on JIG side — must not be folded into MAIN model probability.**
- **Arsenal hunting:** Evaluates pitcher's full pitch repertoire against batter's known vulnerabilities. Slot-specific, not aggregate.
- **Aggressive filtering:** JIG filters are deliberately more aggressive than MAIN. Matchup quality thresholds are stricter; pool is narrower by design.
- **HR environment targeting:** Weights park, wind, temperature, and game-time conditions explicitly in pick selection — not just as multipliers.
- **JIG TCC rules:** Aggressive tactical filtering, matchup hunting, arsenal exploitation, HR environment targeting. Never make JIG filters identical to MAIN filters.
- **Pitch Mix data integrity:** Never fabricate missing data. Graceful fallback when Statcast/Savant is incomplete. Cross-check against Baseball Reference, Savant, Statcast.
- **Output:** Separate pick list from MAIN. Not a subset of MAIN — different criteria, different intent.

## What JIG Does NOT Compute

- MAIN model probability (MAIN owns this)
- EV derivation or bet sizing (MAIN owns this)
- Market odds pricing (MAIN display layer owns this)

## JIG WAY Filter

JIG WAY uses raw-stat-only filtering with AND-stacked thresholds.
It does not use the JIG formula, HVY, or model probability.
Implementation is additive inside JIG Overall — it does not replace
existing JIG logic.

## Protected Surfaces

- JIG internals must not be rewritten during MAIN stabilization passes
- JIG GRADE composite formula is doctrine-sensitive (HIGH risk, operator
  auth required before any change)
- MAIN/JIG separation is an architectural invariant — never merge

## Operator Workflow

MATCHUP — identify pitcher arsenal vulnerability  
CONFIRM — validate environmental and handedness edges  
EXPLOIT — stack confirmed signals into aggressive deployment

## Cross-References

- [MAIN Model Doctrine](main-model-doctrine.md) — the separated quantitative layer
- [MAIN/JIG Separation Rules](main-jig-separation.md) — invariants preventing contamination
- [Environmental Multipliers](../formulas/environmental-multipliers.md) — multipliers JIG weights explicitly
- [Pipeline Data Flow](../architecture/pipeline-data-flow.md) — how JIG data flows separately
