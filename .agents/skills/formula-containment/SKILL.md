---
name: formula-containment
description: Use when touching model formulas, scoring math, thresholds, calibration, or derived rankings.
---

- Confirm repo root, branch, and git status before edits.
- Treat MAIN probability, JIG scoring, thresholds, calibration, and rank logic as protected.
- Do not alter formulas unless the request explicitly authorizes it.
- If a formula-adjacent change is required, isolate it from unrelated code.
- Report whether protected systems were touched: yes/no.
- Report files changed, validation run, and final git status.

