# Room Governance Doctrine

**Last Updated:** 2026-05-26

---

## Room Architecture

| Room | Name | Owns |
|------|------|------|
| 11 | STRATEGIC COMMUNICATIONS HUB | Planning, coordination, strategic discussion, roadmap, cross-room routing |
| 10 | AI WORKFORCE COMMAND | AI orchestration, governance, sequencing, stabilization locks, audit workflows, work-risk classification |
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

Cross-room coordination happens through Room 11 —
STRATEGIC COMMUNICATIONS HUB.

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
| HIGH | Touches engine/*, pipeline.py, calibration, MAIN model probability, scoring composites, MAIN/JIG separation, config.py, any closed surface | Audit-first → operator review → execution as separate authorized assignment |

HIGH risk work cannot be single-step. Ever.

---

## Cross-References

- [Session State Map](../architecture/session-state-map.md)
- [Cache Ownership Map](../architecture/cache-ownership-map.md)
- [Pipeline Data Flow](../architecture/pipeline-data-flow.md)
- [MAIN/JIG Separation Rules](main-jig-separation.md)
