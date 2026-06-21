---
name: diagnosing-bugs
description: Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose"/"debug this", or reports something broken/throwing/failing/slow.
---

# Diagnosing Bugs → ROOT-CAUSE-INVESTIGATOR / LOOPS §1

**Authoritative source:** `AGENTS.md` → ROOT-CAUSE-INVESTIGATOR skill + LOOPS §1

Follow the evidence-before-fix gate: no red-capable command = no Phase 2.

## Preserved mechanics (reference alongside the authoritative procedure)

- **HITL loop:** last-resort human-in-the-loop bash script lives at `scripts/hitl-loop.template.sh`
- **Debug log tagging:** tag every debug log `[DEBUG-<unique-id>]` — cleanup = single grep on the prefix
- **Completion gate (Phase 1 must satisfy all four before proceeding):**
  - Red-capable — loop asserts the user's exact symptom, not just "didn't crash"
  - Deterministic — same verdict every run (flaky: pinned high-repro rate)
  - Fast — seconds, not minutes
  - Agent-runnable — no human in the loop except via `scripts/hitl-loop.template.sh`
- **Post-fix hand-off:** after fix, hand architectural gaps (missing test seams, hidden coupling) to `MLB-HR-ENGINE-ARCHITECT` per LOOPS §7
