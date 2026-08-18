# Design-token refinement

Status: shipped on `main`; reversible token tune.

## Changed tokens

The surface staircase was deepened so adjacent layers remain distinct without lifting the whole interface:

- `--bg-void`: `#04070a` -> `#010304`
- `--bg-base`: `#0a1014` -> `#050a0d`
- `--bg-raised`: `#0e1519` -> `#091019`
- `--bg-elevated`: `#131b21` -> `#0f1720`

Border hairlines were made crisper:

- `--border-1`: alpha `0.08` -> `0.13`
- `--border-2`: alpha `0.16` -> `0.23`
- `--border-strong`: alpha `0.32` -> `0.42`

The changes landed across commits `c71415e` and `941be80`. Because the shared variables own the surface and border values, the tune can be reversed without changing component behavior.

## Locked surfaces

Heatmap colors and tier colors remain locked and were not changed. This pass did not alter layout, MAIN/JIG logic, scoring, calibration, ranking, filters, or payload contracts.

## Planned next pass

Glow coverage is incomplete. Roughly 40 scattered hardcoded `box-shadow` glow declarations still need a dedicated tokenization pass. Introduce shared `--glow-*` tokens and migrate them carefully; do not change heatmap or tier colors while doing that work.
