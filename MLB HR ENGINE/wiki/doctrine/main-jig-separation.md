# MAIN/JIG Separation Rules

## Summary

MAIN and JIG are separate intelligence layers and must remain permanently separated. This document defines the invariants that prevent contamination between the layers. These rules are architectural, not stylistic — violation requires explicit operator authorization and a doctrine update.

## Key Points

### Invariants (never break without operator authorization)

1. **Separate scoring:** MAIN uses `score = model_prob` (current compatibility alias). `bet_value_score` (future Deploy Score) is MAIN-exclusive and additive-only. JIG uses separate tactical scoring (`jigScore`). They must not share a composite formula. Bet Value Rank does not apply to JIG.
2. **Separate filters:** MAIN filters are model-supportive and broader. JIG filters are aggressive and matchup-specific. Never make them identical.
3. **HVY signal isolation:** The HVY pitch-mix modifier is display-only on the JIG side. It must not be folded into MAIN's model probability or λ calculation.
4. **Separate output:** MAIN and JIG produce separate pick lists. A composite/blended list requires explicit new doctrine.
5. **No hidden blending:** Do not introduce hidden composite scoring that blends tactical/HVY signals and model scoring. Any blend must be explicit, documented, and operator-authorized.
6. **TCC orchestrates; does not compute:** The Tactical Control Center (TCC) orchestrates what the operator sees. It does not compute MAIN or JIG scores. See `MASTER_TCC_DOCTRINE.md`.
7. **Separate key namespaces:** MAIN uses `tac_*` session/state keys. JIG uses `jig_tac_*` session/state keys. Cross-engine key access is contamination. Do not read or write across namespaces.

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
| Tier source      | Model score only              | jigTier from jigScore (display-only) + inherited row.tier (see below) |
| Market data role | Display-only                  | Not used                       |

## JIG row.tier Inheritance

JIG `leaderboard_rows_jig` is built from shallow copies of MAIN rows. JIG rows therefore carry `row.tier` assigned by MAIN's model probability thresholds (`FS_TIER_THRESHOLDS`).

**Accepted doctrine (Option A):**

- `row.tier` in JIG context = MAIN model probability tier, displayed as contextual probability information only.
- JIG tactical priority is determined by `jigScore` and JIG sort order — not by `row.tier` and not by `jigTier`.
- Do not interpret or label JIG `row.tier` as JIG tactical confidence, JIG deployment tier, or JIG-native escalation.

**JIG-native `jigTier` field (ratified 2026-07-13):**

The future-jigTier preconditions (jigScore distribution audit, operator authorization, doctrine
update) were all satisfied, and `jigTier` now exists as a separate, additive field:

- Computed server-side in `_build_slate_payload` (`api/main.py`) from `jigScore` (0–100), using
  the single threshold source `config.JIG_TIER_THRESHOLDS` (APEX ≥88 / ELITE ≥75 / EDGE ≥60 /
  SIGNAL ≥40 / WATCH ≥20 / COLD <20). Bands recorded in `tier-vocabulary.md`.
- **Display-only.** `jigTier` does not affect JIG sort (still `jigScore` descending), any
  scoring, any filter, or anything on the MAIN side. The `jigScore` formula (`_jig_score`) is
  untouched.
- Coexists with the inherited MAIN `row.tier` — both fields remain on JIG rows. The JIG board's
  tier label reads `jigTier`; `row.tier` keeps its MAIN-context meaning per the rules above.
- MAIN tiering (`FS_TIER_THRESHOLDS` on `model_prob`) is unchanged and does not read `jigTier`.

This is not scoring contamination. MAIN probability is not affected by JIG. JIG logic does not affect MAIN tiers. HVY remains display-only and does not affect MAIN probability.

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
