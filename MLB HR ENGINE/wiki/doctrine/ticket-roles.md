# Ticket Roles Doctrine

**Last Updated:** 2026-06-15

---

## Summary

Ticket Roles describe HOW to use a batter on a ticket (DFS/parlay usage archetype). They are NOT tiers.

- **Tiers** (APEX/ELITE/EDGE/…) = model probability strength. See [[tier-vocabulary]].
- **Roles** = usage intent on a ticket.

---

## Role Properties

- **DERIVED** from existing row fields + FS tier — no new data fetched.
- **ADDITIVE** — roles never modify `model_prob`, `model_tier_rank`, or `jigScore`.
- **DISPLAY-ONLY** — pure presentation layer.
- **MARKET-FREE** — no odds, EV, or edge data influence role assignment.
- **NON-EXCLUSIVE** — a player can hold multiple roles simultaneously.
- **Renders on both MAIN and JIG boards.**

`config.py` is the authoritative source for all role thresholds. Values below reflect production state as of 2026-06-15; always verify against `config.py`.

---

## Four Roles

### PRIME (green) — Anchor

Use as primary anchor; survives every quality test.

**Gate:**
- Tier is APEX or ELITE
- `barrel >= 9`
- `xslg >= 0.500`
- `HH >= 45`
- `EV >= 90`

---

### EXPLOSIVE (orange) — Slate-Breaking Upside

Ceiling play; massive raw power upside.

**Gate:**
- `maxEV >= 113`
- `barrel >= 8.5`
- At least 1 present trait from: `{ blast >= 12, pullair >= 20 }`

**Null-safe:** a null trait value is not counted and does NOT disqualify.

---

### ADVANTAGE (blue) — Underpriced Quality

Model grades player higher than rank suggests.

**Gate:**
- Tier is NOT APEX and NOT ELITE
- `xslg >= 0.490` OR `barrel >= 9.0`

*Recalibrated 2026-06-15: xslg threshold lowered from 0.500 → 0.490.*

---

### WILDCARD (purple) — Chaos Upside

Narrow elite-tool profile; lower-tier player with one elite indicator.

**Gate:**
- Tier is NOT APEX and NOT ELITE
- At least 1 present trait from: `{ maxEV >= 116, barrel >= 12, xslg >= 0.520, pullair >= 30 }`

*Recalibrated 2026-06-15: maxEV threshold lowered from 117 → 116.*
*Trait-count UPPER CAP REMOVED 2026-06-15 — bug fix: cap was preventing multi-indicator players from qualifying.*

---

## Naming History

| Old Name | Current Name | Reason |
|----------|-------------|--------|
| FOUNDATION | PRIME | Rename for clarity (commit `842946a`) |
| CEILING | EXPLOSIVE | Rename for clarity (commit `842946a`) |

No `foundation` or `ceiling` keys exist in production code.

---

## Invariants

- Roles must never feed back into model probability, tier ranking, or JIG scoring.
- Role filter on both boards uses AND logic (all selected roles must be present).
- Adding a new role requires explicit operator authorization + separate doctrine update.

---

## Cross-References

- [[tier-vocabulary]] — APEX/ELITE/EDGE/… tier definitions
- [[main-jig-separation]] — roles display on both boards but must not contaminate scoring
- [[known-gaps]] — latent gaps related to role calibration
