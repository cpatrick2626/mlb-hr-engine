---
name: mlb-hr-engine-architect
description: "Use for architecture reviews, ownership boundary checks, scope-creep prevention, and PM→Code handoff packet construction for MLB HR Engine work."
---

# /mlb-hr-engine-architect

PURPOSE: Architecture and impact review, ownership boundaries, scope-creep prevention, handoff packet structure.

## PROCEDURE

Implements **Loop 7 — Repository Hygiene** (path invariants, surface assignments) and **Loop 8 — PM → Claude Code Handoff** (packet structure, roles, scope gates) — see LOOPS.md §7 and §8 for the authoritative steps, gates, and rules. Do not duplicate the procedure here.

## Trigger notes

- Use when scoping new work: verify path invariants (§7) then assemble the execution packet (§8).
- §8 gate: Claude Code must not expand scope beyond the packet — scope questions go back to PM before execution begins.
- Protected surfaces (MAIN/JIG separation, session_state, cache, routing, config.py thresholds) must not be modified without operator authorization.
