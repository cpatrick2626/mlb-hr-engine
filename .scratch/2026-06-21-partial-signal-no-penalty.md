# Under-Sampled Pitchers Float Into A/S Tier — Confidence Fallbacks Too Permissive

**Date:** 2026-06-21
**Status:** OPEN — operator decision required before any fix
**Boundary:** Scoring path. Do NOT implement without authorization.
**Prior title (incorrect):** "Partial-Signal Matchups Score Full-Confidence APEX" — premise was wrong; corrected below.

---

## Corrected Finding

Two independent fallback values in `confidence_score()` are too permissive. Under-sampled pitchers (<5 IP) and pitchers with missing handedness data can float into A or S tier with no cap and no flag. Arsenal absence is NOT the trigger — that was a misdiagnosis.

---

## What Was Wrong in the Original Finding

The original finding blamed `arsenal: []` as the confidence-inflation trigger. **That is incorrect.**

- Arsenal (pitch mix) feeds `model_prob` via `pit_factor` in `pipeline.py:189`. It is **not** an input to `confidence_score()`.
- `model_prob` (Poisson core) is clean regardless of arsenal presence.
- Cabrera (pitcher_id 703615) had both empty arsenal AND `pit_ip < 5`, which made them appear causally linked. They are not.

---

## Confirmed Mechanism

Two separate fallback branches in `engine/probability.py` fire when pitcher data is absent:

| Absent data | Code location | Fallback value | Effect |
|-------------|---------------|----------------|--------|
| `pit_ip < 5` (new/spot starter/reliever) | `probability.py:553` | `hr9_conf = 6.0` | Neutral midpoint, not penalized |
| Missing handedness | `probability.py:555` | `plat_conf = 4.0` | Neutral, not penalized |

`confidence_score()` sums these into the score that feeds `confidence_tier()`, which is the **primary sort key** in `rank_picks()` (`ranker.py:75`).

Tier thresholds (`ranker.py:28–33`):
- S ≥ 70
- A ≥ 55
- B ≥ 35

Nothing in the pipeline caps a no-data pitcher below S tier. A pick with hr9_conf=6.0 and plat_conf=4.0 contributing can clear A threshold without any real pitcher read.

---

## What Is NOT Affected

- `model_prob` (Poisson core) — arsenal only enters via `pit_factor`; correctly independent.
- `sc_conf = 0.0` on absent Statcast — already penalizing absence correctly.
- `barrel → 0` on absent Statcast — correct.
- Lineup-unconfirmed `−8` penalty — correct.

Do NOT touch any of these fallbacks.

---

## Fix Lever (Confirmed, No Collateral)

`probability.py:553` else-branch fires **only** on true absence (`pit_ip < 5`). Lowering `6.0 → ~2.0` affects only the missing-data path — zero impact on real-data pitchers.

Same for `:555`: `plat_conf 4.0 → ~1.5` affects only the missing-handedness path.

These match how the rest of `confidence_score()` already treats absence (penalize, not neutralize).

---

## Impact: UNMEASURED

No live slate available (latest 6/15). `full_slate_log.csv` lacks a `pitcher_hr9` column, so the historical frequency of this path firing cannot be sized from logs alone. **Measure against a live slate before choosing fix values.**

---

## Design Decision (Operator Call)

| Option | Tradeoff |
|--------|----------|
| Depress fallbacks: hr9 6→~2, plat 4→~1.5 | Matches existing absence-penalty pattern; calibration loop immediately benefits; scoring-path change |
| Flag + tier cap (max B/STRONG when fallback fires) | Hard gate; visible in output; calibration separates full vs partial reads |
| Leave and log | No output change; blind spot documented; calibration stays polluted |

**Operator recommendation:** depress. Matches the pattern already used for Statcast absence. Scoring-path change → deliberate, gated, requires calibration re-run after.

---

## Reproduction

Cabrera (pitcher_id 703615) vs Buxton. `arsenal: []` present but not the cause. The `pit_ip < 5` branch is what fired `hr9_conf = 6.0`.

---

## Do NOT Implement Reflexively

- Measure impact on a live slate first.
- Solve alongside JIG saturation finding (both are "confident score on thin data") — a single signal-completeness gate may address both.
- Validate calibration before/after.

**Linked:** 2026-06-21-jig-saturation.md, 2026-06-21-velo-signal-parked.md
