# Room Governance Doctrine

**Last Updated:** 2026-06-08

---

## Room Architecture

| Room | Name | Owns |
|------|------|------|
| 11 | STRATEGIC COMMUNICATIONS HUB | Planning, coordination, strategic discussion, roadmap, cross-room routing |
| 10 | AI WORKFORCE COMMAND | AI orchestration, governance, sequencing, stabilization locks, audit workflows, work-risk classification, Obsidian governance enforcement |
| 08 | RUNTIME & STABILITY COMMAND | session_state, rerenders, routing, cache ownership, performance, validation, stabilization |
| 09 | JIG TACTICAL ENGINE | JIG Builder, aggressive filters, tactical stacks, arsenal hunting, high-volatility HR opportunities |
| 05 | LIVE DEPLOYMENT SYSTEMS | EV, odds, exposure, slips, bankroll, portfolio, deployment workflow, risk systems |

---

## Room Ownership Law

If a system belongs to another room:
- Discuss it there
- Implement it there
- Validate it there

Do not duplicate ownership across rooms.

Cross-room coordination happens through Room 11 -
STRATEGIC COMMUNICATIONS HUB.

Room 10 also owns AI workflow governance and durable project-memory enforcement.
When a session creates governance, architecture, stabilization, deployment,
scoring, or other durable project knowledge, Room 10 is responsible for making
sure the Obsidian vault is updated or explicitly reviewed for update need.

---

## Stabilization Lock Rule

Runtime stabilization overrides tactical refinement.

If RUNTIME & STABILITY COMMAND (Room 08) identifies:
- Rerender instability
- session_state corruption
- Routing instability
- Cache contamination

Then all tactical and UI work pauses until stabilization completes.
The lock applies across all rooms. No exceptions without operator
authorization.

---

## Work Risk Classification

| Class | Definition | Process |
|-------|-----------|---------|
| LOW | File moves, archival, doc edits, housekeeping, read-only audits, wiki writes | Single Claude Code pass, normal verification |
| MEDIUM | Single-file runtime edits, narrow scope | Single Claude Code pass, extra diff verification before commit |
| HIGH | Touches engine/*, pipeline.py, calibration, MAIN model probability, scoring composites, MAIN/JIG separation, config.py, any closed surface | Audit-first -> operator review -> execution as a separate authorized assignment |

HIGH risk work cannot be single-step. Ever.

---

## Obsidian Governance Enforcement

Obsidian is the formal long-term project memory system for MLB HR ENGINE.

Room 10 - AI WORKFORCE COMMAND is responsible for governance enforcement across:
- doctrine
- room governance
- architecture decisions
- stabilization history
- major bug decisions
- deployment changes
- formula and scoring decisions
- durable AI execution knowledge

When any of those surfaces change, the acting AI should explicitly evaluate
whether an Obsidian update is required before closing the assignment.

Standard packet language for Claude Code and Codex:

> If this task changes doctrine, architecture, runtime behavior, deployment behavior, scoring behavior, room governance, visual doctrine, or long-term project state, update the Obsidian vault before returning final completion.
>
> Vault path:
>
> C:\MLB HR Engine\mlb-hr-engine-master\MLB HR ENGINE
>
> Before writing:
> - inspect existing relevant notes
> - do not duplicate existing doctrine
> - update the correct note if one exists
> - create a new note only if needed
>
> Do not store:
> - secrets
> - API keys
> - .env values
> - private credentials

Governance command:
- `!obs` generates a copy-ready Obsidian update packet for doctrine changes,
  bug fixes, stabilization work, audits, implementation results, and governance updates.

---

## Cross-References

- [Session State Map](../architecture/session-state-map.md)
- [Cache Ownership Map](../architecture/cache-ownership-map.md)
- [Pipeline Data Flow](../architecture/pipeline-data-flow.md)
- [MAIN/JIG Separation Rules](main-jig-separation.md)
- [Obsidian Governance Doctrine](OBSIDIAN_GOVERNANCE_DOCTRINE.md)
