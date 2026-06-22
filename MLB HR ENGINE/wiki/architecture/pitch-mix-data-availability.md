# Pitch-Mix Data Availability — Arsenal Exploit Score Audit

## Summary

An Arsenal Exploit Score was proposed to quantify batter-vs-pitcher pitch-type matchup damage. A data-availability audit (2026-06-22) found that the score is buildable only in a reduced form with current data. The full barrel-based version is not feasible. The score is **PAUSED** pending a decision on the real production matchup-card/frontend surface. This note records what exists, what does not, and what any future build can honestly claim.

## What Pitch-Type Data Exists Today

| Data | Source | Notes |
|------|--------|-------|
| Pitcher arsenal usage | `clients/arsenal.py` → `get_pitcher_arsenal()` | `pitch_pct`, `rv_per100`, `whiff_pct`, `hard_hit_pct`, `pa` per pitch type |
| Batter SLG/ISO/HR-rate by pitch type | Statcast/Savant | Usable batter-vs-pitch-type damage splits |
| Pitcher allowed SLG/ISO/HR-rate by pitch type | Statcast/Savant | Usable pitcher-allowed-by-pitch-type damage splits |
| Handedness/split context | Pipeline profile fields | `batter_side`, `pitcher_hand`; switch-hitters resolved |
| PA / sample-size fields | `clients/arsenal.py` | `pa` per pitch type; required for reliability gates |

## What Pitch-Type Data Does NOT Exist Today

| Data | Status |
|------|--------|
| Per-pitch barrel% (batter side) | **NOT AVAILABLE** — no reliable pitch-type-level barrel% split for batters |
| Per-pitch xSLG (batter side) | **NOT AVAILABLE** — no reliable pitch-type-level xSLG split for batters |
| Per-pitch barrel% allowed (pitcher side) | **NOT AVAILABLE** |
| Per-pitch xSLG allowed (pitcher side) | **NOT AVAILABLE** |

Season-level barrel/contact-quality stats exist at the player level, but pitch-type-level barrel% and xSLG splits are not reliably available from any current client.

## What the Reduced Arsenal Exploit Score Can Honestly Measure

A reduced score is buildable using the data that does exist:

- SLG, ISO, and HR-rate by pitch type (batter damage profile per pitch type)
- Pitcher arsenal usage mix (`pitch_pct`) crossed against batter damage by pitch type
- Handedness context
- PA-gated reliability filtering

**Correct description:** A SLG/ISO/HR-rate-by-pitch-mix matchup score.

## What It Cannot Claim

- It is **NOT** a barrel-based contact-quality score.
- It cannot report per-pitch barrel% exploitation.
- It cannot report per-pitch xSLG exploitation.
- Do not label or describe any output from this score using "barrel%" or "contact quality" terminology.

## Null / None Handling Rule

Missing or null pitch-type values **must** be treated as neutral/league-average or marked **NO SIGNAL**. They must **never** be treated as zero. Treating a missing value as zero is the same failure class as the confidence-tier "C" bug — a missing value silently masquerades as a real low value and corrupts scoring.

Enforcement:
- Check `pa` field against a minimum sample threshold before using any pitch-type split.
- If a pitch type has `pa` below threshold or is null: emit NO SIGNAL, not 0.
- If a pitch type is entirely absent from the arsenal dict: treat as league-average, not 0.

## UI Surface Warning

The current likely display target is `app.py` / Streamlit. `app.py` is **not** the desired long-term production matchup-card surface. The operator has confirmed that `app.py` is a dead/legacy surface for this class of feature.

**Do not build Arsenal Exploit Score into `app.py`** unless the operator explicitly authorizes it later.

## Implementation Status

**NOT IMPLEMENTED — PAUSED**

The score has been designed at the concept level only. No scoring code, no pipeline integration, no UI integration exists. The pause is intentional pending resolution of the production matchup-card/frontend surface.

## Recommended Next Step

1. Decide and build the real production matchup-card/frontend surface (likely the Vercel board or Next.js frontend, not `app.py`).
2. Once that surface is established and its data contract is clear, revisit this note and scope the reduced Arsenal Exploit Score into it.
3. At that time: implement using SLG/ISO/HR-rate-by-pitch-mix data only; enforce PA reliability gates and null-as-no-signal rule; label output accurately (not as barrel-based).

## Cross-References

- [JIG Tactical Doctrine](../doctrine/jig-tactical-doctrine.md) — arsenal hunting, HVY pitch-mix signal, display-only invariants
- [Design: Pitch Mix Analysis](../doctrine/design-pitch-mix-analysis.md) — modal de-fabrication, real data sources
- [Known Gaps / Parked](../doctrine/known-gaps.md) — pitch mix blanks, dead app.py surface
- [Pipeline Data Flow](pipeline-data-flow.md) — canonical pipeline sequence
- [Feature Backlog](../ideas/feature-backlog.md) — build-later / parked items
