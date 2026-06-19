---
name: root-cause-investigator
description: "Use when diagnosing any bug, failure, data loss, or unexpected behavior in MLB HR Engine — investigates cause before any fix is written, gates execution until root cause is confirmed with evidence."
---

# /root-cause-investigator

PURPOSE: Confirm true cause before writing any fix.

## PROCEDURE

Implements **Loop 1 — Root-Cause Investigation** — see LOOPS.md §1 for the authoritative steps, gates, and rules. Do not duplicate the procedure here.

## Trigger notes

- Fire before any code change when failure source is uncertain.
- Loop 1 gate (step 6) must clear before implementation begins — no exceptions.
- "Safe Production Engineer" rule (smallest safe fix, fewest files, preserve existing behavior) lives in §1; it is not a separate skill.
