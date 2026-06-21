# JIG-001: JIG normalization saturation — power weights inert at elite tier

**Date:** 2026-06-21
**Status:** OPEN — design/calibration finding. NOT a bug. Do NOT patch yet.
**Boundary:** MAIN/JIG separation — formula-containment applies. No quick edits.
**Source:** live-formula verification (recompute + diff against served jigScore).

---

## What was verified (and is confirmed GOOD)

Live API runs the realigned `_jig_score` from `e4d19db`. Confirmed three ways:
- Weights in `api/main.py:284-291` match the realign (xSLG .25 / barrel .20 / xISO .15
  / pull_air .15 / hard_hit .15 / sweet_spot .10).
- `git log e4d19db..HEAD -- api/main.py` empty — no touches after realign.
- v52 image built from a tree containing `e4d19db`.
- Empirical: Alvarez recompute (base 83.91 + implied tactical +7.96) = served 91.87. MATCH.

Final form: `round(((base_score + hr_term) * stab + tactical) * 100, 2)`
- stab = pa/(pa+100); hr_term = min(hrpa/0.08, 1.0)*0.10
- tactical = arsenal(≤0.12) + pitch_dmg(≤0.06) + pitch_mix(≤0.04), max 0.22
  (live Statcast lookups, not in slate payload — accounts for recompute gap)

---

## The finding

The `_n()` normalization saturates to 1.0 **before** elite Statcast values, so among
elite power hitters all six base components clamp to 1.0 and `base_score` is identical
across them. The 60% power weighting cannot differentiate top targets — the thing it was
realigned to do.

Evidence (both APEX, both saturated):
- Alvarez: 13.3% barrel / .719 xSLG → all 6 components = 1.000
- Kurtz:    8.9% barrel / .464 xSLG → all 6 components = 1.000 (identical base_score)
- A 13% barrel and an 8.9% barrel produce the SAME base score.

Saturating centers/sigmas:
- barrel: center 5.0% / sigma 6.0 → ~8% already saturating; 13% far past ceiling
- xSLG:   center 0.40 / sigma 0.15 → saturates ~.55; half the APEX board is >.56

Consequence: at the elite tier, ranking is driven almost entirely by `hr_term` (a sliver)
and `tactical` signals. JIG is effectively a **tactical-signal ranker with a power gate**,
not a power-weighted index. Kurtz#1 > Alvarez#4 is legit *under the code as written*
(+2.35 tactical pts overcomes Alvarez's +1.21 power-term lead) — but that ordering is
tactical-driven, not power-driven.

---

## Why NOT to patch now

1. Unknown if tactical-as-primary-differentiator is actually wrong. Whether the current
   ranking is *good* is a calibration question — unanswerable until the capture loop feeds
   real outcomes. Loop is non-functional / deferred (N=4).
2. Widening sigmas to un-saturate is a scoring change that REQUIRES the feedback loop to
   validate. Changing the formula to fix a problem we can't yet measure reproduces the
   invalidated-calibration-finding trap.
3. MAIN/JIG boundary: any `_jig_score` change is formula-containment, deliberate only.

---

## Carry-forward action

- LOG, don't patch. Revisit when the capture loop can tell us whether the current elite-tier
  ranking has any demonstrable edge.
- When revisited: the lever is the `_n()` centers/sigmas (widen so elite values land mid-ramp,
  not clamped), NOT the weights — the weights are correct, the normalization undercuts them.
- Re-run recompute-and-diff verification after any sigma change to confirm power terms
  actually separate elite hitters before/after.

---

## Labels

`JIG` `calibration` `needs-triage` `formula-containment`
