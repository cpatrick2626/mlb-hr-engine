---
name: stats-engineer
description: "Use for statistical modeling decisions, Poisson HR probability construction, calibration methodology, Statcast/Savant data integrity, signal weight review, and sample-size constraints."
---

# /stats-engineer

PURPOSE: Domain lens for MLB HR probability modeling — Poisson construction, calibration, Statcast integrity, signal weights.

## LENS

This skill is a domain lens. Domain modeling judgment lives here:

- Core pipeline: `P(HR≥1) = 1 − e^(−λ)`. Lambda is a weighted composite of batter, pitcher, park, and environmental multipliers. Do not reorder without operator authorization.
- Signal weights live in `config.py`. Never duplicate into docs.
- No calibration or threshold changes from n<200 settled real picks.
- Never fabricate Statcast/Savant data. Graceful fallback when input is incomplete.
- Cross-check outputs against Baseball Reference, Savant, and Statcast before surfacing.

## Referenced constraint

Calibration runs on **deployed-state sample only** — not engine-qualified picks. Gate and rationale: LOOPS.md §5. Do not restate here.
