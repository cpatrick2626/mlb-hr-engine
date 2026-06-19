---
name: production-auditor
description: "Use before any deploy or ship decision — validates that changes are tested, commit-before-deploy invariant holds, and no silent regression paths exist."
---

# /production-auditor

PURPOSE: Validate before ship; commit before deploy.

## PROCEDURE

Implements **Loop 2 — Validation Before Deploy** and **Loop 3 — Commit Before Deploy** — see LOOPS.md §2 and §3 for the authoritative steps, gates, and rules. Do not duplicate the procedure here.

## Trigger notes

- Run §2 before §3; §3 is the commit/push/deploy sequence.
- §3 deploy gate applies — see LOOPS.md §3.
