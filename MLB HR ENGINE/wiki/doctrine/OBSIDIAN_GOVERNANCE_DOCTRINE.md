# Obsidian Governance Doctrine

**Last Updated:** 2026-06-08

---

## Decision

Obsidian is the formal long-term project memory and governance system for MLB HR ENGINE.

The Obsidian vault is the canonical repository for:
- doctrine
- session logs
- architecture decisions
- reform briefs
- room governance
- implementation history
- stabilization history
- major bug decisions
- visual doctrine locks
- deployment changes
- formula and scoring decisions
- future roadmap notes

This doctrine applies to:
- GPT
- Claude
- Claude Code
- Codex
- future AI operators

Primary governance room:
- Room 10 - AI WORKFORCE COMMAND

---

## Mandatory Update Triggers

An Obsidian update must be considered when:
1. New doctrine is created or modified.
2. MAIN, JIG, or HVY rules are changed or clarified.
3. A protected surface is touched, audited, or reviewed.
4. Runtime or stabilization work completes.
5. A major bug is investigated, fixed, deferred, or escalated.
6. Production or deployment behavior changes.
7. Formula, threshold, calibration, scoring, or model behavior changes.
8. Visual doctrine becomes canonical.
9. A command is added, removed, or modified.
10. Room governance changes.
11. High-risk work is planned, audited, approved, or completed.
12. Claude Code or Codex execution produces durable project knowledge.
13. A session produces information future AI should know before acting.

---

## Required GPT Behavior

When an Obsidian update is required, GPT should explicitly state:

`OBSIDIAN UPDATE REQUIRED`

Then choose one of:
- Generate Obsidian update packet
- Add Obsidian update requirements to execution packet
- Ask operator whether update is warranted for minor changes

---

## Required Claude Code and Codex Packet Language

Include the following language in applicable execution packets:

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

---

## Recommended Vault Structure

- `wiki/sessions/` for session logs, reform briefs, and execution summaries
- `wiki/doctrine/` for doctrine, governance, and operating rules
- `wiki/architecture/` for ADRs, architecture decisions, and protected surface audits
- `wiki/rooms/` for room governance and room ownership
- `ops/` for deployment procedures and operational runbooks
- `index/` for doctrine maps and content indexes

These are organizational targets, not a mandate to duplicate existing content.

---

## Command

Command:
- `!obs`

Purpose:
- generate a copy-ready Obsidian update packet for decisions
- generate a copy-ready Obsidian update packet for doctrine changes
- generate a copy-ready Obsidian update packet for bug fixes
- generate a copy-ready Obsidian update packet for stabilization work
- generate a copy-ready Obsidian update packet for audits
- generate a copy-ready Obsidian update packet for implementation results
- generate a copy-ready Obsidian update packet for governance updates

Required output:
- target vault path
- suggested note location
- update type
- required content
- Claude Code and Codex instructions

---

## Rejected Alternatives

1. Store doctrine only in GPT project instructions.
   Rejected because doctrine becomes fragmented across chats.
2. Store governance only in `CLAUDE.md`.
   Rejected because historical decision tracking is lost.
3. Require manual operator tracking.
   Rejected due to scalability and continuity risks.

---

## Validation Basis

Validated against:
- `CLAUDE.md`
- `MASTER_TCC_DOCTRINE.md`
- `FULL_SLATE_UX_DOCTRINE.md`
- `AGENTS.md`
- Startup Grounding Report

No conflicts identified.

---

## Risks Remaining

- Existing historical decisions may not yet exist in the vault.
- Future agents may fail to update the vault unless governance is enforced.
- Duplicate doctrine notes may emerge without periodic cleanup.

---

## Next Actions

1. Create or update the doctrine note for Obsidian governance.
2. Add an index reference so the doctrine is discoverable.
3. Add Obsidian update language to future Claude Code and Codex execution packets.
4. Begin logging durable governance decisions into the vault going forward.

---

## Cross-References

- [Room Governance Doctrine](room-governance.md)
- [MAIN/JIG Separation Rules](main-jig-separation.md)
