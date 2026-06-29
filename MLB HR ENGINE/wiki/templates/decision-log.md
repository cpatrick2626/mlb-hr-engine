# Decision Log — Template

**Template version:** 1.0  
**Created:** 2026-06-29

---

## Summary

Reusable template for recording a single major decision. Create one file per decision. Use this whenever a change touches a protected surface, alters model parameters, modifies scoring logic, changes deployment config, or creates any state that an operator or future agent needs to understand or reverse.

**Naming convention:** `decision-YYYY-MM-DD-short-title.md` — stored in `wiki/sessions/` or alongside the relevant session log.

---

## Decision

<!-- State what was decided, as a fact. Not options considered — the chosen path. -->

## Why

<!-- The forcing function: bug, user feedback, doctrine conflict, performance data, operator instruction, etc. One paragraph maximum. -->

## Files Affected

<!-- List every file path this decision changes or depends on. -->

## Risk

**Level:** LOW / MEDIUM / HIGH

<!-- Why this risk level. What could go wrong if the decision is wrong or the change is reverted poorly. -->

## Validation Needed

<!-- How to verify this decision worked. Specific commands, checks, or observable outcomes. -->

## Rollback Plan

<!-- Exact steps to undo. If rollback is not possible or would require data recovery, say so explicitly. -->

## Status

**Current:** PROPOSED / APPROVED / SHIPPED / REVERTED

<!-- 
- PROPOSED: decision identified, not yet implemented  
- APPROVED: operator has authorized proceeding  
- SHIPPED: change implemented and validated  
- REVERTED: change was undone; note what failed  
-->

<!-- If SHIPPED: include commit hash -->
<!-- If REVERTED: include what failed and what the recovery action was -->
