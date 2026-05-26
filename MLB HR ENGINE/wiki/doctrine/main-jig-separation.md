# MAIN/JIG Separation Rules

## Summary

MAIN and JIG are separate intelligence layers and must remain permanently separated. This document defines the invariants that prevent contamination between the layers. These rules are architectural, not stylistic — violation requires explicit operator authorization and a doctrine update.

## Key Points

### Invariants (never break without operator authorization)

1. **Separate scoring:** MAIN uses `EV% × 0.40 + Edge% × 0.35 + Confidence × 0.25`. JIG uses separate tactical scoring. They must not share a composite formula.
2. **Separate filters:** MAIN filters are model-supportive and broader. JIG filters are aggressive and matchup-specific. Never make them identical.
3. **HVY signal isolation:** The HVY pitch-mix modifier is display-only on the JIG side. It must not be folded into MAIN's model probability or λ calculation.
4. **Separate output:** MAIN and JIG produce separate pick lists. A composite/blended list requires explicit new doctrine.
5. **No hidden blending:** Do not introduce hidden composite scoring that blends tactical/HVY signals and model scoring. Any blend must be explicit, documented, and operator-authorized.
6. **TCC orchestrates; does not compute:** The Tactical Control Center (TCC) orchestrates what the operator sees. It does not compute MAIN or JIG scores. See `MASTER_TCC_DOCTRINE.md`.

### What counts as contamination
- Feeding JIG tactical scores into MAIN's λ
- Using HVY pitch-mix weight as a MAIN multiplier
- Running identical filters on both layers
- Producing a single merged pick list without operator authorization
- Letting `pipeline.py` inject JIG signals into MAIN probability construction

## Layer Comparison

| Dimension        | MAIN                          | JIG                            |
|------------------|-------------------------------|--------------------------------|
| Type             | Quantitative / model-driven   | Tactical / matchup-driven      |
| Signal source    | Statcast weighted stats       | Arsenal, pitch-mix, environment|
| Output           | HR probability, EV, Edge      | Tactical escalation, HVY       |
| Workflow         | SCAN → QUALIFY → DEPLOY       | MATCHUP → CONFIRM → EXPLOIT    |
| Tier source      | Model score only              | JIG-internal scoring           |
| Market data role | Display-only                  | Not used                       |

## Permitted Patterns

- Operator viewing both MAIN and JIG outputs simultaneously
- JIG flagging targets that MAIN also scores highly (operator synthesis)
- Shared read access to `pipeline.py` and `config.py`
- Separate filters, separate scoring, separate UI surfaces

## Enforcement

Any proposed change that touches the boundary between MAIN and JIG is
automatically HIGH risk. It requires:
1. Read-only audit assignment first
2. Operator review of audit findings
3. Execution as a separate authorized assignment

## Cross-References

- [MAIN Model Doctrine](main-model-doctrine.md)
- [JIG Tactical Doctrine](jig-tactical-doctrine.md)
- [Pipeline Data Flow](../architecture/pipeline-data-flow.md)
- [Session State Map](../architecture/session-state-map.md)
