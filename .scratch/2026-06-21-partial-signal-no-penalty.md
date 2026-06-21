# Partial-Signal Matchups Score Full-Confidence APEX

**Date:** 2026-06-21
**Status:** OPEN — design decision required (operator call, do NOT decide reflexively)
**Boundary:** Touches scoring path — do not implement fix without operator authorization

---

## Finding

Arsenal-absent matchups emit full-confidence APEX tier with no flag or penalty. A 3-of-5-signal matchup is indistinguishable from a full read in output, and this pollutes the calibration loop.

## Reproduction

Cabrera (pitcher_id 703615) vs Buxton:
- `arsenal: []`, `pitch_stats: {}` — both empty
- Output: MODEL TIER APEX / 26.4% / +162

## Mechanism (traced)

1. **Signal 2 & 4** gate on `if pitcher_arsenal:` → skip to 0.0 when empty. `batter_vs_pitches` is only used inside Signal 2, so it drops too.
2. **Pitcher Matchup component** still awards points via neutral fallbacks:
   - `pitcher_hr9 = 0` → `hr9_conf = 6.0` (engine/probability.py:553)
   - `platoon_factor = 1.0` → `plat_conf = 4.0`
3. **`confidence_score()`** (engine/probability.py:478) never checks arsenal presence → no penalty, no flag.

Net: missing arsenal data is silently absorbed as neutral, not penalized.

## Data gap vs fetch bug

Cabrera's empty arsenal is a **legitimate data gap**, not a fetch bug. Fly logs confirmed: pitcher 703615 returned 0 rows for both 2026 and 2025 — no Savant record exists. The problem is the absence of a data-quality mechanism, not a retrieval failure.

## Why this matters

APEX-tier picks with thin data would skew calibration hit rates downward for APEX. Bet sizing against a polluted APEX pool overweights noisy picks.

## Design options (operator call)

| Option | Tradeoff |
|--------|----------|
| Confidence penalty in `confidence_score()` when signals < N | Lowers tier for partial reads; calibration still includes them |
| Data-quality badge (display only) | Visible to operator; calibration loop still polluted |
| Tier cap (e.g. max STRONG when arsenal absent) | Hard gate; calibration separates full vs partial reads |
| Exclude partial-signal matchups from deployment | Cleanest calibration; loses coverage for pitchers with no Savant record |

Implementation point: explicit arsenal-presence check in `confidence_score()` or `_compute_modifier()`.

## Do NOT implement reflexively

This is a scoring-boundary decision. All four options have calibration consequences. Solve together with the JIG saturation finding — both involve "confident score on thin data" — a single signal-completeness gate may address more than one. Validate before/after in the calibration loop.

**Linked:** 2026-06-21-jig-saturation.md, 2026-06-21-velo-signal-parked.md
