---
name: data-integrity-auditor
description: "Use when auditing write/persistence paths, verifying capture completeness, checking calibration sample validity, hunting silent failures, or running bare-except audits on production MLB HR Engine code."
---

# /data-integrity-auditor

PURPOSE: Verify persistence paths fail loudly and captured data is the intended data.

## PROCEDURE

Implements **Loop 4 — Production Error Sweep** and **Loop 5 — Data Integrity / Capture** — see LOOPS.md §4 and §5 for the authoritative steps, gates, and rules. Do not duplicate the procedure here.

## Trigger notes

- §4 HIGH-severity gate applies to all write paths — see LOOPS.md §4.
- §5 calibration gate applies before any calibration run — see LOOPS.md §5.
